# generate_numpy_snippet.py — NumPy 사용 코드 스니펫 이미지 생성
# 실행: python generate_numpy_snippet.py

import os, re
from PIL import Image, ImageDraw, ImageFont


CODE_1_TITLE = "core/roi_manager.py — ROI 다각형 침입 판정 (NumPy 배열 변환 + 좌표 연산)"
CODE_1 = '''import numpy as np
import cv2

def is_point_in_roi(point: tuple, roi_polygon) -> bool:
    if roi_polygon is None or len(roi_polygon) < 3:
        return False

    result = cv2.pointPolygonTest(
        roi_polygon.reshape((-1, 1, 2)).astype(np.int32),
        (float(point[0]), float(point[1])),
        False,
    )
    return result >= 0'''


CODE_2_TITLE = "core/detector.py — 사람 발 위치(bottom_center) 좌표 계산"
CODE_2 = '''x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

center = ((x1 + x2) // 2, (y1 + y2) // 2)

bottom_center = ((x1 + x2) // 2, y2)'''


# ── 색상 (VS Code Dark+ 테마 톤) ──────────────────────
BG       = (30, 30, 30)
TITLE_BG = (46, 125, 50)
TITLE_FG = (255, 255, 255)
DEFAULT  = (212, 212, 212)
KEYWORD  = (197, 134, 192)   # def return if import 등
STRING   = (206, 145, 120)
NUMBER   = (181, 206, 168)
COMMENT  = (106, 153, 85)
BUILTIN  = (78, 201, 176)

KEYWORDS = {"def", "return", "if", "elif", "else", "import", "from", "as", "None",
            "True", "False", "in", "not", "and", "or", "class", "self", "lambda",
            "for", "while", "with", "try", "except", "is"}
BUILTINS = {"tuple", "list", "float", "int", "bool", "str", "len", "print",
            "range", "type", "set", "dict"}

TOKEN_RE = re.compile(
    r'(?P<comment>\#[^\n]*)'
    r'|(?P<string>"[^"]*"|\'[^\']*\')'
    r'|(?P<number>\b\d+\b)'
    r'|(?P<ident>[A-Za-z_]\w*)'
    r'|(?P<other>\s+|.)'
)


def tokenize(line):
    for m in TOKEN_RE.finditer(line):
        kind = m.lastgroup
        text = m.group()
        if kind == 'comment':
            yield text, COMMENT
        elif kind == 'string':
            yield text, STRING
        elif kind == 'number':
            yield text, NUMBER
        elif kind == 'ident':
            if text in KEYWORDS:
                yield text, KEYWORD
            elif text in BUILTINS:
                yield text, BUILTIN
            else:
                yield text, DEFAULT
        else:
            yield text, DEFAULT


def get_mono(size):
    for name in ["consola.ttf", "consolab.ttf", "D2Coding.ttf", "cour.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def get_title_font(size):
    for name in ["malgunbd.ttf", "malgun.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


# ── 레이아웃 ───────────────────────────────────────────
WIDTH    = 1200
LINE_H   = 28
PADDING  = 30
TITLE_H  = 48
GAP      = 30

FONT_CODE  = get_mono(18)
FONT_TITLE = get_title_font(16)


def block_height(code_text):
    return TITLE_H + LINE_H * (code_text.count("\n") + 1) + PADDING * 2


h1 = block_height(CODE_1)
h2 = block_height(CODE_2)
TOTAL_H = h1 + GAP + h2

img = Image.new("RGB", (WIDTH, TOTAL_H), BG)
draw = ImageDraw.Draw(img)


def draw_block(y0, title, code_text):
    draw.rectangle([(0, y0), (WIDTH, y0 + TITLE_H)], fill=TITLE_BG)
    draw.text((PADDING, y0 + 14), title, font=FONT_TITLE, fill=TITLE_FG)

    lines = code_text.split("\n")
    cy = y0 + TITLE_H + PADDING
    for line in lines:
        cx = PADDING
        for text, color in tokenize(line):
            draw.text((cx, cy), text, font=FONT_CODE, fill=color)
            bb = draw.textbbox((0, 0), text, font=FONT_CODE)
            cx += bb[2] - bb[0]
        cy += LINE_H
    return y0 + TITLE_H + LINE_H * len(lines) + PADDING * 2


next_y = draw_block(0, CODE_1_TITLE, CODE_1)
draw_block(next_y + GAP, CODE_2_TITLE, CODE_2)

OUTPUT = os.path.join(os.path.dirname(__file__), "numpy_usage_snippet.png")
img.save(OUTPUT)
print(f"[완료] 코드 스니펫 저장 → {OUTPUT}")

try:
    os.startfile(OUTPUT)
    print("[열기] 기본 이미지 뷰어에서 여는 중...")
except Exception as e:
    print(f"[실패] 자동 열기 실패: {e}")
