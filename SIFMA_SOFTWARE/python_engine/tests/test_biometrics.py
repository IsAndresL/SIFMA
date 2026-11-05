# SIFMA — Pruebas Unitarias de Cálculos Biométricos
import unittest
import numpy as np
import cv2
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vision.biometric_cenital import CenitalBiometrics
from vision.biometric_lateral import LateralBiometrics

class TestBiometrics(unittest.TestCase):
    def test_cenital_biometrics_zero_contours(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        res = CenitalBiometrics.calculate(img, mask, [])

        self.assertEqual(res["plant_pixels"], 0)
        self.assertEqual(res["foliar_area_cm2"], 0.0)
        self.assertEqual(res["compacity_index"], 0.0)

    def test_lateral_biometrics_zero_contours(self):
        res = LateralBiometrics.calculate((480, 640, 3), [])
        self.assertEqual(res["plant_height_cm"], 0.0)
        self.assertEqual(res["stem_diameter_mm"], 0.0)

if __name__ == "__main__":
    unittest.main()

