"""Cấu hình và danh mục giọng đọc cho ứng dụng TTS."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class VoiceInfo:
    id: str
    name: str
    language: str
    gender: str
    engine: str
    description: str


# Danh mục giọng đọc ưu tiên cho Tiếng Việt và Tiếng Anh
VOICE_CATALOG: Dict[str, VoiceInfo] = {
    # --- Tiếng Việt (Edge-TTS AI Neural) ---
    "vi-VN-NamMinhNeural": VoiceInfo(
        id="vi-VN-NamMinhNeural",
        name="Nam Minh (Nam - Trầm ấm, rõ ràng)",
        language="vi-VN",
        gender="Male",
        engine="edge-tts",
        description="Giọng đọc nam truyền cảm, phong cách tin tức/thuyết minh.",
    ),
    "vi-VN-HoaiMyNeural": VoiceInfo(
        id="vi-VN-HoaiMyNeural",
        name="Hoài My (Nữ - Tự nhiên, truyền cảm)",
        language="vi-VN",
        gender="Female",
        engine="edge-tts",
        description="Giọng đọc nữ miền Bắc/chuẩn tự nhiên của Microsoft AI Neural.",
    ),
    # --- Tiếng Việt (gTTS Fallback) ---
    "gtts-vi": VoiceInfo(
        id="vi",
        name="Google Tiếng Việt (Nữ - gTTS)",
        language="vi",
        gender="Female",
        engine="gtts",
        description="Giọng đọc Google Dịch tiếng Việt (phương án phụ).",
    ),
    # --- Tiếng Anh US (Edge-TTS AI Neural) ---
    "en-US-JennyNeural": VoiceInfo(
        id="en-US-JennyNeural",
        name="Jenny (US - Nữ - Chuẩn bản xứ)",
        language="en-US",
        gender="Female",
        engine="edge-tts",
        description="Giọng nữ chuẩn Mỹ tự nhiên và mượt mà.",
    ),
    "en-US-GuyNeural": VoiceInfo(
        id="en-US-GuyNeural",
        name="Guy (US - Nam - Tự nhiên)",
        language="en-US",
        gender="Male",
        engine="edge-tts",
        description="Giọng nam chuẩn Mỹ đĩnh đạc, rõ âm.",
    ),
    "en-US-AriaNeural": VoiceInfo(
        id="en-US-AriaNeural",
        name="Aria (US - Nữ - Năng động)",
        language="en-US",
        gender="Female",
        engine="edge-tts",
        description="Giọng nữ Mỹ biểu cảm phong phú.",
    ),
    # --- Tiếng Anh UK (Edge-TTS AI Neural) ---
    "en-GB-SoniaNeural": VoiceInfo(
        id="en-GB-SoniaNeural",
        name="Sonia (UK - Nữ - Anh Quốc)",
        language="en-GB",
        gender="Female",
        engine="edge-tts",
        description="Giọng nữ phát âm chuẩn British English.",
    ),
    "en-GB-RyanNeural": VoiceInfo(
        id="en-GB-RyanNeural",
        name="Ryan (UK - Nam - Anh Quốc)",
        language="en-GB",
        gender="Male",
        engine="edge-tts",
        description="Giọng nam phát âm chuẩn British English.",
    ),
    # --- Tiếng Anh (gTTS Fallback) ---
    "gtts-en": VoiceInfo(
        id="en",
        name="Google English (Nữ - gTTS)",
        language="en",
        gender="Female",
        engine="gtts",
        description="Giọng đọc Google Dịch tiếng Anh (phương án phụ).",
    ),
}

# Giọng đọc mặc định theo ngôn ngữ
DEFAULT_VOICES = {
    "vi": "vi-VN-NamMinhNeural",
    "en": "en-US-JennyNeural",
}

# Các ngôn ngữ hỗ trợ chính
SUPPORTED_LANGUAGES = {
    "vi": "Tiếng Việt (Vietnamese)",
    "en": "Tiếng Anh (English)",
}


def get_voices_for_language(lang_code: str) -> List[VoiceInfo]:
    """Lấy danh sách các giọng đọc phù hợp với ngôn ngữ (vi hoặc en)."""
    lang_code = lang_code.lower()
    results = []
    for voice in VOICE_CATALOG.values():
        if voice.language.lower().startswith(lang_code):
            results.append(voice)
    return results


def get_voice_info(voice_key_or_id: str) -> Optional[VoiceInfo]:
    """Tìm thông tin giọng đọc theo key hoặc id."""
    if voice_key_or_id in VOICE_CATALOG:
        return VOICE_CATALOG[voice_key_or_id]
    for voice in VOICE_CATALOG.values():
        if voice.id == voice_key_or_id:
            return voice
    return None
