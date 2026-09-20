"""Shared GIF-assembly helper for poster.py and cotd_poster.py — one adaptive
palette shared across all frames (stable colors, no flicker) then handed to
Pillow's own frame-diffing GIF encoder for a smaller file."""
from PIL import Image

def save_gif(frames, path, step_ms):
    base = frames[0].convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
    paletted = [base] + [f.quantize(palette=base) for f in frames[1:]]
    paletted[0].save(str(path), save_all=True, append_images=paletted[1:],
                      duration=step_ms, loop=0, optimize=True)
