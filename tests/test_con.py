# Import necessary libraries
import vtracer
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
import re
from xml.etree import ElementTree

# Define input and output file names
input_file = "image.png"
output_file = "drawing.svg"
gcode_file = "drawing.gcode"

# --- Stage 1: Convert PNG image to SVG vector file ---
try:
    # Use vtracer to convert the image file directly to an SVG file.
    vtracer.convert_image_to_svg_py(input_file, output_file)

    print(f"✅ Successfully converted '{input_file}' to '{output_file}'")

except FileNotFoundError:
    print(f"❌ Error: The input file '{input_file}' was not found.")
except Exception as e:
    print(f"An error occurred during SVG conversion: {e}")


# --- Stage 2: Convert SVG vector file to G-code with scaling ---

# For a plotter, we need to override the default G-code commands (M3/M5)
# to use Z-axis movements for 'tool on' and 'tool off'.
class PlotterGcodeInterface(interfaces.Gcode):
    """
    Custom G-code interface for a plotter that uses the Z-axis to lift and lower a tool.
    This interface explicitly removes M3/M4/M5 commands.
    """
    def __init__(self):
        super().__init__()
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

def get_svg_dimensions(svg_file):
    """
    Parses an SVG file to get its width and height in mm.
    """
    tree = ElementTree.parse(svg_file)
    root = tree.getroot()
    width_str = root.get('width')
    height_str = root.get('height')
    
    # Use regex to extract numerical values from strings like "210mm" or "100px"
    width = float(re.findall(r"[\d\.]+", width_str)[0])
    height = float(re.findall(r"[\d\.]+", height_str)[0])
    
    return width, height

def scale_svg_file(svg_path, scale_factor):
    """
    Wraps all drawing elements in an SVG file with a <g> tag to apply a uniform scale.
    This modifies the SVG file in place.
    """
    if scale_factor == 1.0:
        return # No scaling needed

    # Register the SVG namespace to avoid 'ns0:' prefixes in the output
    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
    
    tree = ElementTree.parse(svg_path)
    root = tree.getroot()

    # Copy all direct children of the root element
    children_to_wrap = list(root)

    # Create the new <g> element with the scale transform
    g_element = ElementTree.Element("g", attrib={"transform": f"scale({scale_factor})"})
    
    # Move all original children into the new <g> element
    for child in children_to_wrap:
        root.remove(child)
        g_element.append(child)
    
    # Append the new <g> element (which now contains all original children) to the root
    root.append(g_element)

    # Write the modified tree back to the file
    tree.write(svg_path)

try:
    # Get drawing dimensions directly from the SVG file attributes.
    drawing_width, drawing_height = get_svg_dimensions(output_file)
    print(f"Detected drawing dimensions: {drawing_width:.2f}mm x {drawing_height:.2f}mm")

    # Determine the scale factor to fit within a 100x100mm area
    scale_factor = 1.0
    if drawing_width > 100 or drawing_height > 100:
        scale_x = 100 / drawing_width if drawing_width > 0 else 1
        scale_y = 100 / drawing_height if drawing_height > 0 else 1
        scale_factor = min(scale_x, scale_y) # Use smaller factor to maintain aspect ratio
        print(f"Scaling down by a factor of {scale_factor:.3f}")

    # If scaling is needed, modify the SVG file itself before parsing for g-code
    if scale_factor != 1.0:
        scale_svg_file(output_file, scale_factor)

    # Initialize the G-code compiler with the custom plotter interface.
    gcode_compiler = Compiler(
        interface_class=PlotterGcodeInterface,
        movement_speed=1000,
        cutting_speed=300,
        pass_depth=5 
    )

    # Parse the (now possibly scaled) SVG file to get the geometric curves
    curves = parse_file(output_file)
    
    # Add the curves to the compiler
    gcode_compiler.append_curves(curves)

    # Compile the curves into a G-code file.
    gcode_compiler.compile_to_file(gcode_file, passes=1)
    
    print(f"✅ Successfully compiled '{output_file}' to '{gcode_file}' with scaling and Z-axis commands.")

except FileNotFoundError:
    print(f"❌ Error: The SVG file '{output_file}' was not found. Make sure the first stage was successful.")
except Exception as e:
    print(f"An error occurred during G-code compilation: {e}")
