"""
tests/test_api.py
------------------
End-to-End API unit tests for StegoLab Flask Backend.
Tests 3 algorithms (Encode, Download, Decode) via Flask Test Client.
"""

import io
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from phase5_webapp.app import app


class TestStegoLabAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.sample_path = os.path.join(os.path.dirname(__file__), "..", "phase1_basics", "images", "input", "sample.png")
        with open(self.sample_path, "rb") as f:
            self.img_bytes = f.read()

    def test_homepage(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

    def test_sample_endpoint(self):
        with self.client.get("/api/sample/sample") as res:
            self.assertEqual(res.status_code, 200)
            self.assertTrue(len(res.data) > 0)

    def test_all_algorithms_e2e(self):
        algorithms = [
            ("lsb", "Basic LSB Test Message"),
            ("rlsb", "Random LSB Keyed Payload"),
            ("edge", "Edge Adaptive Multi-Bit 🚀"),
        ]

        for algo, secret_msg in algorithms:
            with self.subTest(algo=algo):
                # 1. Encode
                encode_payload = {
                    "image": (io.BytesIO(self.img_bytes), "sample.png"),
                    "message": secret_msg,
                    "algo": algo,
                    "key": "testsuite_pass_99",
                }
                with self.client.post("/api/encode", data=encode_payload, content_type="multipart/form-data") as enc_res:
                    self.assertEqual(enc_res.status_code, 200)
                    enc_data = enc_res.get_json()
                    self.assertIn("result_id", enc_data)
                    result_id = enc_data["result_id"]

                # 2. Download stego image
                with self.client.get(f"/api/download/{result_id}") as dl_res:
                    self.assertEqual(dl_res.status_code, 200)
                    stego_bytes = dl_res.data

                # 3. Decode
                decode_payload = {
                    "image": (io.BytesIO(stego_bytes), f"stego_{algo}.png"),
                    "algo": algo,
                    "key": "testsuite_pass_99",
                }
                with self.client.post("/api/decode", data=decode_payload, content_type="multipart/form-data") as dec_res:
                    self.assertEqual(dec_res.status_code, 200)
                    dec_data = dec_res.get_json()

                    self.assertEqual(dec_data.get("message"), secret_msg)
                    self.assertTrue(dec_data.get("delimiter_found"))


if __name__ == "__main__":
    unittest.main()
