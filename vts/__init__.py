"""Package VTS (Video-to-Script) - Phân tích ngữ cảnh video và tự động biên soạn kịch bản/phụ đề.
Hoàn toàn độc lập với module TTS.
"""

from vts.config import STYLE_PRESETS, get_api_key, save_api_key
from vts.formatter import ScriptFormatter, ScriptSegment
from vts.prompts import get_prompt_for_style

__all__ = [
    "STYLE_PRESETS",
    "ScriptFormatter",
    "ScriptSegment",
    "get_api_key",
    "save_api_key",
    "get_prompt_for_style",
]
