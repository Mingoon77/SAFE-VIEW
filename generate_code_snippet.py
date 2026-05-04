# generate_code_snippet.py — PPT용 코드 캡처 이미지 생성
# 실행: python generate_code_snippet.py

from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(os.path.abspath(__file__))


def make_code_image(title, subtitle, code_lines, filename,
                     header_color=(220, 53, 69), bg=(30, 41, 59),
                     width=1600, padding=40):
    """코드 블록 이미지 생성 (제목 헤더 + 코드)"""
    # 폰트 로드
    try:
        font_title = ImageFont.truetype("malgunbd.ttf", 28)
        font_sub   = ImageFont.truetype("malgun.ttf", 18)
        font_code  = ImageFont.truetype("consolab.ttf", 22)
        font_num   = ImageFont.truetype("consola.ttf", 18)
    except:
        font_title = ImageFont.load_default()
        font_sub   = font_title
        font_code  = font_title
        font_num   = font_title

    # 크기 계산
    header_h    = 90
    line_h      = 34
    code_h      = line_h * len(code_lines) + padding * 2
    height      = header_h + code_h + 30

    img = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    # 헤더 배경 (둥근 모서리)
    draw.rounded_rectangle([(20, 20), (width - 20, 20 + header_h)], radius=10, fill=header_color)
    draw.text((padding, 35), title,   font=font_title, fill=(255, 255, 255))
    draw.text((padding, 72), subtitle, font=font_sub,   fill=(255, 220, 220))

    # 코드 배경
    code_top = 30 + header_h
    draw.rounded_rectangle([(20, code_top), (width - 20, code_top + code_h)], radius=10, fill=bg)

    # 상단 맥OS 스타일 점 3개
    dot_y = code_top + 18
    for i, color in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
        cx = 50 + i * 22
        draw.ellipse([(cx - 7, dot_y - 7), (cx + 7, dot_y + 7)], fill=color)

    # 코드 텍스트 (문법 하이라이트)
    def color_for(text):
        stripped = text.strip()
        if stripped.startswith("#"):
            return (115, 138, 148)  # 주석 (회색)
        if any(stripped.startswith(k) for k in ("def ", "class ", "if ", "else:", "elif ", "while ", "for ", "return ", "import ", "from ")):
            return (255, 121, 198)  # 키워드 (핑크)
        if stripped.startswith(("st.", "cv2.")):
            return (139, 233, 253)  # 함수/메서드 (청록)
        return (248, 248, 242)  # 기본 (흰색)

    y = code_top + 50
    for i, line in enumerate(code_lines, 1):
        # 줄 번호
        draw.text((50, y), f"{i:3d}", font=font_num, fill=(100, 116, 139))
        # 코드
        draw.text((110, y), line, font=font_code, fill=color_for(line))
        y += line_h

    img.save(os.path.join(OUT, filename))
    print(f"  ✅ 저장: {filename}")


# ══════════════════════════════════════════════════════
# 1) Before — 문제 코드 (st.rerun 방식)
# ══════════════════════════════════════════════════════
before_code = [
    "if st.session_state.running:",
    "    ret, frame = video.read_frame()",
    "    if ret:",
    "        detections = detector.detect(frame)",
    "        annotated  = draw_detections(frame, detections)",
    "        frame_ph.image(annotated, channels='BGR')",
    "        time.sleep(0.03)",
    "        st.rerun()",
]

make_code_image(
    title    = "❌ 문제 코드 — 화면 깜빡임 발생",
    subtitle = "매 프레임마다 st.rerun() 호출로 페이지 전체가 새로고침됨",
    code_lines = before_code,
    filename = "code_before.png",
    header_color = (220, 53, 69),
)


# ══════════════════════════════════════════════════════
# 2) After — 해결 코드 (while + st.image 직접 갱신)
# ══════════════════════════════════════════════════════
after_code = [
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

make_code_image(
    title    = "✅ 해결 코드 — 깜빡임 제거",
    subtitle = "st.empty() placeholder에 이미지만 갱신 → 페이지 리렌더 없음",
    code_lines = after_code,
    filename = "code_after.png",
    header_color = (40, 167, 69),
)

print("\n완료! PPT 삽입용 이미지 2장 생성됨.")
