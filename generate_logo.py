# generate_logo.py — SAFEVIEW 팀 로고 생성
# 실행: python generate_logo.py

from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

def make_logo(size=512):
    """SAFEVIEW 로고: 방패 + 눈(감시) 모티프"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    s = size / 512  # 스케일

    # ── 방패 외곽 (그라데이션 효과를 위한 다중 레이어) ──
    # 바깥 방패 (진한 녹색)
    shield_outer = [
        (cx, int(40*s)),           # 상단 꼭짓점
        (int(460*s), int(120*s)),  # 오른쪽 상단
        (int(440*s), int(320*s)),  # 오른쪽 중간
        (cx, int(480*s)),          # 하단 꼭짓점
        (int(72*s), int(320*s)),   # 왼쪽 중간
        (int(52*s), int(120*s)),   # 왼쪽 상단
    ]
    draw.polygon(shield_outer, fill=(46, 125, 50))  # 진한 녹색

    # 안쪽 방패 (밝은 녹색)
    shield_inner = [
        (cx, int(70*s)),
        (int(430*s), int(140*s)),
        (int(412*s), int(310*s)),
        (cx, int(455*s)),
        (int(100*s), int(310*s)),
        (int(82*s), int(140*s)),
    ]
    draw.polygon(shield_inner, fill=(76, 175, 80))  # 밝은 녹색

    # ── 눈 모양 (감시/관찰 상징) ──
    # 눈 외곽 (흰색 타원)
    eye_cx, eye_cy = cx, int(220*s)
    eye_rx, eye_ry = int(120*s), int(60*s)

    # 눈 모양: 양쪽 끝이 뾰족한 타원
    eye_points = []
    import math
    for angle in range(0, 360, 5):
        rad = math.radians(angle)
        # 수정된 타원 (위아래 찌그러진 렌즈 형태)
        x = eye_cx + int(eye_rx * math.cos(rad))
        factor = 1.0 if (90 <= angle <= 270) else 1.0
        y = eye_cy + int(eye_ry * math.sin(rad) * factor)
        eye_points.append((x, y))
    draw.polygon(eye_points, fill=(255, 255, 255))

    # 동공 (진한 녹색 원)
    pupil_r = int(35*s)
    draw.ellipse(
        [(eye_cx - pupil_r, eye_cy - pupil_r),
         (eye_cx + pupil_r, eye_cy + pupil_r)],
        fill=(27, 94, 32)
    )

    # 동공 하이라이트 (흰색 점)
    hl_r = int(12*s)
    hl_x, hl_y = eye_cx - int(10*s), eye_cy - int(10*s)
    draw.ellipse(
        [(hl_x - hl_r, hl_y - hl_r),
         (hl_x + hl_r, hl_y + hl_r)],
        fill=(255, 255, 255, 200)
    )

    # ── 체크마크 (안전 상징) ──
    check_points = [
        (int(180*s), int(330*s)),
        (int(230*s), int(380*s)),
        (int(340*s), int(290*s)),
    ]
    draw.line(check_points, fill=(255, 255, 255), width=int(20*s), joint="curve")

    return img


def make_logo_with_text(logo_img, width=800):
    """로고 + SAFEVIEW 텍스트 조합"""
    logo_size = 180
    logo_resized = logo_img.resize((logo_size, logo_size), Image.LANCZOS)

    h = 220
    img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 로고 배치
    logo_y = (h - logo_size) // 2
    img.paste(logo_resized, (20, logo_y), logo_resized)

    # 텍스트
    try:
        font_large = ImageFont.truetype("malgunbd.ttf", 52)
        font_small = ImageFont.truetype("malgun.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text_x = 20 + logo_size + 20

    # SAFE (검정) + VIEW (녹색)
    draw.text((text_x, 55), "SAFE", fill=(26, 26, 26), font=font_large)
    safe_bbox = draw.textbbox((text_x, 55), "SAFE", font=font_large)
    draw.text((safe_bbox[2], 55), "VIEW", fill=(76, 175, 80), font=font_large)

    # 부제
    draw.text((text_x, 120), "안전사각지대 감지 시스템", fill=(100, 116, 139), font=font_small)

    return img


def make_favicon(logo_img, size=32):
    """브라우저 파비콘용 작은 아이콘"""
    return logo_img.resize((size, size), Image.LANCZOS)


# ── 생성 ──
print("SAFEVIEW 로고 생성 중...")

logo = make_logo(512)
logo.save(os.path.join(OUT_DIR, "logo.png"))
print("  ✅ logo.png (512x512)")

logo_text = make_logo_with_text(logo)
logo_text.save(os.path.join(OUT_DIR, "logo_with_text.png"))
print("  ✅ logo_with_text.png (800x220)")

favicon = make_favicon(logo, 32)
favicon.save(os.path.join(OUT_DIR, "favicon.png"))
print("  ✅ favicon.png (32x32)")

# 다크 배경 버전
logo_dark_bg = Image.new("RGBA", (600, 600), (15, 23, 42))
logo_resized = logo.resize((500, 500), Image.LANCZOS)
logo_dark_bg.paste(logo_resized, (50, 50), logo_resized)
logo_dark_bg.save(os.path.join(OUT_DIR, "logo_dark.png"))
print("  ✅ logo_dark.png (600x600, 다크 배경)")

print(f"\n완료! 프로젝트 폴더에서 확인하세요.")
