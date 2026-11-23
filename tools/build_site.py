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

ML_SCRIPT = """<script>(function(w,d,e,u,f,l,n){w[f]=w[f]||function(){(w[f].q=w[f].q||[]).push(arguments);},l=d.createElement(e),l.async=1,l.src=u,n=d.getElementsByTagName(e)[0],n.parentNode.insertBefore(l,n);})(window,document,'script','https://assets.mailerlite.com/js/universal.js','ml');ml('account','2817294');</script>"""
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
.series{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:26px 0}.tile{display:flex;gap:18px;align-items:center;background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 10px rgba(0,0,0,.1);text-decoration:none;color:#1b1b1b;font-size:19px}
.tile img{width:150px;height:auto;border-radius:4px}.tile b{display:block;font-size:30px;color:#1f3a5f;margin-bottom:4px}.tile em{display:block;margin-top:10px;font-style:normal;font-weight:bold;color:#1f3a5f}
.signup{background:#1f3a5f;color:#fff;border-radius:12px;padding:22px 26px;margin:30px 0}.signup h2{color:#fff;margin-top:0}.sf{display:flex;flex-wrap:wrap;gap:10px}
.sf input{font-size:20px;padding:12px 14px;border-radius:8px;border:0;flex:1 1 220px}.small{font-size:16px;opacity:.85}.jump{font-size:18px}
@media(max-width:760px){.two,.series{grid-template-columns:1fr}h1{font-size:32px}nav a{margin-left:10px;font-size:15px}.tile img{width:110px}}"""


def page(path, title, desc, body, canonical):
    depth = path.count("/")
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}"><link rel="icon" href="{up}img/favicon.png"><link rel="apple-touch-icon" href="{up}img/apple-touch-icon.png">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/img/christmas-preview.jpg"><meta name="p:domain_verify" content="5f2e6b6f365deaad7f1cde96575db747"/>{ML_SCRIPT}<style>{CSS}</style></head><body>
<header><div class="w"><img src="{up}img/icon.png" alt=""><a href="{up}">Big Clear Puzzle Books</a>
<nav><a href="{up}word-search/">Word Search</a><a href="{up}sudoku/">Sudoku</a><a href="{up}#signup">Free monthly pack</a><a href="{up}activity-directors/">Activity directors</a><a href="{SHOP}">Shop</a></nav></div></header>
<main class="w">{body}</main>
<footer><div class="w">Big Clear Puzzle Books · Large-print word searches and sudoku that are easy to see and always right.
· <a href="{SHOP}">Etsy shop</a> · <a href="https://www.pinterest.com/bigclearpuzzlebooks/">Pinterest</a> · <a href="mailto:hello@bigclearpuzzlebooks.com">hello@bigclearpuzzlebooks.com</a><br>
Free printables are for personal, family, classroom and activity-group use. Please share the link, not the file.</div></footer>
</body></html>"""


def write(rel, text):
    p = os.path.join(ROOT, rel); os.makedirs(os.path.dirname(p) or ROOT, exist_ok=True); open(p, "w").write(text)


ML_FORM = "75aY4B"       # MailerLite embedded form "Website - Monthly Activity Pack" (account 2817294, group Monthly Activity Pack)
def signup(up=""):
    return f"""<div class="signup" id="signup"><h2>Get a free puzzle pack every month</h2>
<p>December's pack is ready: 5 holiday word searches and 3 sudoku in large print, with solutions. Sign up and it arrives by email in a few minutes.</p>
<div class="ml-embedded" data-form="{ML_FORM}"></div>
<p class="small">For seniors, families and activity directors. We never share your email, and you can unsubscribe anytime.</p></div>"""

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
{signup("../../")}<h2>More free large-print word searches</h2><div class="grid">{''.join(card(o) for o in ORDER if o != k)}</div>"""
    write(f"free/{slug}/index.html", page(f"free/{slug}/", title, intro + " Free printable PDF with solution.", body, url))

# extra free pages (tools/extras.json): more puzzles per book, seasonal, sudoku
extras = json.load(open(os.path.join(ROOT, "tools", "extras.json")))
def xcard(x, up="../../"):
    return (f'<div class="card"><a href="{up}free/{x["slug"]}/"><img src="{up}img/{x["key"]}-preview.jpg" alt="{html.escape(x["title"])}" '
            f'loading="lazy" width="765" height="990"></a><h3><a href="{up}free/{x["slug"]}/">{html.escape(x["puzzle_title"])}</a></h3>'
            f'<p>{"Sudoku" if x.get("sudoku") else (books[x["book"]]["name"] if not x.get("seasonal") else "Thanksgiving")} · free PDF</p></div>')
for x in extras:
    url = f"{BASE}/free/{x['slug']}/"; urls.append(url); k = x["book"]
    if x.get("sudoku"):
        more = (f'<div class="box"><b>Want more?</b> Each <b>Large Print Sudoku for Seniors</b> book has 100 puzzles like this one, one per page, '
                f'with every solution. The series has 7 volumes, from Easy to Hard.<br><a class="btn alt" href="{SHOP}">See the sudoku books (printable PDF)</a></div>')
        bullets = "<li>US Letter (8.5 x 11 in), prints on A4 too</li><li>Extra-large bold numbers, thick 3 x 3 box lines</li><li>Difficulty checked by a logic solver</li><li>Solution on page 2</li><li>Checked by computer: exactly one answer</li>"
    else:
        b = books[k]; lead = ("Get ready for Christmas next: the full <b>Christmas</b> book has 50 large-print puzzles, one per page, with every solution."
                              if x.get("seasonal") else f"This puzzle comes from the full <b>{b['name']}</b> book: 50 large-print puzzles, one per page, with every solution.")
        more = f'<div class="box"><b>Want more?</b> {lead}<br><a class="btn alt" href="{SHOP}/listing/{b["listing"]}">Get all 50 puzzles (printable PDF)</a>'
        if b.get("asin"): more += f'<a class="btn alt" href="https://www.amazon.com/dp/{b["asin"]}">Paperback on Amazon</a>'
        more += "</div>"
        bullets = "<li>US Letter (8.5 x 11 in), prints on A4 too</li><li>Extra-large letters: 21 pt bold grid, 17 pt word list</li><li>Words read forward, down or diagonally. Nothing backwards</li><li>Solution on page 2</li><li>Checked by computer: every word is there exactly once</li>"
    sib = [y for y in extras if y is not x and ((x.get("seasonal") and y.get("seasonal")) or (not x.get("seasonal") and not y.get("seasonal") and k and y["book"] == k))]
    grid = "".join(xcard(y) for y in sib[:3]) + "".join(card(o) for o in ORDER[:6 - min(len(sib), 3)] if o != k)
    body = f"""<h1>{html.escape(x['h1'])}</h1><p class="lead">{html.escape(x['intro'])}</p>
<div class="two"><div><img src="../../img/{x['key']}-preview.jpg" alt="{html.escape(x['title'])}" width="765" height="990"></div>
<div><p><a class="btn" href="../../downloads/{x['pdf']}" download>Download the free PDF</a></p><ul>{bullets}</ul>{more}
<p>Running activities for a whole community? The <a href="../../activity-directors/">Activity Director Pack</a> has all 7 books (350 puzzles) with a facility license.</p>
</div></div>{signup("../../")}<h2>More free large-print puzzles</h2><div class="grid">{grid}</div>"""
    write(f"free/{x['slug']}/index.html", page(f"free/{x['slug']}/", x["title"], x["intro"] + " Free printable PDF with solution.", body, url))

# ---------- shared blocks ----------
SUDOKU = [  # volume, level, Etsy listing (published by Brad), Amazon ASIN when Live
    (1, "Easy", 4623561048), (2, "Easy", 4623569642), (3, "Easy to Medium", 4623562913), (4, "Medium", 4623569840),
    (5, "Medium", 4623570864), (6, "Medium to Hard", 4623564155), (7, "Hard", 4623571180)]
SUDOKU_ASIN = {}          # volume -> ASIN once Live on Amazon
SUDOKU_ON_ETSY = True     # True once the 7 drafts are published; until then buttons go to the shop home
ws_extras = [x for x in extras if not x.get("seasonal") and not x.get("sudoku")]
sd_extras = [x for x in extras if x.get("sudoku")]
seasonal = [x for x in extras if x.get("seasonal")]

def sd_card(v, lv, lid, up):
    href = f"{SHOP}/listing/{lid}" if SUDOKU_ON_ETSY else SHOP
    amz = f'<br><a href="https://www.amazon.com/dp/{SUDOKU_ASIN[v]}">Paperback on Amazon</a>' if v in SUDOKU_ASIN else ""
    return (f'<div class="card"><a href="{href}"><img src="{up}img/cover-sudoku-{v}.jpg" alt="Large Print Sudoku for Seniors volume {v}, {lv}" '
            f'loading="lazy" width="340" height="440"></a><h3>Volume {v}: {lv}</h3><p>100 puzzles · <a href="{href}">Printable PDF</a>{amz}</p></div>')

def ws_book(k, up):
    b = books[k]; slug = SEO[k][0]
    amz = f' · <a href="https://www.amazon.com/dp/{b["asin"]}">Paperback</a>' if b.get("asin") else ""
    return (f'<div class="card"><a href="{up}free/{slug}/"><img src="{up}img/cover-{k}.jpg" alt="Large Print Word Search for Seniors: {html.escape(b["name"])}" '
            f'loading="lazy" width="340" height="440"></a><h3>{html.escape(b["name"])}</h3>'
            f'<p><a href="{up}free/{slug}/">Free puzzle</a> · <a href="{SHOP}/listing/{b["listing"]}">Printable PDF</a>{amz}</p></div>')

# ---------- word search hub ----------
url = f"{BASE}/word-search/"; urls.append(url)
sections = ""
for k in ORDER:
    b = books[k]; mine = [x for x in ws_extras if x["book"] == k]
    amz = f'<a class="btn alt" href="https://www.amazon.com/dp/{b["asin"]}">Paperback on Amazon</a>' if b.get("asin") else ""
    sections += (f'<h2 id="{k}">{html.escape(b["name"])}</h2><div class="grid">{card(k, "../")}{"".join(xcard(x, "../") for x in mine)}</div>'
                 f'<p><a class="btn alt" href="{SHOP}/listing/{b["listing"]}">All 50 puzzles (printable PDF)</a>{amz}</p>')
body = f"""<h1>Free large-print word search printables</h1>
<p class="lead">7 themed books, 50 puzzles each, one puzzle per page with extra-large letters. Print three free from every book.</p>
<p class="jump">{" · ".join(f'<a href="#{k}">{html.escape(books[k]["name"])}</a>' for k in ORDER)}</p>
{sections}{signup("../")}"""
write("word-search/index.html", page("word-search/", "Free Large Print Word Search Printables for Seniors (21 Free PDFs)",
      "21 free printable large-print word searches for seniors from 7 themed books: Christmas, Winter, Bible, Hymns, 1950s, Garden, Cooking.", body, url))

# ---------- sudoku hub ----------
url = f"{BASE}/sudoku/"; urls.append(url)
body = f"""<h1>Large-print sudoku for seniors, Easy to Hard</h1>
<p class="lead">7 books of 100 puzzles each: one puzzle per page, extra-large bold numbers, thick box lines, every solution in the back.
Each puzzle has exactly one answer, and its level is checked by a logic solver.</p>
<h2>Try one free</h2><div class="grid">{"".join(xcard(x, "../") for x in sd_extras)}</div>
<h2>The series</h2><div class="grid">{"".join(sd_card(v, lv, lid, "../") for v, lv, lid in SUDOKU)}</div>
<div class="box"><b>Which level?</b> Easy: every square can be found by simple logic, great for beginners. Medium: a few more logic steps,
never guessing. Hard: for experienced solvers. Volumes 3 and 6 move from one level to the next.</div>
{signup("../")}"""
write("sudoku/index.html", page("sudoku/", "Large Print Sudoku for Seniors: Free Printables, Easy to Hard",
      "Free printable large-print sudoku for seniors (easy, medium and hard) and 7 books of 100 big-number puzzles each.", body, url))

# ---------- activity directors ----------
url = f"{BASE}/activity-directors/"; urls.append(url)
body = f"""<h1>Large-print puzzles for activity directors</h1>
<p class="lead">Word searches and sudoku your residents can actually see: one puzzle per page, big bold letters and numbers, every answer in the back.</p>
<h2>Word search: the Activity Director Pack</h2>
<p>350 word searches across 7 themes, with a license to print for your whole facility. One purchase, no subscription.</p>
<p><a class="btn" href="{SHOP}/listing/{PACK}">See the Activity Director Pack ($19.99)</a><a class="btn alt" href="{SHOP}/listing/{SAMPLER}">Try the 10-puzzle sampler</a></p>
<div class="box"><b>Facility license:</b> print unlimited copies for the residents, participants or members of one facility, program or location
(senior living, memory care, adult day, church group, classroom).</div>
<div class="grid">{"".join(ws_book(k, "../") for k in ORDER)}</div>
<h2>Sudoku for your number lovers</h2>
<p>7 books of 100 large-print sudoku, from Easy to Hard, so every resident finds the right level. Each printable PDF can be printed as many times as your group needs.</p>
<p><a class="btn alt" href="../sudoku/">See the sudoku books and free samples</a></p>
<div class="grid">{"".join(xcard(x, "../") for x in sd_extras[:3])}</div>
<h2>Why residents can finish them</h2><ul>
<li>One puzzle per page: 21 pt bold grid letters, 38 pt sudoku numbers</li><li>Word search words only read forward, down or diagonally. Nothing backwards</li>
<li>Every puzzle checked by computer, and every answer is in the back</li>
<li>Themes people talk about: Christmas, Winter, Bible, Hymns, 1950s & 60s Memories, Garden, Cooking & Baking</li></ul>
{signup("../")}"""
write("activity-directors/index.html", page("activity-directors/", "Large Print Word Search and Sudoku for Activity Directors | Facility License",
      "Large-print word search and sudoku puzzles for senior living, memory care and adult day programs, with free samples and a facility print license.", body, url))

# ---------- home ----------
live = [k for k in ORDER if books[k].get("asin")]
paperbacks = ("<h2>Paperbacks on Amazon</h2><p>Prefer a real book? Printed paperbacks, 8.5 x 11 in. A good gift.</p><p>"
              + "".join(f'<a class="btn alt" href="https://www.amazon.com/dp/{books[k]["asin"]}">{html.escape(books[k]["name"])}</a>' for k in live)
              + "</p>") if live else ""
body = f"""<h1>Free large-print puzzles for seniors</h1>
<p class="lead">Big, clear word searches and sudoku that are easy to see and always right. Print free samples, then get the full books on Etsy or Amazon.</p>
<div class="series">
<a class="tile" href="word-search/"><img src="img/cover-christmas.jpg" alt="Large print word search books" width="340" height="440">
<span><b>Word Search</b>7 themed books, 50 puzzles each<br>21 free printables<em>Browse word searches →</em></span></a>
<a class="tile" href="sudoku/"><img src="img/cover-sudoku-1.jpg" alt="Large print sudoku books" width="340" height="440">
<span><b>Sudoku</b>7 books, Easy to Hard, 100 puzzles each<br>6 free printables<em>Browse sudoku →</em></span></a>
</div>
{signup("")}
<h2>This week: Thanksgiving</h2><div class="grid">{"".join(xcard(x, "") for x in seasonal)}</div>
<h2>Free word searches</h2><div class="grid">{"".join(card(o, "") for o in ORDER[:6])}</div>
<p><a class="btn alt" href="word-search/">See all 21 free word searches</a></p>
<h2>Free sudoku</h2><div class="grid">{"".join(xcard(x, "") for x in sd_extras[:3])}</div>
<p><a class="btn alt" href="sudoku/">See the sudoku series</a></p>
{paperbacks}<h2>For activity directors</h2><p>Facility print license, word search and sudoku: <a href="activity-directors/">see the activity director page</a>.</p>
<h2>What makes them different</h2><ul><li>One puzzle per page with extra-large bold letters and numbers</li><li>Word search words read forward, down or diagonally, never backwards</li>
<li>A computer checks every puzzle, and every answer is in the back</li></ul>"""
write("index.html", page("", "Free Large Print Word Search and Sudoku Printables for Seniors | Big Clear Puzzle Books",
      "Free printable large-print word searches and sudoku for seniors, memory care and activity directors, plus a free monthly activity pack.", body, BASE + "/"))

write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
      "".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
write(".nojekyll", "")
print("pages:", len(urls))
