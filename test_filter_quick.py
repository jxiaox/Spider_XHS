#!/usr/bin/env python3
"""Quick test of is_text_image with new dual-criteria algorithm."""
from PIL import Image
from collections import Counter
import os, glob

def is_text_image_new(img_path):
    """New algorithm: q=32, dominant>=50% AND colors<=25."""
    img = Image.open(img_path).convert('RGB').resize((50, 50))
    pixels = list(img.getdata())
    qpixels = [((r//32)*32, (g//32)*32, (b//32)*32) for r,g,b in pixels]
    counter = Counter(qpixels)
    total = len(qpixels)
    num_colors = len(counter)
    top = counter.most_common(1)[0][1]
    dominant_pct = top / total * 100
    return dominant_pct >= 50.0 and num_colors <= 25, dominant_pct, num_colors

base = '/Users/jxiaox/github.com/Spider_XHS/datas/media_datas/还是叫吴富贵吧_5b6150c56b58b741e26b8c7f'
# Find sample images
samples = glob.glob(os.path.join(base, '*/image_0.jpg'))[:20]
for p in sorted(samples):
    note = p.split('/')[-2][:30]
    is_text, d, n = is_text_image_new(p)
    tag = "TEXT" if is_text else "PHOTO"
    print(f'[{tag:5}] d={d:5.1f}% c={n:3d} | {note}')
