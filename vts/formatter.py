"""Định dạng và xử lý kịch bản, chuyển đổi giữa JSON, tệp .txt và tệp phụ đề .srt."""

import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ScriptSegment:
    start: str
    end: str
    emotion: str
    text: str
    visual_note: Optional[str] = None


class ScriptFormatter:
    """Lớp xử lý và chuyển đổi kịch bản video."""

    @staticmethod
    def _time_str_to_srt_timestamp(time_str: str) -> str:
        """
        Chuyển chuỗi thời gian (MM:SS hoặc HH:MM:SS hoặc giây số) sang chuẩn SRT:
        HH:MM:SS,mmm
        """
        s = str(time_str).strip()
        # Nếu là số giây (float hoặc int)
        try:
            val_sec = float(s)
            hours = int(val_sec // 3600)
            minutes = int((val_sec % 3600) // 60)
            seconds = int(val_sec % 60)
            millis = int(round((val_sec - int(val_sec)) * 1000))
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
        except ValueError:
            pass

        # Xử lý dạng chuỗi MM:SS hoặc HH:MM:SS
        parts = s.split(":")
        if len(parts) == 2:
            try:
                m = int(parts[0])
                sec_parts = parts[1].split(".")
                sec = int(sec_parts[0])
                ms = int(sec_parts[1][:3].ljust(3, "0")) if len(sec_parts) > 1 else 0
                h = m // 60
                m = m % 60
                return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
            except Exception:
                return f"00:{parts[0].zfill(2)}:{parts[1].zfill(2)},000"
        elif len(parts) == 3:
            try:
                h = int(parts[0])
                m = int(parts[1])
                sec_parts = parts[2].split(".")
                sec = int(sec_parts[0])
                ms = int(sec_parts[1][:3].ljust(3, "0")) if len(sec_parts) > 1 else 0
                return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
            except Exception:
                return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)},000"

        return "00:00:00,000"

    @classmethod
    def parse_model_output(cls, raw_output: str) -> List[ScriptSegment]:
        """
        Giải mã phản hồi từ mô hình AI thành danh sách ScriptSegment.
        Hỗ trợ JSON thuần, Markdown JSON block và fallback regex.
        """
        if not raw_output or not raw_output.strip():
            return []

        text = raw_output.strip()

        # Bỏ khối markdown ```json ... ```
        if "```" in text:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1).strip()

        # Thử parse JSON
        try:
            data = json.loads(text)
            if isinstance(data, list):
                segments = []
                for item in data:
                    if isinstance(item, dict):
                        start = str(item.get("start", "00:00")).strip()
                        end = str(item.get("end", "00:05")).strip()
                        emotion = str(item.get("emotion", "binh_thuong")).strip().lower()
                        # Làm sạch tên emotion nếu có kèm ngoặc vuông
                        emotion = emotion.strip("[]")
                        text_val = str(item.get("text", "")).strip()
                        visual_note = item.get("visual_note")
                        if visual_note:
                            visual_note = str(visual_note).strip()
                        if text_val:
                            segments.append(
                                ScriptSegment(
                                    start=start,
                                    end=end,
                                    emotion=emotion,
                                    text=text_val,
                                    visual_note=visual_note,
                                )
                            )
                if segments:
                    return segments
        except Exception:
            pass

        # Fallback: Quét dòng bằng Regex nếu mô hình trả về text tự do
        segments = []
        lines = [line.strip() for line in raw_output.split("\n") if line.strip()]
        current_time = "00:00"
        current_end = "00:05"

        for line in lines:
            # Nhận diện dòng chứa timestamp ví dụ: [00:00 - 00:05]
            time_match = re.search(r"\[(\d{1,2}:\d{2})\s*[-–—]\s*(\d{1,2}:\d{2})\]", line)
            if time_match:
                current_time = time_match.group(1)
                current_end = time_match.group(2)
                # Phần còn lại của dòng có thể là text
                rem = line[time_match.end():].strip()
                if rem:
                    line = rem
                else:
                    continue

            # Nhận diện thẻ emotion ví dụ: [hao_hung] hoặc [vui]
            emo_match = re.search(r"\[([a-zA-Z_]+)\]", line)
            emotion = "binh_thuong"
            if emo_match:
                emotion = emo_match.group(1).lower()
                clean_sentence = line.replace(emo_match.group(0), "").strip()
            else:
                clean_sentence = line.strip()

            if clean_sentence and not clean_sentence.startswith("#"):
                segments.append(
                    ScriptSegment(
                        start=current_time,
                        end=current_end,
                        emotion=emotion,
                        text=clean_sentence,
                    )
                )

        return segments

    @classmethod
    def to_txt(
        cls,
        segments: List[ScriptSegment],
        include_timestamps: bool = True,
        include_notes: bool = True,
    ) -> str:
        """
        Chuyển danh sách phân đoạn sang định dạng .txt chuẩn,
        hoàn toàn tương thích để mở trong my_TTS.
        """
        out_lines = []
        for seg in segments:
            meta_parts = []
            if include_timestamps:
                meta_parts.append(f"{seg.start} - {seg.end}")
            if include_notes and seg.visual_note:
                meta_parts.append(seg.visual_note)

            if meta_parts:
                out_lines.append(f"# [{ ' | '.join(meta_parts) }]")

            emotion_tag = f"[{seg.emotion}] " if seg.emotion and seg.emotion != "binh_thuong" else ""
            out_lines.append(f"{emotion_tag}{seg.text}")
            out_lines.append("")  # Dòng trống ngăn cách các cảnh

        return "\n".join(out_lines).strip()

    @classmethod
    def to_clean_tts_txt(cls, segments: List[ScriptSegment]) -> str:
        """Xuất văn bản chỉ bao gồm thẻ cảm xúc và lời thoại, không kèm chú thích thời gian."""
        out_lines = []
        for seg in segments:
            emotion_tag = f"[{seg.emotion}] " if seg.emotion and seg.emotion != "binh_thuong" else ""
            out_lines.append(f"{emotion_tag}{seg.text}")
        return "\n".join(out_lines)

    @classmethod
    def to_srt(cls, segments: List[ScriptSegment]) -> str:
        """Chuyển danh sách phân đoạn sang định dạng tệp phụ đề tiêu chuẩn SubRip (.srt)."""
        srt_blocks = []
        for idx, seg in enumerate(segments, 1):
            start_srt = cls._time_str_to_srt_timestamp(seg.start)
            end_srt = cls._time_str_to_srt_timestamp(seg.end)
            # Trong phụ đề SRT không cần hiển thị thẻ cảm xúc [vui] mà chỉ hiển thị câu thoại
            srt_blocks.append(f"{idx}\n{start_srt} --> {end_srt}\n{seg.text}\n")

        return "\n".join(srt_blocks).strip()

    @classmethod
    def save_txt(
        cls,
        segments: List[ScriptSegment],
        file_path: str,
        include_timestamps: bool = True,
    ) -> str:
        """Lưu kịch bản ra tệp .txt UTF-8."""
        content = cls.to_txt(segments, include_timestamps=include_timestamps)
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    @classmethod
    def save_srt(cls, segments: List[ScriptSegment], file_path: str) -> str:
        """Lưu phụ đề ra tệp .srt UTF-8."""
        content = cls.to_srt(segments)
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path
