"""Build the static site for Big Clear Puzzle Books (GitHub Pages, repo root).

Usage: python3 tools/build_site.py
Reads tools/books.json (one free puzzle per book) and writes index.html, free/<slug>/index.html,
activity-directors/index.html, sitemap.xml and robots.txt. No dependencies beyond the standard library.
To add a free printable: put the PDF in downloads/, a preview JPG in img/, add an entry to books.json, rebuild.
"""
import json, os, datetime, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://bigclearpuzzlebooks.com"
SHOP = "https://bigclearpuzzlebooks.etsy.com"           # Share & Save format
PACK = 4615304644                                         # Activity Director Pack listing
BUNDLES = {"christmas": 4615214324, "winter": 4615214324, "bible": 4615214518, "hymns": 4615214518}
SAMPLER = 4615223623
books = json.load(open(os.path.join(ROOT, "tools", "books.json")))
TODAY = datetime.date.today().isoformat()

SEO = {  # slug, page title, h1, intro sentence
    "christmas": ("christmas-word-search-for-seniors", "Free Printable Large Print Christmas Word Search for Seniors",
                  "Free large-print Christmas word search", "A big, easy-to-read Christmas puzzle for grandparents, memory care groups and holiday parties."),
    "winter": ("winter-word-search-for-seniors", "Free Printable Large Print Winter Word Search for Seniors",
               "Free large-print winter word search", "A cozy snow-day puzzle in extra-large letters, ready to print."),
    "bible": ("bible-word-search-large-print", "Free Printable Large Print Bible Word Search for Seniors",
              "Free large-print Bible word search", "Words from Genesis in big, clear letters for Sunday school, church groups and seniors."),
    "hymns": ("hymn-word-search-large-print", "Free Printable Large Print Hymn Word Search (Amazing Grace)",
              "Free large-print hymn word search", "Words from Amazing Grace in a big, clear word search for church groups and nursing homes."),
    "nostalgia": ("1950s-word-search-for-seniors", "Free Printable 1950s Nostalgia Word Search for Seniors (Large Print)",
                  "Free large-print 1950s nostalgia word search", "Soda fountain words that spark memories: a reminiscence activity for seniors and memory care."),
    "garden": ("garden-word-search-for-seniors", "Free Printable Large Print Garden Word Search for Seniors",
               "Free large-print garden word search", "Spring flowers in extra-large print: one puzzle per page with the solution."),
    "cooking": ("cooking-word-search-for-seniors", "Free Printable Large Print Cooking Word Search for Seniors",
                "Free large-print cooking word search", "Kitchen words in a big, clear word search for seniors and bakers."),
}
ORDER = ["christmas", "winter", "bible", "hymns", "nostalgia", "garden", "cooking"]

CSS = """*{box-sizing:border-box}body{margin:0;font-family:Verdana,Geneva,'DejaVu Sans',sans-serif;font-size:20px;line-height:1.6;color:#1b1b1b;background:#faf7f0}
a{color:#1f3a5f}header{background:#1f3a5f;color:#fff}header .w{display:flex;align-items:center;gap:16px;padding:14px 20px}
header img{width:56px;height:56px;border-radius:50%;background:#fff}header a{color:#fff;text-decoration:none;font-weight:bold;font-size:24px}
nav a{color:#fff;margin-left:18px;font-size:18px}.w{max-width:1040px;margin:0 auto;padding:0 20px}
h1{font-size:40px;line-height:1.2;margin:36px 0 12px;color:#1f3a5f}h2{font-size:30px;color:#1f3a5f;margin-top:44px}
.lead{font-size:23px}.btn{display:inline-block;background:#ffde73;color:#1f3a5f;font-weight:bold;padding:14px 26px;border-radius:40px;text-decoration:none;margin:8px 8px 8px 0;font-size:21px}
.btn.alt{background:#1f3a5f;color:#fff}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:22px}
.card{background:#fff;border-radius:10px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,.08)}.card img{width:100%;height:auto;border:1px solid #ddd;border-radius:4px}
.card h3{margin:10px 0 4px;font-size:22px}.two{display:grid;grid-template-columns:1fr 1fr;gap:34px;align-items:start}
.two img{width:100%;height:auto;border:1px solid #ccc;border-radius:6px;background:#fff}.box{background:#fff;border-left:8px solid #ffde73;padding:16px 22px;border-radius:6px;margin:24px 0}
ul{padding-left:26px}footer{margin-top:60px;background:#1f3a5f;color:#fff;padding:26px 0;font-size:17px}footer a{color:#fff}
@media(max-width:760px){.two{grid-template-columns:1fr}h1{font-size:32px}nav{display:none}}"""


def page(path, title, desc, body, canonical):
    depth = path.count("/")
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}"><link rel="icon" href="{up}img/favicon.png"><link rel="apple-touch-icon" href="{up}img/apple-touch-icon.png">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/img/christmas-preview.jpg"><meta name="p:domain_verify" content="5f2e6b6f365deaad7f1cde96575db747"/><style>{CSS}</style></head><body>
<header><div class="w"><img src="{up}img/icon.png" alt=""><a href="{up}">Big Clear Puzzle Books</a>
<nav><a href="{up}#free">Free printables</a><a href="{up}activity-directors/">Activity directors</a><a href="{SHOP}">Shop</a></nav></div></header>
<main class="w">{body}</main>
<footer><div class="w">Big Clear Puzzle Books · Large-print word searches that are easy to see and always right.
· <a href="{SHOP}">Etsy shop</a> · <a href="https://www.pinterest.com/bigclearpuzzlebooks/">Pinterest</a> · <a href="mailto:hello@bigclearpuzzlebooks.com">hello@bigclearpuzzlebooks.com</a><br>
Free printables are for personal, family, classroom and activity-group use. Please share the link, not the file.</div></footer>
</body></html>"""


def write(rel, text):
    p = os.path.join(ROOT, rel); os.makedirs(os.path.dirname(p) or ROOT, exist_ok=True); open(p, "w").write(text)


urls = [BASE + "/"]
# free pages
def card(k, up="../../"):
    b = books[k]; slug, title, h1, intro = SEO[k]
    return (f'<div class="card"><a href="{up}free/{slug}/"><img src="{up}img/{k}-preview.jpg" alt="Free large print {b["name"]} word search" '
            f'loading="lazy" width="765" height="990"></a><h3><a href="{up}free/{slug}/">{b["name"]}</a></h3>'
            f'<p>{html.escape(b["puzzle_title"][3:])} · free PDF</p></div>')


for k in ORDER:
    b = books[k]; slug, title, h1, intro = SEO[k]; url = f"{BASE}/free/{slug}/"; urls.append(url)
    bundle = BUNDLES.get(k)
    extra = f'<a class="btn alt" href="{SHOP}/listing/{bundle}">2-book bundle (100 puzzles)</a>' if bundle else ""
    # Paperback link appears only once the book is Live on Amazon: add "asin" to tools/books.json
    if b.get("asin"):
        extra += f'<a class="btn alt" href="https://www.amazon.com/dp/{b["asin"]}">Paperback on Amazon</a>'
    body = f"""<h1>{h1}</h1><p class="lead">{intro}</p>
<div class="two"><div><img src="../../img/{k}-preview.jpg" alt="Large print {b['name']} word search puzzle: {html.escape(b['puzzle_title'][3:])}" width="765" height="990"></div>
<div><p><a class="btn" href="../../downloads/{b['pdf']}" download>Download the free PDF</a></p>
<ul><li>US Letter (8.5 x 11 in), prints on A4 too</li><li>Extra-large letters: 21 pt bold grid, 17 pt word list</li>
<li>Words read forward, down or diagonally. Nothing backwards</li><li>Solution included</li><li>Checked by computer: every word is there exactly once</li></ul>
<div class="box"><b>Want more?</b> This puzzle comes from the full <b>{b['name']}</b> book: 50 large-print puzzles, one per page, with every solution.
<br><a class="btn alt" href="{SHOP}/listing/{b['listing']}">Get all 50 puzzles (printable PDF)</a>{extra}</div>
<p>Running activities for a whole community? The <a href="../../activity-directors/">Activity Director Pack</a> has all 7 books (350 puzzles) with a facility license.</p>
</div></div>
<h2>More free large-print word searches</h2><div class="grid">{''.join(card(o) for o in ORDER if o != k)}</div>"""
    write(f"free/{slug}/index.html", page(f"free/{slug}/", title, intro + " Free printable PDF with solution.", body, url))

# activity directors
url = f"{BASE}/activity-directors/"; urls.append(url)
body = f"""<h1>Large-print word searches for activity directors</h1>
<p class="lead">350 easy-to-read puzzles across 7 themes, with a license to print for your whole facility. One purchase, no subscription.</p>
<p><a class="btn" href="{SHOP}/listing/{PACK}">See the Activity Director Pack ($19.99)</a><a class="btn alt" href="{SHOP}/listing/{SAMPLER}">Try the 10-puzzle sampler</a></p>
<div class="box"><b>Facility license:</b> print unlimited copies for the residents, participants or members of one facility, program or location
(senior living, memory care, adult day, church group, classroom).</div>
<h2>Why residents can finish them</h2><ul>
<li>One puzzle per page, 21 pt bold grid letters, 17 pt word list</li><li>Words only read forward, down or diagonally. Nothing backwards</li>
<li>Every grid checked by computer so each word is really there, exactly once, and every answer is in the back</li>
<li>Themes people talk about: Christmas, Winter, Bible, Hymns, 1950s & 60s Memories, Garden, Cooking & Baking</li></ul>
<h2>Try one free first</h2><div class="grid">{''.join(card(o, '../') for o in ORDER)}</div>"""
write("activity-directors/index.html", page("activity-directors/", "Large Print Word Search Puzzles for Activity Directors | Facility License",
                                           "350 large-print word search puzzles for senior living, memory care and adult day programs, with a facility print license.", body, url))

# home
live = [k for k in ORDER if books[k].get("asin")]
paperbacks = ("<h2>Paperbacks on Amazon</h2><p>Prefer a real book? These are printed paperbacks, 8.5 x 11 in, 50 puzzles each. A good gift.</p><p>"
              + "".join(f'<a class="btn alt" href="https://www.amazon.com/dp/{books[k]["asin"]}">{html.escape(books[k]["name"])} paperback</a>' for k in live)
              + "</p>") if live else ""
body = f"""<h1>Free large-print word search printables for seniors</h1>
<p class="lead">Big, clear puzzles that are easy to see and always right. Print one free, then get the full books on Etsy.</p>
<p><a class="btn" href="#free">Free printables</a><a class="btn alt" href="{SHOP}">Visit the shop</a></p>
<h2 id="free">Free printable puzzles</h2><p>Each free PDF has one puzzle and its solution. New ones are added often.</p>
<div class="grid">{''.join(card(o, '') for o in ORDER)}</div>
{paperbacks}<h2>For activity directors</h2><p>All 7 books, 350 puzzles, with a facility print license: <a href="activity-directors/">Activity Director Pack</a>.</p>
<h2>What makes them different</h2><ul><li>One puzzle per page with extra-large bold letters</li><li>Words read forward, down or diagonally, never backwards</li>
<li>A computer checks every grid so each word appears exactly once, and every answer is in the back</li>
</ul>"""
write("index.html", page("", "Free Large Print Word Search Printables for Seniors | Big Clear Puzzle Books",
                         "Free printable large-print word search puzzles for seniors, memory care and activity directors: Christmas, Bible, hymns, 1950s and more.", body, BASE + "/"))

write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
      "".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
write(".nojekyll", "")
print("pages:", len(urls))
