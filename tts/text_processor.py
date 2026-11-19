"""Xử lý tệp văn bản và tiền xử lý nội dung trước khi chuyển sang TTS."""

import os
import re
from typing import List, Tuple

# Danh sách encoding thử nghiệm theo thứ tự ưu tiên
COMMON_ENCODINGS = [
    "utf-8-sig",  # UTF-8 có BOM
    "utf-8",      # Chuẩn UTF-8 phổ biến nhất
    "utf-16",     # UTF-16 (thường gặp khi xuất từ Windows Notepad)
    "utf-16-le",
    "utf-16-be",
    "cp1258",     # Windows Vietnamese encoding cũ
    "latin-1",    # Fallback dự phòng
]


def read_text_file(file_path: str) -> Tuple[str, str]:
    """
    Đọc tệp văn bản an toàn với khả năng tự động nhận diện encoding.

    Args:
        file_path: Đường dẫn tới file .txt

    Returns:
        Tuple (nội dung văn bản, bảng mã encoding đã phát hiện)

    Raises:
        FileNotFoundError: Nếu file không tồn tại
        ValueError: Nếu file rỗng hoặc không đọc được bằng các bảng mã thông dụng
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Không tìm thấy tệp: {file_path}")

    # Đọc raw bytes để thử giải mã
    with open(file_path, "rb") as f:
        raw_data = f.read()

    if not raw_data or not raw_data.strip():
        raise ValueError(f"Tệp văn bản '{file_path}' hoàn toàn rỗng!")

    detected_encoding = None
    decoded_text = None

    for enc in COMMON_ENCODINGS:
        try:
            decoded_text = raw_data.decode(enc)
            detected_encoding = enc
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if decoded_text is None:
        raise ValueError(f"Không thể giải mã tệp '{file_path}' với các bảng mã thông dụng ({COMMON_ENCODINGS}).")

    cleaned_text = clean_text(decoded_text)
    if not cleaned_text:
        raise ValueError(f"Tệp '{file_path}' không chứa nội dung chữ có thể đọc được.")

    return cleaned_text, detected_encoding


def clean_text(text: str) -> str:
    """
    Làm sạch văn bản thô:
    - Đồng bộ xuống dòng (\r\n -> \n)
    - Loại bỏ các ký tự điều khiển vô hình (trừ tab, newline)
    - Chuẩn hóa khoảng trắng dư thừa
    """
    if not text:
        return ""

    # Chuẩn hóa xuống dòng
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Loại bỏ ký tự điều khiển ẩn (giữ lại newline và tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Thu gọn khoảng trắng thừa trên từng dòng
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

    # Ghép lại, giới hạn tối đa 2 dòng trống liên tiếp
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return cleaned


def split_text_into_chunks(text: str, max_chars: int = 1500) -> List[str]:
    """
    Chia nhỏ văn bản dài thành các đoạn an toàn theo ranh giới câu hoặc đoạn văn,
    giúp Edge-TTS hoặc gTTS không bị quá tải hay timeout khi xử lý file lớn.

    Args:
        text: Văn bản đã được làm sạch
        max_chars: Số ký tự tối đa cho mỗi đoạn (mặc định 1500)

    Returns:
        Danh sách các đoạn văn bản ngắn hơn max_chars
    """
    text = text.strip()
    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    # Tách theo đoạn văn trước
    paragraphs = text.split("\n\n")

    current_chunk = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Nếu cả đoạn văn vượt quá max_chars, tách theo câu
        if len(para) > max_chars:
            sentences = re.split(r"(?<=[.!?。…\n])\s+", para)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Trường hợp đặc biệt: 1 câu đơn lẻ dài hơn max_chars (tách theo dấu phẩy hoặc space)
                if len(sentence) > max_chars:
                    sub_parts = re.split(r"(?<=[,;:\-])\s+", sentence)
                    for sub in sub_parts:
                        if len(sub) > max_chars:
                            # Tách cưỡng bức theo số từ
                            words = sub.split()
                            word_chunk = []
                            word_len = 0
                            for w in words:
                                if word_len + len(w) + 1 > max_chars:
                                    if word_chunk:
                                        chunks.append(" ".join(word_chunk))
                                    word_chunk = [w]
                                    word_len = len(w)
                                else:
                                    word_chunk.append(w)
                                    word_len += len(w) + 1
                            if word_chunk:
                                chunks.append(" ".join(word_chunk))
                        else:
                            if current_len + len(sub) + 1 > max_chars:
                                if current_chunk:
                                    chunks.append(" ".join(current_chunk))
                                current_chunk = [sub]
                                current_len = len(sub)
                            else:
                                current_chunk.append(sub)
                                current_len += len(sub) + 1
                else:
                    if current_len + len(sentence) + 1 > max_chars:
                        if current_chunk:
                            chunks.append(" ".join(current_chunk))
                        current_chunk = [sentence]
                        current_len = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_len += len(sentence) + 1
        else:
            if current_len + len(para) + 2 > max_chars:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_len = len(para)
            else:
                current_chunk.append(para)
                current_len += len(para) + (2 if current_chunk else 0)

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks
