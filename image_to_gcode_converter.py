import os
import glob
import configparser
import vtracer
import tempfile
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces

# --- Configuration ---
INPUT_FOLDER = "plotter_attachments"
OUTPUT_FOLDER = "plotter_gcode"
CONFIG_FILE = "config.ini"
PREAMBLE_FILE = "preamble.gcode"
POSTAMBLE_FILE = "postamble.gcode"

# --- Core Functions ---

class PlotterGcodeInterface(interfaces.Gcode):
    """
    Custom G-code interface for a plotter that uses the Z-axis to lift and lower a tool.
    This interface explicitly removes M3/M4/M5 commands.
    """
    def __init__(self):
        super().__init__()
        # Default values, will be overwritten by config settings
        self.safe_z = 1.0
        self.plunge_depth = -5.0

    def laser_off(self):
        # Overridden to lift the tool to a safe Z height instead of using M5.
        return f"G0 Z{self.safe_z:.2f}"

    def laser_on(self, power):
        # Overridden to plunge the tool to the cutting depth instead of using M3/M4.
        # Power is ignored, but the argument is required by the library.
        return f"G1 Z{self.plunge_depth:.2f}"

    def set_laser_power(self, power):
        # Overridden to do nothing, preventing any M3/M4 S-value commands.
        return ""

    def linear_move(self, x, y):
        # Overridden to include the Z-axis value on every G1 move.
        # This ensures the tool stays at the correct depth during cutting.
        return f"G1 X{x:.3f} Y{y:.3f} Z{self.plunge_depth:.2f}"

def create_default_config(filename):
    """Creates a default config.ini file if one doesn't exist."""
    config = configparser.ConfigParser()
    config['GCodeSettings'] = {
        'pen_down_position_mm': '-10',
        'pen_travel_position_mm': '1',
        'pen_feed_rate_mm_min': '1000',
        'max_plot_x': '210',
        'min_plot_x': '30',
        'max_plot_y': '275',
        'min_plot_y': '30',
        'usb_port': '/dev/ttyAMA10',
        'baud_rate': '115200',
    }
    with open(filename, 'w') as configfile:
        config.write(configfile)
    print(f"✅ Created default configuration file: '{filename}'")

def load_config(filename):
    """Loads settings from the config.ini file."""
    if not os.path.exists(filename):
        create_default_config(filename)
    
    config = configparser.ConfigParser()
    config.read(filename)
    return config['GCodeSettings']

def load_gcode_file(filename):
    """Reads a G-code file and returns its content as a list of lines."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            # Split content into a list of lines to prevent character-by-character iteration
            content = f.read().splitlines()
            print(f"✅ Loaded '{filename}'")
            return content
    print(f"ℹ️  '{filename}' not found, proceeding without it.")
    return [] # Return an empty list if file not found

def _get_points(curve):
    """A helper function to get all vector points from any curve object."""
    points = []
    for attr in ['start', 'end', 'control1', 'control2', 'center']:
        if hasattr(curve, attr) and getattr(curve, attr) is not None:
            points.append(getattr(curve, attr))
    return points

def _calculate_bounds(curves):
    """Manually calculates the bounding box for a list of curve objects."""
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    if not curves:
        return (0, 0), (0, 0)

    for curve in curves:
        for p in _get_points(curve):
            min_x = min(min_x, p.x)
            min_y = min(min_y, p.y)
            max_x = max(max_x, p.x)
            max_y = max(max_y, p.y)

    return (min_x, min_y), (max_x, max_y)

def _manual_transform(curves, scale=1.0, dx=0, dy=0):
    """Manually scales and translates a list of curve objects."""
    for curve in curves:
        for p in _get_points(curve):
            p.x = p.x * scale + dx
            p.y = p.y * scale + dy

def process_image_to_gcode(image_path, output_folder, config):
    """
    Processes a single image file to a G-code file. This is the core testable logic.
    Returns the path to the generated G-code file.
    """
    # 1. Read the image file into bytes
    with open(image_path, 'rb') as f:
        input_img_bytes = f.read()

    # Get the image format
    img_format = os.path.splitext(image_path)[1].lstrip('.').lower()
    
    # 2. Convert the raw image bytes to an SVG string
    svg_str = vtracer.convert_raw_image_to_svg(input_img_bytes, img_format=img_format, colormode='binary')

    # 3. Instantiate a compiler with the custom plotter interface
    compiler = Compiler(interface_class=PlotterGcodeInterface,
                        movement_speed=float(config['pen_feed_rate_mm_min']),
                        cutting_speed=float(config['pen_feed_rate_mm_min']))
    
    # 4. Set the safe_z and plunge_depth on the interface from the config file
    compiler.interface.safe_z = float(config['pen_travel_position_mm'])
    compiler.interface.plunge_depth = float(config['pen_down_position_mm'])
    
    # 5. Set preamble and postamble
    compiler.header = load_gcode_file(PREAMBLE_FILE)
    compiler.footer = load_gcode_file(POSTAMBLE_FILE)

    # 6. Save SVG to a temporary file to be parsed
    tmp_svg_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as f:
            f.write(svg_str)
            tmp_svg_file = f.name

        # 7. Parse the svg file into geometric curves
        curves = parse_file(tmp_svg_file)
        
        # 8. Manually scale and center the drawing
        (min_cx, min_cy), (max_cx, max_cy) = _calculate_bounds(curves)
        drawing_width = max_cx - min_cx
        drawing_height = max_cy - min_cy

        plot_width = float(config['max_plot_x']) - float(config['min_plot_x'])
        plot_height = float(config['max_plot_y']) - float(config['min_plot_y'])

        if drawing_width == 0 or drawing_height == 0:
            scale_factor = 1.0
        else:
            scale_factor = min(plot_width / drawing_width, plot_height / drawing_height)

        # First, translate the drawing so its top-left corner is at the origin (0,0)
        _manual_transform(curves, dx=-min_cx, dy=-min_cy)
        
        # Next, scale the drawing
        _manual_transform(curves, scale=scale_factor)

        # Finally, translate the scaled drawing to the center of the plot area
        plot_center_x = float(config['min_plot_x']) + plot_width / 2
        plot_center_y = float(config['min_plot_y']) + plot_height / 2
        
        (scaled_min_cx, scaled_min_cy), (scaled_max_cx, scaled_max_cy) = _calculate_bounds(curves)
        scaled_center_x = scaled_min_cx + (scaled_max_cx - scaled_min_cx) / 2
        scaled_center_y = scaled_min_cy + (scaled_max_cy - scaled_min_cy) / 2
        
        _manual_transform(curves, dx=(plot_center_x - scaled_center_x), dy=(plot_center_y - scaled_center_y))

        # 9. Append the transformed curves and compile to a G-code file
        compiler.append_curves(curves)
        filename = os.path.basename(image_path)
        output_filename = os.path.splitext(filename)[0] + ".gcode"
        output_path = os.path.join(output_folder, output_filename)
        compiler.compile_to_file(output_path, passes=2)
        
        return output_path
    finally:
        # 10. Clean up the temporary file
        if tmp_svg_file and os.path.exists(tmp_svg_file):
            os.remove(tmp_svg_file)


def main():
    """Main execution function."""
    config = load_config(CONFIG_FILE)

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    image_files = glob.glob(os.path.join(INPUT_FOLDER, "*.png")) + \
                  glob.glob(os.path.join(INPUT_FOLDER, "*.jpg")) + \
                  glob.glob(os.path.join(INPUT_FOLDER, "*.jpeg"))

    if not image_files:
        print("No new images to convert.")
        return

    print(f"Found {len(image_files)} images to convert to G-code.")
    
    for image_path in image_files:
        try:
            print(f"Processing '{os.path.basename(image_path)}'...")
            output_path = process_image_to_gcode(image_path, OUTPUT_FOLDER, config)
            print(f"  ✅ Successfully converted to '{os.path.basename(output_path)}'")
        except Exception as e:
            print(f"❌ Failed to convert {os.path.basename(image_path)}: {e}")

if __name__ == "__main__":
    main()
