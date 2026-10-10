"""Shared graphics, typography, and video encoding utilities for Privreach Launch Film."""

import os
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Color Palette
BG_WARM_WHITE = (250, 250, 248)
WHITE = (255, 255, 255)
INK_NAVY = (23, 32, 51)
INK_DARK = (15, 23, 42)
ELECTRIC_BLUE = (36, 92, 255)
PALE_BLUE = (238, 244, 255)
SOFT_SLATE = (221, 229, 242)
BORDER_MIST = (226, 232, 240)
TEXT_MUTED = (110, 125, 148)
TEXT_SUBTLE = (148, 163, 184)
MINT_GREEN = (16, 185, 129)
MINT_BG = (236, 253, 245)

FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_LIGHT = r"C:\Windows\Fonts\segoeuil.ttf"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"

_font_cache = {}

def get_font(size: int, weight: str = "regular"):
    key = (size, weight)
    if key in _font_cache:
        return _font_cache[key]
    
    path = FONT_REG
    if weight == "bold":
        path = FONT_BOLD
    elif weight == "light":
        path = FONT_LIGHT
    elif weight == "mono":
        path = FONT_MONO
        
    try:
        font = ImageFont.truetype(path, size)
    except Exception:
        font = ImageFont.load_default()
    _font_cache[key] = font
    return font

def draw_grid(draw: ImageDraw.ImageDraw, w=1920, h=1080, step=80, alpha_factor=1.0):
    """Draw a microscopic architectural grid."""
    color = (228, 234, 243)
    for x in range(step, w, step):
        draw.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(step, h, step):
        draw.line([(0, y), (w, y)], fill=color, width=1)

def draw_card(draw: ImageDraw.ImageDraw, box, fill=WHITE, border=BORDER_MIST, radius=12, shadow=True):
    """Draw an elegant minimalist card with soft drop shadow."""
    x0, y0, x1, y1 = box
    if shadow:
        # Subtle ambient shadow
        for offset in range(1, 5):
            s_color = (235 - offset * 3, 238 - offset * 2, 242 - offset * 2)
            draw.rounded_rectangle([x0 - offset, y0 - offset + 2, x1 + offset, y1 + offset + 4], radius=radius + offset, outline=s_color, width=1)
            
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=border, width=1)

def draw_text_centered(draw: ImageDraw.ImageDraw, text: str, cy: int, w=1920, font=None, fill=INK_NAVY):
    """Draw text centered horizontally."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    tx = (w - tw) // 2
    draw.text((tx, cy), text, font=font, fill=fill)

def get_fade_alpha(t_sec, start_fade_in, end_fade_in, start_fade_out, end_fade_out):
    """Calculate opacity factor (0.0 to 1.0) based on time windows."""
    if t_sec < start_fade_in:
        return 0.0
    elif t_sec < end_fade_in:
        return (t_sec - start_fade_in) / max(end_fade_in - start_fade_in, 0.001)
    elif t_sec < start_fade_out:
        return 1.0
    elif t_sec < end_fade_out:
        return 1.0 - (t_sec - start_fade_out) / max(end_fade_out - start_fade_out, 0.001)
    else:
        return 0.0

def blend_color(c1, c2, factor):
    """Blend between color c1 and c2 by factor 0..1."""
    return tuple(int(a + (b - a) * factor) for a, b in zip(c1, c2))

def create_video_writer(output_path, width=1920, height=1080, fps=24):
    """Open an ffmpeg pipe process for raw video frame streaming."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "medium",
        output_path
    ]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p
