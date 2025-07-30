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

# --- Core Functions ---

def create_default_config(filename):
    """Creates a default config.ini file if one doesn't exist."""
    config = configparser.ConfigParser()
    config['GCodeSettings'] = {
        'pen_down_position_mm': '0',
        'pen_travel_position_mm': '5',
        'pen_feed_rate_mm_min': '1000',
        'max_plot_x': '210',
        'min_plot_x': '30',import os
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
        
        def create_default_config(filename):
            """Creates a default config.ini file if one doesn't exist."""
            config = configparser.ConfigParser()
            config['GCodeSettings'] = {
                'pen_down_position_mm': '0',
                'pen_travel_position_mm': '5',
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
            """Reads a G-code file and returns its content, or an empty string if not found."""
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    content = f.read()
                    print(f"✅ Loaded '{filename}'")
                    return content
            print(f"ℹ️  '{filename}' not found, proceeding without it.")
            return ""
        
        def process_image_to_gcode(image_path, output_folder, config):
            """
            Processes a single image file to a G-code file. This is the core testable logic.
            Returns the path to the generated G-code file.
            """
            # 1. Read the image file into bytes
            with open(image_path, 'rb') as f:
                input_img_bytes = f.read()
        
            # Get the image format (e.g., 'png', 'jpg') from the file extension
            img_format = os.path.splitext(image_path)[1].lstrip('.').lower()
            
            # 2. Convert the raw image bytes to an SVG string using the correct function
            svg_str = vtracer.convert_raw_image_to_svg(input_img_bytes, img_format=img_format, colormode='binary')
        
            # 3. Instantiate a compiler, providing the required interface_class and safe_z arguments.
            compiler = Compiler(interface_class=interfaces.Gcode,
                                movement_speed=float(config['pen_feed_rate_mm_min']),
                                cutting_speed=float(config['pen_feed_rate_mm_min']),
                                pass_depth=float(config['pen_down_position_mm']),
                                safe_z=float(config['pen_travel_position_mm']))
            
            # 4. Set the preamble and postamble from external files
            compiler.header = load_gcode_file(PREAMBLE_FILE)
            compiler.footer = load_gcode_file(POSTAMBLE_FILE)
        
            # 5. Save the SVG string to a temporary file to be parsed
            tmp_svg_file = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as f:
                    f.write(svg_str)
                    tmp_svg_file = f.name
        
                # 6. Parse the svg file into geometric curves.
                curves = parse_file(tmp_svg_file)
                compiler.append_curves(curves)
        
                # 7. Compile the G-code to a file
                filename = os.path.basename(image_path)
                output_filename = os.path.splitext(filename)[0] + ".gcode"
                output_path = os.path.join(output_folder, output_filename)
                compiler.compile_to_file(output_path, passes=2)
                
                return output_path
            finally:
                # 8. Clean up the temporary file
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
        
        'max_plot_y': '275',
        'min_plot_y': '30',
        'usb_port': '/dev/ttyAMA10',
        'baud_rate': '115200',
    }
    with open(filename, 'w') as configfile:
        config.write(configfile)import os
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
        
        # --- Core Functions ---
        
        def create_default_config(filename):
            """Creates a default config.ini file if one doesn't exist."""
            config = configparser.ConfigParser()
            config['GCodeSettings'] = {
                'pen_down_position_mm': '0',
                'pen_travel_position_mm': '5',
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
        
        def process_image_to_gcode(image_path, output_folder, config):
            """
            Processes a single image file to a G-code file. This is the core testable logic.
            Returns the path to the generated G-code file.
            """
            # 1. Read the image file into bytes
            with open(image_path, 'rb') as f:
                input_img_bytes = f.read()
        
            # Get the image format (e.g., 'png', 'jpg') from the file extension
            img_format = os.path.splitext(image_path)[1].lstrip('.').lower()
            
            # 2. Convert the raw image bytes to an SVG string using the correct function
            svg_str = vtracer.convert_raw_image_to_svg(input_img_bytes, img_format=img_format, colormode='binary')
        
            # 3. Instantiate a compiler, providing the required interface_class and safe_z arguments.
            compiler = Compiler(interface_class=interfaces.Gcode,
                                movement_speed=float(config['pen_feed_rate_mm_min']),
                                cutting_speed=float(config['pen_feed_rate_mm_min']),
                                pass_depth=float(config['pen_down_position_mm']),
                                safe_z=float(config['pen_travel_position_mm']))
        
            # 4. Save the SVG string to a temporary file to be parsed
            tmp_svg_file = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as f:
                    f.write(svg_str)
                    tmp_svg_file = f.name
        
                # 5. Parse the svg file into geometric curves.
                curves = parse_file(tmp_svg_file)
                compiler.append_curves(curves)
        
                # 6. Compile the G-code to a file
                filename = os.path.basename(image_path)
                output_filename = os.path.splitext(filename)[0] + ".gcode"
                output_path = os.path.join(output_folder, output_filename)
                compiler.compile_to_file(output_path, passes=2)
                
                return output_path
            finally:
                # 7. Clean up the temporary file
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
        
    print(f"✅ Created default configuration file: '{filename}'")

def load_config(filename):
    """Loads settings from the config.ini file."""
    if not os.path.exists(filename):
        create_default_config(filename)
    
    config = configparser.ConfigParser()
    config.read(filename)
    return config['GCodeSettings']

def process_image_to_gcode(image_path, output_folder, config):
    """
    Processes a single image file to a G-code file. This is the core testable logic.
    Returns the path to the generated G-code file.
    """
    # 1. Read the image file into bytes
    with open(image_path, 'rb') as f:
        input_img_bytes = f.read()

    # Get the image format (e.g., 'png', 'jpg') from the file extension
    img_format = os.path.splitext(image_path)[1].lstrip('.').lower()
    
    # 2. Convert the raw image bytes to an SVG string using the correct function
    svg_str = vtracer.convert_raw_image_to_svg(input_img_bytes, img_format=img_format, colormode='binary')

    # 3. Instantiate a compiler, providing the required interface_class argument.
    compiler = Compiler(interface_class=interfaces.Gcode,
                        movement_speed=float(config['pen_feed_rate_mm_min']),
                        cutting_speed=float(config['pen_feed_rate_mm_min']),
                        pass_depth=float(config['pen_down_position_mm']))

    # 4. Save the SVG string to a temporary file to be parsed
    tmp_svg_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as f:
            f.write(svg_str)
            tmp_svg_file = f.name

        # 5. Parse the svg file into geometric curves.
        curves = parse_file(tmp_svg_file)
        compiler.append_curves(curves)

        # 6. Compile the G-code to a file
        filename = os.path.basename(image_path)
        output_filename = os.path.splitext(filename)[0] + ".gcode"
        output_path = os.path.join(output_folder, output_filename)
        compiler.compile_to_file(output_path, passes=2)
        
        return output_path
    finally:
        # 7. Clean up the temporary file
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
