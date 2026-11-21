#!/usr/bin/env python3
"""
my_TTS - Desktop Graphical User Interface (GUI) with Tkinter.
Converts plain text (.txt) into high-quality speech audio (.mp3).
Supports bilingual UI (English & Vietnamese), voice selection, speed adjustment, and emotion tags.
"""

import os
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict

from tts.code_switch import get_paired_voice
from tts.config import DEFAULT_VOICES, VoiceInfo, get_voices_for_language
from tts.emotion import EMOTION_PRESETS, get_emotion_preset
from tts.engine import TTSEngine, parse_speed
from tts.text_processor import read_text_file

# Internationalization Dictionary (i18n)
TRANSLATIONS = {
    "en": {
        "app_title": "Text-to-Speech Converter (Vietnamese & English)",
        "header_title": "TEXT-TO-SPEECH CONVERTER (TTS)",
        "header_sub": "Vietnamese & English • Speed Customization (0.5x-2.0x) • Emotion Tags [tag] • AI Neural",
        "ui_lang_label": "🌐 Language:",
        "input_frame": " 1. Input Text File (.txt) ",
        "browse_txt_btn": "📁 Browse .txt file...",
        "text_preview_frame": " Text Content & Editor ",
        "insert_tag_btn": "➕ Insert Emotion Tag [tag]",
        "insert_lang_btn": "🌐 Lang Tag [en]/[vi]",
        "tag_hint": "Add [tag] or [en]...[/en] in text",
        "block_tag_label": "{}...[/{}] (Block for long paragraph)",
        "settings_frame": " Voice, Speed & Emotion Settings ",
        "target_lang_label": "Speech Language:",
        "lang_vi": "Vietnamese (vi)",
        "lang_en": "English (en)",
        "engine_label": "Engine:",
        "engine_edge": "edge-tts (Microsoft AI Neural - Recommended)",
        "engine_gtts": "gtts (Google Translate)",
        "voice_label": "Voice:",
        "code_switch_frame": " English Code-Switching (Bilingual) ",
        "code_switch_chk": "Native English pronunciation for English terms",
        "auto_lang_chk": "Auto-detect English terms (AI, deadline...)",
        "paired_voice_lbl": "Paired Voice:",
        "emotion_label": "Default Emotion (for untagged sentences):",
        "detect_tags_chk": "Detect [tag] emotion tags in text",
        "auto_emotion_chk": "Auto-detect emotion from punctuation (!, ...)",
        "speed_header": "Base Speed:",
        "speed_factor": "Factor: ",
        "save_mp3_label": "Save MP3 file at:",
        "char_count": "{chars:,} characters | {words:,} words",
        "start_btn": "▶ START CONVERTING TO MP3",
        "converting_btn": "⏳ Converting audio...",
        "status_ready": "Ready. Choose a .txt file or type text to begin.",
        "status_file_loaded": "Loaded file: {name} (Encoding: {enc})",
        "status_success": "Success ({speed:.2f}x - {size:.1f} KB): {name}",
        "status_error": "Error: {err}",
        "open_folder_btn": "📂 Open File Location",
        "play_audio_btn": "🎵 Play MP3 Audio",
        "dialog_empty_title": "Warning",
        "dialog_empty_msg": "Text content is empty! Please choose a .txt file or enter text.",
        "dialog_file_err_title": "File Read Error",
        "dialog_file_err_msg": "Cannot read text file:\n{err}",
        "dialog_success_title": "Completed",
        "dialog_success_msg": "Text-to-Speech conversion successful!\n\nFile: {name}\nBase Speed: {speed:.2f}x\nFile Size: {size:.1f} KB\nPath: {path}",
        "dialog_conv_err_title": "Conversion Error",
        "dialog_conv_err_msg": "An error occurred during audio synthesis:\n\n{err}",
        "dialog_no_audio_title": "Notice",
        "dialog_no_audio_msg": "No audio file has been generated yet.",
        "dialog_missing_audio_msg": "Cannot find MP3 file to play.",
        "speed_normal": "Normal",
        "speed_very_slow": "Very Slow",
        "speed_slow": "Slow",
        "speed_slightly_fast": "Slightly Fast",
        "speed_fast": "Fast",
        "speed_very_fast": "Very Fast",
    },
    "vi": {
        "app_title": "Chuyển đổi Văn bản thành Giọng nói (Tiếng Việt & English)",
        "header_title": "CHUYỂN ĐỔI VĂN BẢN THÀNH GIỌNG NÓI (TTS)",
        "header_sub": "Tiếng Việt & Tiếng Anh • Tùy chỉnh tốc độ (0.5x-2.0x) • Cảm xúc từng câu [tag] • AI Neural",
        "ui_lang_label": "🌐 Ngôn ngữ:",
        "input_frame": " 1. Tệp văn bản đầu vào (.txt) ",
        "browse_txt_btn": "📁 Duyệt tệp .txt...",
        "text_preview_frame": " Nội dung văn bản & Soạn thảo ",
        "insert_tag_btn": "➕ Chèn thẻ cảm xúc [tag]",
        "insert_lang_btn": "🌐 Thẻ [en]/[vi]",
        "tag_hint": "Gắn [tag] hoặc [en]...[/en] trong văn bản",
        "block_tag_label": "{}...[/{}] (Cặp thẻ cho đoạn dài)",
        "settings_frame": " Cài đặt Giọng nói, Tốc độ & Cảm xúc ",
        "target_lang_label": "Ngôn ngữ đọc:",
        "lang_vi": "Tiếng Việt (vi)",
        "lang_en": "Tiếng Anh (en)",
        "engine_label": "Công nghệ (Engine):",
        "engine_edge": "edge-tts (Microsoft AI Neural - Khuyên dùng)",
        "engine_gtts": "gtts (Google Translate)",
        "voice_label": "Giọng đọc (Voice):",
        "code_switch_frame": " Phát âm Tiếng Anh chuẩn (Song ngữ) ",
        "code_switch_chk": "Phát âm chuẩn bản ngữ cho từ/câu Tiếng Anh",
        "auto_lang_chk": "Tự động phát hiện từ mượn tiếng Anh (AI, deadline...)",
        "paired_voice_lbl": "Giọng Anh ghép đôi:",
        "emotion_label": "Cảm xúc mặc định (cho câu không gắn thẻ):",
        "detect_tags_chk": "Nhận diện thẻ [tag] cảm xúc trong văn bản",
        "auto_emotion_chk": "Tự động đoán cảm xúc qua dấu câu (!, ...)",
        "speed_header": "Tốc độ cơ sở (Speed):",
        "speed_factor": "Hệ số: ",
        "save_mp3_label": "Lưu file MP3 tại:",
        "char_count": "{chars:,} ký tự | {words:,} từ",
        "start_btn": "▶ BẮT ĐẦU CHUYỂN ĐỔI SANG MP3",
        "converting_btn": "⏳ Đang xử lý chuyển đổi...",
        "status_ready": "Sẵn sàng. Hãy chọn file .txt hoặc nhập văn bản để bắt đầu.",
        "status_file_loaded": "Đã nạp file: {name} (Bảng mã: {enc})",
        "status_success": "Thành công ({speed:.2f}x - {size:.1f} KB): {name}",
        "status_error": "Lỗi: {err}",
        "open_folder_btn": "📂 Mở thư mục chứa file",
        "play_audio_btn": "🎵 Nghe file MP3",
        "dialog_empty_title": "Cảnh báo",
        "dialog_empty_msg": "Nội dung văn bản đang trống! Hãy chọn file .txt hoặc gõ văn bản.",
        "dialog_file_err_title": "Lỗi đọc file",
        "dialog_file_err_msg": "Không thể đọc file văn bản:\n{err}",
        "dialog_success_title": "Hoàn tất",
        "dialog_success_msg": "Đã chuyển đổi văn bản sang MP3 thành công!\n\nTệp: {name}\nTốc độ đọc cơ sở: {speed:.2f}x\nDung lượng: {size:.1f} KB\nĐường dẫn: {path}",
        "dialog_conv_err_title": "Lỗi chuyển đổi",
        "dialog_conv_err_msg": "Đã xảy ra lỗi khi tạo âm thanh:\n\n{err}",
        "dialog_no_audio_title": "Thông báo",
        "dialog_no_audio_msg": "Chưa có file âm thanh nào được tạo.",
        "dialog_missing_audio_msg": "Không tìm thấy file MP3 để phát.",
        "speed_normal": "Bình thường",
        "speed_very_slow": "Rất chậm",
        "speed_slow": "Chậm",
        "speed_slightly_fast": "Hơi nhanh",
        "speed_fast": "Nhanh",
        "speed_very_fast": "Rất nhanh",
    },
}


class TTSAppGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.geometry("960x780")
        self.root.minsize(860, 700)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.engine = TTSEngine()
        self.is_converting = False
        self.last_output_file = ""

        # UI Language state ("en" or "vi")
        self.ui_lang = "en"  # Default UI language is English

        # State Variables
        self.var_input_file = tk.StringVar()
        self.var_output_file = tk.StringVar()
        self.var_speech_lang = tk.StringVar(value="vi")
        self.var_voice_name = tk.StringVar()
        self.var_engine = tk.StringVar(value="edge-tts")
        self.var_ui_lang_combo = tk.StringVar(value="English")

        # Speed variables
        self.var_speed_mult = tk.DoubleVar(value=1.0)
        self.var_speed_spin = tk.StringVar(value="1.00")
        self.var_rate_label = tk.StringVar()

        # Emotion variables
        self.var_emotion_default = tk.StringVar()
        self.var_emotions_enabled = tk.BooleanVar(value=True)
        self.var_auto_emotion = tk.BooleanVar(value=False)

        # Code-switching variables
        self.var_code_switch = tk.BooleanVar(value=True)
        self.var_auto_lang = tk.BooleanVar(value=True)
        self.var_paired_voice = tk.StringVar()

        self.var_status = tk.StringVar()
        self.var_progress = tk.DoubleVar(value=0.0)
        self.var_char_count = tk.StringVar(value="0 characters | 0 words")

        self.voice_map: Dict[str, VoiceInfo] = {}
        self.paired_voice_map: Dict[str, VoiceInfo] = {}

        self._build_ui()
        self._update_ui_language()
        self._update_voice_list()

    def t(self, key: str, **kwargs) -> str:
        """Fetch translated text according to current UI language."""
        lang_dict = TRANSLATIONS.get(self.ui_lang, TRANSLATIONS["en"])
        template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
        if kwargs:
            return template.format(**kwargs)
        return template

    def _build_ui(self):
        # Header banner
        self.header_frame = tk.Frame(self.root, bg="#1E3A8A", height=75)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)

        # UI Language Selector in Header (Top-Right)
        lang_select_box = tk.Frame(self.header_frame, bg="#1E3A8A")
        lang_select_box.pack(side=tk.RIGHT, padx=14, pady=10)

        self.lbl_ui_lang = tk.Label(
            lang_select_box,
            text="🌐 Language:",
            font=("Segoe UI", 9, "bold"),
            fg="#BFDBFE",
            bg="#1E3A8A",
        )
        self.lbl_ui_lang.pack(side=tk.LEFT, padx=(0, 4))

        self.cb_ui_lang = ttk.Combobox(
            lang_select_box,
            textvariable=self.var_ui_lang_combo,
            values=["English", "Tiếng Việt"],
            state="readonly",
            width=10,
        )
        self.cb_ui_lang.pack(side=tk.LEFT)
        self.cb_ui_lang.bind("<<ComboboxSelected>>", self._on_ui_lang_changed)

        # Title & Subtitle in Header (Left)
        title_box = tk.Frame(self.header_frame, bg="#1E3A8A")
        title_box.pack(side=tk.LEFT, padx=14, pady=6)

        self.title_lbl = tk.Label(
            title_box,
            text="",
            font=("Segoe UI", 14, "bold"),
            fg="#FFFFFF",
            bg="#1E3A8A",
        )
        self.title_lbl.pack(anchor=tk.W)

        self.sub_lbl = tk.Label(
            title_box,
            text="",
            font=("Segoe UI", 8),
            fg="#BFDBFE",
            bg="#1E3A8A",
        )
        self.sub_lbl.pack(anchor=tk.W)

        # Main content container
        main_container = ttk.Frame(self.root, padding=12)
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- 1. Input File Frame ---
        self.file_frame = ttk.LabelFrame(main_container, text="", padding=10)
        self.file_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Entry(self.file_frame, textvariable=self.var_input_file, font=("Segoe UI", 10)).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8)
        )
        self.btn_browse_input = ttk.Button(
            self.file_frame, text="", command=self._browse_input_file
        )
        self.btn_browse_input.pack(side=tk.LEFT)

        # --- 2. Middle Paned: Left (Text Preview) & Right (Settings) ---
        mid_paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        mid_paned.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Left Column: Editor & Preview
        self.preview_frame = ttk.LabelFrame(mid_paned, text="", padding=8)
        mid_paned.add(self.preview_frame, weight=3)

        toolbar = ttk.Frame(self.preview_frame)
        toolbar.pack(fill=tk.X, pady=(0, 6))

        self.btn_insert_tag = ttk.Menubutton(toolbar, text="")
        self.tag_menu = tk.Menu(self.btn_insert_tag, tearoff=0)
        self.btn_insert_tag["menu"] = self.tag_menu
        self.btn_insert_tag.pack(side=tk.LEFT)

        self.btn_insert_lang = ttk.Menubutton(toolbar, text="")
        self.lang_tag_menu = tk.Menu(self.btn_insert_lang, tearoff=0)
        self.btn_insert_lang["menu"] = self.lang_tag_menu
        self.btn_insert_lang.pack(side=tk.LEFT, padx=(6, 0))

        self.lbl_tag_hint = ttk.Label(
            toolbar,
            text="",
            font=("Segoe UI", 8, "italic"),
            foreground="#6B7280",
        )
        self.lbl_tag_hint.pack(side=tk.LEFT, padx=(8, 0))

        self.text_preview = tk.Text(
            self.preview_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            padx=8,
            pady=8,
            relief=tk.SOLID,
            borderwidth=1,
        )
        self.text_preview.tag_config("emotion_tag", foreground="#B45309", font=("Segoe UI", 10, "bold"))
        self.text_preview.tag_config("lang_tag", foreground="#0D9488", font=("Segoe UI", 10, "bold"))

        scroll_y = ttk.Scrollbar(self.preview_frame, orient=tk.VERTICAL, command=self.text_preview.yview)
        self.text_preview.configure(yscrollcommand=scroll_y.set)
        self.text_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_preview.bind("<KeyRelease>", self._on_text_modified)

        # Right Column: Settings
        self.settings_frame = ttk.LabelFrame(mid_paned, text="", padding=10)
        mid_paned.add(self.settings_frame, weight=2)

        # Speech Target Language
        self.lbl_target_lang = ttk.Label(self.settings_frame, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_target_lang.pack(anchor=tk.W, pady=(2, 2))

        lang_box = ttk.Frame(self.settings_frame)
        lang_box.pack(fill=tk.X, pady=(0, 6))
        self.rb_lang_vi = ttk.Radiobutton(
            lang_box,
            text="",
            value="vi",
            variable=self.var_speech_lang,
            command=self._on_speech_lang_changed,
        )
        self.rb_lang_vi.pack(side=tk.LEFT, padx=(0, 10))
        self.rb_lang_en = ttk.Radiobutton(
            lang_box,
            text="",
            value="en",
            variable=self.var_speech_lang,
            command=self._on_speech_lang_changed,
        )
        self.rb_lang_en.pack(side=tk.LEFT)

        # Engine
        self.lbl_engine = ttk.Label(self.settings_frame, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_engine.pack(anchor=tk.W, pady=(4, 2))

        self.cb_engine = ttk.Combobox(
            self.settings_frame,
            textvariable=self.var_engine,
            state="readonly",
        )
        self.cb_engine.pack(fill=tk.X, pady=(0, 6))
        self.cb_engine.bind("<<ComboboxSelected>>", self._on_engine_changed)

        # Voice
        self.lbl_voice = ttk.Label(self.settings_frame, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_voice.pack(anchor=tk.W, pady=(4, 2))
        self.cb_voice = ttk.Combobox(self.settings_frame, textvariable=self.var_voice_name, state="readonly")
        self.cb_voice.pack(fill=tk.X, pady=(0, 8))
        self.cb_voice.bind("<<ComboboxSelected>>", self._on_voice_changed)

        # Code-Switching Section (Bilingual Pronunciation)
        self.cs_frame = ttk.LabelFrame(self.settings_frame, text="", padding=6)
        self.cs_frame.pack(fill=tk.X, pady=(0, 8))

        self.chk_code_switch = ttk.Checkbutton(
            self.cs_frame,
            text="",
            variable=self.var_code_switch,
            command=self._on_code_switch_toggled,
        )
        self.chk_code_switch.pack(anchor=tk.W)

        self.chk_auto_lang = ttk.Checkbutton(
            self.cs_frame,
            text="",
            variable=self.var_auto_lang,
        )
        self.chk_auto_lang.pack(anchor=tk.W)

        paired_v_box = ttk.Frame(self.cs_frame)
        paired_v_box.pack(fill=tk.X, pady=(4, 2))
        self.lbl_paired_voice = ttk.Label(paired_v_box, text="", font=("Segoe UI", 8, "bold"))
        self.lbl_paired_voice.pack(side=tk.LEFT)

        self.cb_paired_voice = ttk.Combobox(
            paired_v_box,
            textvariable=self.var_paired_voice,
            state="readonly",
        )
        self.cb_paired_voice.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))

        # Default Emotion
        self.lbl_emotion = ttk.Label(self.settings_frame, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_emotion.pack(anchor=tk.W, pady=(4, 2))
        self.cb_emotion = ttk.Combobox(
            self.settings_frame,
            textvariable=self.var_emotion_default,
            state="readonly",
        )
        self.cb_emotion.pack(fill=tk.X, pady=(0, 4))

        emo_check_frame = ttk.Frame(self.settings_frame)
        emo_check_frame.pack(fill=tk.X, pady=(0, 8))
        self.chk_detect_tags = ttk.Checkbutton(
            emo_check_frame,
            text="",
            variable=self.var_emotions_enabled,
        )
        self.chk_detect_tags.pack(anchor=tk.W)
        self.chk_auto_emotion = ttk.Checkbutton(
            emo_check_frame,
            text="",
            variable=self.var_auto_emotion,
        )
        self.chk_auto_emotion.pack(anchor=tk.W)

        # Speed Section
        speed_header = ttk.Frame(self.settings_frame)
        speed_header.pack(fill=tk.X, pady=(4, 2))
        self.lbl_speed_header = ttk.Label(speed_header, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_speed_header.pack(side=tk.LEFT)

        self.spin_speed = ttk.Spinbox(
            speed_header,
            from_=0.50,
            to=2.00,
            increment=0.05,
            textvariable=self.var_speed_spin,
            width=7,
            font=("Segoe UI", 9, "bold"),
            command=self._on_speed_spin_changed,
        )
        self.spin_speed.pack(side=tk.RIGHT)
        self.spin_speed.bind("<Return>", self._on_speed_spin_changed)
        self.spin_speed.bind("<FocusOut>", self._on_speed_spin_changed)
        self.lbl_speed_factor = ttk.Label(speed_header, text="", font=("Segoe UI", 9))
        self.lbl_speed_factor.pack(side=tk.RIGHT)

        self.scale_speed = ttk.Scale(
            self.settings_frame,
            from_=0.50,
            to=2.00,
            orient=tk.HORIZONTAL,
            variable=self.var_speed_mult,
            command=self._on_speed_slider,
        )
        self.scale_speed.pack(fill=tk.X, pady=(2, 2))

        self.lbl_rate_info = ttk.Label(
            self.settings_frame,
            textvariable=self.var_rate_label,
            font=("Segoe UI", 8, "italic"),
            foreground="#1D4ED8",
        )
        self.lbl_rate_info.pack(anchor=tk.W, pady=(0, 4))

        # Speed Quick Presets
        preset_frame = ttk.Frame(self.settings_frame)
        preset_frame.pack(fill=tk.X, pady=(0, 8))
        for preset_val, preset_text in [
            (0.75, "0.75x"),
            (1.00, "1.0x"),
            (1.25, "1.25x"),
            (1.50, "1.5x"),
            (2.00, "2.0x"),
        ]:
            btn_p = ttk.Button(
                preset_frame,
                text=preset_text,
                command=lambda v=preset_val: self.set_speed(v),
            )
            btn_p.pack(side=tk.LEFT, padx=(0, 2), expand=True, fill=tk.X)

        # Output MP3 Location
        self.lbl_save_mp3 = ttk.Label(self.settings_frame, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_save_mp3.pack(anchor=tk.W, pady=(4, 2))
        out_box = ttk.Frame(self.settings_frame)
        out_box.pack(fill=tk.X, pady=(0, 6))
        ttk.Entry(out_box, textvariable=self.var_output_file, font=("Segoe UI", 9)).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4)
        )
        ttk.Button(out_box, text="...", width=4, command=self._browse_output_file).pack(side=tk.LEFT)

        # Character Counter
        ttk.Label(self.settings_frame, textvariable=self.var_char_count, font=("Segoe UI", 8)).pack(
            anchor=tk.W, pady=(4, 0)
        )

        # --- 3. Bottom Action Bar ---
        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill=tk.X, pady=(4, 0))

        self.btn_convert = tk.Button(
            action_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._start_conversion_thread,
        )
        self.btn_convert.pack(fill=tk.X, pady=(0, 6))

        self.progress_bar = ttk.Progressbar(
            action_frame, orient=tk.HORIZONTAL, mode="determinate", variable=self.var_progress
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 4))

        status_bar = ttk.Frame(action_frame)
        status_bar.pack(fill=tk.X)

        self.lbl_status = ttk.Label(
            status_bar, textvariable=self.var_status, font=("Segoe UI", 9), foreground="#1F2937"
        )
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_open_folder = ttk.Button(
            status_bar, text="", state=tk.DISABLED, command=self._open_output_folder
        )
        self.btn_open_folder.pack(side=tk.RIGHT, padx=(4, 0))

        self.btn_play_audio = ttk.Button(
            status_bar, text="", state=tk.DISABLED, command=self._open_mp3_file
        )
        self.btn_play_audio.pack(side=tk.RIGHT)

    def _on_ui_lang_changed(self, event=None):
        selected = self.var_ui_lang_combo.get()
        new_lang = "vi" if "Việt" in selected else "en"
        if new_lang != self.ui_lang:
            self.ui_lang = new_lang
            self._update_ui_language()

    def _update_ui_language(self):
        """Update all text labels in the UI according to self.ui_lang."""
        self.root.title(self.t("app_title"))
        self.title_lbl.config(text=self.t("header_title"))
        self.sub_lbl.config(text=self.t("header_sub"))
        self.lbl_ui_lang.config(text=self.t("ui_lang_label"))
        self.file_frame.config(text=self.t("input_frame"))
        self.btn_browse_input.config(text=self.t("browse_txt_btn"))
        self.preview_frame.config(text=self.t("text_preview_frame"))
        self.btn_insert_tag.config(text=self.t("insert_tag_btn"))
        self.btn_insert_lang.config(text=self.t("insert_lang_btn"))
        self.lbl_tag_hint.config(text=self.t("tag_hint"))

        # Re-populate emotion tag menu
        self.tag_menu.delete(0, tk.END)
        for tag_key, preset in EMOTION_PRESETS.items():
            self.tag_menu.add_command(
                label=f"[{tag_key}] {preset.label}",
                command=lambda k=tag_key: self._insert_emotion_tag(k),
            )
        self.tag_menu.add_separator()
        for b_tag in ["vui", "hao_hung", "buon", "gian"]:
            lbl_block = self.t("block_tag_label", b_tag, b_tag) if "{}" not in self.t("block_tag_label") else f"[{b_tag}]...[/{b_tag}]"
            self.tag_menu.add_command(
                label=f"[{b_tag}]...[/{b_tag}]",
                command=lambda k=b_tag: self._insert_block_tag(k),
            )

        # Re-populate language tag menu
        self.lang_tag_menu.delete(0, tk.END)
        self.lang_tag_menu.add_command(
            label=f"[en]...[/en] - {self.t('insert_en_tag')}",
            command=lambda: self._insert_lang_tag("en"),
        )
        self.lang_tag_menu.add_command(
            label=f"[vi]...[/vi] - {self.t('insert_vi_tag')}",
            command=lambda: self._insert_lang_tag("vi"),
        )

        self.settings_frame.config(text=self.t("settings_frame"))
        self.lbl_target_lang.config(text=self.t("target_lang_label"))
        self.rb_lang_vi.config(text=self.t("lang_vi"))
        self.rb_lang_en.config(text=self.t("lang_en"))
        self.lbl_engine.config(text=self.t("engine_label"))

        # Engine combobox values
        curr_engine_idx = self.cb_engine.current()
        self.cb_engine["values"] = [self.t("engine_edge"), self.t("engine_gtts")]
        if curr_engine_idx >= 0:
            self.cb_engine.current(curr_engine_idx)
        else:
            self.cb_engine.current(0)

        self.lbl_voice.config(text=self.t("voice_label"))

        # Code-Switching section
        self.cs_frame.config(text=self.t("code_switch_frame"))
        self.chk_code_switch.config(text=self.t("code_switch_chk"))
        self.chk_auto_lang.config(text=self.t("auto_lang_chk"))
        self.lbl_paired_voice.config(text=self.t("paired_voice_lbl"))
        self._on_code_switch_toggled()

        self.lbl_emotion.config(text=self.t("emotion_label"))

        # Emotion presets combobox
        emo_labels = [p.label for p in EMOTION_PRESETS.values()]
        curr_emo_idx = self.cb_emotion.current()
        self.cb_emotion["values"] = emo_labels
        if curr_emo_idx >= 0 and curr_emo_idx < len(emo_labels):
            self.cb_emotion.current(curr_emo_idx)
        else:
            self.cb_emotion.current(0)

        self.chk_detect_tags.config(text=self.t("detect_tags_chk"))
        self.chk_auto_emotion.config(text=self.t("auto_emotion_chk"))
        self.lbl_speed_header.config(text=self.t("speed_header"))
        self.lbl_speed_factor.config(text=self.t("speed_factor"))
        self.lbl_save_mp3.config(text=self.t("save_mp3_label"))

        if not self.is_converting:
            self.btn_convert.config(text=self.t("start_btn"))
        else:
            self.btn_convert.config(text=self.t("converting_btn"))

        self.btn_open_folder.config(text=self.t("open_folder_btn"))
        self.btn_play_audio.config(text=self.t("play_audio_btn"))

        # Update dynamic labels
        self._update_speed_description(self.var_speed_mult.get())
        self._update_char_count()
        if not self.is_converting and not self.last_output_file:
            self.var_status.set(self.t("status_ready"))

    def _insert_emotion_tag(self, tag_key: str):
        self.text_preview.insert(tk.INSERT, f"[{tag_key}] ")
        self._highlight_tags()
        self._update_char_count()
        self.text_preview.focus_set()

    def _insert_block_tag(self, tag_key: str):
        try:
            sel_first = self.text_preview.index(tk.SEL_FIRST)
            sel_last = self.text_preview.index(tk.SEL_LAST)
            sel_text = self.text_preview.get(sel_first, sel_last)
            self.text_preview.delete(sel_first, sel_last)
            self.text_preview.insert(sel_first, f"[{tag_key}]{sel_text}[/{tag_key}]")
        except tk.TclError:
            self.text_preview.insert(tk.INSERT, f"[{tag_key}]content[/{tag_key}]")
        self._highlight_tags()
        self._update_char_count()
        self.text_preview.focus_set()

    def _insert_lang_tag(self, lang_code: str):
        try:
            sel_first = self.text_preview.index(tk.SEL_FIRST)
            sel_last = self.text_preview.index(tk.SEL_LAST)
            sel_text = self.text_preview.get(sel_first, sel_last)
            self.text_preview.delete(sel_first, sel_last)
            self.text_preview.insert(sel_first, f"[{lang_code}]{sel_text}[/{lang_code}]")
        except tk.TclError:
            default_word = "Machine Learning" if lang_code == "en" else "xin chào"
            self.text_preview.insert(tk.INSERT, f"[{lang_code}]{default_word}[/{lang_code}]")
        self._highlight_tags()
        self._update_char_count()
        self.text_preview.focus_set()

    def _highlight_tags(self):
        self.text_preview.tag_remove("emotion_tag", "1.0", tk.END)
        self.text_preview.tag_remove("lang_tag", "1.0", tk.END)
        content = self.text_preview.get("1.0", tk.END)
        for m in re.finditer(r"\[(/?)([a-zA-Z0-9_]+)\]", content):
            start_idx = f"1.0+{m.start()}c"
            end_idx = f"1.0+{m.end()}c"
            tag_name = m.group(2).lower()
            if tag_name in ["en", "english", "us", "uk", "vi", "vietnamese"]:
                self.text_preview.tag_add("lang_tag", start_idx, end_idx)
            else:
                self.text_preview.tag_add("emotion_tag", start_idx, end_idx)

    def _on_code_switch_toggled(self):
        enabled = self.var_code_switch.get()
        state = tk.NORMAL if enabled else tk.DISABLED
        self.chk_auto_lang.config(state=state)
        self.cb_paired_voice.config(state="readonly" if enabled else tk.DISABLED)

    def _on_voice_changed(self, event=None):
        selected_display = self.cb_voice.get() or self.var_voice_name.get()
        base_v = self.voice_map.get(selected_display)
        if not base_v:
            return
        target_lang = "en" if self.var_speech_lang.get().startswith("vi") else "vi"
        paired_id = get_paired_voice(base_v.id, target_lang=target_lang)
        for d_name, v_info in self.paired_voice_map.items():
            if v_info.id == paired_id:
                self.cb_paired_voice.set(d_name)
                self.var_paired_voice.set(d_name)
                break

    def set_speed(self, multiplier: float):
        mult = max(0.25, min(3.0, round(float(multiplier), 2)))
        self.var_speed_mult.set(mult)
        self.var_speed_spin.set(f"{mult:.2f}")
        self._update_speed_description(mult)

    def _update_speed_description(self, mult: float):
        pct = int(round((mult - 1.0) * 100))
        sign = "+" if pct >= 0 else ""
        if abs(mult - 1.0) < 0.03:
            desc = self.t("speed_normal")
        elif mult < 0.7:
            desc = self.t("speed_very_slow")
        elif mult < 1.0:
            desc = self.t("speed_slow")
        elif mult <= 1.3:
            desc = self.t("speed_slightly_fast")
        elif mult <= 1.6:
            desc = self.t("speed_fast")
        else:
            desc = self.t("speed_very_fast")
        self.var_rate_label.set(f"{desc} ({mult:.2f}x / {sign}{pct}%)")

    def _on_speed_slider(self, val):
        raw = float(val)
        snapped = round(raw * 20.0) / 20.0
        self.var_speed_spin.set(f"{snapped:.2f}")
        self._update_speed_description(snapped)

    def _on_speed_spin_changed(self, event=None):
        raw_str = self.var_speed_spin.get().strip()
        try:
            mult, _ = parse_speed(raw_str)
            self.set_speed(mult)
        except ValueError:
            self.set_speed(1.0)

    def _browse_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Text File (.txt)",
            filetypes=[("Text Files (*.txt)", "*.txt"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        self.var_input_file.set(file_path)
        base_name = os.path.splitext(file_path)[0]
        self.var_output_file.set(f"{base_name}.mp3")

        try:
            content, enc = read_text_file(file_path)
            self.text_preview.delete("1.0", tk.END)
            self.text_preview.insert(tk.END, content)
            self._highlight_tags()
            self._update_char_count()
            self.var_status.set(self.t("status_file_loaded", name=os.path.basename(file_path), enc=enc))
        except Exception as e:
            messagebox.showerror(self.t("dialog_file_err_title"), self.t("dialog_file_err_msg", err=str(e)))

    def _browse_output_file(self):
        init_file = os.path.basename(self.var_output_file.get()) or "output.mp3"
        file_path = filedialog.asksaveasfilename(
            title="Choose MP3 destination",
            defaultextension=".mp3",
            initialfile=init_file,
            filetypes=[("MP3 Audio (*.mp3)", "*.mp3")],
        )
        if file_path:
            self.var_output_file.set(file_path)

    def _on_speech_lang_changed(self):
        self._update_voice_list()

    def _on_engine_changed(self, event=None):
        self._update_voice_list()

    def _update_voice_list(self):
        lang = self.var_speech_lang.get()
        engine_idx = self.cb_engine.current()
        use_gtts = engine_idx == 1  # 0 is edge-tts, 1 is gtts

        voices = get_voices_for_language(lang)
        self.voice_map.clear()
        display_names = []

        for v in voices:
            if use_gtts and v.engine != "gtts":
                continue
            if not use_gtts and v.engine != "edge-tts":
                continue

            display_name = f"{v.name}"
            self.voice_map[display_name] = v
            display_names.append(display_name)

        if not display_names:
            for v in voices:
                display_name = f"{v.name} ({v.engine})"
                self.voice_map[display_name] = v
                display_names.append(display_name)

        self.cb_voice["values"] = display_names
        if display_names:
            curr_selection = self.cb_voice.get() or self.var_voice_name.get()
            selected_idx = -1
            if curr_selection in display_names:
                selected_idx = display_names.index(curr_selection)
            else:
                default_voice_id = DEFAULT_VOICES.get(lang)
                for idx, d_name in enumerate(display_names):
                    v_info = self.voice_map.get(d_name)
                    if v_info and v_info.id == default_voice_id:
                        selected_idx = idx
                        break
            if selected_idx < 0:
                selected_idx = 0
            self.cb_voice.current(selected_idx)
            self.var_voice_name.set(display_names[selected_idx])

        # Update paired voices for Code-Switching
        paired_lang = "en" if lang.startswith("vi") else "vi"
        paired_voices = get_voices_for_language(paired_lang)
        self.paired_voice_map.clear()
        paired_display_names = []
        for pv in paired_voices:
            if use_gtts and pv.engine != "gtts":
                continue
            if not use_gtts and pv.engine != "edge-tts":
                continue
            p_display = f"{pv.name}"
            self.paired_voice_map[p_display] = pv
            paired_display_names.append(p_display)

        self.cb_paired_voice["values"] = paired_display_names
        if paired_display_names:
            base_v = self.voice_map.get(self.var_voice_name.get())
            default_paired_id = get_paired_voice(base_v.id if base_v else "", target_lang=paired_lang)
            matched_name = None
            for d_name, p_info in self.paired_voice_map.items():
                if p_info.id == default_paired_id:
                    matched_name = d_name
                    break
            if matched_name:
                self.cb_paired_voice.set(matched_name)
                self.var_paired_voice.set(matched_name)
            else:
                self.cb_paired_voice.current(0)
                self.var_paired_voice.set(paired_display_names[0])

    def _on_text_modified(self, event=None):
        self._highlight_tags()
        self._update_char_count()

    def _update_char_count(self):
        content = self.text_preview.get("1.0", tk.END).strip()
        chars = len(content)
        words = len(content.split()) if content else 0
        self.var_char_count.set(self.t("char_count", chars=chars, words=words))

    def _start_conversion_thread(self):
        if self.is_converting:
            return

        text_content = self.text_preview.get("1.0", tk.END).strip()
        if not text_content:
            messagebox.showwarning(self.t("dialog_empty_title"), self.t("dialog_empty_msg"))
            return

        output_path = self.var_output_file.get().strip()
        if not output_path:
            input_p = self.var_input_file.get().strip()
            if input_p:
                output_path = f"{os.path.splitext(input_p)[0]}.mp3"
            else:
                output_path = os.path.abspath("output.mp3")
            self.var_output_file.set(output_path)

        self._on_speed_spin_changed()
        speed_mult, rate_str = parse_speed(self.var_speed_spin.get())

        selected_display = self.cb_voice.get() or self.var_voice_name.get()
        voice_info = self.voice_map.get(selected_display)
        voice_id = voice_info.id if voice_info else None

        engine_type = "gtts" if self.cb_engine.current() == 1 else "edge-tts"

        # Emotion selection
        sel_emo_idx = self.cb_emotion.current()
        emo_keys = list(EMOTION_PRESETS.keys())
        default_emo_key = emo_keys[sel_emo_idx] if 0 <= sel_emo_idx < len(emo_keys) else "binh_thuong"

        emotions_enabled = self.var_emotions_enabled.get()
        auto_emotion = self.var_auto_emotion.get()

        # Code-switching selection
        code_switch_enabled = self.var_code_switch.get()
        auto_lang = self.var_auto_lang.get()
        selected_paired_display = self.cb_paired_voice.get() or self.var_paired_voice.get()
        paired_voice_info = self.paired_voice_map.get(selected_paired_display)
        paired_voice_id = paired_voice_info.id if paired_voice_info else None

        self.is_converting = True
        self.btn_convert.config(text=self.t("converting_btn"), state=tk.DISABLED, bg="#9CA3AF")
        self.btn_open_folder.config(state=tk.DISABLED)
        self.btn_play_audio.config(state=tk.DISABLED)
        self.var_progress.set(0.0)

        thread = threading.Thread(
            target=self._run_conversion,
            args=(
                text_content,
                output_path,
                voice_id,
                self.var_speech_lang.get(),
                speed_mult,
                rate_str,
                engine_type,
                emotions_enabled,
                default_emo_key,
                auto_emotion,
                code_switch_enabled,
                paired_voice_id,
                auto_lang,
            ),
            daemon=True,
        )
        thread.start()

    def _run_conversion(
        self,
        text,
        output_path,
        voice_id,
        lang,
        speed_mult,
        rate_str,
        engine_type,
        emotions_enabled,
        default_emo_key,
        auto_emotion,
        code_switch,
        paired_voice_id,
        auto_detect_en,
    ):
        def update_progress(pct, msg):
            self.root.after(0, lambda: self._on_progress_update(pct, msg))

        try:
            saved_file = self.engine.convert_text_to_mp3(
                text=text,
                output_file=output_path,
                voice_id=voice_id,
                language=lang,
                rate=rate_str,
                speed=speed_mult,
                engine=engine_type,
                emotions=emotions_enabled,
                default_emotion=default_emo_key,
                auto_emotion=auto_emotion,
                code_switch=code_switch,
                paired_voice_id=paired_voice_id,
                auto_detect_en=auto_detect_en,
                progress_callback=update_progress,
            )
            self.last_output_file = saved_file
            self.root.after(0, lambda: self._on_conversion_success(saved_file, speed_mult))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda: self._on_conversion_error(err_msg))

    def _on_progress_update(self, pct, msg):
        self.var_progress.set(pct * 100)
        self.var_status.set(msg)

    def _on_conversion_success(self, saved_file, speed_mult: float):
        self.is_converting = False
        self.btn_convert.config(text=self.t("start_btn"), state=tk.NORMAL, bg="#2563EB")
        self.btn_open_folder.config(state=tk.NORMAL)
        self.btn_play_audio.config(state=tk.NORMAL)
        self.var_progress.set(100.0)
        file_size_kb = os.path.getsize(saved_file) / 1024
        self.var_status.set(
            self.t("status_success", speed=speed_mult, size=file_size_kb, name=os.path.basename(saved_file))
        )
        messagebox.showinfo(
            self.t("dialog_success_title"),
            self.t(
                "dialog_success_msg",
                name=os.path.basename(saved_file),
                speed=speed_mult,
                size=file_size_kb,
                path=saved_file,
            ),
        )

    def _on_conversion_error(self, err_msg):
        self.is_converting = False
        self.btn_convert.config(text=self.t("start_btn"), state=tk.NORMAL, bg="#2563EB")
        self.var_status.set(self.t("status_error", err=err_msg))
        messagebox.showerror(self.t("dialog_conv_err_title"), self.t("dialog_conv_err_msg", err=err_msg))

    def _open_output_folder(self):
        if not self.last_output_file or not os.path.exists(self.last_output_file):
            target = self.var_output_file.get()
            if target and os.path.exists(target):
                self.last_output_file = target
            else:
                messagebox.showwarning(self.t("dialog_no_audio_title"), self.t("dialog_no_audio_msg"))
                return

        folder = os.path.dirname(os.path.abspath(self.last_output_file))
        if sys.platform == "win32":
            subprocess.run(["explorer", f"/select,{os.path.abspath(self.last_output_file)}"])
        else:
            subprocess.run(["xdg-open", folder])

    def _open_mp3_file(self):
        if not self.last_output_file or not os.path.exists(self.last_output_file):
            messagebox.showwarning(self.t("dialog_no_audio_title"), self.t("dialog_missing_audio_msg"))
            return

        os.startfile(os.path.abspath(self.last_output_file))


def main():
    root = tk.Tk()
    app = TTSAppGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
