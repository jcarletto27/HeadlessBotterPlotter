import os
import glob
import configparser
import vtracer
import re
from xml.etree import ElementTree
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces

# --- Configuration ---
INPUT_FOLDER = "plotter_attachments"
OUTPUT_FOLDER = "plotter_gcode"
SVG_OUTPUT_FOLDER = "plotter_svgs" # For saving the intermediate SVGs
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
            content = f.read().splitlines()
            print(f"✅ Loaded '{filename}'")
            return content
    print(f"ℹ️  '{filename}' not found, proceeding without it.")
    return []

def get_svg_dimensions(svg_file):
    """Parses an SVG file to get its width and height."""
    tree = ElementTree.parse(svg_file)
    root = tree.getroot()
    width_str = root.get('width')
    height_str = root.get('height')
    
    # Use regex to extract numerical values from strings like "210mm" or "100px"
    width = float(re.findall(r"[\d\.]+", width_str)[0])
    height = float(re.findall(r"[\d\.]+", height_str)[0])
    
    return width, height

def scale_svg_file(svg_path, scale_factor):
    """Wraps all drawing elements in an SVG file with a <g> tag to apply a uniform scale."""
    if scale_factor == 1.0:
        return # No scaling needed

    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
    
    tree = ElementTree.parse(svg_path)
    root = tree.getroot()

    children_to_wrap = list(root)
    g_element = ElementTree.Element("g", attrib={"transform": f"scale({scale_factor})"})
    
    for child in children_to_wrap:
        root.remove(child)
        g_element.append(child)
    
    root.append(g_element)
    tree.write(svg_path)

def process_image_to_gcode(image_path, output_folder, svg_folder, config):
    """
    Processes a single image file to a G-code file.
    Returns the path to the generated G-code file.
    """
    base_filename = os.path.basename(image_path)
    filename_no_ext = os.path.splitext(base_filename)[0]
    
    svg_path = os.path.join(svg_folder, f"{filename_no_ext}.svg")
    gcode_path = os.path.join(output_folder, f"{filename_no_ext}.gcode")

    # 1. Convert the image file directly to an SVG file.
    vtracer.convert_image_to_svg_py(image_path, svg_path)
    print(f"  💾 Saved traced SVG to '{svg_path}'")

    # 2. Get drawing dimensions from the SVG file.
    drawing_width, drawing_height = get_svg_dimensions(svg_path)

    # 3. Determine the scale factor to fit within the plotter's boundaries.
    plot_width = float(config['max_plot_x']) - float(config['min_plot_x'])
    plot_height = float(config['max_plot_y']) - float(config['min_plot_y'])
    
    scale_factor = 1.0
    if drawing_width > plot_width or drawing_height > plot_height:
        scale_x = plot_width / drawing_width if drawing_width > 0 else 1
        scale_y = plot_height / drawing_height if drawing_height > 0 else 1
        scale_factor = min(scale_x, scale_y)
        print(f"  - Scaling down by a factor of {scale_factor:.3f}")
        scale_svg_file(svg_path, scale_factor)

    # 4. Initialize the G-code compiler with the custom plotter interface.
    compiler = Compiler(
        interface_class=PlotterGcodeInterface,
        movement_speed=float(config['pen_feed_rate_mm_min']),
        cutting_speed=float(config['pen_feed_rate_mm_min']),
        pass_depth=float(config['pen_down_position_mm'])
    )
    
    compiler.interface.safe_z = float(config['pen_travel_position_mm'])
    compiler.interface.plunge_depth = float(config['pen_down_position_mm'])

    compiler.header = load_gcode_file(PREAMBLE_FILE)
    compiler.footer = load_gcode_file(POSTAMBLE_FILE)

    # 5. Parse the (now possibly scaled) SVG file and compile to G-code.
    curves = parse_file(svg_path)
    compiler.append_curves(curves)
    compiler.compile_to_file(gcode_path, passes=1)
    
    return gcode_path

def main():
    """Main execution function."""
    config = load_config(CONFIG_FILE)

    for folder in [OUTPUT_FOLDER, SVG_OUTPUT_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)

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
            output_path = process_image_to_gcode(image_path, OUTPUT_FOLDER, SVG_OUTPUT_FOLDER, config)
            print(f"  ✅ Successfully converted to '{os.path.basename(output_path)}'")
        except Exception as e:
            print(f"❌ Failed to convert {os.path.basename(image_path)}: {e}")

if __name__ == "__main__":
    main()
