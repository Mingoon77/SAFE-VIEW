# generate_code_snippet_clip.py — 영상 클립 재생 이슈 코드 이미지 생성
# 실행: python generate_code_snippet_clip.py

from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(os.path.abspath(__file__))


def make_code_image(title, subtitle, code_lines, filename,
                     header_color=(220, 53, 69), bg=(30, 41, 59),
                     width=1600, padding=40):
    try:
        font_title = ImageFont.truetype("malgunbd.ttf", 28)
        font_sub   = ImageFont.truetype("malgun.ttf", 18)
        font_code  = ImageFont.truetype("consolab.ttf", 22)
        font_num   = ImageFont.truetype("consola.ttf", 18)
    except:
        font_title = ImageFont.load_default()
        font_sub = font_title; font_code = font_title; font_num = font_title

    header_h = 90
    line_h   = 34
    code_h   = line_h * len(code_lines) + padding * 2
    height   = header_h + code_h + 30

    img  = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    # 헤더
    draw.rounded_rectangle([(20, 20), (width - 20, 20 + header_h)], radius=10, fill=header_color)
    draw.text((padding, 35), title,    font=font_title, fill=(255, 255, 255))
    draw.text((padding, 72), subtitle, font=font_sub,   fill=(255, 220, 220))

    # 코드 배경
    code_top = 30 + header_h
    draw.rounded_rectangle([(20, code_top), (width - 20, code_top + code_h)], radius=10, fill=bg)

    # macOS 스타일 점
    dot_y = code_top + 18
    for i, color in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
        cx = 50 + i * 22
        draw.ellipse([(cx - 7, dot_y - 7), (cx + 7, dot_y + 7)], fill=color)

    # 문법 하이라이트
    def color_for(text):
        stripped = text.strip()
        if stripped.startswith("#"):
            return (115, 138, 148)
        if any(stripped.startswith(k) for k in (
            "def ", "class ", "if ", "else:", "elif ", "while ", "for ",
            "return ", "import ", "from ", "try:", "except", "with ", "pass",
        )):
            return (255, 121, 198)
        if stripped.startswith(("st.", "cv2.", "os.", "subprocess.")):
            return (139, 233, 253)
        return (248, 248, 242)

    y = code_top + 50
    for i, line in enumerate(code_lines, 1):
        draw.text((50, y),  f"{i:3d}", font=font_num,  fill=(100, 116, 139))
        draw.text((110, y), line,       font=font_code, fill=color_for(line))
        y += line_h

    img.save(os.path.join(OUT, filename))
    print(f"  ✅ 저장: {filename}")


# ══════════════════════════════════════════════════════
# BEFORE — 문제 코드 (mp4v 코덱 저장 → 브라우저 재생 불가)
# ══════════════════════════════════════════════════════
before_code = [
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

make_code_image(
    title        = "❌ 문제 코드 — 브라우저 재생 불가",
    subtitle     = "mp4v 코덱(MPEG-4 Part 2)은 HTML5 Video에서 지원되지 않음",
    code_lines   = before_code,
    filename     = "code_clip_before.png",
    header_color = (220, 53, 69),
)


# ══════════════════════════════════════════════════════
# AFTER — 해결 코드 (ffmpeg로 H.264 자동 변환 + 캐싱)
# ══════════════════════════════════════════════════════
after_code = [
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

make_code_image(
    title        = "✅ 해결 코드 — H.264 자동 변환 + 캐싱",
    subtitle     = "imageio-ffmpeg로 내장 FFmpeg 활용 → 첫 재생 시 1회만 변환",
    code_lines   = after_code,
    filename     = "code_clip_after.png",
    header_color = (40, 167, 69),
)

print("\n완료! 영상 클립 이슈 코드 이미지 2장 생성됨.")
