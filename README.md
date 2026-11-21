# Text-to-Speech (TTS) Converter

A versatile, high-quality Python Text-to-Speech (TTS) application that converts plain text files (`.txt`) into audio files (`.mp3`), with prioritized, crystal-clear support for **Vietnamese** and **English**.

---

## 🌟 Key Features

- **Flexible Input:** Reads plain text (`.txt`) files with automatic encoding detection (`UTF-8`, `UTF-8 with BOM`, `UTF-16`, `Windows-1258 / CP1258`).
- **Standard MP3 Output:** Generates clean `.mp3` audio files playable on any device or media player.
- **Natural Neural AI Voices:**
  - **Vietnamese (`vi-VN`):** **Nam Minh** (Warm, authoritative male voice) and **Hoài My** (Clear, expressive female voice) powered by Microsoft Edge Neural TTS.
  - **English (`en-US`, `en-GB`):** **Jenny**, **Aria**, **Sonia** (female) and **Guy**, **Ryan** (male) native voices.
  - **Google TTS Integration:** Built-in `gTTS` backup ensuring 100% reliable synthesis even during network fluctuations.
- **Speed Customization (0.5x - 2.0x):**
  - Adjust speaking speed smoothly using multipliers (`0.75x`, `1.25x`, `1.5x`, `2.0x`) or percentages (`+25%`, `-20%`).
  - Preserves natural voice pitch without distortion using FFmpeg `atempo` processing (via `PyAV`).
- **Sentence-Level Emotion Tags:**
  - Control emotions on a per-sentence or per-block basis using tags such as `[vui]` / `[happy]`, `[buon]` / `[sad]`, `[hao_hung]` / `[excited]`, `[gian]` / `[angry]`, `[thi_tham]` / `[whisper]`, `[so_hai]` / `[scared]`, and `[nghiem_tuc]` / `[serious]`.
  - Optional automatic emotion detection based on punctuation (`!` for excitement, `...` for sadness/pause).
- **Mixed-Language Code-Switching (Vietnamese & English):**
  - **Native English Pronunciation:** When reading Vietnamese text containing English words or sentences, the system seamlessly switches to a native English neural voice with 100% natural pronunciation.
  - **Gender-Matched Voice Pairing:** Automatically pairs `Nam Minh` (Male Vietnamese) with `Guy` (Male US English) and `Hoài My` (Female Vietnamese) with `Jenny` (Female US English) for a smooth, single-speaker experience.
  - **Smart Loanword Detection & Explicit Tags:** Automatically recognizes common tech and business loanwords (*AI, Machine Learning, deadline, feedback, database, developer...*) or lets you explicitly mark phrases with `[en]...[/en]` and `[vi]...[/vi]` tags.
- **Two User Interfaces:**
  - **Desktop GUI (Tkinter):** Clean, modern, responsive window supporting **bilingual UI (English & Vietnamese)** with on-the-fly language switching, text preview/editor, emotion tag insertion, character/word counter, and one-click audio playback.
  - **Command-Line Interface (CLI):** Full-featured CLI for automation, scripting, and interactive step-by-step prompts.

---

## 🚀 Installation

Requirements: **Python 3.8+** (Tested and verified on Python 3.11).

Install dependencies:
```bash
pip install -r requirements.txt
```

*(Note: An active internet connection is required to fetch neural voice streams from Microsoft/Google servers).*

---

## 🖥️ Graphical User Interface (GUI)

### How to Launch

- **Option A (Double-click):**
  Double-click **`Run_GUI.bat`** (or **`Chay_GUI.bat`**) in the project folder.
- **Option B (Terminal):**
  ```bash
  python gui.py
  ```

### GUI Features

1. **🌐 Bilingual Interface:**
   - Switch the entire application language between **English** and **Tiếng Việt** at any time using the language selector in the top-right corner.
2. **Text Editor & Tag Inserter:**
   - Load `.txt` files or type/paste text directly into the preview area.
   - Click **"➕ Insert Emotion Tag [tag]"** to quickly insert emotion tags (`[happy]`, `[sad]`, `[excited]`, etc.).
   - Emotion tags are automatically highlighted with color for easy readability.
3. **Voice & Speed Controls:**
   - Select speech language (Vietnamese / English), TTS engine, and specific voice.
   - Adjust speed with quick preset buttons (`0.75x`, `1.0x`, `1.25x`, `1.5x`, `2.0x`), a continuous slider, or exact numeric spinbox.
4. **Instant Actions:**
   - Visual progress bar during conversion.
   - Click **"🎵 Play MP3 Audio"** or **"📂 Open File Location"** immediately once conversion finishes.

---

## 💻 Command-Line Interface (CLI)

### 1. View Supported Voices
```bash
python main.py --list-voices
```

### 2. View Supported Emotion Tags
```bash
python main.py --list-emotions
```

### 3. Basic Conversions
- **Vietnamese (Default):**
  ```bash
  python main.py sample_texts/tieng_viet.txt -o audio_vi.mp3
  ```
- **English:**
  ```bash
  python main.py sample_texts/english.txt -o audio_en.mp3 --lang en
  ```

### 4. Voice Selection
You can specify voices by ID, short name, index number, or gender:
```bash
# By short name
python main.py sample_texts/tieng_viet.txt -o out.mp3 --voice namminh
python main.py sample_texts/english.txt -o out.mp3 --lang en -v jenny

# By index from --list-voices
python main.py sample_texts/english.txt -o out.mp3 --voice 5

# By gender (respects --lang)
python main.py sample_texts/tieng_viet.txt -o out.mp3 --voice female
```

### 5. Speed Customization
Set speed using multipliers or percentages:
```bash
# 1.25x speed (+25% faster)
python main.py sample_texts/tieng_viet.txt -o fast.mp3 --speed 1.25x

# 0.8x speed (20% slower)
python main.py sample_texts/english.txt -o slow.mp3 --lang en -s 0.8

# Percentage format
python main.py sample_texts/tieng_viet.txt -o custom.mp3 -s +20%
```

### 6. Emotion Customization per Sentence

Add emotion tags directly to sentences in your `.txt` file:

```text
[vui] Welcome to our special podcast episode today!
[hao_hung] We have officially achieved our target ahead of schedule!
[buon] Unfortunately, several team members could not attend today...
[gian] I repeat: do not violate the safety guidelines!
[thi_tham] Shh, speak very quietly so no one overhears us.
[nghiem_tuc] This is an official notice effective immediately.
Regular sentences without tags will be spoken with natural normal tone.
```

- **Convert text file with emotion tags:**
  ```bash
  python main.py sample_texts/cam_xuc.txt -o audio_camxuc.mp3 --voice namminh
  ```
- **Auto-detect emotion from punctuation (`!` -> excited, `...` -> sad):**
  ```bash
  python main.py input.txt -o output.mp3 --auto-emotion
  ```
- **Disable emotion processing (strips tags and reads plain text):**
  ```bash
  python main.py sample_texts/cam_xuc.txt -o plain.mp3 --no-emotion
  ```

### 7. Bilingual Mixed-Language Code-Switching (Vietnamese & English)

When reading Vietnamese text containing English words or phrases, the engine automatically pronounces English terms with native US English pronunciation:

- **Smart Auto-Detection (Default):**
  Common tech and business terms (*AI, machine learning, Python, database, deadline, feedback, developer...*) are automatically detected and spoken with the paired native English voice without needing any tags:
  ```bash
  python main.py sample_texts/song_ngu.txt -o audio_songngu.mp3 --voice namminh
  ```
- **Explicit Language Tags `[en]...[/en]` & `[vi]...[/vi]`:**
  For any sentence, idiom, or custom phrase, wrap it in `[en]...[/en]` for English or `[vi]...[/vi]` for Vietnamese:
  ```text
  Thông điệp quan trọng của buổi meeting hôm nay:
  [en]Innovation distinguishes between a leader and a follower.[/en]
  [en]Thank you very much for your feedback and support![/en]
  ```
- **Custom Paired English Voice:**
  Override the default gender pairing with `--en-voice`:
  ```bash
  python main.py sample_texts/song_ngu.txt -o out.mp3 --voice namminh --en-voice jenny
  ```
- **Disable Auto-Detection (Tags Only):**
  ```bash
  python main.py sample_texts/song_ngu.txt -o out.mp3 --no-auto-lang
  ```
- **Disable Code-Switching (Single Voice Only):**
  ```bash
  python main.py sample_texts/song_ngu.txt -o out.mp3 --no-code-switch
  ```

### 8. Interactive Mode
Run without arguments for an interactive step-by-step questionnaire:
```bash
python main.py
```

---

## 📋 Emotion Presets Reference

| Vietnamese Tag | English Tag | Emotion Name | Speed (`rate`) | Pitch (`pitch`) | Volume (`volume`) | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `[binh_thuong]` | `[normal]` | Neutral | +0% | +0Hz | +0% | Standard, natural tone |
| `[vui]` | `[happy]` | Cheerful | +12% | +25Hz | +5% | Upbeat tempo, brighter pitch |
| `[hao_hung]` | `[excited]` | Excited | +22% | +40Hz | +15% | Energetic, higher pitch, louder |
| `[buon]` | `[sad]` | Sad | -18% | -25Hz | -15% | Slower pace, somber low pitch |
| `[gian]` | `[angry]` | Angry | +10% | -10Hz | +25% | Forceful, stern, louder |
| `[so_hai]` | `[scared]` | Scared | +15% | +30Hz | -10% | Fast-paced, high pitched, anxious |
| `[thi_tham]` | `[whisper]` | Whispering | -10% | -15Hz | -40% | Soft, confidential low volume |
| `[nghiem_tuc]` | `[serious]` | Serious | -8% | -15Hz | +0% | Firm, solemn, steady cadence |

---

## 🎙️ Popular Voices Reference

| # | Language | Voice ID | Short Name | Gender | Characteristics |
| :-: | :--- | :--- | :--- | :-: | :--- |
| 1 | `vi-VN` | `vi-VN-NamMinhNeural` | `namminh` | Male | Warm, clear, authoritative (Default Vietnamese) |
| 2 | `vi-VN` | `vi-VN-HoaiMyNeural` | `hoaimy` | Female | Natural, expressive, standard accent |
| 3 | `vi` | `vi` | `gtts-vi` | Female | Google Translate Vietnamese (Backup) |
| 4 | `en-US` | `en-US-JennyNeural` | `jenny` | Female | Natural US female voice (Default English) |
| 5 | `en-US` | `en-US-GuyNeural` | `guy` | Male | Smooth, conversational US male voice |
| 6 | `en-US` | `en-US-AriaNeural` | `aria` | Female | Expressive, dynamic US female voice |
| 7 | `en-GB` | `en-GB-SoniaNeural` | `sonia` | Female | Standard British English female voice |
| 8 | `en-GB` | `en-GB-RyanNeural` | `ryan` | Male | Standard British English male voice |
| 9 | `en` | `en` | `gtts-en` | Female | Google Translate English (Backup) |

---

## 📂 Project Architecture

```
my_TTS/
├── # --- Module TTS (Text-to-Speech) ---
├── tts/
│   ├── __init__.py
│   ├── code_switch.py      # Mixed-language parser, gender voice pairing & auto-detection
│   ├── config.py           # Voice catalog and default configurations
│   ├── emotion.py          # Emotion presets, tag parsing, and parameter blending
│   ├── text_processor.py   # Multi-encoding file reader and sentence chunker
│   └── engine.py          # Core synthesis engine (Edge-TTS, gTTS, PyAV speed filter)
├── main.py                 # TTS CLI entry point
├── gui.py                  # TTS Desktop GUI entry point
├── Run_GUI.bat / Chay_GUI.bat # Launchers for TTS GUI
│
├── # --- Module VTS (Video-to-Script / Video-to-Sub) [Độc lập] ---
├── vts/
│   ├── __init__.py
│   ├── client.py           # Gemini Multimodal Vision API client
│   ├── config.py           # VTS configuration & style presets
│   ├── formatter.py        # Script & Subtitle formatter (.txt, .srt)
│   └── prompts.py          # Vision analysis prompts by genres
├── vts_cli.py              # VTS CLI entry point
├── vts_gui.py              # VTS Desktop GUI entry point
├── Run_VTS.bat / Chay_VTS.bat # Launchers for VTS GUI
├── requirements-vts.txt    # VTS dependencies (google-generativeai)
│
├── sample_texts/           # Sample text files (.txt)
├── tests/
│   ├── test_tts.py         # TTS test suite (25 unit tests)
│   └── test_vts.py         # VTS test suite (13 unit tests)
├── requirements.txt        # Full dependencies
├── AGENTS.md               # AI Agent operating guidelines
└── README.md               # Complete documentation
```

---

## 🎬 my_VTS: Video to Script & Subtitle Generator (Độc lập)

`my_VTS` là công cụ **hoàn toàn độc lập** với `my_TTS`, giúp bạn phân tích ngữ cảnh hình ảnh trong video (kể cả **video câm, không lời thoại, không chữ viết**) và tự động biên soạn kịch bản / phụ đề `.txt` và `.srt`.

### 1. Khởi chạy Giao diện Desktop (GUI)
- Nhấp đúp vào **`Run_VTS.bat`** (hoặc **`Chay_VTS.bat`**).
- Hoặc chạy lệnh:
  ```bash
  python vts_gui.py
  ```

### 2. Sử dụng qua dòng lệnh (CLI)
```bash
# Xem danh sách các phong cách hỗ trợ (recap, tiktok, documentary, monologue, descriptive)
python vts_cli.py --list-styles

# Phân tích video và xuất kịch bản .txt kèm thẻ cảm xúc
python vts_cli.py my_video.mp4 -o my_script.txt --style recap

# Xuất đồng thời tệp phụ đề tiêu chuẩn .srt
python vts_cli.py my_video.mp4 -o my_script.txt --srt

# Nhập và lưu Gemini API Key
python vts_cli.py my_video.mp4 --api-key YOUR_API_KEY --save-key
```

### 3. Phối hợp nhịp nhàng giữa VTS và TTS:
1. Dùng `my_VTS` để xem video và tạo kịch bản `kich_ban.txt` (đã tự động gán sẵn các thẻ cảm xúc `[vui]`, `[hao_hung]`, `[thi_tham]`).
2. Nạp file `kich_ban.txt` sang `my_TTS` để tạo âm thanh `.mp3` chuẩn giọng bản ngữ:
   ```bash
   python main.py kich_ban.txt -o thuyet_minh.mp3 --voice namminh
   ```

---

## 🧪 Testing

Run automated unit tests:
```bash
python -m unittest discover tests -v
```
Toàn bộ 38 bài kiểm thử (25 tests cho TTS và 13 tests cho VTS) tự động xác minh:
- Tự động nhận diện encoding, chia chunk, parse speed, time-stretching qua PyAV, thẻ cảm xúc và code-switching cho **TTS**.
- Phân tích kịch bản, chuyển đổi timestamp sang SRT chuẩn, lưu file, xử lý lỗi và phân đoạn đa phong cách cho **VTS**.
