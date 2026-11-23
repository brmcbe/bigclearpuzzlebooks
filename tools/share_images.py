"""2:3 (1000x1500) share images for free printable pages: Pinterest Save button image and og:image.
Reads a JSON list on stdin from build_site.py: [{out, src, pdf, title, sudoku}]. Renders the page from the PDF
(pdftoppm) when available, else uses the preview JPG. Skips images that already exist, so a rebuild only renders new pages
(run with --force to redo all, e.g. after changing this design)."""
import json, os, sys, subprocess, tempfile, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAVY = (31, 58, 95); GOLD = (255, 222, 115); CREAM = (250, 247, 240)
FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"]
def F(size):
    for f in FONTS:
        if os.path.exists(f): return ImageFont.truetype(f, size)
    return ImageFont.load_default()

def puzzle_image(item):
    pdf = os.path.join(ROOT, item["pdf"]) if item.get("pdf") else ""
    if pdf and os.path.exists(pdf):
        try:
            t = tempfile.mkdtemp(); out = os.path.join(t, "p")
            subprocess.run(["pdftoppm", "-jpeg", "-singlefile", "-f", "1", "-l", "1", "-scale-to-x", "1000", "-scale-to-y", "-1", pdf, out],
                           check=True, capture_output=True)
            return Image.open(out + ".jpg").convert("RGB")
        except Exception:
            pass
    return Image.open(os.path.join(ROOT, item["src"])).convert("RGB")

def render(item):
    W, H = 1000, 1500; img = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(img)
    title = item["title"]; size = 58
    while True:                                   # largest size that fits in 3 lines
        lines = textwrap.wrap(title, width=int(1700 / size))
        if len(lines) <= 3 or size <= 40: break
        size -= 4
    top = 70 + len(lines) * (size + 12) + 40
    d.rectangle([0, 0, W, top], fill=NAVY)
    y = 60
    for ln in lines:
        d.text((W / 2, y), ln, font=F(size), fill="white", anchor="ma"); y += size + 12
    foot = 150; avail_h = H - top - foot - 50; avail_w = W - 90
    p = puzzle_image(item); s = min(avail_w / p.width, avail_h / p.height)
    p = p.resize((int(p.width * s), int(p.height * s)), Image.LANCZOS)
    x = (W - p.width) // 2; py = top + 25
    d.rectangle([x + 8, py + 8, x + p.width + 8, py + p.height + 8], fill=(205, 200, 190))
    img.paste(p, (x, py)); d.rectangle([x, py, x + p.width, py + p.height], outline=(170, 170, 170), width=2)
    d.rectangle([0, H - foot, W, H], fill=GOLD)
    d.text((W / 2, H - foot + 28), "FREE PRINTABLE · ANSWERS INCLUDED", font=F(40), fill=NAVY, anchor="ma")
    d.text((W / 2, H - foot + 86), "bigclearpuzzlebooks.com", font=F(36), fill=NAVY, anchor="ma")
    out = os.path.join(ROOT, item["out"]); os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, quality=86, optimize=True, progressive=True)

if __name__ == "__main__":
    items = json.load(sys.stdin); made = 0
    for it in items:
        if os.path.exists(os.path.join(ROOT, it["out"])) and "--force" not in sys.argv: continue
        render(it); made += 1
    print(f"{made} made, {len(items)} total")
