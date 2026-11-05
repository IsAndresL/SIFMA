# SIFMA — Pruebas Unitarias del Filtro ExG
import unittest
import numpy as np
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vision.exg_segmentation import ExgSegmenter

class TestExgSegmentation(unittest.TestCase):
    def setUp(self):
        self.segmenter = ExgSegmenter(exg_thresh=10.0)

    def test_exg_matrix_positive_for_pure_green(self):
        # Pixel BGR verde puro: [0, 255, 0]
        # ExG = 2*255 - 0 - 0 = 510
        green_img = np.zeros((10, 10, 3), dtype=np.uint8)
        green_img[:, :] = [0, 255, 0]

        exg = self.segmenter.compute_exg_matrix(green_img)
        self.assertAlmostEqual(exg[0, 0], 510.0)

    def test_exg_matrix_negative_for_pure_red(self):
        # Pixel BGR rojo puro: [0, 0, 255]
        # ExG = 2*0 - 255 - 0 = -255
        red_img = np.zeros((10, 10, 3), dtype=np.uint8)
        red_img[:, :] = [0, 0, 255]

        exg = self.segmenter.compute_exg_matrix(red_img)
        self.assertAlmostEqual(exg[0, 0], -255.0)

    def test_empty_image_raises_error(self):
        with self.assertRaises(ValueError):
            self.segmenter.compute_exg_matrix(np.array([]))

if __name__ == "__main__":
    unittest.main()
