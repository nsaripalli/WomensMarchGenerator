import unittest

from visual_meme_generator import *


class PosterGenerationTests(unittest.TestCase):
    def test_update_src(self):
        """This test does two things. First it verifies the image output by comparing its file size by a
        previously generated image size. Second it verifies that the caching layer is working by repeatedly running
         requests. If the test is taking a while to run then the caching layer is probably broken"""
        for _ in range(2000):
            image_path = make_the_image("TEXT WILL GO HERE", '101D0001_DSC4292.jpg')
            self.assertAlmostEqual(os.stat(image_path).st_size, 51911, 50)

    def test_update_poster_name(self):
        creativity = update_name_for_poster_selection(43)
        self.assertEqual('{"response": {"props": {"children": "Heart"}}}',
                         creativity)

    def test_text_generation(self):
        number_of_generations = 5
        text = generate_text(number_of_generations, .6)
        self.assertEqual(len(text), number_of_generations)
        self.assertNotEqual(text[0], "")

    def test_split_lines(self):
        really_long_string = "this is a test to See if the thing can correctly split " \
                             "input which is obviously- long and I think this is good."
        split_long_string = split_lines(really_long_string)
        self.assertEqual(split_long_string,
                         ('this is a test to See if the thing can correctly split',
                          'input which is obviously- long and I think this is good.')
                         )


if __name__ == '__main__':
    unittest.main()
