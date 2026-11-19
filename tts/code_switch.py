"""Module xử lý chuyển đổi ngôn ngữ hỗn hợp (Code-Switching / Mixed-Language TTS).
Hỗ trợ gắn thẻ ngôn ngữ [en]...[/en], [vi]...[/vi] và tự động phát hiện từ/câu tiếng Anh
trong văn bản tiếng Việt để phát âm chuẩn bản ngữ.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from tts.config import DEFAULT_VOICES, VOICE_CATALOG, VoiceInfo, get_voice_info
from tts.emotion import EmotionPreset, get_emotion_preset, parse_segments

# Cặp giọng đọc đồng điệu theo giới tính giữa Tiếng Việt và Tiếng Anh
VOICE_PAIRS = {
    # Nam tiếng Việt -> Nam tiếng Mỹ
    "vi-VN-NamMinhNeural": "en-US-GuyNeural",
    # Nữ tiếng Việt -> Nữ tiếng Mỹ
    "vi-VN-HoaiMyNeural": "en-US-JennyNeural",
    # Google TTS
    "vi": "en",
    "gtts-vi": "en",
    # Chiều ngược lại (nếu bài đọc tiếng Anh xen tiếng Việt)
    "en-US-GuyNeural": "vi-VN-NamMinhNeural",
    "en-US-JennyNeural": "vi-VN-HoaiMyNeural",
    "en-US-AriaNeural": "vi-VN-HoaiMyNeural",
    "en-GB-RyanNeural": "vi-VN-NamMinhNeural",
    "en-GB-SoniaNeural": "vi-VN-HoaiMyNeural",
    "en": "vi",
    "gtts-en": "vi",
}

# Regex bắt thẻ ngôn ngữ: [en]...[/en], [vi]...[/vi], [english]...[/english], [vietnamese]...[/vietnamese]
LANG_TAG_REGEX = re.compile(
    r"\[(en|english|us|uk|vi|vietnamese)\](.*?)\[/\1\]",
    re.IGNORECASE | re.DOTALL,
)

# Danh sách từ mượn và thuật ngữ tiếng Anh thông dụng trong công nghệ, kinh doanh, đời sống
COMMON_ENGLISH_WORDS: Set[str] = {
    # Thuật ngữ công nghệ / IT
    "ai", "api", "app", "apps", "backend", "frontend", "fullstack", "bug", "bugs",
    "code", "coding", "coder", "database", "data", "deep learning", "machine learning",
    "framework", "hardware", "software", "laptop", "pc", "server", "cloud",
    "deploy", "release", "version", "update", "upgrade", "setup", "install",
    "python", "javascript", "react", "vue", "angular", "node", "nodejs",
    "docker", "kubernetes", "git", "github", "gitlab", "commit", "push", "pull",
    "cache", "cookie", "session", "token", "login", "logout", "signin", "signup",
    "algorithm", "neural", "network", "ui", "ux", "interface", "designer", "developer",
    # Công sở, văn phòng, quản lý
    "deadline", "feedback", "meeting", "review", "slide", "presentation",
    "project", "task", "tasks", "team", "leader", "manager", "ceo", "cto",
    "kpi", "okr", "report", "sale", "sales", "marketing", "customer", "client",
    "check-in", "checkin", "checkout", "follow-up", "brief", "pitch", "deal",
    "email", "mail", "message", "chat", "call", "online", "offline", "remote",
    # Từ mượn đời sống / giao tiếp thông dụng
    "hello", "hi", "goodbye", "bye", "thanks", "thank you", "welcome",
    "sorry", "ok", "okay", "yes", "no", "cool", "super", "smart", "pro",
    "fast", "slow", "easy", "free", "hot", "trend", "trending", "vlog", "stream",
    "livestream", "podcast", "video", "audio", "sound", "track", "music",
    "smartphone", "wifi", "bluetooth", "camera", "game", "gamer", "play",
}

# Các từ tiếng Việt không dấu dễ bị nhầm thành từ tiếng Anh (Blacklist để tránh nhận diện sai)
VIETNAMESE_HOMOGRAPHS: Set[str] = {
    "la", "va", "co", "di", "to", "me", "an", "em", "so", "ca", "do", "ra", "ma",
    "con", "nam", "bat", "cho", "lam", "den", "ngay", "muon", "biet", "duoc", "khong",
    "hay", "luc", "sau", "truoc", "chua", "theo", "trong", "ngoai", "tren", "duoi",
}


@dataclass
class CodeSwitchChunk:
    text: str
    lang: str          # 'vi' hoặc 'en'
    voice_id: str      # Mã giọng đọc cụ thể cho đoạn này
    emotion_preset: EmotionPreset


def get_paired_voice(base_voice_id: str, target_lang: str = "en") -> str:
    """
    Tìm giọng đọc phù hợp cùng giới tính và engine cho ngôn ngữ đích.
    Ví dụ: NamMinh (Nam) -> Guy (Nam), HoaiMy (Nữ) -> Jenny (Nữ).
    """
    if base_voice_id in VOICE_PAIRS:
        return VOICE_PAIRS[base_voice_id]

    base_info = get_voice_info(base_voice_id)
    if not base_info:
        return DEFAULT_VOICES.get(target_lang, "en-US-JennyNeural")

    target_lang_prefix = target_lang.lower()[:2]
    candidate_voices = [
        v for v in VOICE_CATALOG.values()
        if v.language.lower().startswith(target_lang_prefix) and v.engine == base_info.engine
    ]

    # Ưu tiên giọng cùng giới tính
    for v in candidate_voices:
        if v.gender.lower() == base_info.gender.lower():
            return v.id

    if candidate_voices:
        return candidate_voices[0].id

    return DEFAULT_VOICES.get(target_lang, "en-US-JennyNeural")


def is_english_token(word: str) -> bool:
    """
    Kiểm tra xem một từ đơn có phải là tiếng Anh không dựa trên đặc trưng:
    1. Chứa các chữ cái không thuộc bảng chữ cái tiếng Việt: w, f, j, z
    2. Nằm trong từ điển thuật ngữ tiếng Anh phổ biến
    3. Chứa hậu tố ngữ pháp đặc trưng tiếng Anh (-ing, -tion, -ment, -ed...)
    """
    w = word.strip(".,!?:;\"'()[]{}«»-–—").lower()
    if not w or len(w) < 2:
        return False

    # Loại bỏ nếu nằm trong danh sách từ tiếng Việt không dấu dễ nhầm
    if w in VIETNAMESE_HOMOGRAPHS:
        return False

    # Nếu nằm trong từ điển phổ biến
    if w in COMMON_ENGLISH_WORDS:
        return True

    # Nếu chứa ký tự đặc thù tiếng Anh không có trong chữ quốc ngữ thuần túy
    if any(c in "wfjz" for c in w):
        return True

    # Nếu có hậu tố ngữ pháp tiếng Anh rõ rệt
    if len(w) >= 5 and (
        w.endswith("ing")
        or w.endswith("tion")
        or w.endswith("tions")
        or w.endswith("ment")
        or w.endswith("able")
        or w.endswith("ship")
        or w.endswith("ness")
    ):
        return True

    return False


def detect_english_phrases(sentence: str) -> List[Tuple[str, str]]:
    """
    Phân tích một câu văn tiếng Việt và nhận diện các cụm từ / từ tiếng Anh.
    Trả về danh sách các đoạn (text, lang) với lang là 'vi' hoặc 'en'.
    """
    sentence = sentence.strip()
    if not sentence:
        return []

    tokens = re.split(r"(\s+|[.,!?:;\"'()]+)", sentence)
    segments: List[Tuple[str, str]] = []
    current_text = []
    current_lang = "vi"

    i = 0
    while i < len(tokens):
        token = tokens[i]
        clean_tok = token.strip()

        if not clean_tok:
            # Khoảng trắng
            if current_text:
                current_text.append(token)
            i += 1
            continue

        # Nếu token chỉ là dấu câu / ký tự đặc biệt (không chứa chữ hoặc số), gắn luôn vào phân đoạn hiện tại
        if not re.search(r"\w", clean_tok):
            current_text.append(token)
            i += 1
            continue

        # Kiểm tra cụm 2 từ (ví dụ: "machine learning", "deep learning", "thank you")
        if i + 2 < len(tokens):
            two_words = f"{token}{tokens[i+1]}{tokens[i+2]}".lower()
            two_clean = f"{token} {tokens[i+2]}".lower()
            if two_clean in COMMON_ENGLISH_WORDS or two_words in COMMON_ENGLISH_WORDS:
                if current_lang != "en" and current_text:
                    segments.append(("".join(current_text), current_lang))
                    current_text = []
                current_lang = "en"
                current_text.append(f"{token}{tokens[i+1]}{tokens[i+2]}")
                i += 3
                continue

        # Kiểm tra từ đơn
        tok_is_en = is_english_token(token)
        tok_lang = "en" if tok_is_en else "vi"

        if tok_lang != current_lang:
            if current_text:
                segments.append(("".join(current_text), current_lang))
                current_text = []
            current_lang = tok_lang

        current_text.append(token)
        i += 1

    if current_text:
        segments.append(("".join(current_text), current_lang))

    # Gộp và làm sạch phân đoạn
    cleaned_segments: List[Tuple[str, str]] = []
    for s_text, s_lang in segments:
        s_clean = s_text.strip()
        if not s_clean:
            continue
        # Nếu đoạn chỉ toàn dấu câu, ghép luôn vào đoạn trước
        if not re.search(r"\w", s_clean):
            if cleaned_segments:
                prev_t, prev_l = cleaned_segments[-1]
                cleaned_segments[-1] = (f"{prev_t} {s_clean}", prev_l)
            continue

        if cleaned_segments and cleaned_segments[-1][1] == s_lang:
            prev_t, prev_l = cleaned_segments[-1]
            cleaned_segments[-1] = (f"{prev_t} {s_clean}", prev_l)
        else:
            cleaned_segments.append((s_clean, s_lang))

    return cleaned_segments if cleaned_segments else [(sentence, "vi")]


def parse_code_switch_segments(
    text: str,
    base_voice_id: str,
    base_lang: str = "vi",
    paired_voice_id: Optional[str] = None,
    auto_detect: bool = True,
    default_emotion: str = "binh_thuong",
    auto_emotion: bool = False,
) -> List[CodeSwitchChunk]:
    """
    Phân tách toàn bộ văn bản thành danh sách CodeSwitchChunk, kết hợp cả
    thẻ cảm xúc [vui]...[/vui] và thẻ ngôn ngữ [en]...[/en] hoặc tự động phát hiện.
    """
    if not paired_voice_id:
        target_paired_lang = "en" if base_lang.startswith("vi") else "vi"
        paired_voice_id = get_paired_voice(base_voice_id, target_lang=target_paired_lang)

    # 1. Bước 1: Phân tách theo thẻ cảm xúc trước (giữ nguyên ngữ cảnh cảm xúc của câu)
    emotion_segments = parse_segments(
        text=text,
        default_emotion=default_emotion,
        auto_emotion=auto_emotion,
    )

    final_chunks: List[CodeSwitchChunk] = []

    for seg_text, emo_preset in emotion_segments:
        seg_text = seg_text.strip()
        if not seg_text:
            continue

        # 2. Bước 2: Kiểm tra thẻ ngôn ngữ tường minh [en]...[/en], [vi]...[/vi]
        cursor = 0
        explicit_parts: List[Tuple[str, str]] = []

        for m in LANG_TAG_REGEX.finditer(seg_text):
            start, end = m.span()
            tag_type = m.group(1).lower()
            inner_content = m.group(2).strip()

            target_l = "en" if tag_type in ["en", "english", "us", "uk"] else "vi"

            # Phần văn bản trước thẻ
            pre = seg_text[cursor:start].strip()
            if pre:
                explicit_parts.append((pre, base_lang))

            if inner_content:
                explicit_parts.append((inner_content, target_l))

            cursor = end

        remaining = seg_text[cursor:].strip()
        if remaining:
            explicit_parts.append((remaining, base_lang))

        if not explicit_parts:
            explicit_parts = [(seg_text, base_lang)]

        # 3. Bước 3: Nếu auto_detect bật và đoạn mang base_lang == 'vi', tìm các từ tiếng Anh xen kẽ
        for exp_text, exp_lang in explicit_parts:
            if auto_detect and exp_lang == "vi":
                sub_lang_segs = detect_english_phrases(exp_text)
            else:
                sub_lang_segs = [(exp_text, exp_lang)]

            for sub_text, sub_lang in sub_lang_segs:
                sub_clean = sub_text.strip()
                if not sub_clean:
                    continue

                if sub_lang == "en":
                    chosen_voice = paired_voice_id if base_lang == "vi" else base_voice_id
                else:
                    chosen_voice = base_voice_id if base_lang == "vi" else paired_voice_id

                final_chunks.append(
                    CodeSwitchChunk(
                        text=sub_clean,
                        lang=sub_lang,
                        voice_id=chosen_voice,
                        emotion_preset=emo_preset,
                    )
                )

    # 4. Gộp các chunk liên tiếp nếu cùng giọng đọc, cùng ngôn ngữ và cùng cảm xúc
    merged: List[CodeSwitchChunk] = []
    for chunk in final_chunks:
        c_text = chunk.text.strip()
        if not c_text:
            continue
        # Nếu chunk không chứa chữ/số (chỉ là dấu câu thừa), ghép vào chunk trước
        if not re.search(r"\w", c_text):
            if merged:
                prev = merged[-1]
                merged[-1] = CodeSwitchChunk(
                    text=f"{prev.text} {c_text}",
                    lang=prev.lang,
                    voice_id=prev.voice_id,
                    emotion_preset=prev.emotion_preset,
                )
            continue

        if (
            merged
            and merged[-1].voice_id == chunk.voice_id
            and merged[-1].lang == chunk.lang
            and merged[-1].emotion_preset.key == chunk.emotion_preset.key
        ):
            prev = merged[-1]
            merged[-1] = CodeSwitchChunk(
                text=f"{prev.text} {c_text}",
                lang=prev.lang,
                voice_id=prev.voice_id,
                emotion_preset=prev.emotion_preset,
            )
        else:
            merged.append(chunk)

    return merged
