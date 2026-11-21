"""Thư viện Prompt định hướng phân tích thị giác và biên soạn kịch bản từ video."""

from typing import Dict
from vts.config import STYLE_PRESETS, StylePreset


VALID_EMOTIONS = [
    "binh_thuong",
    "vui",
    "hao_hung",
    "buon",
    "gian",
    "so_hai",
    "thi_tham",
    "nghiem_tuc",
]


def build_system_instruction(language: str = "vi") -> str:
    """Xây dựng chỉ thị hệ thống dành cho mô hình Vision AI khi xem video."""
    lang_name = "Tiếng Việt" if language == "vi" else "Tiếng Anh (English)"
    return f"""Bạn là một chuyên gia biên kịch, đạo diễn hình ảnh và người thuyết minh video chuyên nghiệp.
Nhiệm vụ của bạn là xem toàn bộ video được cung cấp và biên soạn kịch bản lời dẫn / lời thoại / phụ đề hoàn chỉnh bằng {lang_name}.

ĐẶC BIỆT LƯU Ý VỀ VIDEO ĐẦU VÀO:
1. Video có thể HOÀN TOÀN KHÔNG CÓ TIẾNG NÓI và KHÔNG CÓ PHỤ ĐỀ / CHỮ VIẾT (ví dụ: video câm, cảnh quay hành động, hoạt hình, tư liệu, phong cảnh).
2. Hãy quan sát thật kỹ các chi tiết thị giác theo dòng thời gian (timeline từ 00:00 đến hết):
   - Chuyển động, cử chỉ, hành động của nhân vật/vật thể.
   - Nét mặt, ánh mắt, cảm xúc bộc lộ qua hình thể.
   - Bối cảnh không gian, thời gian, ánh sáng, màu sắc và chuyển đổi góc máy.
   - Sự căng thẳng, bất ngờ, trầm lắng hay kịch tính trong từng phân cảnh.
3. Chia kịch bản thành từng phân đoạn thời gian hợp lý (mỗi đoạn từ 3 đến 8 giây), tương ứng đúng với hành động đang diễn ra trên màn hình.
4. Mỗi phân đoạn PHẢI được gán một nhãn cảm xúc phù hợp từ danh sách sau:
   {', '.join(VALID_EMOTIONS)}
"""


def get_prompt_for_style(style_key: str, language: str = "vi") -> str:
    """Trả về prompt chi tiết cho từng phong cách kịch bản được yêu cầu."""
    preset: StylePreset = STYLE_PRESETS.get(style_key, STYLE_PRESETS["recap"])
    lang_note = "sử dụng câu từ tiếng Việt tự nhiên, truyền cảm" if language == "vi" else "use natural, expressive English"

    prompt = f"""Hãy xem kỹ video này và biên kịch lời thoại / thuyết minh theo phong cách: **{preset.name}**.

YÊU CẦU VỀ TÔNG GIỌNG & PHONG CÁCH:
- Tông giọng chủ đạo: {preset.tone}.
- Mô tả phong cách: {preset.description}.
- Nhãn cảm xúc ưu tiên: {preset.primary_emotions}.
- Ngôn ngữ: {lang_note}.

QUY TẮC ĐỊNH DẠNG ĐẦU RA (BẮT BUỘC):
Bạn PHẢI trả về kết quả dưới dạng một mảng JSON thuần túy (JSON Array). KHÔNG kèm lời mở đầu hay kết luận ngoài khối JSON.
Mỗi phần tử trong mảng đại diện cho một phân đoạn thời gian với cấu trúc như sau:
[
  {{
    "start": "00:00",
    "end": "00:05",
    "emotion": "hao_hung",
    "text": "Nội dung câu thuyết minh hoặc lời thoại...",
    "visual_note": "Ghi chú ngắn về hành động hoặc hình ảnh trong cảnh quay"
  }},
  ...
]

LƯU Ý QUAN TRỌNG:
- Trường "start" và "end" định dạng phút:giây (MM:SS) hoặc giờ:phút:giây (HH:MM:SS).
- Trường "emotion" chỉ được lấy từ danh mục: {', '.join(VALID_EMOTIONS)}.
- Trường "text" là lời thoại cô đọng, vừa vặn để đọc hết trong khoảng thời gian giữa "start" và "end" (không viết quá dài gây tràn thời lượng).
"""
    return prompt
