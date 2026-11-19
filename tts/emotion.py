"""Module quản lý cảm xúc giọng đọc (Emotion Presets & Parser)."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class EmotionPreset:
    key: str
    label: str
    rate_pct: int      # Điều chỉnh tốc độ (%)
    pitch_hz: int      # Điều chỉnh cao độ (Hz)
    volume_pct: int    # Điều chỉnh âm lượng (%)
    description: str


# Danh mục preset cảm xúc chuẩn hóa
EMOTION_PRESETS: Dict[str, EmotionPreset] = {
    "binh_thuong": EmotionPreset(
        key="binh_thuong",
        label="Bình thường (Neutral)",
        rate_pct=0,
        pitch_hz=0,
        volume_pct=0,
        description="Giọng đọc tự nhiên, chuẩn mực.",
    ),
    "vui": EmotionPreset(
        key="vui",
        label="Vui vẻ (Cheerful/Happy)",
        rate_pct=12,
        pitch_hz=25,
        volume_pct=5,
        description="Tươi vui, nhịp nhanh nhẹn, âm vực cao hơn.",
    ),
    "hao_hung": EmotionPreset(
        key="hao_hung",
        label="Hào hứng (Excited)",
        rate_pct=22,
        pitch_hz=40,
        volume_pct=15,
        description="Nhiệt huyết, phấn khởi, âm lượng lớn và cao.",
    ),
    "buon": EmotionPreset(
        key="buon",
        label="Buồn bã (Sad)",
        rate_pct=-18,
        pitch_hz=-25,
        volume_pct=-15,
        description="Chậm rãi, trầm lắng, âm lượng nhỏ.",
    ),
    "gian": EmotionPreset(
        key="gian",
        label="Giận dữ (Angry)",
        rate_pct=10,
        pitch_hz=-10,
        volume_pct=25,
        description="Dứt khoát, âm vực gằn, âm lượng mạnh.",
    ),
    "so_hai": EmotionPreset(
        key="so_hai",
        label="Sợ hãi (Scared)",
        rate_pct=15,
        pitch_hz=30,
        volume_pct=-10,
        description="Hơi thở gấp, giọng cao và run.",
    ),
    "thi_tham": EmotionPreset(
        key="thi_tham",
        label="Thì thầm (Whispering)",
        rate_pct=-10,
        pitch_hz=-15,
        volume_pct=-40,
        description="Nhỏ nhẹ, thì thào bí mật.",
    ),
    "nghiem_tuc": EmotionPreset(
        key="nghiem_tuc",
        label="Nghiêm túc (Serious)",
        rate_pct=-8,
        pitch_hz=-15,
        volume_pct=0,
        description="Chắc chắn, trang trọng, tông trầm vừa.",
    ),
}

# Ánh xạ tên gọi tắt hoặc tiếng Anh
EMOTION_ALIASES: Dict[str, str] = {
    # Tiếng Việt rút gọn / không dấu
    "normal": "binh_thuong",
    "neutral": "binh_thuong",
    "binhthuong": "binh_thuong",
    "happy": "vui",
    "cheerful": "vui",
    "vui_ve": "vui",
    "vuive": "vui",
    "excited": "hao_hung",
    "haohung": "hao_hung",
    "sad": "buon",
    "buon_ba": "buon",
    "buonba": "buon",
    "angry": "gian",
    "giandu": "gian",
    "gian_du": "gian",
    "scared": "so_hai",
    "fear": "so_hai",
    "sohai": "so_hai",
    "whisper": "thi_tham",
    "thitham": "thi_tham",
    "serious": "nghiem_tuc",
    "nghiemtuc": "nghiem_tuc",
}


def get_emotion_preset(key_or_alias: Optional[str]) -> EmotionPreset:
    """Tra cứu preset cảm xúc theo tên hoặc alias."""
    if not key_or_alias:
        return EMOTION_PRESETS["binh_thuong"]
    k = key_or_alias.strip().lower()
    if k in EMOTION_PRESETS:
        return EMOTION_PRESETS[k]
    resolved = EMOTION_ALIASES.get(k)
    if resolved and resolved in EMOTION_PRESETS:
        return EMOTION_PRESETS[resolved]
    return EMOTION_PRESETS["binh_thuong"]


# Pattern bắt thẻ: [tag] hoặc [/tag]
TAG_REGEX = re.compile(r"\[(/?)([a-zA-Z0-9_]+)\]")


def parse_segments(
    text: str,
    default_emotion: str = "binh_thuong",
    auto_emotion: bool = False,
) -> List[Tuple[str, EmotionPreset]]:
    """
    Phân tách văn bản thành các phân đoạn (đoạn text, EmotionPreset).

    Hỗ trợ 2 kiểu thẻ:
    1. Kiểu cặp khối: [vui]Nội dung nhiều câu...[/vui]
    2. Kiểu đầu dòng/dòng: [vui] Câu này vui. (áp dụng cho hết dòng)

    Nếu auto_emotion=True và câu không có thẻ chỉ định:
    - Câu kết thúc bằng '!' -> hao_hung
    - Câu kết thúc bằng '...' -> buon
    - Mặc định -> default_emotion
    """
    default_preset = get_emotion_preset(default_emotion)
    if not text or not text.strip():
        return []

    lines = text.split("\n")
    segments: List[Tuple[str, EmotionPreset]] = []

    active_block_emotion: Optional[EmotionPreset] = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Kiểm tra nếu dòng chứa thẻ khối [tag]...[/tag] hoặc nhiều thẻ
        # Duyệt qua các token trong dòng
        cursor = 0
        current_line_emotion = active_block_emotion

        # Kiểm tra xem đầu dòng có gắn thẻ theo dòng không: ví dụ "[vui] Xin chào"
        line_start_match = re.match(r"^\[([a-zA-Z0-9_]+)\]\s*(.*)$", line_stripped)
        if line_start_match and not line_stripped.endswith(f"[/{line_start_match.group(1)}]"):
            tag_name = line_start_match.group(1).lower()
            if tag_name in EMOTION_PRESETS or tag_name in EMOTION_ALIASES:
                preset = get_emotion_preset(tag_name)
                content = line_start_match.group(2).strip()
                if content:
                    segments.append((content, preset))
                continue

        # Xử lý các thẻ cảm xúc inline / block trong dòng (chỉ bắt các thẻ cảm xúc hợp lệ, bỏ qua thẻ ngôn ngữ như [en], [vi])
        matches = [
            m for m in TAG_REGEX.finditer(line)
            if m.group(2).lower() in EMOTION_PRESETS or m.group(2).lower() in EMOTION_ALIASES
        ]
        if not matches:
            # Không có thẻ nào trên dòng này
            effective_preset = active_block_emotion or default_preset
            if auto_emotion and active_block_emotion is None:
                effective_preset = _infer_emotion_from_sentence(line_stripped, default_preset)
            segments.append((line_stripped, effective_preset))
            continue

        # Có thẻ trong dòng
        for m in matches:
            start, end = m.span()
            is_closing = bool(m.group(1))
            tag_name = m.group(2).lower()

            # Văn bản trước thẻ
            pre_text = line[cursor:start].strip()
            if pre_text:
                eff = current_line_emotion or default_preset
                segments.append((pre_text, eff))

            cursor = end

            if is_closing:
                # Đóng block
                if active_block_emotion and (
                    active_block_emotion.key == tag_name
                    or EMOTION_ALIASES.get(tag_name) == active_block_emotion.key
                ):
                    active_block_emotion = None
                    current_line_emotion = None
            else:
                # Mở block hoặc thẻ inline
                if tag_name in EMOTION_PRESETS or tag_name in EMOTION_ALIASES:
                    preset = get_emotion_preset(tag_name)
                    current_line_emotion = preset
                    active_block_emotion = preset

        # Phần còn lại sau thẻ cuối cùng
        remaining = line[cursor:].strip()
        if remaining:
            eff = current_line_emotion or default_preset
            segments.append((remaining, eff))

    # Gộp các segment liên tiếp có cùng EmotionPreset lại với nhau để tối ưu tổng hợp audio
    merged_segments: List[Tuple[str, EmotionPreset]] = []
    for seg_text, seg_preset in segments:
        clean_seg = seg_text.strip()
        if not clean_seg:
            continue
        if merged_segments and merged_segments[-1][1].key == seg_preset.key:
            prev_text, prev_preset = merged_segments[-1]
            merged_segments[-1] = (f"{prev_text}\n{clean_seg}", prev_preset)
        else:
            merged_segments.append((clean_seg, seg_preset))

    return merged_segments


def _infer_emotion_from_sentence(sentence: str, fallback: EmotionPreset) -> EmotionPreset:
    """Tự động suy luận cảm xúc dựa vào dấu câu nếu bật auto_emotion."""
    s = sentence.strip()
    if s.endswith("!") or "!" in s[-3:]:
        return EMOTION_PRESETS["hao_hung"]
    if s.endswith("...") or "…" in s[-2:]:
        return EMOTION_PRESETS["buon"]
    return fallback


def combine_emotion_and_speed(
    preset: EmotionPreset,
    user_speed_multiplier: float = 1.0,
    user_pitch_str: str = "+0Hz",
) -> Tuple[str, str, str, float]:
    """
    Kết hợp EmotionPreset với tùy chỉnh tốc độ và cao độ từ người dùng.

    Returns:
        (rate_str, pitch_str, volume_str, effective_speed_multiplier)
    """
    # 1. Tốc độ (Rate)
    # Tốc độ hiệu dụng = user_speed_multiplier * (1.0 + preset.rate_pct / 100.0)
    base_mult = 1.0 + (preset.rate_pct / 100.0)
    effective_mult = user_speed_multiplier * base_mult
    effective_mult = max(0.25, min(3.0, effective_mult))

    pct = int(round((effective_mult - 1.0) * 100))
    rate_str = f"+{pct}%" if pct >= 0 else f"{pct}%"

    # 2. Cao độ (Pitch)
    # Phân tích user_pitch (ví dụ: '+2Hz', '-3Hz', '+0Hz')
    user_pitch_val = 0
    match = re.match(r"^([+-]?\d+)\s*Hz$", user_pitch_str.strip(), re.I)
    if match:
        user_pitch_val = int(match.group(1))

    total_pitch = preset.pitch_hz + user_pitch_val
    pitch_str = f"+{total_pitch}Hz" if total_pitch >= 0 else f"{total_pitch}Hz"

    # 3. Âm lượng (Volume)
    vol_pct = preset.volume_pct
    volume_str = f"+{vol_pct}%" if vol_pct >= 0 else f"{vol_pct}%"

    return rate_str, pitch_str, volume_str, round(effective_mult, 2)
