#!/usr/bin/env python3
"""
my_TTS - Ứng dụng Chuyển đổi Văn bản thành Giọng nói (Text-to-Speech)
Giao diện dòng lệnh (CLI) kèm tính năng tùy chỉnh cảm xúc theo từng câu.
"""

import argparse
import os
import sys
import time

from tts.config import DEFAULT_VOICES, VOICE_CATALOG, get_voices_for_language
from tts.emotion import EMOTION_ALIASES, EMOTION_PRESETS, get_emotion_preset
from tts.engine import TTSEngine, parse_speed


def print_banner():
    print("=" * 68)
    print("        ỨNG DỤNG CHUYỂN ĐỔI VĂN BẢN THÀNH GIỌNG NÓI (TTS)")
    print("        Hỗ trợ: Tiếng Việt & Tiếng Anh • Tùy chỉnh cảm xúc & tốc độ")
    print("=" * 68)


def list_voices_table():
    """Hiển thị danh sách các giọng đọc hỗ trợ."""
    print("\n[DANH SÁCH GIỌNG ĐỌC HỖ TRỢ]")
    print(f"{'#':<3} | {'Mã giọng (Voice ID)':<24} | {'Ngôn ngữ':<8} | {'Giới tính':<8} | {'Tên mô tả'}")
    print("-" * 72)
    for i, v in enumerate(VOICE_CATALOG.values(), 1):
        print(f"{i:<3} | {v.id:<24} | {v.language:<8} | {v.gender:<8} | {v.name}")
    print("\nDùng: --voice <số thứ tự | Voice ID | tên ngắn (hoaimy, namminh, jenny...) | male/female>")
    print()


def list_emotions_table():
    """Hiển thị danh sách các thẻ cảm xúc hỗ trợ."""
    print("\n[DANH SÁCH THẺ CẢM XÚC HỖ TRỢ (EMOTION TAGS)]")
    print(f"{'Thẻ cú pháp':<16} | {'Tên cảm xúc':<22} | {'Tốc độ':<8} | {'Cao độ':<8} | {'Âm lượng':<8} | {'Mô tả'}")
    print("-" * 88)
    for k, p in EMOTION_PRESETS.items():
        tag_str = f"[{k}]"
        r_str = f"{p.rate_pct:+d}%"
        p_str = f"{p.pitch_hz:+d}Hz"
        v_str = f"{p.volume_pct:+d}%"
        print(f"{tag_str:<16} | {p.label:<22} | {r_str:<8} | {p_str:<8} | {v_str:<8} | {p.description}")
    print("\nCách dùng trong file .txt:")
    print("  - Kiểu dòng:   [vui] Câu này đọc với cảm xúc vui vẻ.")
    print("  - Kiểu khối:   [hao_hung]Đoạn văn này... rất hào hứng![/hao_hung]")
    print("  - Tiếng Anh:   [happy], [sad], [angry], [whisper], [excited]...")
    print()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Chuyển đổi file văn bản thuần túy (.txt) sang âm thanh (.mp3).",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        help="Đường dẫn đến file văn bản đầu vào (.txt).",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        help="Đường dẫn file âm thanh đầu ra (.mp3). Mặc định cùng tên với file txt.",
    )
    parser.add_argument(
        "-l",
        "--lang",
        dest="language",
        choices=["vi", "en"],
        default="vi",
        help="Ngôn ngữ chính: 'vi' (Tiếng Việt - mặc định) hoặc 'en' (Tiếng Anh).",
    )
    parser.add_argument(
        "-v",
        "--voice",
        dest="voice",
        help="Chọn giọng đọc, chấp nhận:\n"
        "  - Voice ID: vi-VN-NamMinhNeural, vi-VN-HoaiMyNeural, en-US-JennyNeural\n"
        "  - Tên ngắn: hoaimy, namminh, jenny, guy, aria, sonia, ryan\n"
        "  - Số thứ tự trong --list-voices: 1, 2, 4...\n"
        "  - Từ khóa: male / female (theo --lang)",
    )
    parser.add_argument(
        "-s",
        "--speed",
        dest="speed",
        default=None,
        help="Tùy chỉnh tốc độ đọc theo hệ số hoặc phần trăm.\n"
        "Ví dụ: '1.25' (hoặc '1.25x'), '0.8' (chậm lại), '1.5x', '+20%%', '-15%%'.\n"
        "Mặc định: 1.0x (+0%%).",
    )
    parser.add_argument(
        "-r",
        "--rate",
        dest="rate",
        default="+0%",
        help="Điều chỉnh tốc độ đọc theo phần trăm hoặc hệ số (tương tự --speed).",
    )
    parser.add_argument(
        "-p",
        "--pitch",
        dest="pitch",
        default="+0Hz",
        help="Điều chỉnh cao độ giọng nói cơ sở (ví dụ: '+2Hz', '-3Hz', '+0Hz').",
    )
    parser.add_argument(
        "-e",
        "--engine",
        dest="engine",
        choices=["edge-tts", "gtts"],
        default="edge-tts",
        help="Bộ chuyển đổi: 'edge-tts' (AI Neural chất lượng cao, mặc định) hoặc 'gtts' (Google TTS).",
    )
    parser.add_argument(
        "-em",
        "--emotion",
        dest="emotion",
        default="binh_thuong",
        help="Cảm xúc mặc định cho câu không gắn thẻ (ví dụ: vui, hao_hung, buon, thi_tham...).\n"
        "Mặc định: 'binh_thuong'.",
    )
    parser.add_argument(
        "--auto-emotion",
        dest="auto_emotion",
        action="store_true",
        help="Tự động gán cảm xúc cho các câu dựa vào dấu câu ('!' -> hào hứng, '...' -> buồn).",
    )
    parser.add_argument(
        "--no-emotion",
        dest="no_emotion",
        action="store_true",
        help="Bỏ qua phân tích cảm xúc (các thẻ cảm xúc sẽ bị lọc bỏ khỏi âm thanh).",
    )
    parser.add_argument(
        "--no-code-switch",
        dest="no_code_switch",
        action="store_true",
        help="Tắt tính năng chuyển đổi song ngữ (Code-Switching). Chỉ đọc 1 giọng duy nhất.",
    )
    parser.add_argument(
        "--no-auto-lang",
        dest="no_auto_lang",
        action="store_true",
        help="Tắt tự động nhận diện từ tiếng Anh xen kẽ. (Vẫn hỗ trợ thẻ tường minh [en]...[/en]).",
    )
    parser.add_argument(
        "--en-voice",
        dest="en_voice",
        default=None,
        help="Chọn giọng đọc tiếng Anh ghép đôi (ví dụ: jenny, guy, en-US-JennyNeural...).\n"
        "Mặc định tự động ghép đôi theo giới tính (NamMinh -> Guy, HoaiMy -> Jenny).",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="Hiển thị danh sách tất cả các giọng đọc được cấu hình sẵn.",
    )
    parser.add_argument(
        "--list-emotions",
        action="store_true",
        help="Hiển thị danh sách các thẻ cảm xúc và thông số preset.",
    )

    return parser.parse_args()


def resolve_voice_choice(voice_arg: str, lang: str) -> str:
    """Xác định mã giọng đọc từ tham số đầu vào."""
    if not voice_arg:
        return DEFAULT_VOICES.get(lang, "vi-VN-NamMinhNeural")

    v_lower = voice_arg.lower()

    if lang == "vi":
        if v_lower in ["female", "nu", "nữ"]:
            return "vi-VN-HoaiMyNeural"
        if v_lower in ["male", "nam"]:
            return "vi-VN-NamMinhNeural"
    elif lang == "en":
        if v_lower in ["female", "nu", "nữ"]:
            return "en-US-JennyNeural"
        if v_lower in ["male", "nam"]:
            return "en-US-GuyNeural"

    if voice_arg in VOICE_CATALOG:
        return VOICE_CATALOG[voice_arg].id

    # Chọn theo số thứ tự trong --list-voices
    if voice_arg.isdigit():
        voices = list(VOICE_CATALOG.values())
        idx = int(voice_arg) - 1
        if 0 <= idx < len(voices):
            return voices[idx].id
        raise ValueError(f"Số thứ tự giọng '{voice_arg}' không hợp lệ (1-{len(voices)}).")

    # Tên ngắn: hoaimy, namminh, jenny, guy, aria, sonia, ryan
    for v in VOICE_CATALOG.values():
        short = v.id.split("-")[-1].replace("Neural", "").lower()
        if v_lower == short:
            return v.id

    return voice_arg


def run_interactive_mode():
    """Chế độ hỏi đáp tương tác trực quan nếu người dùng chạy không kèm tham số."""
    print_banner()
    print("\n[CHẾ ĐỘ TƯƠNG TÁC NHANH]")

    while True:
        input_path = input("1. Nhập đường dẫn file text (.txt): ").strip().strip('"').strip("'")
        if not input_path:
            print("  [!] Vui lòng nhập đường dẫn file!")
            continue
        if not os.path.isfile(input_path):
            print(f"  [!] Không tìm thấy file: {input_path}")
            continue
        break

    lang = input("2. Chọn ngôn ngữ [vi = Tiếng Việt (mặc định), en = Tiếng Anh]: ").strip().lower()
    if lang not in ["vi", "en"]:
        lang = "vi"

    voices = get_voices_for_language(lang)
    print(f"\n3. Chọn giọng đọc cho ngôn ngữ '{lang}':")
    for idx, v in enumerate(voices, 1):
        print(f"   [{idx}] {v.name} ({v.id})")
    choice = input(f"   Nhập số lựa chọn (1-{len(voices)}, mặc định 1): ").strip()
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(voices):
            selected_voice = voices[choice_idx].id
        else:
            selected_voice = voices[0].id
    except ValueError:
        selected_voice = voices[0].id

    while True:
        speed_raw = input(
            "4. Tùy chỉnh tốc độ đọc (ví dụ: 0.75, 1.0, 1.25x, 1.5x hoặc +20%, mặc định 1.0x): "
        ).strip()
        try:
            multiplier, rate_str = parse_speed(speed_raw if speed_raw else "1.0")
            break
        except ValueError as err:
            print(f"  [!] {err}")

    print("\n5. Tùy chọn cảm xúc mặc định:")
    emo_keys = list(EMOTION_PRESETS.keys())
    for idx, k in enumerate(emo_keys, 1):
        print(f"   [{idx}] {EMOTION_PRESETS[k].label}")
    emo_choice = input(f"   Chọn cảm xúc (1-{len(emo_keys)}, Enter để chọn Bình thường): ").strip()
    selected_emotion = "binh_thuong"
    try:
        idx_e = int(emo_choice) - 1
        if 0 <= idx_e < len(emo_keys):
            selected_emotion = emo_keys[idx_e]
    except ValueError:
        pass

    out_file = input("\n6. Nhập tên/đường dẫn file MP3 đầu ra (Enter để lấy tự động): ").strip().strip('"').strip("'")
    if not out_file:
        out_file = None

    return input_path, out_file, lang, selected_voice, multiplier, rate_str, "+0Hz", "edge-tts", selected_emotion


def main():
    args = parse_args()

    if args.list_voices:
        list_voices_table()
        return 0

    if args.list_emotions:
        list_emotions_table()
        return 0

    if not args.input_file:
        input_path, out_file, lang, voice_id, speed_mult, rate_str, pitch, engine, def_emotion = run_interactive_mode()
        emotions_enabled = True
        auto_emotion = False
        code_switch = True
        auto_lang = True
        paired_en_voice = None
    else:
        input_path = args.input_file
        out_file = args.output_file
        lang = args.language
        try:
            voice_id = resolve_voice_choice(args.voice, lang)
        except ValueError as err:
            print(f"[LỖI GIỌNG ĐỌC]: {err}", file=sys.stderr)
            return 1
        raw_speed = args.speed if args.speed is not None else args.rate
        try:
            speed_mult, rate_str = parse_speed(raw_speed)
        except ValueError as err:
            print(f"[LỖI TỐC ĐỘ]: {err}", file=sys.stderr)
            return 1
        pitch = args.pitch
        engine = args.engine
        def_emotion = args.emotion
        emotions_enabled = not args.no_emotion
        auto_emotion = args.auto_emotion
        code_switch = not args.no_code_switch
        auto_lang = not args.no_auto_lang
        paired_en_voice = None
        if args.en_voice:
            try:
                paired_en_voice = resolve_voice_choice(args.en_voice, "en")
            except ValueError as err:
                print(f"[LỖI GIỌNG TIẾNG ANH]: {err}", file=sys.stderr)
                return 1

    if not os.path.isfile(input_path):
        print(f"[LỖI] Không tìm thấy file đầu vào: '{input_path}'", file=sys.stderr)
        return 1

    emo_info = get_emotion_preset(def_emotion).label if emotions_enabled else "Tắt (Chỉ đọc nội dung thô)"
    print("\n" + "-" * 55)
    print(f" File đầu vào:        {input_path}")
    print(f" Ngôn ngữ:            {lang}")
    print(f" Giọng đọc:           {voice_id}")
    print(f" Tốc độ cơ sở:        {speed_mult:.2f}x ({rate_str})")
    print(f" Cảm xúc câu:         {emo_info}")
    if auto_emotion:
        print(f" Tự động nhận diện:   Bật (qua '!' và '...')")
    if code_switch:
        cs_info = "Bật (Thẻ [en]...[/en]"
        if auto_lang:
            cs_info += " + Tự động quét từ mượn tiếng Anh"
        if paired_en_voice:
            cs_info += f", Giọng Anh: {paired_en_voice}"
        cs_info += ")"
        print(f" Song ngữ (Code-Switch): {cs_info}")
    else:
        print(" Song ngữ (Code-Switch): Tắt (Chỉ đọc giọng đơn)")
    print(f" Engine:              {engine}")
    print("-" * 55)

    engine_instance = TTSEngine()
    start_time = time.time()

    def progress(pct: float, message: str):
        bar_len = 25
        filled = int(bar_len * pct)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r[{bar}] {int(pct * 100):>3}% - {message:<55}")
        sys.stdout.flush()

    try:
        saved_path = engine_instance.convert_file_to_mp3(
            input_file=input_path,
            output_file=out_file,
            voice_id=voice_id,
            language=lang,
            rate=rate_str,
            speed=speed_mult,
            pitch=pitch,
            engine=engine,
            emotions=emotions_enabled,
            default_emotion=def_emotion,
            auto_emotion=auto_emotion,
            code_switch=code_switch,
            paired_voice_id=paired_en_voice,
            auto_detect_en=auto_lang,
            progress_callback=progress,
        )
        sys.stdout.write("\n")
        elapsed = time.time() - start_time
        file_size_kb = os.path.getsize(saved_path) / 1024
        print(f"\n[THÀNH CÔNG] File MP3 đã được tạo!")
        print(f" -> Đường dẫn: {saved_path}")
        print(f" -> Tốc độ đọc: {speed_mult:.2f}x")
        print(f" -> Kích thước: {file_size_kb:.1f} KB")
        print(f" -> Thời gian xử lý: {elapsed:.2f} giây\n")
        return 0
    except Exception as e:
        sys.stdout.write("\n")
        print(f"\n[LỖI CHUYỂN ĐỔI]: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
