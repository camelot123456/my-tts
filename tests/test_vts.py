"""Unit tests cho module vts (config, prompts, formatter, client)."""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from vts.config import (
    DEFAULT_STYLE,
    STYLE_PRESETS,
    get_api_key,
    save_api_key,
)
from vts.formatter import ScriptFormatter, ScriptSegment
from vts.prompts import build_system_instruction, get_prompt_for_style
from vts.client import VTSClient


class TestVTSConfig(unittest.TestCase):
    def test_style_presets_exist(self):
        self.assertIn("recap", STYLE_PRESETS)
        self.assertIn("tiktok", STYLE_PRESETS)
        self.assertIn("documentary", STYLE_PRESETS)
        self.assertIn("monologue", STYLE_PRESETS)
        self.assertIn("descriptive", STYLE_PRESETS)
        self.assertEqual(DEFAULT_STYLE, "recap")

    def test_get_api_key_explicit(self):
        key = get_api_key("test_explicit_key_123")
        self.assertEqual(key, "test_explicit_key_123")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "env_test_key_456"})
    def test_get_api_key_env(self):
        key = get_api_key()
        self.assertEqual(key, "env_test_key_456")

    def test_save_and_get_api_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_cfg = os.path.join(tmpdir, ".vts_config.json")
            with patch("vts.config.get_config_path", return_value=tmp_cfg):
                self.assertTrue(save_api_key("saved_key_789"))
                self.assertTrue(os.path.isfile(tmp_cfg))
                with patch.dict(os.environ, {}, clear=True):
                    # Bỏ biến môi trường để đọc từ file
                    if "GEMINI_API_KEY" in os.environ:
                        del os.environ["GEMINI_API_KEY"]
                    read_key = get_api_key()
                    self.assertEqual(read_key, "saved_key_789")


class TestVTSPrompts(unittest.TestCase):
    def test_build_system_instruction(self):
        sys_vi = build_system_instruction("vi")
        self.assertIn("Tiếng Việt", sys_vi)
        self.assertIn("KHÔNG CÓ TIẾNG NÓI", sys_vi)
        self.assertIn("hao_hung", sys_vi)

        sys_en = build_system_instruction("en")
        self.assertIn("English", sys_en)

    def test_get_prompt_for_style(self):
        for style in STYLE_PRESETS.keys():
            prompt = get_prompt_for_style(style, "vi")
            self.assertIn(STYLE_PRESETS[style].name, prompt)
            self.assertIn("JSON", prompt)
            self.assertIn('"start"', prompt)
            self.assertIn('"end"', prompt)


class TestVTSFormatter(unittest.TestCase):
    def test_parse_json_markdown_output(self):
        raw_json = """```json
[
  {
    "start": "00:00",
    "end": "00:05",
    "emotion": "hao_hung",
    "text": "Khung cảnh bình minh tuyệt đẹp trên đỉnh núi.",
    "visual_note": "Cảnh toàn đỉnh núi"
  },
  {
    "start": "00:05",
    "end": "00:10",
    "emotion": "thi_tham",
    "text": "Mọi vật đều đang chìm trong sự tĩnh lặng.",
    "visual_note": "Cận cảnh sương mai"
  }
]
```"""
        segments = ScriptFormatter.parse_model_output(raw_json)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].start, "00:00")
        self.assertEqual(segments[0].end, "00:05")
        self.assertEqual(segments[0].emotion, "hao_hung")
        self.assertEqual(segments[0].text, "Khung cảnh bình minh tuyệt đẹp trên đỉnh núi.")
        self.assertEqual(segments[0].visual_note, "Cảnh toàn đỉnh núi")

        self.assertEqual(segments[1].emotion, "thi_tham")

    def test_parse_fallback_regex_output(self):
        raw_text = """
[00:00 - 00:04] [vui] Chú cún con đang tung tăng chạy trên bãi cỏ.
# [00:05 - 00:09]
[buon] Trời bỗng đổ cơn mưa rào khiến nó phải chạy đi tìm chỗ trú.
"""
        segments = ScriptFormatter.parse_model_output(raw_text)
        self.assertGreaterEqual(len(segments), 2)
        self.assertEqual(segments[0].emotion, "vui")
        self.assertIn("Chú cún con", segments[0].text)
        self.assertEqual(segments[1].emotion, "buon")
        self.assertIn("mưa rào", segments[1].text)

    def test_to_txt_and_clean_tts(self):
        segments = [
            ScriptSegment("00:00", "00:05", "hao_hung", "Đoạn 1", "Cảnh 1"),
            ScriptSegment("00:05", "00:10", "binh_thuong", "Đoạn 2", None),
        ]
        txt = ScriptFormatter.to_txt(segments, include_timestamps=True)
        self.assertIn("# [00:00 - 00:05 | Cảnh 1]", txt)
        self.assertIn("[hao_hung] Đoạn 1", txt)
        self.assertIn("Đoạn 2", txt)

        clean_txt = ScriptFormatter.to_clean_tts_txt(segments)
        self.assertNotIn("#", clean_txt)
        self.assertIn("[hao_hung] Đoạn 1", clean_txt)
        self.assertIn("Đoạn 2", clean_txt)

    def test_to_srt(self):
        segments = [
            ScriptSegment("00:00", "00:04", "vui", "Xin chào mọi người!"),
            ScriptSegment("00:05", "00:10", "hao_hung", "Chào mừng đến với tập podcast!"),
        ]
        srt = ScriptFormatter.to_srt(segments)
        self.assertIn("1\n00:00:00,000 --> 00:00:04,000\nXin chào mọi người!", srt)
        self.assertIn("2\n00:00:05,000 --> 00:00:10,000\nChào mừng đến với tập podcast!", srt)

    def test_save_txt_and_srt(self):
        segments = [ScriptSegment("00:00", "00:03", "vui", "Test câu thoại")]
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = os.path.join(tmpdir, "test.txt")
            srt_path = os.path.join(tmpdir, "test.srt")

            ScriptFormatter.save_txt(segments, txt_path)
            ScriptFormatter.save_srt(segments, srt_path)

            self.assertTrue(os.path.isfile(txt_path))
            self.assertTrue(os.path.isfile(srt_path))

            with open(txt_path, "r", encoding="utf-8") as f:
                self.assertIn("Test câu thoại", f.read())

            with open(srt_path, "r", encoding="utf-8") as f:
                self.assertIn("00:00:00,000 --> 00:00:03,000", f.read())


class TestVTSClient(unittest.TestCase):
    def test_client_missing_key(self):
        with patch("vts.client.get_api_key", return_value=None):
            client = VTSClient(api_key=None)
            with self.assertRaises(ValueError):
                client.analyze_video("dummy.mp4")

    def test_client_missing_video_file(self):
        client = VTSClient(api_key="valid_dummy_key")
        with self.assertRaises(FileNotFoundError):
            client.analyze_video("non_existent_video_12345.mp4")


if __name__ == "__main__":
    unittest.main()
