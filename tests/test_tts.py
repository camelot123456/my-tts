"""Unit tests cho module tts (config, text_processor, engine speed, emotion)."""

import io
import os
import tempfile
import unittest

from tts.config import (
    DEFAULT_VOICES,
    VOICE_CATALOG,
    get_voice_info,
    get_voices_for_language,
)
from tts.code_switch import (
    CodeSwitchChunk,
    detect_english_phrases,
    get_paired_voice,
    is_english_token,
    parse_code_switch_segments,
)
from tts.emotion import (
    EMOTION_PRESETS,
    combine_emotion_and_speed,
    get_emotion_preset,
    parse_segments,
)
from tts.engine import adjust_mp3_speed, parse_speed
from tts.text_processor import (
    clean_text,
    read_text_file,
    split_text_into_chunks,
)


class TestTTSConfig(unittest.TestCase):
    def test_default_voices_exist(self):
        self.assertIn("vi", DEFAULT_VOICES)
        self.assertIn("en", DEFAULT_VOICES)
        vi_voice = DEFAULT_VOICES["vi"]
        en_voice = DEFAULT_VOICES["en"]
        self.assertIn(vi_voice, VOICE_CATALOG)
        self.assertIn(en_voice, VOICE_CATALOG)
        self.assertEqual(vi_voice, "vi-VN-NamMinhNeural")

    def test_get_voices_for_language(self):
        vi_voices = get_voices_for_language("vi")
        self.assertGreaterEqual(len(vi_voices), 2)
        self.assertEqual(vi_voices[0].id, "vi-VN-NamMinhNeural")
        for v in vi_voices:
            self.assertTrue(v.language.startswith("vi"))

        en_voices = get_voices_for_language("en")
        self.assertGreaterEqual(len(en_voices), 3)
        for v in en_voices:
            self.assertTrue(v.language.startswith("en"))

    def test_get_voice_info(self):
        info = get_voice_info("vi-VN-HoaiMyNeural")
        self.assertIsNotNone(info)
        self.assertEqual(info.gender, "Female")
        self.assertEqual(info.engine, "edge-tts")


class TestTextProcessor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_read_utf8_vietnamese(self):
        sample_path = os.path.join(self.test_dir.name, "sample_utf8.txt")
        content = "Xin chào Việt Nam! Đây là bài kiểm tra đọc văn bản tiếng Việt có dấu: ế, ắ, ồ, ừ, đ, ạ, ỹ."
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write(content)

        read_content, enc = read_text_file(sample_path)
        self.assertEqual(read_content, content)
        self.assertIn("utf-8", enc.lower())

    def test_read_utf8_bom(self):
        sample_path = os.path.join(self.test_dir.name, "sample_utf8_bom.txt")
        content = "Xin chào có BOM!"
        with open(sample_path, "w", encoding="utf-8-sig") as f:
            f.write(content)

        read_content, enc = read_text_file(sample_path)
        self.assertEqual(read_content, content)
        self.assertEqual(enc, "utf-8-sig")

    def test_read_utf16(self):
        sample_path = os.path.join(self.test_dir.name, "sample_utf16.txt")
        content = "Thử nghiệm file định dạng UTF-16 từ Windows Notepad."
        with open(sample_path, "w", encoding="utf-16") as f:
            f.write(content)

        read_content, enc = read_text_file(sample_path)
        self.assertEqual(read_content, content)
        self.assertTrue(enc.startswith("utf-16"))

    def test_read_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            read_text_file("non_existent_file_12345.txt")

    def test_read_empty_file(self):
        sample_path = os.path.join(self.test_dir.name, "empty.txt")
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write("   \n\n  \t  ")

        with self.assertRaises(ValueError):
            read_text_file(sample_path)

    def test_clean_text(self):
        raw = "  Dòng 1   với nhiều khoảng trắng.   \r\n\r\nDòng 2\r\n\n\n\nDòng 3.  "
        cleaned = clean_text(raw)
        self.assertEqual(cleaned, "Dòng 1 với nhiều khoảng trắng.\n\nDòng 2\n\nDòng 3.")

    def test_clean_text_normalizes_quotes(self):
        raw = 'Chào bạn: “Một câu nói trong ngoặc kép” và ‘ngoặc đơn’.'
        cleaned = clean_text(raw)
        self.assertEqual(cleaned, 'Chào bạn: "Một câu nói trong ngoặc kép" và \'ngoặc đơn\'.')

    def test_split_text_into_chunks(self):
        short_text = "Câu ngắn dưới 100 ký tự."
        chunks = split_text_into_chunks(short_text, max_chars=100)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], short_text)

        long_para1 = "Đây là câu thứ nhất của đoạn văn dài. " * 10
        long_para2 = "Đây là câu thứ hai của đoạn văn dài. " * 10
        full_text = f"{long_para1}\n\n{long_para2}"

        chunks = split_text_into_chunks(full_text, max_chars=200)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertTrue(len(c) > 0)


class TestSpeedCustomization(unittest.TestCase):
    def test_parse_speed_multipliers(self):
        self.assertEqual(parse_speed(1.0), (1.0, "+0%"))
        self.assertEqual(parse_speed(1.25), (1.25, "+25%"))
        self.assertEqual(parse_speed("1.25x"), (1.25, "+25%"))
        self.assertEqual(parse_speed("1.5X"), (1.5, "+50%"))
        self.assertEqual(parse_speed(0.75), (0.75, "-25%"))
        self.assertEqual(parse_speed("0.8"), (0.8, "-20%"))

    def test_parse_speed_percentages(self):
        self.assertEqual(parse_speed("+20%"), (1.2, "+20%"))
        self.assertEqual(parse_speed("-15%"), (0.85, "-15%"))
        self.assertEqual(parse_speed("+0%"), (1.0, "+0%"))
        self.assertEqual(parse_speed("30%"), (1.3, "+30%"))

    def test_parse_speed_invalid(self):
        with self.assertRaises(ValueError):
            parse_speed("abc")
        with self.assertRaises(ValueError):
            parse_speed(0)
        with self.assertRaises(ValueError):
            parse_speed(-1.5)

    def test_adjust_mp3_speed(self):
        import av
        import numpy as np

        buf_in = io.BytesIO()
        with av.open(buf_in, mode="w", format="mp3") as container:
            stream = container.add_stream("mp3", rate=24000)
            samples = (np.sin(2 * np.pi * 440 * np.arange(24000) / 24000) * 10000).astype(
                np.int16
            )
            frame = av.AudioFrame.from_ndarray(
                samples.reshape(1, -1), format="s16", layout="mono"
            )
            frame.sample_rate = 24000
            for packet in stream.encode(frame):
                container.mux(packet)
            for packet in stream.encode(None):
                container.mux(packet)

        orig_bytes = buf_in.getvalue()
        fast_bytes = adjust_mp3_speed(orig_bytes, 1.5)
        slow_bytes = adjust_mp3_speed(orig_bytes, 0.75)

        self.assertLess(len(fast_bytes), len(orig_bytes))
        self.assertGreater(len(slow_bytes), len(orig_bytes))


class TestEmotionSystem(unittest.TestCase):
    def test_presets_exist(self):
        for key in ["binh_thuong", "vui", "hao_hung", "buon", "gian", "so_hai", "thi_tham", "nghiem_tuc"]:
            self.assertIn(key, EMOTION_PRESETS)

    def test_get_preset_with_aliases(self):
        self.assertEqual(get_emotion_preset("vui").key, "vui")
        self.assertEqual(get_emotion_preset("happy").key, "vui")
        self.assertEqual(get_emotion_preset("sad").key, "buon")
        self.assertEqual(get_emotion_preset("whisper").key, "thi_tham")
        self.assertEqual(get_emotion_preset("unknown_tag_xyz").key, "binh_thuong")

    def test_parse_segments_line_tags(self):
        raw = "[vui] Hôm nay trời nắng đẹp.\n[buon] Thật tiếc vì bạn vắng mặt."
        segs = parse_segments(raw)
        self.assertEqual(len(segs), 2)
        self.assertEqual(segs[0][0], "Hôm nay trời nắng đẹp.")
        self.assertEqual(segs[0][1].key, "vui")
        self.assertEqual(segs[1][0], "Thật tiếc vì bạn vắng mặt.")
        self.assertEqual(segs[1][1].key, "buon")

    def test_parse_segments_block_tags(self):
        raw = "Câu mở đầu.\n[hao_hung]Đoạn 1.\nĐoạn 2.[/hao_hung]\nCâu kết thúc."
        segs = parse_segments(raw)
        self.assertEqual(len(segs), 3)
        self.assertEqual(segs[0][1].key, "binh_thuong")
        self.assertEqual(segs[1][1].key, "hao_hung")
        self.assertEqual(segs[2][1].key, "binh_thuong")

    def test_parse_segments_auto_emotion(self):
        raw = "Tuyệt vời quá đi!\nTôi thấy hơi buồn...\nThông tin này hoàn toàn bình thường."
        segs = parse_segments(raw, auto_emotion=True)
        self.assertEqual(len(segs), 3)
        self.assertEqual(segs[0][1].key, "hao_hung")
        self.assertEqual(segs[1][1].key, "buon")
        self.assertEqual(segs[2][1].key, "binh_thuong")

    def test_combine_emotion_and_speed(self):
        preset_vui = get_emotion_preset("vui")  # +12% rate, +25Hz pitch, +5% vol
        # user speed = 1.0x, user pitch = +0Hz
        r, p, v, mult = combine_emotion_and_speed(preset_vui, user_speed_multiplier=1.0)
        self.assertEqual(r, "+12%")
        self.assertEqual(p, "+25Hz")
        self.assertEqual(v, "+5%")
        self.assertAlmostEqual(mult, 1.12)

        # user speed = 1.25x (+25%), user pitch = +5Hz
        r2, p2, v2, mult2 = combine_emotion_and_speed(preset_vui, user_speed_multiplier=1.25, user_pitch_str="+5Hz")
        # 1.25 * 1.12 = 1.40 (+40%)
        self.assertEqual(r2, "+40%")
        self.assertEqual(p2, "+30Hz")
        self.assertEqual(v2, "+5%")
        self.assertAlmostEqual(mult2, 1.40)


class TestCodeSwitch(unittest.TestCase):
    def test_get_paired_voice(self):
        # Male Vietnamese -> Male English
        self.assertEqual(get_paired_voice("vi-VN-NamMinhNeural"), "en-US-GuyNeural")
        # Female Vietnamese -> Female English
        self.assertEqual(get_paired_voice("vi-VN-HoaiMyNeural"), "en-US-JennyNeural")
        # gTTS pairing
        self.assertEqual(get_paired_voice("vi"), "en")
        self.assertEqual(get_paired_voice("en"), "vi")
        # Reverse pairing
        self.assertEqual(get_paired_voice("en-US-GuyNeural"), "vi-VN-NamMinhNeural")

    def test_is_english_token(self):
        # Common English tech / business terms
        self.assertTrue(is_english_token("deadline"))
        self.assertTrue(is_english_token("Python"))
        self.assertTrue(is_english_token("AI"))
        self.assertTrue(is_english_token("feedback"))
        self.assertTrue(is_english_token("meeting"))

        # Words with letters w, f, j, z
        self.assertTrue(is_english_token("flow"))
        self.assertTrue(is_english_token("zoom"))
        self.assertTrue(is_english_token("join"))

        # English suffixes
        self.assertTrue(is_english_token("training"))
        self.assertTrue(is_english_token("management"))

        # Vietnamese homographs without diacritics must NOT be detected as English
        self.assertFalse(is_english_token("la"))
        self.assertFalse(is_english_token("va"))
        self.assertFalse(is_english_token("di"))
        self.assertFalse(is_english_token("co"))
        self.assertFalse(is_english_token("to"))
        self.assertFalse(is_english_token("me"))
        self.assertFalse(is_english_token("an"))

    def test_detect_english_phrases(self):
        text = "Dự án này ứng dụng machine learning và deep learning rất hiệu quả."
        segments = detect_english_phrases(text)
        # Should identify machine learning and deep learning as en
        en_texts = [t for t, lang in segments if lang == "en"]
        self.assertTrue(any("machine learning" in t for t in en_texts))
        self.assertTrue(any("deep learning" in t for t in en_texts))

        vi_texts = [t for t, lang in segments if lang == "vi"]
        self.assertTrue(any("Dự án này ứng dụng" in t for t in vi_texts))

    def test_parse_code_switch_explicit_tags(self):
        text = "Hôm nay tôi nghiên cứu [en]Artificial Intelligence[/en] để làm đồ án."
        chunks = parse_code_switch_segments(
            text=text,
            base_voice_id="vi-VN-NamMinhNeural",
            base_lang="vi",
            auto_detect=False,
        )
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].lang, "vi")
        self.assertEqual(chunks[0].voice_id, "vi-VN-NamMinhNeural")

        self.assertEqual(chunks[1].lang, "en")
        self.assertEqual(chunks[1].text, "Artificial Intelligence")
        self.assertEqual(chunks[1].voice_id, "en-US-GuyNeural")

        self.assertEqual(chunks[2].lang, "vi")
        self.assertEqual(chunks[2].voice_id, "vi-VN-NamMinhNeural")

    def test_parse_code_switch_with_emotion_preservation(self):
        text = "[hao_hung]Chúng tôi vừa ra mắt [en]machine learning[/en] model mới![/hao_hung]"
        chunks = parse_code_switch_segments(
            text=text,
            base_voice_id="vi-VN-HoaiMyNeural",
            base_lang="vi",
            auto_detect=True,
        )
        self.assertGreaterEqual(len(chunks), 2)
        for c in chunks:
            self.assertEqual(c.emotion_preset.key, "hao_hung")

        # Female Vietnamese pairs with Jenny
        vi_chunk = next(c for c in chunks if c.lang == "vi")
        en_chunk = next(c for c in chunks if c.lang == "en")
        self.assertEqual(vi_chunk.voice_id, "vi-VN-HoaiMyNeural")
        self.assertEqual(en_chunk.voice_id, "en-US-JennyNeural")


if __name__ == "__main__":
    unittest.main()
