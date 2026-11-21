#!/usr/bin/env python3
"""
my_VTS - Desktop Graphical User Interface (GUI) with Tkinter.
Phân tích ngữ cảnh video và tự động biên kịch lời thoại / phụ đề.
Hoàn toàn độc lập với module TTS.
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional

from vts.config import DEFAULT_STYLE, STYLE_PRESETS, get_api_key, save_api_key
from vts.formatter import ScriptFormatter, ScriptSegment
from vts.client import VTSClient

# Từ điển đa ngôn ngữ cho giao diện (i18n)
TRANSLATIONS = {
    "vi": {
        "app_title": "my_VTS - Phân Tích Video & Tạo Kịch Bản / Phụ Đề",
        "header_title": "my_VTS: VIDEO-TO-SCRIPT & SUBTITLE",
        "header_sub": "Xem video • Phân tích ngữ cảnh hình ảnh • Tự động gắn thẻ cảm xúc cho TTS",
        "ui_lang_label": "🌐 Ngôn ngữ:",
        "input_frame": " 1. Chọn Tệp Video Đầu Vào ",
        "browse_video_btn": "📁 Chọn Video...",
        "video_hint": "Hỗ trợ các định dạng .mp4, .mov, .mkv, .avi, .webm (kể cả video câm, không có tiếng/chữ)",
        "settings_frame": " 2. Cài Đặt Phong Cách & Gemini API ",
        "style_label": "Phong cách kịch bản:",
        "speech_lang_label": "Ngôn ngữ kịch bản:",
        "lang_vi": "Tiếng Việt (vi)",
        "lang_en": "Tiếng Anh (en)",
        "api_key_label": "Gemini API Key:",
        "api_key_placeholder": "Nhập API Key từ aistudio.google.com...",
        "save_key_chk": "Ghi nhớ API Key trên máy",
        "show_key_chk": "Hiện Key",
        "analyze_btn": "▶ BẮT ĐẦU PHÂN TÍCH VIDEO",
        "analyzing_btn": "⏳ AI đang phân tích video...",
        "preview_frame": " 3. Kịch Bản & Phụ Đề (Có thể chỉnh sửa) ",
        "save_txt_btn": "💾 Lưu file Kịch bản (.txt)",
        "save_srt_btn": "📄 Xuất file Phụ đề (.srt)",
        "open_folder_btn": "📂 Mở thư mục lưu",
        "status_ready": "Sẵn sàng. Hãy chọn tệp video và nhấn 'Bắt đầu phân tích Video'.",
        "status_analyzing": "Đang xử lý: {msg}",
        "status_success": "Thành công! Đã phân tích {count} phân đoạn kịch bản.",
        "msg_no_video": "Vui lòng chọn tệp video trước khi phân tích!",
        "msg_no_key": "Vui lòng nhập Gemini API Key để tiếp tục!\n(Đăng ký miễn phí tại https://aistudio.google.com/)",
        "msg_saved_txt": "Đã lưu kịch bản tại:\n{path}",
        "msg_saved_srt": "Đã lưu phụ đề SRT tại:\n{path}",
        "stats_label": "{segments} phân cảnh | {chars:,} ký tự",
    },
    "en": {
        "app_title": "my_VTS - Video to Script & Subtitle Generator",
        "header_title": "my_VTS: VIDEO-TO-SCRIPT & SUBTITLE",
        "header_sub": "Analyze visual context in videos • Generate timed script with emotion tags for TTS",
        "ui_lang_label": "🌐 UI Language:",
        "input_frame": " 1. Select Input Video File ",
        "browse_video_btn": "📁 Browse Video...",
        "video_hint": "Supports .mp4, .mov, .mkv, .avi, .webm (even silent videos without audio/text)",
        "settings_frame": " 2. Script Style & Gemini API Settings ",
        "style_label": "Script Style:",
        "speech_lang_label": "Script Language:",
        "lang_vi": "Vietnamese (vi)",
        "lang_en": "English (en)",
        "api_key_label": "Gemini API Key:",
        "api_key_placeholder": "Enter API Key from aistudio.google.com...",
        "save_key_chk": "Remember API Key locally",
        "show_key_chk": "Show Key",
        "analyze_btn": "▶ START VIDEO ANALYSIS",
        "analyzing_btn": "⏳ AI is watching & analyzing video...",
        "preview_frame": " 3. Generated Script & Subtitles (Editable) ",
        "save_txt_btn": "💾 Save Script (.txt)",
        "save_srt_btn": "📄 Export Subtitles (.srt)",
        "open_folder_btn": "📂 Open Folder",
        "status_ready": "Ready. Select a video file and click 'Start Video Analysis'.",
        "status_analyzing": "Processing: {msg}",
        "status_success": "Success! Generated {count} script segments.",
        "msg_no_video": "Please select a video file first!",
        "msg_no_key": "Please provide a Gemini API Key to proceed!\n(Get one free at https://aistudio.google.com/)",
        "msg_saved_txt": "Saved script file at:\n{path}",
        "msg_saved_srt": "Saved SRT subtitle file at:\n{path}",
        "stats_label": "{segments} segments | {chars:,} characters",
    },
}


class VTSGuiApp(tk.Tk):
    """Giao diện người dùng Desktop cho công cụ VTS."""

    def __init__(self):
        super().__init__()

        self.current_lang = "vi"
        self.segments: List[ScriptSegment] = []
        self.last_saved_path: Optional[str] = None
        self.is_analyzing = False

        self.setup_window()
        self.create_widgets()
        self.apply_language()

        # Tải sẵn API Key nếu có
        saved_key = get_api_key()
        if saved_key:
            self.api_key_var.set(saved_key)
            self.save_key_var.set(True)

    def t(self, key: str, **kwargs) -> str:
        """Lấy chuỗi dịch theo ngôn ngữ UI."""
        template = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["vi"]).get(key, key)
        if kwargs:
            return template.format(**kwargs)
        return template

    def setup_window(self):
        self.title("my_VTS - Video to Script")
        self.geometry("960x780")
        self.minsize(800, 650)

        # Style cấu hình ttk
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Màu sắc hiện đại
        self.configure(bg="#F4F6F9")
        self.style.configure(".", background="#F4F6F9", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#1A202C", background="#F4F6F9")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#718096", background="#F4F6F9")
        self.style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), foreground="#FFFFFF", background="#2B6CB0")
        self.style.map("Primary.TButton", background=[("active", "#2C5282"), ("disabled", "#CBD5E0")])
        self.style.configure("Secondary.TButton", font=("Segoe UI", 9, "bold"), foreground="#2D3748", background="#E2E8F0")

    def create_widgets(self):
        # 1. Header Frame
        header_frame = tk.Frame(self, bg="#FFFFFF", padx=16, pady=12, highlightthickness=1, highlightbackground="#E2E8F0")
        header_frame.pack(fill="x")

        self.header_title = ttk.Label(header_frame, text="", style="Header.TLabel")
        self.header_title.pack(anchor="w")

        self.header_sub = ttk.Label(header_frame, text="", style="SubHeader.TLabel")
        self.header_sub.pack(anchor="w", pady=(2, 0))

        # Chọn ngôn ngữ UI ở góc trên bên phải
        lang_switch_frame = tk.Frame(header_frame, bg="#FFFFFF")
        lang_switch_frame.place(relx=1.0, rely=0.5, anchor="e")

        self.ui_lang_lbl = ttk.Label(lang_switch_frame, text="", background="#FFFFFF")
        self.ui_lang_lbl.pack(side="left", padx=(0, 4))

        self.ui_lang_combo = ttk.Combobox(
            lang_switch_frame,
            values=["Tiếng Việt", "English"],
            state="readonly",
            width=11,
        )
        self.ui_lang_combo.current(0)
        self.ui_lang_combo.bind("<<ComboboxSelected>>", self.on_ui_lang_changed)
        self.ui_lang_combo.pack(side="left")

        # Vùng nội dung cuộn chính
        content_frame = tk.Frame(self, bg="#F4F6F9", padx=16, pady=12)
        content_frame.pack(fill="both", expand=True)

        # 2. Frame Chọn Video
        self.video_group = ttk.LabelFrame(content_frame, text="", padding=10)
        self.video_group.pack(fill="x", pady=(0, 8))

        v_top = tk.Frame(self.video_group, bg="#F4F6F9")
        v_top.pack(fill="x")

        self.video_path_var = tk.StringVar()
        self.video_entry = ttk.Entry(v_top, textvariable=self.video_path_var, font=("Segoe UI", 10))
        self.video_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_btn = ttk.Button(v_top, text="", style="Secondary.TButton", command=self.browse_video)
        self.browse_btn.pack(side="right")

        self.video_hint_lbl = ttk.Label(self.video_group, text="", foreground="#718096", font=("Segoe UI", 8))
        self.video_hint_lbl.pack(anchor="w", pady=(4, 0))

        # 3. Frame Cài đặt & API Key
        self.settings_group = ttk.LabelFrame(content_frame, text="", padding=10)
        self.settings_group.pack(fill="x", pady=(0, 8))

        # Dòng 1: Phong cách kịch bản + Ngôn ngữ thoại
        s_row1 = tk.Frame(self.settings_group, bg="#F4F6F9")
        s_row1.pack(fill="x", pady=(0, 6))

        self.style_lbl = ttk.Label(s_row1, text="")
        self.style_lbl.pack(side="left", padx=(0, 6))

        self.style_keys = list(STYLE_PRESETS.keys())
        style_names = [STYLE_PRESETS[k].name for k in self.style_keys]
        self.style_combo = ttk.Combobox(s_row1, values=style_names, state="readonly", width=38)
        self.style_combo.current(0)
        self.style_combo.pack(side="left", padx=(0, 16))

        self.speech_lang_lbl = ttk.Label(s_row1, text="")
        self.speech_lang_lbl.pack(side="left", padx=(0, 6))

        self.speech_lang_var = tk.StringVar(value="vi")
        self.lang_vi_rb = ttk.Radiobutton(s_row1, text="", value="vi", variable=self.speech_lang_var)
        self.lang_vi_rb.pack(side="left", padx=(0, 8))
        self.lang_en_rb = ttk.Radiobutton(s_row1, text="", value="en", variable=self.speech_lang_var)
        self.lang_en_rb.pack(side="left")

        # Dòng 2: Gemini API Key
        s_row2 = tk.Frame(self.settings_group, bg="#F4F6F9")
        s_row2.pack(fill="x")

        self.api_key_lbl = ttk.Label(s_row2, text="")
        self.api_key_lbl.pack(side="left", padx=(0, 6))

        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(s_row2, textvariable=self.api_key_var, show="•", width=35)
        self.api_key_entry.pack(side="left", padx=(0, 8))

        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_chk = ttk.Checkbutton(s_row2, text="", variable=self.show_key_var, command=self.toggle_key_visibility)
        self.show_key_chk.pack(side="left", padx=(0, 10))

        self.save_key_var = tk.BooleanVar(value=True)
        self.save_key_chk = ttk.Checkbutton(s_row2, text="", variable=self.save_key_var)
        self.save_key_chk.pack(side="left")

        # 4. Nút Action Bắt đầu & Progress Bar
        action_frame = tk.Frame(content_frame, bg="#F4F6F9")
        action_frame.pack(fill="x", pady=(2, 8))

        self.analyze_btn = ttk.Button(
            action_frame,
            text="",
            style="Primary.TButton",
            command=self.start_analysis_thread,
        )
        self.analyze_btn.pack(fill="x", ipady=4)

        self.progress_bar = ttk.Progressbar(action_frame, mode="determinate")
        self.progress_bar.pack(fill="x", pady=(6, 2))

        self.status_lbl = ttk.Label(action_frame, text="", foreground="#4A5568", font=("Segoe UI", 9))
        self.status_lbl.pack(anchor="w")

        # 5. Khung Soạn thảo Kịch bản / Phụ đề
        self.preview_group = ttk.LabelFrame(content_frame, text="", padding=10)
        self.preview_group.pack(fill="both", expand=True, pady=(0, 8))

        text_container = tk.Frame(self.preview_group)
        text_container.pack(fill="both", expand=True)

        self.text_editor = tk.Text(
            text_container,
            wrap="word",
            font=("Consolas", 10),
            bg="#FFFFFF",
            fg="#2D3748",
            padx=8,
            pady=8,
            relief="solid",
            bd=1,
        )
        self.text_editor.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(text_container, orient="vertical", command=self.text_editor.yview)
        scroll.pack(side="right", fill="y")
        self.text_editor.config(yscrollcommand=scroll.set)
        self.text_editor.bind("<KeyRelease>", self.update_stats)

        # Thanh chân trang (Lưu & Mở thư mục)
        bottom_frame = tk.Frame(content_frame, bg="#F4F6F9")
        bottom_frame.pack(fill="x")

        self.stats_lbl = ttk.Label(bottom_frame, text="0 phân cảnh | 0 ký tự", foreground="#718096")
        self.stats_lbl.pack(side="left")

        btn_box = tk.Frame(bottom_frame, bg="#F4F6F9")
        btn_box.pack(side="right")

        self.save_txt_btn = ttk.Button(btn_box, text="", style="Secondary.TButton", command=self.save_txt_action)
        self.save_txt_btn.pack(side="left", padx=4)

        self.save_srt_btn = ttk.Button(btn_box, text="", style="Secondary.TButton", command=self.save_srt_action)
        self.save_srt_btn.pack(side="left", padx=4)

        self.open_folder_btn = ttk.Button(btn_box, text="", style="Secondary.TButton", command=self.open_output_folder)
        self.open_folder_btn.pack(side="left", padx=4)

    def apply_language(self):
        """Cập nhật toàn bộ nhãn văn bản theo ngôn ngữ đang chọn."""
        self.title(self.t("app_title"))
        self.header_title.config(text=self.t("header_title"))
        self.header_sub.config(text=self.t("header_sub"))
        self.ui_lang_lbl.config(text=self.t("ui_lang_label"))

        self.video_group.config(text=self.t("input_frame"))
        self.browse_btn.config(text=self.t("browse_video_btn"))
        self.video_hint_lbl.config(text=self.t("video_hint"))

        self.settings_group.config(text=self.t("settings_frame"))
        self.style_lbl.config(text=self.t("style_label"))
        self.speech_lang_lbl.config(text=self.t("speech_lang_label"))
        self.lang_vi_rb.config(text=self.t("lang_vi"))
        self.lang_en_rb.config(text=self.t("lang_en"))
        self.api_key_lbl.config(text=self.t("api_key_label"))
        self.save_key_chk.config(text=self.t("save_key_chk"))
        self.show_key_chk.config(text=self.t("show_key_chk"))

        if not self.is_analyzing:
            self.analyze_btn.config(text=self.t("analyze_btn"))
            self.status_lbl.config(text=self.t("status_ready"))

        self.preview_group.config(text=self.t("preview_frame"))
        self.save_txt_btn.config(text=self.t("save_txt_btn"))
        self.save_srt_btn.config(text=self.t("save_srt_btn"))
        self.open_folder_btn.config(text=self.t("open_folder_btn"))

    def on_ui_lang_changed(self, event=None):
        idx = self.ui_lang_combo.current()
        self.current_lang = "vi" if idx == 0 else "en"
        self.apply_language()

    def toggle_key_visibility(self):
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="•")

    def browse_video(self):
        filetypes = [
            ("Video Files", "*.mp4 *.mov *.mkv *.avi *.webm *.flv *.wmv"),
            ("All Files", "*.*"),
        ]
        chosen = filedialog.askopenfilename(title=self.t("browse_video_btn"), filetypes=filetypes)
        if chosen:
            self.video_path_var.set(chosen)

    def update_stats(self, event=None):
        text = self.text_editor.get("1.0", tk.END).strip()
        chars = len(text)
        # Đếm số dòng câu thoại (không tính dòng ghi chú #)
        speech_lines = [l for l in text.split("\n") if l.strip() and not l.strip().startswith("#")]
        self.stats_lbl.config(text=self.t("stats_label", segments=len(speech_lines), chars=chars))

    def start_analysis_thread(self):
        if self.is_analyzing:
            return

        video_path = self.video_path_var.get().strip().strip('"').strip("'")
        if not video_path or not os.path.isfile(video_path):
            messagebox.showwarning("my_VTS", self.t("msg_no_video"))
            return

        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("my_VTS", self.t("msg_no_key"))
            return

        # Lưu key nếu checkbox được bật
        if self.save_key_var.get():
            save_api_key(api_key)

        # Lấy style key
        style_idx = self.style_combo.current()
        selected_style = self.style_keys[style_idx] if 0 <= style_idx < len(self.style_keys) else DEFAULT_STYLE
        language = self.speech_lang_var.get()

        self.is_analyzing = True
        self.analyze_btn.config(state="disabled", text=self.t("analyzing_btn"))
        self.progress_bar["value"] = 5

        thread = threading.Thread(
            target=self._run_analysis_worker,
            args=(video_path, selected_style, language, api_key),
            daemon=True,
        )
        thread.start()

    def _run_analysis_worker(self, video_path: str, style: str, language: str, api_key: str):
        def progress_callback(pct: int, msg: str):
            self.after(0, self._update_progress_ui, pct, msg)

        try:
            client = VTSClient(api_key=api_key)
            segments = client.analyze_video(
                video_path=video_path,
                style=style,
                language=language,
                progress_callback=progress_callback,
            )
            self.after(0, self._on_analysis_success, video_path, segments)
        except Exception as e:
            self.after(0, self._on_analysis_error, str(e))

    def _update_progress_ui(self, pct: int, msg: str):
        self.progress_bar["value"] = pct
        self.status_lbl.config(text=self.t("status_analyzing", msg=msg))

    def _on_analysis_success(self, video_path: str, segments: List[ScriptSegment]):
        self.is_analyzing = False
        self.analyze_btn.config(state="normal", text=self.t("analyze_btn"))
        self.progress_bar["value"] = 100
        self.segments = segments

        formatted_txt = ScriptFormatter.to_txt(segments, include_timestamps=True)
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", formatted_txt)
        self.update_stats()

        self.status_lbl.config(text=self.t("status_success", count=len(segments)))

        # Tự động lưu 1 bản .txt cùng thư mục video
        base, _ = os.path.splitext(video_path)
        default_out = f"{base}_script.txt"
        ScriptFormatter.save_txt(segments, default_out)
        self.last_saved_path = default_out

    def _on_analysis_error(self, err_msg: str):
        self.is_analyzing = False
        self.analyze_btn.config(state="normal", text=self.t("analyze_btn"))
        self.progress_bar["value"] = 0
        self.status_lbl.config(text=f"Lỗi: {err_msg}")
        messagebox.showerror("my_VTS - Error", f"Đã xảy ra lỗi:\n{err_msg}")

    def save_txt_action(self):
        text_content = self.text_editor.get("1.0", tk.END).strip()
        if not text_content:
            return

        initial_file = "script.txt"
        if self.video_path_var.get():
            base = os.path.splitext(os.path.basename(self.video_path_var.get()))[0]
            initial_file = f"{base}_script.txt"

        chosen = filedialog.asksaveasfilename(
            title=self.t("save_txt_btn"),
            defaultextension=".txt",
            initialfile=initial_file,
            filetypes=[("Text File", "*.txt"), ("All Files", "*.*")],
        )
        if chosen:
            with open(chosen, "w", encoding="utf-8") as f:
                f.write(text_content)
            self.last_saved_path = chosen
            messagebox.showinfo("my_VTS", self.t("msg_saved_txt", path=chosen))

    def save_srt_action(self):
        if not self.segments:
            # Nếu người dùng đã sửa text trong editor, thử parse lại
            text_content = self.text_editor.get("1.0", tk.END).strip()
            self.segments = ScriptFormatter.parse_model_output(text_content)

        if not self.segments:
            messagebox.showwarning("my_VTS", "Chưa có nội dung phân đoạn để xuất SRT!")
            return

        initial_file = "subtitles.srt"
        if self.video_path_var.get():
            base = os.path.splitext(os.path.basename(self.video_path_var.get()))[0]
            initial_file = f"{base}.srt"

        chosen = filedialog.asksaveasfilename(
            title=self.t("save_srt_btn"),
            defaultextension=".srt",
            initialfile=initial_file,
            filetypes=[("SubRip Subtitle", "*.srt"), ("All Files", "*.*")],
        )
        if chosen:
            ScriptFormatter.save_srt(self.segments, chosen)
            self.last_saved_path = chosen
            messagebox.showinfo("my_VTS", self.t("msg_saved_srt", path=chosen))

    def open_output_folder(self):
        target_path = self.last_saved_path or self.video_path_var.get()
        if target_path and os.path.exists(target_path):
            folder = os.path.dirname(os.path.abspath(target_path))
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])


def main():
    app = VTSGuiApp()
    app.mainloop()


if __name__ == "__main__":
    main()
