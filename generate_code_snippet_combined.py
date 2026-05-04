# generate_code_snippet_combined.py — Before/After 통합 이미지 생성
# 실행: python generate_code_snippet_combined.py

from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# 색상
RED_HEADER   = (220, 53, 69)
GREEN_HEADER = (40, 167, 69)
CODE_BG      = (30, 41, 59)
COMMENT      = (115, 138, 148)
KEYWORD      = (255, 121, 198)
FUNC         = (139, 233, 253)
DEFAULT      = (248, 248, 242)
LINE_NUM     = (100, 116, 139)
PAGE_BG      = (248, 250, 252)


def color_for(text):
    s = text.strip()
    if s.startswith("#"):
        return COMMENT
    if any(s.startswith(k) for k in (
        "def ", "class ", "if ", "else:", "elif ", "while ", "for ",
        "return ", "import ", "from ", "try:", "except", "with ", "pass",
    )):
        return KEYWORD
    if s.startswith(("st.", "cv2.", "os.", "subprocess.")):
        return FUNC
    return DEFAULT


def draw_block(draw, x, y, w, h, header_color, title, subtitle, code_lines,
               font_title, font_sub, font_code, font_num):
    """하나의 코드 블록(헤더 + 코드)을 특정 위치에 그립니다."""
    header_h = 90
    line_h   = 34
    padding  = 40

    # 헤더
    draw.rounded_rectangle([(x, y), (x + w, y + header_h)],
                           radius=10, fill=header_color)
    draw.text((x + padding, y + 20), title,    font=font_title, fill=(255, 255, 255))
    draw.text((x + padding, y + 58), subtitle, font=font_sub,   fill=(255, 220, 220))

    # 코드 영역
    code_top = y + header_h + 10
    code_h   = h - header_h - 10
    draw.rounded_rectangle([(x, code_top), (x + w, code_top + code_h)],
                           radius=10, fill=CODE_BG)

    # macOS 스타일 점
    dot_y = code_top + 18
    for i, color in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
        cx = x + 30 + i * 22
        draw.ellipse([(cx - 7, dot_y - 7), (cx + 7, dot_y + 7)], fill=color)

    # 코드 라인
    line_y = code_top + 50
    for i, line in enumerate(code_lines, 1):
        draw.text((x + 30,  line_y), f"{i:3d}", font=font_num,  fill=LINE_NUM)
        draw.text((x + 90,  line_y), line,       font=font_code, fill=color_for(line))
        line_y += line_h


def make_combined_image(main_title, before_code, after_code,
                         before_subtitle, after_subtitle, filename):
    try:
        font_main  = ImageFont.truetype("malgunbd.ttf", 34)
        font_title = ImageFont.truetype("malgunbd.ttf", 24)
        font_sub   = ImageFont.truetype("malgun.ttf", 16)
        font_code  = ImageFont.truetype("consolab.ttf", 20)
        font_num   = ImageFont.truetype("consola.ttf", 16)
    except:
        font_main = font_title = font_sub = font_code = font_num = ImageFont.load_default()

    # 크기 계산
    line_h       = 34
    max_lines    = max(len(before_code), len(after_code))
    block_h      = 90 + 10 + 50 + line_h * max_lines + 30   # 헤더 + 패딩 + 코드
    width        = 2200
    block_w      = (width - 60) // 2                          # 좌우 2분할
    total_height = 100 + block_h + 40                         # 메인 타이틀 + 코드 블록

    img  = Image.new("RGB", (width, total_height), PAGE_BG)
    draw = ImageDraw.Draw(img)

    # 메인 타이틀
    draw.text((40, 30), main_title, font=font_main, fill=(26, 26, 26))
    draw.line([(40, 85), (width - 40, 85)], fill=(226, 232, 240), width=2)

    # Before (좌)
    draw_block(draw, 20, 100, block_w, block_h,
               RED_HEADER, "Before", before_subtitle,
               before_code, font_title, font_sub, font_code, font_num)

    # After (우)
    draw_block(draw, 20 + block_w + 20, 100, block_w, block_h,
               GREEN_HEADER, "After", after_subtitle,
               after_code, font_title, font_sub, font_code, font_num)

    img.save(os.path.join(OUT, filename))
    print(f"  ✅ 저장: {filename}")


# ══════════════════════════════════════════════════════
# 1) 화면 깜빡임 이슈
# ══════════════════════════════════════════════════════
before_flicker = [
    "if st.session_state.running:",
    "    ret, frame = video.read_frame()",
    "    if ret:",
    "        detections = detector.detect(frame)",
    "        annotated  = draw_detections(frame, detections)",
    "        frame_ph.image(annotated, channels='BGR')",
    "        time.sleep(0.03)",
    "        st.rerun()",
]

after_flicker = [
    "frame_ph = st.empty()",
    "",
    "while st.session_state.running:",
    "    if is_rtsp:",
    "        frame = rtsp_reader.get_latest_frame()",
    "    else:",
    "        ret, frame = vs.read_frame()",
    "",
    "    annotated = draw_detections(frame, danger_result)",
    "    rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)",
    "    frame_ph.image(rgb, channels='RGB')",
    "",
    "    time.sleep(0.001 if is_rtsp else 0.020)",
]

make_combined_image(
    main_title       = "이슈 ① 실시간 영상 화면 깜빡임 — st.rerun() → while 루프 + st.empty()",
    before_code      = before_flicker,
    after_code       = after_flicker,
    before_subtitle  = "매 프레임마다 st.rerun()으로 페이지 전체 리렌더",
    after_subtitle   = "placeholder에 이미지만 갱신하여 페이지 리렌더 제거",
    filename         = "code_flicker_combined.png",
)


# ══════════════════════════════════════════════════════
# 2) 영상 클립 재생 이슈
# ══════════════════════════════════════════════════════
before_clip = [
    "def save_event_clip(frames, source_name, fps=10):",
    "    filename = f'clip_{source_name}_{timestamp}.mp4'",
    "    filepath = os.path.join(EVENTS_DIR, filename)",
    "",
    "    h, w = frames[0].shape[:2]",
    "    fourcc = cv2.VideoWriter_fourcc(*'mp4v')",
    "    writer = cv2.VideoWriter(filepath, fourcc, fps, (w, h))",
    "",
    "    for f in frames:",
    "        writer.write(f)",
    "    writer.release()",
]

after_clip = [
    "from imageio_ffmpeg import get_ffmpeg_exe",
    "",
    "def get_playable_video(clip_path):",
    "    cached = os.path.join(EVENTS_DIR, '_converted',",
    "                          os.path.basename(clip_path))",
    "    if os.path.exists(cached):",
    "        return cached",
    "",
    "    ffmpeg = get_ffmpeg_exe()",
    "    subprocess.run([",
    "        ffmpeg, '-y', '-i', clip_path,",
    "        '-c:v', 'libx264', '-preset', 'fast',",
    "        '-movflags', '+faststart',",
    "        '-an',",
    "        cached,",
    "    ], capture_output=True, timeout=30)",
    "    return cached",
]

make_combined_image(
    main_title       = "이슈 ② 영상 클립 브라우저 재생 불가 — mp4v → H.264 자동 변환",
    before_code      = before_clip,
    after_code       = after_clip,
    before_subtitle  = "OpenCV 기본 mp4v 코덱은 HTML5 Video 미지원",
    after_subtitle   = "imageio-ffmpeg로 H.264 자동 변환 + 결과 캐싱",
    filename         = "code_clip_combined.png",
)

print("\n완료! 통합 이미지 2장 생성됨.")
