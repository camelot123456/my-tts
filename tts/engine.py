"""Engine xử lý chuyển đổi Text sang Speech (MP3) sử dụng Edge-TTS và gTTS,
kèm hỗ trợ tùy chỉnh tốc độ, cảm xúc và chuyển đổi song ngữ (Code-Switching).
"""

import asyncio
import io
import os
import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Union

from tts.code_switch import (
    CodeSwitchChunk,
    get_paired_voice,
    parse_code_switch_segments,
)
from tts.config import DEFAULT_VOICES, VOICE_CATALOG, VoiceInfo, get_voice_info
from tts.emotion import (
    EMOTION_PRESETS,
    EmotionPreset,
    combine_emotion_and_speed,
    get_emotion_preset,
    parse_segments,
)
from tts.text_processor import clean_text, read_text_file, split_text_into_chunks


def parse_speed(speed_input: Union[str, float, int, None]) -> Tuple[float, str]:
    """
    Chuẩn hóa tham số tốc độ đọc (speed / rate) về 2 định dạng:
    - Hệ số nhân (multiplier: float, ví dụ 1.25 cho 1.25x, 0.8 cho 0.8x)
    - Chuỗi phần trăm cho Edge-TTS (rate_str: str, ví dụ '+25%', '-20%')
    """
    if speed_input is None:
        return 1.0, "+0%"

    if isinstance(speed_input, (int, float)):
        multiplier = float(speed_input)
    elif isinstance(speed_input, str):
        s = speed_input.strip().lower()
        if not s:
            return 1.0, "+0%"

        try:
            if s.endswith("%"):
                pct_val = float(s[:-1].strip())
                multiplier = 1.0 + (pct_val / 100.0)
            else:
                if s.endswith("x"):
                    s = s[:-1].strip()
                val = float(s)
                if (s.startswith("+") or s.startswith("-")) and abs(val) >= 5.0:
                    multiplier = 1.0 + (val / 100.0)
                else:
                    multiplier = val
        except ValueError:
            raise ValueError(
                f"Giá trị tốc độ '{speed_input}' không hợp lệ! "
                "Hãy nhập hệ số (ví dụ: 0.75, 1.0, 1.25x, 1.5x) hoặc phần trăm (ví dụ: +20%, -15%)."
            )
    else:
        raise ValueError(f"Kiểu dữ liệu tốc độ không hợp lệ: {type(speed_input)}")

    if multiplier <= 0:
        raise ValueError("Tốc độ đọc (speed) phải lớn hơn 0 (khuyên dùng từ 0.5x đến 2.0x).")

    multiplier = max(0.25, min(3.0, multiplier))
    pct = int(round((multiplier - 1.0) * 100))
    rate_str = f"+{pct}%" if pct >= 0 else f"{pct}%"

    return round(multiplier, 2), rate_str


def adjust_mp3_speed(mp3_bytes: bytes, speed_multiplier: float) -> bytes:
    """
    Điều chỉnh tốc độ âm thanh MP3 (Time-Stretching giữ nguyên cao độ giọng)
    sử dụng bộ lọc FFmpeg `atempo` tích hợp qua thư viện PyAV (`av`).
    """
    if not mp3_bytes or abs(speed_multiplier - 1.0) < 0.01:
        return mp3_bytes

    try:
        import av
    except ImportError:
        return mp3_bytes

    buf_src = io.BytesIO(mp3_bytes)
    buf_out = io.BytesIO()

    with av.open(buf_src, mode="r", format="mp3") as in_c, av.open(
        buf_out, mode="w", format="mp3"
    ) as out_c:
        in_s = in_c.streams.audio[0]
        sample_rate = in_s.rate or 24000
        out_s = out_c.add_stream("mp3", rate=sample_rate)

        graph = av.filter.Graph()
        abuffer = graph.add_abuffer(template=in_s)

        factors = []
        rem = float(speed_multiplier)
        while rem < 0.5:
            factors.append(0.5)
            rem /= 0.5
        while rem > 2.0:
            factors.append(2.0)
            rem /= 2.0
        factors.append(rem)

        prev_node = abuffer
        for f_val in factors:
            atempo_node = graph.add("atempo", f"{f_val:.4f}")
            prev_node.link_to(atempo_node)
            prev_node = atempo_node

        aformat = graph.add(
            "aformat", f"sample_fmts=s16p:channel_layouts=mono:sample_rates={sample_rate}"
        )
        abuffersink = graph.add("abuffersink")
        prev_node.link_to(aformat)
        aformat.link_to(abuffersink)
        graph.configure()

        for frame in in_c.decode(in_s):
            graph.push(frame)
            while True:
                try:
                    f_out = graph.pull()
                    f_out.pts = None
                    for pkt in out_s.encode(f_out):
                        out_c.mux(pkt)
                except (av.BlockingIOError, av.EOFError):
                    break

        graph.push(None)
        while True:
            try:
                f_out = graph.pull()
                f_out.pts = None
                for pkt in out_s.encode(f_out):
                    out_c.mux(pkt)
            except (av.BlockingIOError, av.EOFError):
                break

        for pkt in out_s.encode(None):
            out_c.mux(pkt)

    return buf_out.getvalue()


@dataclass
class SynthesisChunk:
    text: str
    voice_id: str
    lang: str
    rate: str
    pitch: str
    volume: str
    speed_multiplier: float
    emotion_label: str


class TTSEngine:
    """Bộ chuyển đổi văn bản sang âm thanh MP3 với cơ chế tự phục hồi, tốc độ, cảm xúc và song ngữ."""

    def __init__(self):
        pass

    def convert_file_to_mp3(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        voice_id: Optional[str] = None,
        language: str = "vi",
        rate: str = "+0%",
        speed: Optional[Union[float, str]] = None,
        pitch: str = "+0Hz",
        engine: str = "edge-tts",
        emotions: bool = True,
        default_emotion: str = "binh_thuong",
        auto_emotion: bool = False,
        code_switch: bool = True,
        paired_voice_id: Optional[str] = None,
        auto_detect_en: bool = True,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> str:
        """Đọc file văn bản và chuyển đổi thành file MP3."""
        if progress_callback:
            progress_callback(0.05, f"Đang đọc tệp văn bản: {os.path.basename(input_file)}...")

        text, encoding = read_text_file(input_file)

        if not output_file:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}.mp3"

        return self.convert_text_to_mp3(
            text=text,
            output_file=output_file,
            voice_id=voice_id,
            language=language,
            rate=rate,
            speed=speed,
            pitch=pitch,
            engine=engine,
            emotions=emotions,
            default_emotion=default_emotion,
            auto_emotion=auto_emotion,
            code_switch=code_switch,
            paired_voice_id=paired_voice_id,
            auto_detect_en=auto_detect_en,
            progress_callback=progress_callback,
        )

    def convert_text_to_mp3(
        self,
        text: str,
        output_file: str,
        voice_id: Optional[str] = None,
        language: str = "vi",
        rate: str = "+0%",
        speed: Optional[Union[float, str]] = None,
        pitch: str = "+0Hz",
        engine: str = "edge-tts",
        emotions: bool = True,
        default_emotion: str = "binh_thuong",
        auto_emotion: bool = False,
        code_switch: bool = True,
        paired_voice_id: Optional[str] = None,
        auto_detect_en: bool = True,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> str:
        """Chuyển đổi chuỗi văn bản trực tiếp thành file MP3."""
        cleaned_text = clean_text(text)
        if not cleaned_text:
            raise ValueError("Nội dung văn bản để chuyển đổi trống!")

        # Chuẩn hóa tốc độ người dùng
        speed_input = speed if speed is not None else rate
        user_speed_mult, _ = parse_speed(speed_input)

        # Chuẩn hóa voice_id và engine
        voice_info = None
        if voice_id:
            voice_info = get_voice_info(voice_id)

        if voice_info is None and voice_id and "Neural" in voice_id:
            voice_info = VoiceInfo(voice_id, voice_id, voice_id[:5], "", "edge-tts", "")

        if voice_info is None:
            lang_key = "vi" if language.lower().startswith("vi") else "en"
            default_voice_key = DEFAULT_VOICES.get(lang_key, "vi-VN-NamMinhNeural")
            voice_info = VOICE_CATALOG.get(default_voice_key, VOICE_CATALOG["vi-VN-NamMinhNeural"])

        target_engine = engine or voice_info.engine

        out_dir = os.path.dirname(os.path.abspath(output_file))
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        chunks: List[SynthesisChunk] = []

        if code_switch:
            # Chế độ chuyển đổi song ngữ (Code-Switching)
            cs_segments = parse_code_switch_segments(
                text=cleaned_text,
                base_voice_id=voice_info.id,
                base_lang=language,
                paired_voice_id=paired_voice_id,
                auto_detect=auto_detect_en,
                default_emotion=default_emotion,
                auto_emotion=auto_emotion,
            )
            for cs in cs_segments:
                sub_chunks = split_text_into_chunks(cs.text, max_chars=350)
                c_rate, c_pitch, c_vol, eff_speed = combine_emotion_and_speed(
                    preset=cs.emotion_preset,
                    user_speed_multiplier=user_speed_mult,
                    user_pitch_str=pitch,
                )
                for sub in sub_chunks:
                    chunks.append(
                        SynthesisChunk(
                            text=sub,
                            voice_id=cs.voice_id,
                            lang=cs.lang,
                            rate=c_rate,
                            pitch=c_pitch,
                            volume=c_vol,
                            speed_multiplier=eff_speed,
                            emotion_label=cs.emotion_preset.label,
                        )
                    )
        else:
            # Chế độ đơn ngữ thông thường
            if emotions:
                segments = parse_segments(
                    cleaned_text,
                    default_emotion=default_emotion,
                    auto_emotion=auto_emotion,
                )
            else:
                plain = re.sub(r"\[(/?)[a-zA-Z0-9_]+\]", "", cleaned_text).strip()
                def_preset = get_emotion_preset(default_emotion)
                segments = [(plain, def_preset)]

            for seg_text, seg_preset in segments:
                sub_chunks = split_text_into_chunks(seg_text, max_chars=350)
                c_rate, c_pitch, c_vol, eff_speed = combine_emotion_and_speed(
                    preset=seg_preset,
                    user_speed_multiplier=user_speed_mult,
                    user_pitch_str=pitch,
                )
                for sub in sub_chunks:
                    chunks.append(
                        SynthesisChunk(
                            text=sub,
                            voice_id=voice_info.id,
                            lang=language,
                            rate=c_rate,
                            pitch=c_pitch,
                            volume=c_vol,
                            speed_multiplier=eff_speed,
                            emotion_label=seg_preset.label,
                        )
                    )

        total_chunks = len(chunks)
        if progress_callback:
            progress_callback(
                0.1,
                f"Đã phân tích văn bản ({total_chunks} đoạn, tốc độ cơ sở {user_speed_mult:.2f}x)...",
            )

        if target_engine == "gtts":
            self._convert_with_gtts(
                chunks=chunks,
                output_file=output_file,
                default_lang=language,
                progress_callback=progress_callback,
            )
        else:
            self._convert_with_edge_tts(
                chunks=chunks,
                output_file=output_file,
                fallback_voice=voice_info.id,
                default_lang=language,
                progress_callback=progress_callback,
            )

        if progress_callback:
            progress_callback(1.0, f"Hoàn tất! File âm thanh đã lưu tại: {os.path.basename(output_file)}")

        return os.path.abspath(output_file)

    def _get_gtts_audio_bytes(
        self, text: str, language: str, speed_multiplier: float = 1.0
    ) -> bytes:
        """Lấy dữ liệu âm thanh MP3 từ Google TTS và áp dụng tốc độ đọc."""
        if not text or not re.search(r"\w", text):
            return b""

        from gtts import gTTS

        lang_code = "vi" if language.lower().startswith("vi") else "en"
        fp = io.BytesIO()
        try:
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.write_to_fp(fp)
            raw_mp3 = fp.getvalue()
            return adjust_mp3_speed(raw_mp3, speed_multiplier)
        except Exception:
            return b""

    def _convert_with_edge_tts(
        self,
        chunks: List[SynthesisChunk],
        output_file: str,
        fallback_voice: str,
        default_lang: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ):
        """Chuyển đổi sử dụng Edge-TTS cho từng đoạn (hỗ trợ đổi giọng/ngôn ngữ từng chunk) và dự phòng gTTS."""
        import edge_tts

        async def _run_edge_tts():
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except OSError:
                    pass

            with open(output_file, "wb") as f_out:
                for idx, chunk in enumerate(chunks, 1):
                    if not chunk.text or not re.search(r"\w", chunk.text):
                        continue

                    pct = 0.1 + (0.85 * (idx - 0.5) / len(chunks))
                    v_target = chunk.voice_id or fallback_voice
                    l_target = chunk.lang or default_lang
                    voice_short = v_target.split("-")[-1].replace("Neural", "")

                    if progress_callback:
                        progress_callback(
                            pct,
                            f"Đang đọc [{l_target.upper()}-{voice_short}]: {chunk.emotion_label} ({chunk.speed_multiplier:.2f}x) [{idx}/{len(chunks)}]...",
                        )

                    chunk_success = False
                    for attempt in range(1, 4):
                        try:
                            communicate = edge_tts.Communicate(
                                text=chunk.text,
                                voice=v_target,
                                rate=chunk.rate,
                                pitch=chunk.pitch,
                                volume=chunk.volume,
                            )
                            chunk_data = bytearray()
                            async for message in communicate.stream():
                                if message["type"] == "audio":
                                    chunk_data.extend(message["data"])
                            if chunk_data:
                                f_out.write(chunk_data)
                                chunk_success = True
                                break
                            else:
                                raise edge_tts.exceptions.NoAudioReceived(
                                    "No audio received from Edge-TTS stream"
                                )
                        except Exception:
                            if attempt < 3:
                                await asyncio.sleep(0.8 * attempt)
                            else:
                                chunk_success = False

                    if not chunk_success:
                        if progress_callback:
                            progress_callback(
                                pct,
                                f"Cảnh báo: Đoạn {idx} ([{l_target.upper()}]) không thể đọc bằng {voice_short}, chuyển sang Google TTS dự phòng...",
                            )
                        fallback_data = self._get_gtts_audio_bytes(
                            chunk.text, l_target, speed_multiplier=chunk.speed_multiplier
                        )
                        f_out.write(fallback_data)
                    else:
                        # Khoảng nghỉ nhỏ (pacing) giữa các đoạn để tránh quá tải kết nối WebSocket
                        if idx < len(chunks):
                            await asyncio.sleep(0.15)

                    if progress_callback:
                        pct_done = 0.1 + (0.85 * idx / len(chunks))
                        progress_callback(pct_done, f"Hoàn thành đoạn {idx}/{len(chunks)}")

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(asyncio.run, _run_edge_tts()).result()
            else:
                loop.run_until_complete(_run_edge_tts())
        except RuntimeError:
            asyncio.run(_run_edge_tts())

    def _convert_with_gtts(
        self,
        chunks: List[SynthesisChunk],
        output_file: str,
        default_lang: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ):
        """Chuyển đổi sử dụng gTTS cho từng phân đoạn ngôn ngữ."""
        with open(output_file, "wb") as f_out:
            for idx, chunk in enumerate(chunks, 1):
                if not chunk.text or not re.search(r"\w", chunk.text):
                    continue

                l_target = chunk.lang or default_lang
                if progress_callback:
                    pct = 0.1 + (0.85 * (idx - 0.5) / len(chunks))
                    progress_callback(
                        pct,
                        f"Đang gọi Google TTS [{l_target.upper()}]: ({chunk.speed_multiplier:.2f}x) [{idx}/{len(chunks)}]...",
                    )

                audio_data = self._get_gtts_audio_bytes(
                    chunk.text, l_target, speed_multiplier=chunk.speed_multiplier
                )
                f_out.write(audio_data)

                if progress_callback:
                    pct = 0.1 + (0.85 * idx / len(chunks))
                    progress_callback(pct, f"Hoàn thành đoạn {idx}/{len(chunks)}")
