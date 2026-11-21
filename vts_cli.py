#!/usr/bin/env python3
"""
my_VTS - Công cụ Chuyển đổi Video sang Kịch bản / Phụ đề (Video-to-Script / Video-to-Sub).
Giao diện dòng lệnh (CLI) độc lập với module TTS.
"""

import argparse
import os
import sys
import time

from vts.config import DEFAULT_STYLE, STYLE_PRESETS, get_api_key, save_api_key
from vts.formatter import ScriptFormatter
from vts.client import VTSClient


def print_banner():
    print("=" * 72)
    print("        my_VTS - PHÂN TÍCH NGỮ CẢNH VIDEO & BIÊN SOẠN KỊCH BẢN / PHỤ ĐỀ")
    print("        Hỗ trợ: Video câm, video hành động, đời sống • Gắn thẻ cảm xúc AI")
    print("=" * 72)


def list_styles_table():
    """Hiển thị danh sách các phong cách kịch bản hỗ trợ."""
    print("\n[DANH SÁCH PHONG CÁCH BIÊN SOẠN (STYLES)]")
    print(f"{'Mã style':<14} | {'Tên phong cách':<35} | {'Thẻ cảm xúc ưu tiên'}")
    print("-" * 76)
    for k, s in STYLE_PRESETS.items():
        print(f"{k:<14} | {s.name:<35} | {s.primary_emotions}")
    print("\nDùng: --style <recap | tiktok | documentary | monologue | descriptive>")
    print()


def parse_args():
    parser = argparse.ArgumentParser(
        description="my_VTS: Phân tích ngữ cảnh video và tự động biên soạn kịch bản / phụ đề (.txt, .srt).",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "video_file",
        nargs="?",
        help="Đường dẫn đến tệp video đầu vào (.mp4, .mov, .mkv, .avi...).",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        help="Đường dẫn tệp kịch bản đầu ra (.txt). Mặc định cùng tên video.",
    )
    parser.add_argument(
        "-s",
        "--style",
        dest="style",
        default=DEFAULT_STYLE,
        choices=list(STYLE_PRESETS.keys()),
        help=(
            "Phong cách biên soạn:\n"
            "  recap       : Review / Tóm tắt kịch tính (mặc định)\n"
            "  tiktok      : Shorts / TikTok / Reels dí dỏm, viral\n"
            "  documentary : Phim tài liệu / Thuyết minh sâu sắc\n"
            "  monologue   : Độc thoại nội tâm nhân vật\n"
            "  descriptive : Mô tả hành động / Phụ đề trợ năng"
        ),
    )
    parser.add_argument(
        "-l",
        "--lang",
        dest="language",
        choices=["vi", "en"],
        default="vi",
        help="Ngôn ngữ kịch bản: 'vi' (Tiếng Việt - mặc định) hoặc 'en' (Tiếng Anh).",
    )
    parser.add_argument(
        "--srt",
        action="store_true",
        help="Xuất thêm tệp phụ đề tiêu chuẩn SubRip (.srt) cùng tên.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Chỉ xuất câu thoại kèm thẻ cảm xúc (không kèm mốc thời gian # [00:00 - 00:05]).",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        help="Google Gemini API Key (hoặc lưu biến môi trường GEMINI_API_KEY).",
    )
    parser.add_argument(
        "--save-key",
        action="store_true",
        help="Lưu API Key đã nhập vào cấu hình cục bộ để dùng cho các lần sau.",
    )
    parser.add_argument(
        "--list-styles",
        action="store_true",
        help="Hiển thị danh sách các phong cách biên kịch hỗ trợ và thoát.",
    )

    return parser.parse_args()


def interactive_wizard():
    """Chế độ tương tác từng bước khi chạy không kèm tham số."""
    print("\n[CHẾ ĐỘ TƯƠNG TÁC TỪNG BƯỚC]")
    video_file = input("1. Nhập đường dẫn tệp video (.mp4, .mov...): ").strip().strip('"').strip("'")
    if not video_file:
        print("Lỗi: Bạn chưa nhập đường dẫn video!")
        sys.exit(1)

    print("\n2. Chọn phong cách kịch bản:")
    styles = list(STYLE_PRESETS.keys())
    for i, k in enumerate(styles, 1):
        print(f"   [{i}] {STYLE_PRESETS[k].name}")
    style_choice = input(f"Chọn (1-{len(styles)}, mặc định 1): ").strip()
    style = "recap"
    try:
        idx = int(style_choice) - 1
        if 0 <= idx < len(styles):
            style = styles[idx]
    except ValueError:
        pass

    lang_choice = input("\n3. Ngôn ngữ kịch bản (vi = Tiếng Việt, en = Tiếng Anh, mặc định vi): ").strip().lower()
    language = "en" if lang_choice == "en" else "vi"

    srt_choice = input("\n4. Có muốn xuất thêm tệp phụ đề .srt không? (y/N): ").strip().lower()
    export_srt = srt_choice in ("y", "yes")

    return video_file, style, language, export_srt


def main():
    args = parse_args()

    if args.list_styles:
        print_banner()
        list_styles_table()
        sys.exit(0)

    print_banner()

    # Kiểm tra API Key
    api_key = get_api_key(args.api_key)
    if args.save_key and args.api_key:
        save_api_key(args.api_key)
        print("[*] Đã lưu Gemini API Key vào cấu hình cục bộ.")

    if not api_key:
        print("\n[!] CHƯA TÌM THẤY GEMINI API KEY!")
        print("    Công cụ VTS sử dụng Gemini Multimodal Vision AI hoàn toàn miễn phí.")
        print("    Bạn có thể lấy API Key miễn phí (không cần thẻ tín dụng) tại:")
        print("    👉 https://aistudio.google.com/\n")
        entered_key = input("Nhập Gemini API Key của bạn: ").strip()
        if entered_key:
            api_key = entered_key
            save_choice = input("Bạn có muốn lưu API Key này cho các lần sau không? (Y/n): ").strip().lower()
            if save_choice != "n":
                save_api_key(entered_key)
                print("[*] Đã lưu API Key vào .vts_config.json")
        else:
            print("[!] Lỗi: Không thể tiếp tục nếu không có API Key.")
            sys.exit(1)

    # Xác định video đầu vào
    video_file = args.video_file
    style = args.style
    language = args.language
    export_srt = args.srt

    if not video_file:
        video_file, style, language, export_srt = interactive_wizard()

    if not os.path.isfile(video_file):
        print(f"\n[!] Lỗi: Không tìm thấy tệp video tại '{video_file}'!")
        sys.exit(1)

    # Xác định đường dẫn file đầu ra
    base_name, _ = os.path.splitext(video_file)
    output_txt = args.output_file or f"{base_name}_script.txt"
    output_srt = f"{base_name}.srt"

    print(f"\n[*] Tệp video:    {video_file}")
    print(f"[*] Phong cách:   {STYLE_PRESETS.get(style, STYLE_PRESETS['recap']).name}")
    print(f"[*] Ngôn ngữ:     {'Tiếng Việt' if language == 'vi' else 'Tiếng Anh'}")
    print(f"[*] Đầu ra TXT:   {output_txt}")
    if export_srt:
        print(f"[*] Đầu ra SRT:   {output_srt}")
    print("-" * 72)

    def on_progress(pct: int, msg: str):
        bar_len = 25
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r[{bar}] {pct:3d}% - {msg}")
        sys.stdout.flush()

    client = VTSClient(api_key=api_key)

    start_time = time.time()
    try:
        segments = client.analyze_video(
            video_path=video_file,
            style=style,
            language=language,
            progress_callback=on_progress,
        )
    except Exception as e:
        print(f"\n\n[!] Đã xảy ra lỗi trong quá trình phân tích video: {e}")
        sys.exit(1)

    print()  # Xuống dòng sau progress bar
    elapsed = time.time() - start_time

    if not segments:
        print("[!] Không tạo được phân đoạn kịch bản nào từ video này.")
        sys.exit(1)

    # Lưu tệp .txt
    if args.clean:
        clean_content = ScriptFormatter.to_clean_tts_txt(segments)
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(clean_content)
    else:
        ScriptFormatter.save_txt(segments, output_txt, include_timestamps=True)

    print(f"\n[✓] THÀNH CÔNG! (Thời gian xử lý: {elapsed:.1f}s)")
    print(f"    - Đã lưu kịch bản tại: {os.path.abspath(output_txt)}")
    print(f"    - Tổng số phân đoạn:  {len(segments)} câu thoại có gán thẻ cảm xúc.")

    if export_srt:
        ScriptFormatter.save_srt(segments, output_srt)
        print(f"    - Đã lưu phụ đề tại:  {os.path.abspath(output_srt)}")

    print("\n💡 Gợi ý tiếp theo:")
    print("   Để đọc kịch bản này thành âm thanh qua TTS, hãy chạy:")
    print(f"   python main.py \"{output_txt}\" -o \"{base_name}.mp3\"")
    print()


if __name__ == "__main__":
    main()
