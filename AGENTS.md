# AGENTS.md — Hướng Dẫn & Quy Tắc Dành Cho AI Agent (my_TTS)

Tài liệu này cung cấp toàn bộ thông tin kiến trúc, quy chuẩn lập trình, lệnh thực thi và các quy tắc bắt buộc dành cho AI Agent khi thao tác, phát triển và bảo trì trong kho mã nguồn **my_TTS**.

---

## 1. Tổng Quan Dự Án (Project Overview)

- **Tên dự án:** `my_TTS` (Text-to-Speech & Video-to-Script Suite).
- **Mục tiêu:** Cung cấp 2 công cụ AI độc lập, chất lượng cao phục vụ sáng tạo nội dung:
  1. **TTS (`my_TTS`):** Chuyển đổi văn bản thuần túy (`.txt`) thành tệp âm thanh (`.mp3`) chất lượng cao, ưu tiên hàng đầu cho **Tiếng Việt** (`vi-VN`) và **Tiếng Anh** (`en-US`, `en-GB`).
  2. **VTS (`my_VTS`):** Phân tích ngữ cảnh hình ảnh trong video (kể cả video câm, không có tiếng/chữ) và tự động biên kịch lời thoại / phụ đề (`.txt`, `.srt`) kèm gắn nhãn cảm xúc.
- **Nguyên tắc cốt lõi: TÁCH RỜI ĐỘC LẬP (Decoupled Architecture):**
  - TTS và VTS hoạt động riêng biệt, không gộp chung mã nguồn, không gây phụ thuộc chéo.
  - Điểm kết nối duy nhất giữa 2 bên là tệp văn bản `.txt`.

---

## 2. Tech Stack & Môi Trường Hoạt Động

- **Ngôn ngữ:** Python 3.8+ (khuyên dùng và đã kiểm thử trên Python 3.10 - 3.11).
- **Thư viện chính cho TTS (`requirements.txt`):**
  - `edge-tts>=7.0.0` (Microsoft Edge AI Neural Voices qua giao thức WebSocket).
  - `gTTS>=2.5.0` (Google Translate TTS REST API - cơ chế dự phòng).
  - Tùy chọn: `av` (PyAV) cho FFmpeg `atempo` time-stretching giữ nguyên pitch.
- **Thư viện chính cho VTS (`requirements-vts.txt`):**
  - `google-generativeai>=0.8.0` hoặc `google-genai` (Google Gemini 2.0 Flash Vision AI).
- **Thư viện tiêu chuẩn Python (Standard Library):**
  - `asyncio`, `tkinter`, `threading`, `unittest`, `json`, `re`.

---

## 3. Cấu Trúc Mã Nguồn & Trách Nhiệm Từng Module

```
my_TTS/
├── # ================= [MODULE TTS - TEXT-TO-SPEECH] =================
├── tts/                         # Package xử lý nghiệp vụ TTS cốt lõi
│   ├── __init__.py              # Khởi tạo package
│   ├── config.py                # Danh mục giọng đọc (VOICE_CATALOG), DEFAULT_VOICES, VoiceInfo
│   ├── text_processor.py        # Nhận diện encoding file, làm sạch text, chia chunk an toàn
│   ├── emotion.py               # Presets cảm xúc (rate, pitch, volume), parser thẻ cảm xúc
│   ├── code_switch.py           # Phân tích song ngữ Việt-Anh, từ mượn, cặp giọng (VOICE_PAIRS)
│   └── engine.py                # TTSEngine điều phối synthesis, PyAV speed adjustment, ghép MP3
├── main.py                      # Giao diện dòng lệnh TTS (CLI entrypoint)
├── gui.py                       # Giao diện người dùng Desktop TTS (Tkinter GUI entrypoint)
├── Run_GUI.bat / Chay_GUI.bat   # Script khởi chạy nhanh GUI TTS trên Windows
│
├── # ================= [MODULE VTS - VIDEO-TO-SCRIPT] =================
├── vts/                         # Package phân tích video & biên kịch kịch bản (Độc lập)
│   ├── __init__.py              # Khởi tạo package VTS
│   ├── config.py                # Cấu hình VTS, API Key, STYLE_PRESETS
│   ├── prompts.py               # Prompts phân tích thị giác theo từng thể loại
│   ├── formatter.py             # ScriptFormatter chuyển đổi .txt (chuẩn TTS) và .srt
│   └── client.py                # VTSClient kết nối Gemini Multimodal Vision API
├── vts_cli.py                   # Giao diện dòng lệnh VTS (CLI entrypoint)
├── vts_gui.py                   # Giao diện người dùng Desktop VTS (Tkinter GUI entrypoint)
├── Run_VTS.bat / Chay_VTS.bat   # Script khởi chạy nhanh GUI VTS trên Windows
├── requirements-vts.txt         # Dependencies độc lập cho VTS
│
├── tests/                       # Bộ kiểm thử tự động
│   ├── test_tts.py              # Unit tests cho module TTS (25 tests)
│   └── test_vts.py              # Unit tests cho module VTS (13 tests)
├── requirements.txt             # Danh sách dependencies tổng thể
├── README.md                    # Tài liệu hướng dẫn sử dụng chi tiết
└── AGENTS.md                    # File quy tắc và hướng dẫn dành cho AI Agent
```

### Chi tiết nhiệm vụ từng module trong `tts/`:
1. **`tts.config`**:
   - Quản lý danh bạ giọng đọc `VOICE_CATALOG` (`vi-VN-NamMinhNeural`, `vi-VN-HoaiMyNeural`, `en-US-JennyNeural`, `en-US-GuyNeural`...).
   - Đảm bảo các hàm truy vấn `get_voice_info()`, `get_voices_for_language()` hoạt động nhất quán, phân loại rõ engine (`edge-tts` vs `gtts`).
2. **`tts.text_processor`**:
   - `read_text_file(path)`: Tự động phát hiện encoding theo thứ tự ưu tiên (`utf-8-sig`, `utf-8`, `utf-16`, `cp1258`, `latin-1`). Không được sửa thành mở file mặc định không chỉ định bảng mã.
   - `clean_text(text)`: Chuẩn hóa `\r\n` -> `\n`, loại bỏ control chars vô hình, co gọn khoảng trắng.
   - `split_text_into_chunks(text, max_chars=1500)`: Tách văn bản dài theo câu/đoạn tránh timeout khi gọi API.
3. **`tts.emotion`**:
   - `EMOTION_PRESETS`: Định nghĩa các cảm xúc (`binh_thuong`, `vui`, `hao_hung`, `buon`, `gian`, `so_hai`, `thi_tham`, `nghiem_tuc`).
   - `parse_segments(text)`: Tách văn bản thành danh sách `(sentence, EmotionPreset)` hỗ trợ cả thẻ inline `[vui]...` lẫn khối `[vui]...[/vui]`.
   - `combine_emotion_and_speed()`: Tính toán tốc độ tổng hợp giữa base speed và emotion rate.
4. **`tts.code_switch`**:
   - Quản lý `VOICE_PAIRS`: Ánh xạ giọng Nam Việt -> Nam Mỹ (`Guy`), Nữ Việt -> Nữ Mỹ (`Jenny`).
   - `parse_code_switch_segments()`: Bóc tách đoạn văn bản thành danh sách `CodeSwitchChunk` dựa theo thẻ tường minh `[en]...[/en]` hoặc từ điển từ mượn `COMMON_ENGLISH_WORDS`.
   - `VIETNAMESE_HOMOGRAPHS`: Blacklist loại trừ các từ tiếng Việt không dấu dễ nhầm với từ tiếng Anh (ví dụ: `la`, `va`, `co`, `to`, `do`, `an`).
5. **`tts.engine`**:
   - `TTSEngine`: Lớp điều phối chính. Thực thi chuyển đổi qua `convert_text_to_mp3()` và `convert_file_to_mp3()`.
   - `adjust_mp3_speed()`: Sử dụng `av.filter.Graph` với bộ lọc `atempo` nếu thư viện `av` khả dụng; fallback mượt mà nếu không có.
   - Hỗ trợ callback tiến độ `progress_callback(percent, status_message)`.

---

## 4. Các Lệnh Thực Thi & Quy Trình Kiểm Thử (Commands & Testing)

Mọi Agent khi thực hiện công việc cần nắm vững các câu lệnh sau:

### 4.1. Cài Đặt Môi Trường
```powershell
pip install -r requirements.txt
# Tùy chọn (cho tính năng time-stretching nâng cao):
pip install av
```

### 4.2. Chạy Kiểm Thử Đơn Vị (Bắt buộc sau mỗi chỉnh sửa)
```powershell
# Chạy toàn bộ test suite
python -m unittest discover tests

# Chạy riêng file test_tts.py kèm hiển thị chi tiết (verbose)
python -m unittest tests/test_tts.py -v
```

### 4.3. Chạy Thử CLI
```powershell
# Xem danh sách giọng đọc
python main.py --list-voices

# Xem danh sách thẻ cảm xúc
python main.py --list-emotions

# Chuyển đổi file mẫu tiếng Việt
python main.py sample_texts/tieng_viet.txt -o output_vi.mp3

# Chuyển đổi file mẫu tiếng Anh kèm chỉnh tốc độ 1.25x
python main.py sample_texts/english.txt -o output_en.mp3 --lang en -s 1.25x

# Chuyển đổi kèm xử lý cảm xúc & tự động code-switching
python main.py sample_texts/song_ngu.txt -o output_mixed.mp3
```

### 4.4. Chạy Thử GUI
```powershell
python gui.py
```

---

## 5. Quy Chuẩn Lập Trình (Coding Conventions)

1. **Chuẩn Phong Cách Mã Nguồn:**
   - Tuân thủ nghiêm ngặt **PEP 8**.
   - Đặt tên hàm và biến dạng `snake_case`, tên lớp dạng `PascalCase`, hằng số dạng `UPPER_SNAKE_CASE`.
   - Sử dụng Type Annotations (`typing.List`, `typing.Dict`, `typing.Optional`, `typing.Tuple`, `typing.Union`) trên mọi định nghĩa hàm/phương thức mới.
   - Docstrings rõ ràng (ưu tiên tiếng Việt hoặc tiếng Anh kỹ thuật) mô tả đầu vào (Args), đầu ra (Returns) và ngoại lệ (Raises).

2. **Xử Lý Bất Đồng Bộ (Async / Concurrency):**
   - Thư viện `edge-tts` sử dụng coroutines `async def` và `asyncio`. Trong các hàm bọc đồng bộ (sync wrapper) của `engine.py`, sử dụng `asyncio.run()` hoặc quản lý event loop cẩn thận để tránh lỗi `RuntimeError: Event loop is closed` hoặc `This event loop is already running`.
   - Trong `gui.py`, tuyệt đối **không** chạy tác vụ TTS hoặc gọi mạng trực tiếp trên main thread của Tkinter vì sẽ làm đứng đơ (freeze) giao diện. Luôn dùng `threading.Thread(target=..., daemon=True)` và cập nhật UI thông qua các biến trạng thái an toàn.

3. **Khả Năng Chịu Lỗi & Cơ Chế Dự Phòng (Resilience & Fallbacks):**
   - Nếu `edge-tts` gặp sự cố (mất mạng, server Microsoft từ chối kết nối, rate limit), `TTSEngine` phải có khả năng fallback sang `gTTS` hoặc thông báo lỗi tường minh, không để crash ứng dụng không kiểm soát.
   - Khi xử lý file văn bản, **không được** gọi hàm `open(file, "r")` trần trụi mà phải luôn dùng `read_text_file()` từ `tts.text_processor` để hỗ trợ giải mã đa bảng mã (UTF-8, UTF-8 BOM, UTF-16, CP1258).

4. **Đa Ngôn Ngữ Giao Diện (i18n):**
   - Mọi chuỗi ký tự hiển thị trên giao diện `gui.py` phải được đăng ký trong từ điển `TRANSLATIONS` cho cả hai khóa `"en"` và `"vi"`. Tuyệt đối không hardcode chuỗi text đơn ngữ vào component giao diện.

5. **Xử Lý Tệp Âm Thanh MP3:**
   - Khi ghép nối (concatenate) nhiều đoạn byte MP3 từ các chunk khác nhau, đảm bảo luồng byte hợp lệ.
   - Không can thiệp sửa đổi các byte audio thô mà không kiểm tra tính tương thích của decoder.

---

## 6. Quy Tắc Bắt Buộc Dành Cho AI Agent (Agent Rules & Boundaries)

- **Không Bao Giờ Phá Vỡ Test Suite:**
  - Sau khi thêm, sửa hoặc tối ưu hóa bất kỳ đoạn mã nào, Agent **bắt buộc** phải chạy lệnh `python -m unittest discover tests`.
  - Toàn bộ các test cases hiện có phải vượt qua 100% (`OK`). Nếu có test bị hỏng, Agent phải sửa code hoặc cập nhật test phù hợp trước khi hoàn thành công việc.

- **Bổ Sung Test Khi Thêm Tính Năng:**
  - Nếu Agent bổ sung giọng đọc mới, preset cảm xúc mới, hoặc thuật toán phát hiện từ mượn mới, Agent phải viết thêm test case tương ứng vào `tests/test_tts.py`.

- **Không Commit Tệp Âm Thanh Lớn:**
  - Các file âm thanh `.mp3`, `.wav` sinh ra trong quá trình test hoặc thực thi mẫu không được đưa vào git commit (đã được cấu hình trong `.gitignore`).

- **Giữ Gìn Tính Gọn Nhẹ Của Dự Án:**
  - Không tự ý thêm các thư viện học sâu cồng kềnh (như `torch`, `transformers`, `tensorflow`) vào `requirements.txt`. Điểm mạnh của `my_TTS` là công cụ lightweight, cài đặt nhanh, tận dụng Cloud Neural TTS.

- **Tương Thích Đa Nền Tảng:**
  - Viết code xử lý đường dẫn bằng `os.path` hoặc `pathlib.Path`, tránh dùng dấu phân cách cứng `/` hoặc `\` dễ gây lỗi trên các hệ điều hành khác nhau (Windows, Linux, macOS).

- **Thao Tác File Cẩn Trọng:**
  - Luôn kiểm tra sự tồn tại của tệp trước khi đọc/ghi.
  - Sử dụng encoding `utf-8` khi ghi log, ghi file cấu hình hoặc tạo file mã nguồn mới.
