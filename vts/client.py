"""Client kết nối Google Gemini API để phân tích video đa phương thức (VTS Client)."""

import os
import time
from typing import Callable, List, Optional

from vts.config import DEFAULT_MODEL, FALLBACK_MODEL, get_api_key
from vts.formatter import ScriptFormatter, ScriptSegment
from vts.prompts import build_system_instruction, get_prompt_for_style


class VTSClient:
    """Lớp kết nối Gemini Multimodal Vision API để phân tích video và sinh kịch bản."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
    ):
        self.api_key = get_api_key(api_key)
        self.model_name = model_name

    def analyze_video(
        self,
        video_path: str,
        style: str = "recap",
        language: str = "vi",
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> List[ScriptSegment]:
        """
        Xem và phân tích video để tạo kịch bản/phụ đề.

        Args:
            video_path: Đường dẫn tệp video (.mp4, .mov, .mkv, .avi...)
            style: Phong cách kịch bản ('recap', 'tiktok', 'documentary', 'monologue', 'descriptive')
            language: Ngôn ngữ ('vi' hoặc 'en')
            progress_callback: Hàm nhận callback (percent: int, message: str)

        Returns:
            Danh sách ScriptSegment đã được phân đoạn thời gian và gắn nhãn cảm xúc
        """
        if not self.api_key:
            raise ValueError(
                "Chưa tìm thấy Gemini API Key!\n"
                "Vui lòng lấy API Key miễn phí tại: https://aistudio.google.com/\n"
                "Sau đó đặt biến môi trường GEMINI_API_KEY hoặc truyền tham số --api-key."
            )

        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Không tìm thấy tệp video: {video_path}")

        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)

        if progress_callback:
            progress_callback(10, f"Đang chuẩn bị tệp video ({file_size_mb:.1f} MB)...")

        # Thử sử dụng google.genai trước, nếu chưa có thì dùng google.generativeai
        try:
            return self._analyze_with_genai_new(
                video_path, style, language, progress_callback
            )
        except ImportError:
            return self._analyze_with_generativeai_legacy(
                video_path, style, language, progress_callback
            )

    def _analyze_with_genai_new(
        self,
        video_path: str,
        style: str,
        language: str,
        progress_callback: Optional[Callable[[int, str], None]],
    ) -> List[ScriptSegment]:
        """Sử dụng SDK mới google.genai."""
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        if progress_callback:
            progress_callback(20, "Đang tải video lên Google Gemini...")

        uploaded_file = client.files.upload(file=video_path)

        # Chờ video chuyển sang trạng thái ACTIVE
        if progress_callback:
            progress_callback(40, "Đang phân tích khung hình video...")

        max_wait = 180  # 3 phút tối đa
        elapsed = 0
        while uploaded_file.state == "PROCESSING" and elapsed < max_wait:
            time.sleep(3)
            elapsed += 3
            uploaded_file = client.files.get(name=uploaded_file.name)
            if progress_callback:
                progress_callback(min(65, 40 + int(elapsed * 0.15)), "Đang xử lý dữ liệu hình ảnh...")

        if uploaded_file.state != "ACTIVE":
            raise RuntimeError(f"Tải video không thành công hoặc hết hạn chờ (Trạng thái: {uploaded_file.state})")

        if progress_callback:
            progress_callback(70, "AI đang xem video và biên soạn kịch bản...")

        sys_instruction = build_system_instruction(language=language)
        user_prompt = get_prompt_for_style(style_key=style, language=language)

        config = types.GenerateContentConfig(
            system_instruction=sys_instruction,
            temperature=0.7,
            response_mime_type="application/json",
        )

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=[uploaded_file, user_prompt],
                config=config,
            )
        except Exception as e:
            # Fallback sang model 1.5 nếu 2.0 quá tải
            if self.model_name != FALLBACK_MODEL:
                if progress_callback:
                    progress_callback(75, f"Thử lại với mô hình dự phòng ({FALLBACK_MODEL})...")
                response = client.models.generate_content(
                    model=FALLBACK_MODEL,
                    contents=[uploaded_file, user_prompt],
                    config=config,
                )
            else:
                raise e

        # Dọn dẹp tệp trên cloud
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass

        if progress_callback:
            progress_callback(90, "Đang hoàn thiện định dạng kịch bản...")

        raw_text = response.text or ""
        segments = ScriptFormatter.parse_model_output(raw_text)

        if progress_callback:
            progress_callback(100, f"Hoàn tất! Đã tạo {len(segments)} phân đoạn kịch bản.")

        return segments

    def _analyze_with_generativeai_legacy(
        self,
        video_path: str,
        style: str,
        language: str,
        progress_callback: Optional[Callable[[int, str], None]],
    ) -> List[ScriptSegment]:
        """Sử dụng SDK google.generativeai (phiên bản phổ biến)."""
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)

        if progress_callback:
            progress_callback(20, "Đang tải video lên Google Gemini...")

        uploaded_file = genai.upload_file(path=video_path)

        if progress_callback:
            progress_callback(40, "Đang phân tích khung hình video...")

        max_wait = 180
        elapsed = 0
        while uploaded_file.state.name == "PROCESSING" and elapsed < max_wait:
            time.sleep(3)
            elapsed += 3
            uploaded_file = genai.get_file(uploaded_file.name)
            if progress_callback:
                progress_callback(min(65, 40 + int(elapsed * 0.15)), "Đang xử lý dữ liệu hình ảnh...")

        if uploaded_file.state.name != "ACTIVE":
            raise RuntimeError(f"Tải video không thành công (Trạng thái: {uploaded_file.state.name})")

        if progress_callback:
            progress_callback(70, "AI đang xem video và biên soạn kịch bản...")

        sys_instruction = build_system_instruction(language=language)
        user_prompt = get_prompt_for_style(style_key=style, language=language)

        full_prompt = f"{sys_instruction}\n\n{user_prompt}"

        # Cấu hình model
        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={"temperature": 0.7, "response_mime_type": "application/json"},
        )

        try:
            response = model.generate_content([uploaded_file, full_prompt])
        except Exception as e:
            if self.model_name != FALLBACK_MODEL:
                if progress_callback:
                    progress_callback(75, f"Thử lại với mô hình dự phòng ({FALLBACK_MODEL})...")
                fallback_m = genai.GenerativeModel(
                    model_name=FALLBACK_MODEL,
                    generation_config={"temperature": 0.7, "response_mime_type": "application/json"},
                )
                response = fallback_m.generate_content([uploaded_file, full_prompt])
            else:
                raise e

        # Dọn dẹp tệp cloud
        try:
            genai.delete_file(uploaded_file.name)
        except Exception:
            pass

        if progress_callback:
            progress_callback(90, "Đang hoàn thiện định dạng kịch bản...")

        raw_text = response.text or ""
        segments = ScriptFormatter.parse_model_output(raw_text)

        if progress_callback:
            progress_callback(100, f"Hoàn tất! Đã tạo {len(segments)} phân đoạn kịch bản.")

        return segments
