"""Set search-friendly metadata and clickable links on every free PDF in downloads/.

Usage: python3 tools/pdf_meta.py          (run after any free PDF is regenerated; safe to run again)
- Title / Author / Subject / Keywords: Google shows a PDF's Title in results, and the factory leaves Author "anonymous".
- Page 3 (the "Want more?" page) prints the Amazon, Etsy and site addresses as plain text; this adds link areas over them.
Needs pypdf and poppler's pdftotext. Mapping of PDF -> page comes from tools/books.json and tools/extras.json.
"""
import json, os, re, subprocess
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link
from pypdf.generic import NameObject

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://bigclearpuzzlebooks.com"
SHOP = "https://bigclearpuzzlebooks.etsy.com"
SERIES = "https://www.amazon.com/dp/B0HRDKM5VV"
AUTHOR = "https://www.amazon.com/Callan-Brooks/e/B0HRK5K7FT"
books = json.load(open(os.path.join(ROOT, "tools", "books.json")))
extras = json.load(open(os.path.join(ROOT, "tools", "extras.json")))
SLUG = {"christmas": "christmas-word-search-for-seniors", "winter": "winter-word-search-for-seniors", "bible": "bible-word-search-large-print",
        "hymns": "hymn-word-search-large-print", "nostalgia": "1950s-word-search-for-seniors", "garden": "garden-word-search-for-seniors",
        "cooking": "cooking-word-search-for-seniors"}
NAME = {"christmas": "Christmas", "winter": "Winter", "bible": "Bible", "hymns": "Hymn", "nostalgia": "1950s & 60s", "garden": "Garden",
        "cooking": "Cooking", "thanksgiving": "Thanksgiving", "fall": "Fall Harvest"}
def lc(n):
    return n if n in ("Christmas", "Bible", "Thanksgiving", "1950s & 60s") else n.lower()


LEVEL = {"sudoku-1": "Easy", "sudoku-easy-2": "Easy", "sudoku-medium": "Medium", "sudoku-medium-2": "Medium", "sudoku-hard": "Hard", "sudoku-hard-2": "Hard"}

items = []   # pdf, page url, title, subject, keywords, etsy url, amazon url
for k, b in books.items():
    items.append((b["pdf"], f"{BASE}/free/{SLUG[k]}/", f"Free Large Print {NAME[k]} Word Search: {b['puzzle_title'][3:]} | Big Clear Puzzle Books",
                  f"Large print {lc(NAME[k])} word search for seniors and adults: 21 pt grid, 18 pt word list, answer key",
                  f"large print word search, {lc(NAME[k])} word search, seniors, printable, answer key", f"{SHOP}/listing/{b['listing']}", SERIES))
for x in extras:
    url = f"{BASE}/free/{x['slug']}/"
    if x.get("extra_easy"):
        items.append((x["pdf"], url, f"Free Extra Easy Large Print Word Search: {x['puzzle_title']} | Big Clear Puzzle Books",
                      "Extra easy large print word search for seniors and memory care: 10 x 10 grid, giant 34 pt letters, across or down only, answer key",
                      "extra easy word search, giant print word search, large print, seniors, memory care, printable, answer key", SHOP, SERIES))
    elif x.get("sudoku"):
        lv = x.get("level") or LEVEL[x["key"]]
        items.append((x["pdf"], url, f"Free Large Print {lv} Sudoku: {x['puzzle_title']} | Big Clear Puzzle Books",
                      f"Large print {lv.lower()} sudoku for seniors and adults: big bold numbers, one puzzle per page, answer key",
                      f"large print sudoku, {lv.lower()} sudoku, seniors, printable, answer key", SHOP, AUTHOR))
    else:
        th = ("fall" if "harvest" in x["slug"] else "thanksgiving") if x.get("seasonal") else x["book"]
        items.append((x["pdf"], url, f"Free Large Print {NAME[th]} Word Search: {x['puzzle_title']} | Big Clear Puzzle Books",
                      f"Large print {lc(NAME[th])} word search for seniors and adults: 21 pt grid, 18 pt word list, answer key",
                      f"large print word search, {lc(NAME[th])} word search, seniors, printable, answer key",
                      f"{SHOP}/listing/{books[x['book']]['listing']}", SERIES))


def words(pdf, page):
    out = subprocess.run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page), pdf, "-"], capture_output=True, text=True).stdout
    return [(float(a), float(b), float(c), float(d), w) for a, b, c, d, w in
            re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', out)]


done = 0
for pdf, url, title, subject, keywords, etsy, amazon in items:
    path = os.path.join(ROOT, "downloads", pdf)
    if not os.path.exists(path):
        print("missing", pdf); continue
    r = PdfReader(path); n = len(r.pages); H = float(r.pages[-1].mediabox.height)
    w = PdfWriter(clone_from=path)
    last = w.pages[n - 1]
    if "/Annots" in last:                      # idempotent: drop links added by an earlier run
        del last[NameObject("/Annots")]
    ws = words(path, n); links = []
    for i, (x0, y0, x1, y1, t) in enumerate(ws):
        if t == "Amazon":                      # link the rest of that line ("Amazon (search Callan Brooks large print)")
            xe = max(c for a, b, c, d, tt in ws if abs(b - y0) < 1 and a >= x0)
            links.append((x0, y0, xe, y1, amazon))
        elif t == "bigclearpuzzlebooks.etsy.com":
            links.append((x0, y0, x1, y1, etsy))
        elif t == "bigclearpuzzlebooks.com":
            links.append((x0, y0, x1, y1, f"{BASE}/#signup" if y0 < H - 120 else url))
    for x0, y0, x1, y1, href in links:
        w.add_annotation(page_number=n - 1, annotation=Link(rect=(x0 - 2, H - y1 - 2, x1 + 2, H - y0 + 2), url=href))
    w.add_metadata({"/Title": title, "/Author": "Big Clear Puzzle Books", "/Subject": subject, "/Keywords": keywords, "/Creator": "Big Clear Puzzle Books"})
    tmp = path + ".tmp"; w.write(tmp); os.replace(tmp, path); done += 1
    print(f"{pdf}: {len(links)} links")
print("pdfs updated:", done)
