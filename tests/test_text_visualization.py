import os
import shutil
import unittest
from pathlib import Path

from dianna.visualization.text import highlight_text


class Example1:
    original_text = 'Doloremque aliquam totam ut. Aspernatur repellendus autem quia deleniti. Natus accusamus ' \
                    'doloribus et in quam officiis veniam et. '
    explanation = [('ut', 25, -0.06405025896517044),
                   ('in', 102, -0.05127647027074053),
                   ('et', 99, 0.02254588506724936),
                   ('quia', 58, -0.0008216335740370412),
                   ('aliquam', 11, -0.0006268298968242725),
                   ('Natus', 73, -0.0005556223616156406),
                   ('totam', 19, -0.0005126140261410219),
                   ('veniam', 119, -0.0005058379023790869),
                   ('quam', 105, -0.0004573258796550468),
                   ('repellendus', 40, -0.0003253862469633824)]


class Example2:
    expected_html = ''  # Figure out what should be the output first
    original_text = 'Such a bad movie.'
    explanation = [('bad', 7, -0.4922624307995777),
                   ('such', 0, 0.04637815000309109),
                   ('movie', 11, -0.03648111256069627),
                   ('a', 5, 0.008377155657765745)]


class MyTestCase(unittest.TestCase):
    temp_folder = 'temp_text_visualization_test'
    html_file_path = str(Path(temp_folder) / 'output.html')

    def test_text_visualization_no_output(self):
        highlight_text(Example1.explanation, original_data=Example1.original_text)

        assert not Path(self.html_file_path).exists()

    def test_text_visualization_html_output_exists(self):
        highlight_text(Example1.explanation, original_data=Example1.original_text,
                       output_html_filename=self.html_file_path)

        assert Path(self.html_file_path).exists()

    def test_text_visualization_html_output_contains_text(self):
        highlight_text(Example1.explanation, original_data=Example1.original_text,
                       output_html_filename=self.html_file_path)

        assert Path(self.html_file_path).exists()

        with open(self.html_file_path) as result_file:
            result = result_file.read()
        for word in Example1.original_text.split(' '):
            assert word in result

    def test_text_visualization_html_output_is_correct(self):
        highlight_text(Example2.explanation, original_data=Example2.original_text,
                       output_html_filename=self.html_file_path)

        assert Path(self.html_file_path).exists()

        with open(self.html_file_path) as result_file:
            result = result_file.read()
        assert result == Example2.expected_html

    def setUp(self) -> None:
        os.mkdir(self.temp_folder)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_folder, ignore_errors=True)
