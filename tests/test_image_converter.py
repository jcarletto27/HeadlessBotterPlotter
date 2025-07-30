import unittest
from unittest.mock import patch, MagicMock
import os
import configparser

# Import the function to be tested from the main script
from image_to_gcode_converter import process_image_to_gcode

class TestImageToGcodeConverter(unittest.TestCase):

    def setUp(self):
        """Set up a dummy config file and a test image for each test."""
        self.config_filename = "test_config.ini"
        self.image_filename = "test_image.png"

        # Create a dummy config file
        config = configparser.ConfigParser()
        config['GCodeSettings'] = {
            'pen_down_position_mm': '0',
            'pen_travel_position_mm': '5',
            'pen_feed_rate_mm_min': '1000',
        }
        with open(self.config_filename, 'w') as f:
            config.write(f)
        
        self.config = config['GCodeSettings']

        # Create a dummy image file if it doesn't exist
        if not os.path.exists(self.image_filename):
            try:
                from PIL import Image
                Image.new('RGB', (10, 10), color='red').save(self.image_filename)
            except ImportError:
                raise FileNotFoundError(
                    f"Please create a dummy '{self.image_filename}' file or install Pillow (`pip install Pillow`) to run this test."
                )

    def tearDown(self):
        """Clean up any files created during the test."""
        if os.path.exists(self.config_filename):
            os.remove(self.config_filename)
        if os.path.exists(self.image_filename):
            os.remove(self.image_filename)

    # Patch all external dependencies and file system interactions
    @patch('image_to_gcode_converter.vtracer')
    @patch('image_to_gcode_converter.parse_file')
    @patch('image_to_gcode_converter.Compiler')
    @patch('image_to_gcode_converter.tempfile.NamedTemporaryFile')
    @patch('os.remove')
    @patch('os.path.exists')
    def test_process_image_to_gcode(self, mock_os_path_exists, mock_os_remove, MockNamedTemporaryFile, MockCompiler, mock_parse_file, mock_vtracer):
        """
        Tests the core image processing logic by mocking external libraries and file I/O.
        """
        # --- 1. Setup Mocks ---

        # Mock os.path.exists to return True so that os.remove is called for the temp file
        mock_os_path_exists.return_value = True

        # Mock the vtracer call to return a fake SVG string
        mock_vtracer.trace.return_value = "<svg>...</svg>"

        # Mock the temporary file creation process
        mock_file_handle = MagicMock()
        mock_file_handle.name = "dummy_temp_file.svg"
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_file_handle
        MockNamedTemporaryFile.return_value = mock_context_manager

        # Mock the parse_file call to return fake curve data
        mock_parse_file.return_value = "mocked_curves"

        # Mock the Compiler instance to check its methods
        mock_compiler_instance = MockCompiler.return_value

        # --- 2. Call the function under test ---
        output_folder = "test_output"
        result_path = process_image_to_gcode(self.image_filename, output_folder, self.config)

        # --- 3. Assertions ---

        # Assert that the function returns the correct output path
        self.assertEqual(result_path, os.path.join(output_folder, "test_image.gcode"))

        # Assert that vtracer was called correctly
        mock_vtracer.trace.assert_called_once_with(self.image_filename, colormode='binary')

        # Assert that a temporary file was created and written to
        MockNamedTemporaryFile.assert_called_once_with(mode='w', suffix='.svg', delete=False, encoding='utf-8')
        mock_file_handle.write.assert_called_once_with("<svg>...</svg>")

        # Assert that parse_file was called with the temp file's path
        mock_parse_file.assert_called_once_with("dummy_temp_file.svg")

        # Assert that the Compiler was initialized correctly
        MockCompiler.assert_called_once_with(interface=unittest.mock.ANY,
                                             movement_speed=1000.0,
                                             cutting_speed=1000.0,
                                             pass_depth=0.0)

        # Assert that the compiler's methods were called in order
        mock_compiler_instance.append_curves.assert_called_once_with("mocked_curves")
        mock_compiler_instance.compile_to_file.assert_called_once_with(os.path.join(output_folder, "test_image.gcode"), passes=2)

        # Assert that os.path.exists was called to check for the temp file
        mock_os_path_exists.assert_called_once_with("dummy_temp_file.svg")

        # Assert that the temporary file was cleaned up
        mock_os_remove.assert_called_once_with("dummy_temp_file.svg")

if __name__ == '__main__':
    # This allows you to run the tests by executing `python test_image_converter.py`
    unittest.main()
