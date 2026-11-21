"""Cấu hình và danh mục phong cách biên soạn cho công cụ VTS (Video-to-Script)."""

import json
import os
from dataclasses import dataclass
from typing import Dict, Optional

# Tên mô hình Gemini tối ưu cho Video
DEFAULT_MODEL = "gemini-2.0-flash"
FALLBACK_MODEL = "gemini-1.5-flash"

# Tên tệp lưu cấu hình cục bộ (chứa API Key nếu người dùng lưu lại)
CONFIG_FILENAME = ".vts_config.json"


@dataclass
class StylePreset:
    key: str
    name: str
    description: str
    tone: str
    primary_emotions: str


# Danh mục các phong cách biên soạn kịch bản từ video
STYLE_PRESETS: Dict[str, StylePreset] = {
    "recap": StylePreset(
        key="recap",
        name="Review / Tóm tắt kịch tính (Recap)",
        description="Lối dẫn dắt lôi cuốn, hồi hộp, nhịp điệu dồn dập, tạo sự kích thích tò mò cho người xem.",
        tone="Kịch tính, lôi cuốn, gay cấn",
        primary_emotions="[hao_hung], [so_hai], [gian], [vui]",
    ),
    "tiktok": StylePreset(
        key="tiktok",
        name="Shorts / TikTok / Reels (Dí dỏm, viral)",
        description="Câu từ ngắn gọn, bắt trend, hài hước, tiết tấu nhanh, tạo điểm nhấn trong 3 giây đầu.",
        tone="Trẻ trung, dí dỏm, năng động, bắt tai",
        primary_emotions="[vui], [hao_hung]",
    ),
    "documentary": StylePreset(
        key="documentary",
        name="Phim tài liệu / Thuyết minh (Documentary)",
        description="Quan sát bối cảnh, mô tả thiên nhiên, hành động và chiều sâu không gian một cách điềm đạm, sâu sắc.",
        tone="Điềm đạm, trang trọng, sâu sắc, tinh tế",
        primary_emotions="[nghiem_tuc], [binh_thuong], [thi_tham]",
    ),
    "monologue": StylePreset(
        key="monologue",
        name="Độc thoại nội tâm nhân vật (Monologue)",
        description="Tự động nhập vai vào nhân vật hoặc đối tượng chính trong video để nói ra cảm nghĩ thầm kín.",
        tone="Chân thật, giàu cảm xúc, gần gũi",
        primary_emotions="[thi_tham], [buon], [vui], [so_hai]",
    ),
    "descriptive": StylePreset(
        key="descriptive",
        name="Mô tả hành động / Phụ đề trợ năng (Descriptive)",
        description="Mô tả khách quan, chuẩn xác những gì đang diễn ra trên khung hình theo từng giây.",
        tone="Khách quan, rõ ràng, gãy gọn",
        primary_emotions="[binh_thuong], [nghiem_tuc]",
    ),
}

DEFAULT_STYLE = "recap"


def get_config_path() -> str:
    """Trả về đường dẫn tệp cấu hình .vts_config.json."""
    # Ưu tiên lưu trong thư mục dự án
    local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), CONFIG_FILENAME)
    return local_path


def get_api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    """
    Lấy Gemini API Key theo thứ tự ưu tiên:
    1. Tham số truyền vào trực tiếp
    2. Biến môi trường GEMINI_API_KEY
    3. Tệp cấu hình .vts_config.json
    """
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()

    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key

    config_path = get_config_path()
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                key = data.get("gemini_api_key", "").strip()
                if key:
                    return key
        except Exception:
            pass

    return None


def save_api_key(api_key: str) -> bool:
    """Lưu Gemini API Key vào tệp cấu hình cục bộ .vts_config.json."""
    if not api_key:
        return False

    config_path = get_config_path()
    data = {}
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    data["gemini_api_key"] = api_key.strip()

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
