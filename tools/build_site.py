"""Build the static site for Big Clear Puzzle Books (Cloudflare Pages, repo root).

Usage: python3 tools/build_site.py
Reads tools/books.json (one free puzzle per book), tools/extras.json (more free puzzles, seasonal, sudoku) and
tools/wordlists.json (word list for every free word search, copied from the factory themes) and writes every page,
404.html, _headers, sitemap.xml and robots.txt. Standard library only (share images use Pillow when present).
To add a free printable: put the PDF in downloads/, a preview JPG in img/, add an entry to books.json or extras.json
(and its words to wordlists.json for a word search), rebuild.

SEO rules (audit 2026-11-22, ventures repo puzzle-books/marketing/seo-audit-2026-11-22.md):
- root-relative links ("/free/..."), one canonical per page, per-page og:image, og:type article/website (Pinterest rich pins)
- JSON-LD: site graph (Organization, WebSite, Person Callan Brooks, BookSeries) + page graph (breadcrumbs, document, FAQ)
- every free page carries unique text: the real word list, puzzle facts, a use tip and an FAQ
- Pinterest: pinit.js Save button on hover; each free page gets a 1000x1500 (2:3) share image img/share/<slug>.jpg
  (tools/share_images.py, run at the end like pdf_meta.py) used as og:image and as the Pin image
- sitemap.xml lists each page's images (Google image sitemap)
- no health claims (voice.md): "easy to see", never "good for dementia" or "brain health"
"""
import json, os, re, datetime, html, subprocess, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://bigclearpuzzlebooks.com"
SHOP = "https://bigclearpuzzlebooks.etsy.com"           # Share & Save format
AMAZON_SERIES = "https://www.amazon.com/dp/B0HRDKM5VV"                  # Amazon series page "Big Clear Puzzle Books" (all paperbacks)
AMAZON_AUTHOR = "https://www.amazon.com/Callan-Brooks/e/B0HRK5K7FT"      # Callan Brooks author page
PACK = 4615304644                                         # Activity Director Pack listing
BUNDLES = {"christmas": 4615214324, "winter": 4615214324, "bible": 4615214518, "hymns": 4615214518}
SAMPLER = 4615223623
books = json.load(open(os.path.join(ROOT, "tools", "books.json")))
extras = json.load(open(os.path.join(ROOT, "tools", "extras.json")))
WORDS = json.load(open(os.path.join(ROOT, "tools", "wordlists.json")))
# Word lists for new word-search pages are filled in automatically from the factory themes when the ventures repo is
# cloned next to this one (../ventures/research/tools/puzzle-books/themes). Without it, a page just skips its word list.
THEMES_DIR = os.path.join(os.path.dirname(ROOT), "ventures", "research", "tools", "puzzle-books", "themes")
THEME_FILE = {"garden": "garden", "bible": "bible", "nostalgia": "nostalgia-50s-60s", "christmas": "christmas", "winter": "winter",
              "cooking": "cooking-baking", "hymns": "hymns"}


def fill_words():
    need = [(k, b["puzzle_title"][3:], k) for k, b in books.items() if k not in WORDS]
    need += [(x["key"], x["puzzle_title"], x.get("theme") or ("thanksgiving-free" if x.get("seasonal") else x["book"]))
             for x in extras if not x.get("sudoku") and x["key"] not in WORDS]
    added = 0
    for key, title, th in need:
        f = os.path.join(THEMES_DIR, THEME_FILE.get(th, th) + ".json")
        if not os.path.exists(f):
            print("no word list (theme file not found):", key); continue
        for t, w in json.load(open(f))["puzzles"]:
            if t.lower() == title.lower():
                WORDS[key] = w; added += 1; break
        else:
            print("no word list (puzzle not in theme):", key)
    if added:
        json.dump(WORDS, open(os.path.join(ROOT, "tools", "wordlists.json"), "w"), indent=1)
        print("word lists added:", added)


fill_words()
ISBN = {"nostalgia": "9798143472990", "christmas": "9798143474529", "winter": "9798145110173", "hymns": "9798145111453"}
TODAY = datetime.date.today().isoformat()
E = html.escape

# ---------- names ----------
EE_LISTING = 4623874467    # Etsy listing for Extra Easy vol. 1 (published by Brad 2026-11-23)
TITLE_NAME = {"extra": "Extra Easy", "christmas": "Christmas", "winter": "Winter", "bible": "Bible", "hymns": "Hymn", "nostalgia": "1950s & 60s",
              "garden": "Garden", "cooking": "Cooking", "thanksgiving": "Thanksgiving", "fall": "Fall Harvest"}
TEXT_NAME = {"extra": "extra easy", "christmas": "Christmas", "winter": "winter", "bible": "Bible", "hymns": "hymn", "nostalgia": "1950s and 60s",
             "garden": "garden", "cooking": "cooking", "thanksgiving": "Thanksgiving", "fall": "fall harvest"}
USE_TIP = {
    "christmas": "Print a stack for a holiday party, a December activity hour or a card to tuck in with a gift for Grandma.",
    "winter": "A good snow-day or January activity: quiet, cozy and easy to share at a table.",
    "bible": "Use it to open a Bible study, in Sunday school or at a church senior lunch. Ask which story each word comes from.",
    "hymns": "Hand it out before a hymn sing; when everyone finishes, sing the hymn together.",
    "nostalgia": "A reminiscence activity: after the puzzle, ask who remembers each word. The stories are the best part.",
    "garden": "Pair it with a seed catalog or a vase of flowers and talk about favorite gardens.",
    "cooking": "Ask each person to share a family recipe that uses one of the words.",
    "thanksgiving": "Print a few for the kids' and grandparents' table while the turkey rests.",
    "fall": "A cozy autumn activity for a senior center, memory care group or the family table.",
}
SEO = {  # slug, title tag, h1, lead, meta description (title tags ~60 chars, metas 140-160)
    "christmas": ("christmas-word-search-for-seniors", "Free Large Print Christmas Word Search for Seniors & Adults (PDF)",
                  "Free large-print Christmas word search for seniors and adults",
                  "A big, easy-to-read Christmas puzzle for grandparents, memory care groups and holiday parties.",
                  "Free printable Christmas word search in extra-large 21 pt letters, one puzzle per page, with the answer key. Easy to read for seniors and memory care groups."),
    "winter": ("winter-word-search-for-seniors", "Free Large Print Winter Word Search for Seniors & Adults (PDF)",
               "Free large-print winter word search for seniors and adults", "A cozy snow-day puzzle in extra-large letters, ready to print.",
               "Free printable winter word search in extra-large 21 pt letters, one puzzle per page, with the answer key. A cozy January activity for seniors and adults."),
    "bible": ("bible-word-search-large-print", "Free Large Print Bible Word Search for Adults & Seniors (PDF)",
              "Free large-print Bible word search for adults and seniors",
              "Words from Genesis in big, clear letters for Sunday school, church groups and seniors.",
              "Free printable Bible word search with words from Genesis in big 21 pt letters, one puzzle per page, answer key included. For church groups and seniors."),
    "hymns": ("hymn-word-search-large-print", "Free Large Print Hymn Word Search: Amazing Grace (PDF)",
              "Free large-print hymn word search: Amazing Grace",
              "Words from Amazing Grace in a big, clear word search for church groups and nursing homes.",
              "Free printable Amazing Grace hymn word search in extra-large 21 pt letters, one puzzle per page, answer key included. For church groups and seniors."),
    "nostalgia": ("1950s-word-search-for-seniors", "Free 1950s Word Search for Seniors: Large Print Reminiscence Activity",
                  "Free large-print 1950s word search for seniors",
                  "Soda fountain words that spark memories: a reminiscence activity for seniors and memory care.",
                  "A free large-print 1950s and 60s word search that sparks memories and conversation. 21 pt letters, one puzzle per page, answer key included. Printable PDF."),
    "garden": ("garden-word-search-for-seniors", "Free Large Print Garden Word Search for Seniors & Adults (PDF)",
               "Free large-print garden word search for seniors and adults", "Spring flowers in extra-large print: one puzzle per page with the solution.",
               "Free printable garden word search with spring flower words in extra-large 21 pt letters, one puzzle per page, answer key included. For seniors and adults."),
    "cooking": ("cooking-word-search-for-seniors", "Free Large Print Cooking Word Search for Seniors & Adults (PDF)",
                "Free large-print cooking word search for seniors and adults", "Kitchen words in a big, clear word search for seniors and bakers.",
                "Free printable cooking word search with kitchen words in extra-large 21 pt letters, one puzzle per page, answer key included. For seniors and bakers."),
}
ORDER = ["christmas", "winter", "bible", "hymns", "nostalgia", "garden", "cooking"]
SUDOKU_SEO = {  # key: title tag, h1, meta (each level page aims at a different search)
    "sudoku-1": ("Free Large Print Easy Sudoku for Seniors, Puzzle 1 (PDF)", "Free large-print easy sudoku for seniors",
                 "Free printable easy sudoku with big bold numbers and thick box lines, one puzzle per page, answer key included. Solvable by simple logic, no guessing."),
    "sudoku-easy-2": ("Easy Sudoku Printable for Adults, Large Print (Free PDF #2)", "Easy sudoku printable for adults: large print #2",
                      "A second free easy sudoku for adults and seniors: extra-large numbers, thick box lines, one puzzle per page and the answer key on page 2."),
    "sudoku-medium": ("Medium Sudoku Printable, Large Print for Seniors (Free PDF)", "Free large-print medium sudoku",
                      "Free printable medium sudoku in large print: a few more logic steps than easy, never guessing. Big numbers, one per page, answer key included."),
    "sudoku-medium-2": ("Medium Sudoku Large Print #2: Free Printable with Answers", "Medium sudoku large print #2",
                        "Another free medium sudoku with extra-large numbers and thick box lines. One puzzle per page, exactly one solution, answer key on page 2."),
    "sudoku-hard": ("Hard Sudoku Printable, Large Print for Adults (Free PDF)", "Free large-print hard sudoku",
                    "Free printable hard sudoku in large print for experienced solvers: big bold numbers, one puzzle per page, exactly one solution, answer key included."),
    "sudoku-hard-2": ("Hard Sudoku Large Print #2: Free Printable with Answers", "Hard sudoku large print #2",
                      "A second free hard sudoku with extra-large numbers for experienced solvers. One puzzle per page, exactly one solution, answer key on page 2."),
}
EXTRA_TITLE = {  # title-tag overrides where the pattern runs long or repeats itself
    "thanksgiving-1": "Free Large Print Thanksgiving Word Search for Seniors (PDF)",
    "thanksgiving-3": "Free Large Print Fall Harvest Word Search for Seniors (PDF)",
    "nostalgia-3": "Drive-In Movie Night Word Search, Large Print 1950s (Free PDF)",
}
LEVEL = {"sudoku-1": "Easy", "sudoku-easy-2": "Easy", "sudoku-medium": "Medium", "sudoku-medium-2": "Medium", "sudoku-hard": "Hard", "sudoku-hard-2": "Hard"}
for _x in extras:   # newer sudoku pages (growth builder) carry "level" in extras.json; title/h1/meta follow a pattern
    if _x.get("sudoku") and _x["key"] not in LEVEL:
        _lv = _x["level"]; _n = _x["puzzle_title"].split()[-1]; LEVEL[_x["key"]] = _lv
        SUDOKU_SEO[_x["key"]] = (f"{_lv} Sudoku Large Print #{_n}: Free Printable with Answers", f"{_lv} sudoku large print #{_n}",
                                 f"Free printable {_lv.lower()} sudoku #{_n} in large print: extra-large bold numbers, thick box lines, one puzzle per page, exactly one solution, answer key on page 2.")

PIN_SCRIPT = '<script async defer src="https://assets.pinterest.com/js/pinit.js" data-pin-hover="true" data-pin-tall="true" data-pin-round="true"></script>'
HAVE_PIL = importlib.util.find_spec("PIL") is not None
SHARE = []      # share images to render: {out, src, pdf, title, sudoku}
IMGS = {}       # page URL -> [(img src, alt)] for the image sitemap
ML_SCRIPT = """<script>(function(w,d,e,u,f,l,n){w[f]=w[f]||function(){(w[f].q=w[f].q||[]).push(arguments);},l=d.createElement(e),l.async=1,l.src=u,n=d.getElementsByTagName(e)[0],n.parentNode.insertBefore(l,n);})(window,document,'script','https://assets.mailerlite.com/js/universal.js','ml');ml('account','2817294');</script>"""
CSS = """*{box-sizing:border-box}body{margin:0;font-family:Verdana,Geneva,'DejaVu Sans',sans-serif;font-size:20px;line-height:1.6;color:#1b1b1b;background:#faf7f0}
a{color:#1f3a5f}header{background:#1f3a5f;color:#fff}header .w{display:flex;flex-wrap:wrap;align-items:center;gap:10px 16px;padding:14px 20px}
header img{width:56px;height:56px;border-radius:50%;background:#fff}header a{color:#fff;text-decoration:none;font-weight:bold;font-size:24px}
nav{display:flex;flex-wrap:wrap;gap:4px 18px}nav a{color:#fff;font-size:18px}.w{max-width:1040px;margin:0 auto;padding:0 20px}
h1{font-size:40px;line-height:1.2;margin:20px 0 12px;color:#1f3a5f}h2{font-size:30px;color:#1f3a5f;margin-top:44px}
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
.crumbs{font-size:16px;margin:18px 0 0}.crumbs a{color:#1f3a5f}.words{columns:3 170px;list-style:none;padding:0;font-size:22px;font-weight:bold;letter-spacing:.5px}
.facts{font-size:18px;color:#444}.faq h3{font-size:22px;margin:22px 0 4px;color:#1f3a5f}.faq p{margin:0 0 8px}
table{border-collapse:collapse;width:100%;background:#fff;margin:18px 0}td,th{border:1px solid #ccc;padding:10px 12px;text-align:left;vertical-align:top}th{background:#eef2f7}
@media(max-width:760px){.two,.series{grid-template-columns:1fr}h1{font-size:32px}nav a{font-size:16px}.tile img{width:110px}}"""

SITE_LD = {"@context": "https://schema.org", "@graph": [
    {"@type": "Organization", "@id": f"{BASE}/#org", "name": "Big Clear Puzzle Books", "url": f"{BASE}/",
     "logo": f"{BASE}/img/icon.png", "email": "hello@bigclearpuzzlebooks.com",
     "sameAs": [SHOP, "https://www.pinterest.com/bigclearpuzzlebooks/"]},
    {"@type": "WebSite", "@id": f"{BASE}/#site", "url": f"{BASE}/", "name": "Big Clear Puzzle Books", "publisher": {"@id": f"{BASE}/#org"}},
    {"@type": "Person", "@id": f"{BASE}/#callan-brooks", "name": "Callan Brooks", "url": AMAZON_AUTHOR, "sameAs": [AMAZON_AUTHOR], "worksFor": {"@id": f"{BASE}/#org"}},
    {"@type": "BookSeries", "@id": f"{BASE}/#series", "name": "Big Clear Puzzle Books", "url": AMAZON_SERIES,
     "author": {"@id": f"{BASE}/#callan-brooks"}, "publisher": {"@id": f"{BASE}/#org"}}]}


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, separators=(",", ":")).replace("</", "<\\/") + "</script>"


def crumbs_ld(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        dict({"@type": "ListItem", "position": i, "name": n}, **({"item": BASE + u} if u else {})) for i, (n, u) in enumerate(items, 1)]}


def crumbs_html(items):
    return '<p class="crumbs">' + " › ".join(f'<a href="{u}">{E(n)}</a>' if u else E(n) for n, u in items) + "</p>"


def page(path, title, desc, body, image="/img/christmas-preview.jpg", img_wh=(765, 990), img_alt="Large print puzzle page",
         og_type="article", graph=None, crumbs=None, noindex=False):
    canonical = BASE + "/" + path
    pin_attr = ""
    if path.startswith("free/") and image.endswith("-preview.jpg") and not noindex:   # free printable: 2:3 share image for Pinterest/og
        slug = path.strip("/").split("/")[-1]; share = f"/img/share/{slug}.jpg"
        if os.path.exists(ROOT + share) or HAVE_PIL:
            m = re.search(r"<h1>(.*?)</h1>", body, re.S); pdf = re.search(r'/downloads/([^"#?]+\.pdf)', body)
            h1 = html.unescape(re.sub("<[^>]+>", "", m.group(1))) if m else title
            SHARE.append({"out": share.lstrip("/"), "src": image.lstrip("/"), "pdf": ("downloads/" + pdf.group(1)) if pdf else "", "title": h1,
                          "sudoku": "sudoku" in path})
            pin_attr = f' data-pin-media="{BASE}{share}" data-pin-description="{E(h1)}. Printable PDF with answer key from Big Clear Puzzle Books."'
            body = body.replace(f'<img src="{image}"', f'<img src="{image}"{pin_attr}', 1)
            image, img_wh = share, (1000, 1500)
    nodes = list(graph or []) + ([crumbs_ld(crumbs)] if crumbs else [])
    page_ld = ld({"@context": "https://schema.org", "@graph": nodes}) if nodes else ""
    robots = '<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="{canonical}">'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
{robots}<link rel="icon" href="/img/favicon.png"><link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Big Clear Puzzle Books">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}{image}"><meta property="og:image:width" content="{img_wh[0]}"><meta property="og:image:height" content="{img_wh[1]}"><meta property="og:image:alt" content="{E(img_alt)}">
<meta name="twitter:card" content="summary_large_image"><meta name="p:domain_verify" content="5f2e6b6f365deaad7f1cde96575db747"/>
{ld(SITE_LD)}{page_ld}{ML_SCRIPT}{PIN_SCRIPT}<style>{CSS}</style></head><body>
<header><div class="w"><img src="/img/icon.png" alt="" data-pin-nopin="true"><a href="/">Big Clear Puzzle Books</a>
<nav><a href="/word-search/">Word Search</a><a href="/sudoku/">Sudoku</a><a href="/#signup">Free monthly pack</a><a href="/books/">Books</a><a href="/activity-directors/">Activity directors</a><a href="{SHOP}">Shop</a></nav></div></header>
<main class="w">{crumbs_html(crumbs) if crumbs else ""}{body}</main>
<footer><div class="w">Big Clear Puzzle Books · Large-print word searches and sudoku that are easy to see and always right.
· <a href="{SHOP}">Etsy shop</a> · <a href="{AMAZON_AUTHOR}">Paperbacks by Callan Brooks on Amazon</a> · <a href="https://www.pinterest.com/bigclearpuzzlebooks/">Pinterest</a> · <a href="mailto:hello@bigclearpuzzlebooks.com">hello@bigclearpuzzlebooks.com</a><br>
Guides: <a href="/books/">All our books</a> · <a href="/dementia-friendly-printables/">Dementia-friendly printables</a> · <a href="/large-print-font-size/">What font size is large print?</a> · <a href="/activity-directors/">For activity directors</a><br>
Free printables are for personal, family, classroom and activity-group use. Please share the link, not the file.</div></footer>
</body></html>"""


def write(rel, text):
    if rel.endswith("index.html") and 'name="robots" content="noindex"' not in text:
        u = BASE + "/" + rel[:-len("index.html")]
        IMGS[u] = list(dict.fromkeys((src, html.unescape(alt)) for src, alt in re.findall(r'<img src="(/img/[^"]+)" alt="([^"]*)"', text) if alt))
    p = os.path.join(ROOT, rel); os.makedirs(os.path.dirname(p) or ROOT, exist_ok=True); open(p, "w").write(text)


ML_FORM = "75aY4B"       # MailerLite embedded form "Website - Monthly Activity Pack" (account 2817294, group Monthly Activity Pack)
def signup(up=""):
    return f"""<div class="signup" id="signup"><h2>Get a free puzzle pack every month</h2>
<p>December's pack is ready: 5 holiday word searches and 3 sudoku in large print, with solutions. Sign up and it arrives by email in a few minutes.</p>
<div class="ml-embedded" data-form="{ML_FORM}"></div>
<p class="small">For seniors, families and activity directors. We never share your email, and you can unsubscribe anytime.</p></div>"""


# ---------- shared page parts ----------
def faq_ws(words_n):
    qa = [("Is this large-print word search really free?",
           "Yes. Download the PDF and print as many copies as you need for your family, class or activity group. Please share the link rather than the file."),
          ("How big is the print?",
           "Grid letters are 21 point bold and the word list is 18 point, one puzzle on a US Letter page (it prints on A4 too)."),
          ("Is there an answer key?",
           f"Yes. The solution is on page 2, and a computer checked that all {words_n} words appear exactly once."),
          ("Can I copy it for residents in senior living or memory care?",
           "Yes, for your group. For a whole facility's activity calendar, the Activity Director Pack has 350 puzzles and a facility print license.")]
    return qa


def faq_sd(level):
    qa = [("Is this large-print sudoku really free?",
           "Yes. Download the PDF and print as many copies as you need for your family, class or activity group."),
          ("How big are the numbers?", "The numbers are extra-large and bold (38 point), with thick lines around each 3 x 3 box, one puzzle per page."),
          ("Is there an answer key?", "Yes, on page 2. A computer checked that the puzzle has exactly one solution."),
          (f"How hard is a {level.lower()} puzzle?",
           {"Easy": "Every square can be found with simple logic, so it suits beginners and relaxed solving. No guessing is ever needed.",
            "Medium": "It takes a few more logic steps than easy, but never guessing. A good next step after the easy puzzles.",
            "Hard": "It needs longer chains of logic and suits experienced solvers. It still has exactly one solution and never needs guessing."}[level])]
    return qa


def faq_block(qa):
    return ('<div class="faq"><h2>Questions</h2>' + "".join(f"<h3>{E(q)}</h3><p>{E(a)}</p>" for q, a in qa) + "</div>",
            {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]})


def words_block(words, extra_easy=False):
    if not words: return ""
    facts = ("10 x 10 grid · giant 34 pt letters · words read only across or down, never diagonal or backwards" if extra_easy
             else "14 x 14 grid · words read right, down or diagonally down-right, never backwards")
    return (f'<h2>Words to find</h2><ul class="words">{"".join(f"<li>☐ {E(w)}</li>" for w in sorted(words))}</ul>'
            f'<p class="facts">{len(words)} words · {facts}</p>')


def doc_ld(name, url, image, pdf, keywords, series=True):
    d = {"@type": "DigitalDocument", "name": name, "url": url, "image": BASE + image, "isAccessibleForFree": True, "inLanguage": "en",
         "audience": {"@type": "PeopleAudience", "audienceType": "Seniors, adults, memory care and activity groups"}, "keywords": keywords,
         "encoding": {"@type": "MediaObject", "contentUrl": f"{BASE}/downloads/{pdf}", "encodingFormat": "application/pdf"},
         "publisher": {"@id": f"{BASE}/#org"}}
    if series: d["isPartOf"] = {"@id": f"{BASE}/#series"}
    return d


urls = [BASE + "/"]; pdf_pages = []   # (pdf, page path) for _headers
def card(k, up="/"):
    b = books[k]; slug = SEO[k][0]
    return (f'<div class="card"><a href="/free/{slug}/"><img src="/img/{k}-preview.jpg" alt="Free large print {E(b["name"])} word search: {E(b["puzzle_title"][3:])}" '
            f'loading="lazy" width="765" height="990"></a><h3><a href="/free/{slug}/">{E(b["name"])}</a></h3>'
            f'<p>{E(b["puzzle_title"][3:])} · free PDF</p></div>')


def theme_of(x):
    if x.get("extra_easy"): return "extra"
    if x.get("seasonal"): return "fall" if "harvest" in x["slug"] else "thanksgiving"
    return x["book"]


def xalt(x):
    if x.get("sudoku"): return f"Large print {LEVEL[x['key']].lower()} sudoku puzzle with answer key"
    return f"Large print {TEXT_NAME[theme_of(x)]} word search \"{x['puzzle_title']}\" with answer key"


def xcard(x, up="/"):
    label = "Sudoku" if x.get("sudoku") else ("Extra Easy" if x.get("extra_easy") else ("Thanksgiving" if x.get("seasonal") else books[x["book"]]["name"]))
    return (f'<div class="card"><a href="/free/{x["slug"]}/"><img src="/img/{x["key"]}-preview.jpg" alt="{E(xalt(x))}" '
            f'loading="lazy" width="765" height="990"></a><h3><a href="/free/{x["slug"]}/">{E(x["puzzle_title"])}</a></h3>'
            f'<p>{label} · free PDF</p></div>')


ws_extras = [x for x in extras if not x.get("seasonal") and not x.get("sudoku") and not x.get("extra_easy")]
ee_extras = [x for x in extras if x.get("extra_easy")]
sd_extras = [x for x in extras if x.get("sudoku")]
seasonal = [x for x in extras if x.get("seasonal")]
WS_N = len(ORDER) + len(ws_extras) + len(ee_extras)        # free word search pages (seasonal pages not counted)

# ---------- base free pages (puzzle 1 of each book) ----------
for k in ORDER:
    b = books[k]; slug, title, h1, intro, meta = SEO[k]; path = f"free/{slug}/"; url = BASE + "/" + path; urls.append(url)
    pdf_pages.append((b["pdf"], path)); words = WORDS.get(k, []); puzzle = b["puzzle_title"][3:]
    bundle = BUNDLES.get(k)
    extra = f'<a class="btn alt" href="{SHOP}/listing/{bundle}">2-book bundle (100 puzzles)</a>' if bundle else ""
    if b.get("asin"):   # paperback link only once Live on Amazon: add "asin" to tools/books.json
        extra += f'<a class="btn alt" href="https://www.amazon.com/dp/{b["asin"]}">Paperback on Amazon</a>'
    qa = faq_ws(len(words) or "the"); faq_html, faq_ld = faq_block(qa)
    mine = [x for x in ws_extras if x["book"] == k]
    body = f"""<h1>{E(h1)}</h1><p class="lead">{E(intro)}</p>
<div class="two"><div><img src="/img/{k}-preview.jpg" alt="Large print {E(TEXT_NAME[k])} word search “{E(puzzle)}” with answer key" width="765" height="990"></div>
<div><p><a class="btn" href="/downloads/{b['pdf']}" download>Download the free PDF</a></p>
<ul><li>US Letter (8.5 x 11 in), prints on A4 too</li><li>Extra-large letters: 21 pt bold grid, 18 pt word list</li>
<li>Words read forward, down or diagonally. Nothing backwards</li><li>Answer key on page 2</li><li>Checked by computer: every word is there exactly once</li></ul>
<div class="box"><b>Want more?</b> This puzzle comes from the full <b>{E(b['name'])}</b> book: 50 large-print puzzles, one per page, with every solution.
<br><a class="btn alt" href="{SHOP}/listing/{b['listing']}">Get all 50 puzzles (printable PDF)</a>{extra}</div>
<p>Running activities for a whole community? The <a href="/activity-directors/">Activity Director Pack</a> has all 7 books (350 puzzles) with a facility license.</p>
</div></div>
<h2>{E(puzzle)}: puzzle 1 of the {E(b['name'])} book</h2>{words_block(words)}<p>{E(USE_TIP[k])}</p>
{faq_html}
<h2>More {E(b['name'])} puzzles, free</h2><div class="grid">{''.join(xcard(x) for x in mine)}</div>
{signup()}<h2>More free large-print word searches</h2><div class="grid">{''.join(card(o) for o in ORDER if o != k)}</div>"""
    crumbs = [("Home", "/"), ("Word Search", "/word-search/"), (b["name"], None)]
    graph = [doc_ld(f"{puzzle}: free large-print {TEXT_NAME[k]} word search", url, f"/img/{k}-preview.jpg", b["pdf"],
                    f"large print word search, {TEXT_NAME[k]} word search for seniors, printable, answer key"), faq_ld]
    write(path + "index.html", page(path, title, meta, body, image=f"/img/{k}-preview.jpg",
                                     img_alt=f"Large print {TEXT_NAME[k]} word search page", graph=graph, crumbs=crumbs))

# ---------- extra free pages: more puzzles per book, seasonal, sudoku ----------
for x in extras:
    path = f"free/{x['slug']}/"; url = BASE + "/" + path; urls.append(url); k = x["book"]; pdf_pages.append((x["pdf"], path))
    if x.get("sudoku"):
        lv = LEVEL[x["key"]]; title, h1, meta = SUDOKU_SEO[x["key"]]
        more = (f'<div class="box"><b>Want more?</b> Each <b>Large Print Sudoku for Seniors</b> book has 100 puzzles like this one, one per page, '
                f'with every solution. The series has 7 volumes, from Easy to Hard.<br><a class="btn alt" href="/sudoku/#series">See the 7 sudoku books</a></div>')
        bullets = "<li>US Letter (8.5 x 11 in), prints on A4 too</li><li>Extra-large bold numbers, thick 3 x 3 box lines</li><li>Difficulty checked by a logic solver</li><li>Answer key on page 2</li><li>Checked by computer: exactly one answer</li>"
        detail = (f'<h2>About this puzzle</h2><p class="facts">9 x 9 sudoku · {lv} level · exactly one solution · solvable by logic, never guessing</p>'
                  f'<p>Fill every row, column and 3 x 3 box with the numbers 1 to 9. {"Start with a row or box that is almost full." if lv == "Easy" else "Look for the square with the fewest possible numbers, then work outward."}</p>')
        qa = faq_sd(lv); sib = [y for y in sd_extras if y is not x]
        grid = "".join(xcard(y) for y in sib)
        crumbs = [("Home", "/"), ("Sudoku", "/sudoku/"), (x["puzzle_title"], None)]
        doc = doc_ld(h1[0].upper() + h1[1:], url, f"/img/{x['key']}-preview.jpg", x["pdf"], f"large print sudoku, {lv.lower()} sudoku printable, sudoku for seniors, answer key", series=False)
        more_title = "More free large-print sudoku"
    elif x.get("extra_easy"):
        words = WORDS.get(x["key"], []); p = x["puzzle_title"]
        title = f"Extra Easy Large Print Word Search: {p} (Free PDF)"
        h1 = f"{p}: free extra easy large-print word search"
        meta = f'Free extra easy "{p}" word search with giant 34 pt letters: a 10 x 10 grid, {len(words) or 7} short words, across or down only, answer key included.'
        href = f"{SHOP}/listing/{EE_LISTING}" if EE_LISTING else SHOP
        more = (f'<div class="box"><b>Want more?</b> The <b>Extra Easy</b> book has 50 puzzles like this one, giant letters, one per page, with every answer.'
                f'<br><a class="btn alt" href="{href}">Get all 50 Extra Easy puzzles (printable PDF)</a></div>')
        bullets = "<li>US Letter (8.5 x 11 in), prints on A4 too</li><li>Giant letters: 34 pt bold grid, 26 pt word list</li><li>Small 10 x 10 grid with 6 to 8 short words</li><li>Words read only across or down. Never diagonal, never backwards</li><li>Answer key on page 2</li>"
        detail = words_block(words, extra_easy=True) + "<p>Good for anyone who finds regular word searches too busy: memory care groups, low vision, or a gentle start. See our guide to <a href=\"/dementia-friendly-printables/\">dementia-friendly printables</a>.</p>"
        qa = faq_ws(len(words) or "the"); qa[1] = ("How big is the print?", "Grid letters are 34 point bold and the word list is 26 point, on a small 10 x 10 grid, one puzzle per US Letter page.")
        sib = [y for y in ee_extras if y is not x]
        grid = "".join(xcard(y) for y in sib) + "".join(card(o) for o in ["nostalgia", "hymns", "christmas"])
        crumbs = [("Home", "/"), ("Word Search", "/word-search/"), ("Extra Easy", "/word-search/#extra-easy"), (p, None)]
        doc = doc_ld(h1[0].upper() + h1[1:], url, f"/img/{x['key']}-preview.jpg", x["pdf"], "extra easy word search, giant print word search, large print, seniors, memory care, answer key", series=False)
        more_title = "More free large-print puzzles"
    else:
        th = theme_of(x); T, t = TITLE_NAME[th], TEXT_NAME[th]; words = WORDS.get(x["key"], []); p = x["puzzle_title"]
        title = EXTRA_TITLE.get(x["key"], f"{p} Word Search, Large Print {T} (Free PDF)")
        h1 = f"{p}: free large-print {t} word search"
        meta = f'Free "{p}" {t} word search in big 21 pt letters: {len(words) or 10} words, one page, answer key included. For seniors, adults and memory care groups.'
        b = books[k]; lead = ("Get ready for Christmas next: the full <b>Christmas</b> book has 50 large-print puzzles, one per page, with every solution."
                              if x.get("seasonal") else f"This puzzle comes from the full <b>{E(b['name'])}</b> book: 50 large-print puzzles, one per page, with every solution.")
        more = f'<div class="box"><b>Want more?</b> {lead}<br><a class="btn alt" href="{SHOP}/listing/{b["listing"]}">Get all 50 puzzles (printable PDF)</a>'
        if b.get("asin"): more += f'<a class="btn alt" href="https://www.amazon.com/dp/{b["asin"]}">Paperback on Amazon</a>'
        more += "</div>"
        bullets = "<li>US Letter (8.5 x 11 in), prints on A4 too</li><li>Extra-large letters: 21 pt bold grid, 18 pt word list</li><li>Words read forward, down or diagonally. Nothing backwards</li><li>Answer key on page 2</li><li>Checked by computer: every word is there exactly once</li>"
        detail = words_block(words) + f"<p>{E(USE_TIP[th])}</p>"
        qa = faq_ws(len(words) or "the")
        sib = [y for y in extras if y is not x and not y.get("sudoku") and ((x.get("seasonal") and y.get("seasonal")) or (not x.get("seasonal") and not y.get("seasonal") and y["book"] == k))]
        base = [] if x.get("seasonal") else [k]
        others = [o for o in ORDER if o not in base][:max(0, 6 - len(sib) - len(base))]
        grid = "".join(card(o) for o in base) + "".join(xcard(y) for y in sib) + "".join(card(o) for o in others)
        hub = ("Thanksgiving", "/#thanksgiving") if x.get("seasonal") else (b["name"], f"/word-search/#{k}")
        crumbs = [("Home", "/"), ("Word Search", "/word-search/"), hub, (p, None)]
        doc = doc_ld(h1, url, f"/img/{x['key']}-preview.jpg", x["pdf"], f"large print word search, {t} word search for seniors, printable, answer key")
        more_title = "More free large-print puzzles"
    faq_html, faq_ld = faq_block(qa)
    body = f"""<h1>{E(h1[0].upper() + h1[1:])}</h1><p class="lead">{E(x['intro'])}</p>
<div class="two"><div><img src="/img/{x['key']}-preview.jpg" alt="{E(xalt(x))}" width="765" height="990"></div>
<div><p><a class="btn" href="/downloads/{x['pdf']}" download>Download the free PDF</a></p><ul>{bullets}</ul>{more}
<p>Running activities for a whole community? The <a href="/activity-directors/">Activity Director Pack</a> has 350 word searches with a facility license.</p>
</div></div>{detail}{faq_html}{signup()}<h2>{more_title}</h2><div class="grid">{grid}</div>"""
    write(path + "index.html", page(path, title, meta, body, image=f"/img/{x['key']}-preview.jpg", img_alt=xalt(x),
                                     graph=[doc, faq_ld], crumbs=crumbs))

# ---------- shared blocks ----------
SUDOKU = [  # volume, level, Etsy listing (published by Brad), Amazon ASIN when Live
    (1, "Easy", 4623561048), (2, "Easy", 4623569642), (3, "Easy to Medium", 4623562913), (4, "Medium", 4623569840),
    (5, "Medium", 4623570864), (6, "Medium to Hard", 4623564155), (7, "Hard", 4623571180)]
SUDOKU_ASIN = {}          # volume -> ASIN once Live on Amazon
SUDOKU_ON_ETSY = True     # True once the 7 drafts are published; until then buttons go to the shop home


def sd_card(v, lv, lid, up="/"):
    href = f"{SHOP}/listing/{lid}" if SUDOKU_ON_ETSY else SHOP
    amz = f'<br><a href="https://www.amazon.com/dp/{SUDOKU_ASIN[v]}">Paperback on Amazon</a>' if v in SUDOKU_ASIN else ""
    return (f'<div class="card"><a href="{href}"><img src="/img/cover-sudoku-{v}.jpg" alt="Large Print Sudoku for Seniors volume {v}, {lv}" '
            f'loading="lazy" width="340" height="440"></a><h3>Volume {v}: {lv}</h3><p>100 puzzles · <a href="{href}">Printable PDF</a>{amz}</p></div>')


def ws_book(k, up="/"):
    b = books[k]; slug = SEO[k][0]
    amz = f' · <a href="https://www.amazon.com/dp/{b["asin"]}">Paperback</a>' if b.get("asin") else ""
    return (f'<div class="card"><a href="/free/{slug}/"><img src="/img/cover-{k}.jpg" alt="Large Print Word Search for Seniors: {E(b["name"])}" '
            f'loading="lazy" width="340" height="440"></a><h3>{E(b["name"])}</h3>'
            f'<p><a href="/free/{slug}/">Free puzzle</a> · <a href="{SHOP}/listing/{b["listing"]}">Printable PDF</a>{amz}</p></div>')


def book_ld(k):
    b = books[k]
    d = {"@type": "Book", "name": f"Large Print Word Search for Seniors: {b['name']}", "author": {"@id": f"{BASE}/#callan-brooks"},
         "isPartOf": {"@id": f"{BASE}/#series"}, "bookFormat": "https://schema.org/Paperback", "numberOfPages": 80, "inLanguage": "en",
         "image": f"{BASE}/img/cover-{k}.jpg",
         "offers": {"@type": "Offer", "price": "9.99", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": f"https://www.amazon.com/dp/{b['asin']}"}}
    if k in ISBN: d["isbn"] = ISBN[k]
    return d


def item_list(name, links):
    return {"@type": "ItemList", "name": name, "itemListElement": [{"@type": "ListItem", "position": i, "url": BASE + u} for i, u in enumerate(links, 1)]}


# ---------- word search hub ----------
path = "word-search/"; url = BASE + "/" + path; urls.append(url)
sections = ""
for k in ORDER:
    b = books[k]; mine = [x for x in ws_extras if x["book"] == k]
    amz = f'<a class="btn alt" href="https://www.amazon.com/dp/{b["asin"]}">Paperback on Amazon</a>' if b.get("asin") else ""
    sections += (f'<h2 id="{k}">{E(b["name"])}</h2><div class="grid">{card(k)}{"".join(xcard(x) for x in mine)}</div>'
                 f'<p><a class="btn alt" href="{SHOP}/listing/{b["listing"]}">All 50 puzzles (printable PDF)</a>{amz}</p>')
ws_links = [f"/free/{SEO[k][0]}/" for k in ORDER] + [f"/free/{x['slug']}/" for x in ws_extras]
hub_qa = [("Are these word searches really free?", "Yes. Each free page has a one-page PDF with the answer key. Print as many as you need for your family or group."),
          ("What makes them large print?", "Grid letters are 21 point bold and word lists are 18 point, one puzzle per page. Words never run backwards."),
          ("Who are they for?", "Seniors, adults who like a relaxing puzzle, memory care and assisted living groups, church groups and classrooms.")]
faq_html, faq_ld = faq_block(hub_qa)
if ee_extras:
    sections = (f'<h2 id="extra-easy">Extra Easy (giant print)</h2><p>Small 10 x 10 grids, 6 to 8 short words, giant 34 pt letters, and words that only read across or down.</p>'
                f'<div class="grid">{"".join(xcard(x) for x in ee_extras)}</div>') + sections
    ws_links += [f"/free/{x['slug']}/" for x in ee_extras]
body = f"""<h1>Free large-print word search printables for seniors and adults</h1>
<p class="lead">7 themed books, 50 puzzles each, one puzzle per page with extra-large letters. Print free puzzles from every book: {WS_N} free PDFs, each with the answer key.</p>
<p class="jump">{'<a href="#extra-easy">Extra Easy</a> · ' if ee_extras else ""}{" · ".join(f'<a href="#{k}">{E(books[k]["name"])}</a>' for k in ORDER)} · <a href="/#thanksgiving">Thanksgiving</a></p>
{sections}{faq_html}{signup()}"""
write(path + "index.html", page(path, "Free Large Print Word Search Printables for Seniors & Adults",
      f"Browse {WS_N} free large-print word searches: Christmas, winter, Bible, hymns, 1950s, garden and cooking. One puzzle per page, answer key included. Printable PDF.",
      body, image="/img/cover-christmas.jpg", img_wh=(340, 440), img_alt="Large print word search books", og_type="website",
      graph=[{"@type": "CollectionPage", "name": "Free large-print word search printables", "url": url},
             item_list("Free large-print word searches", ws_links)] + [book_ld(k) for k in ORDER if books[k].get("asin")] + [faq_ld],
      crumbs=[("Home", "/"), ("Word Search", None)]))

# ---------- sudoku hub ----------
path = "sudoku/"; url = BASE + "/" + path; urls.append(url)
_lvn = {lv: sum(1 for x in sd_extras if LEVEL[x["key"]] == lv) for lv in ("Easy", "Medium", "Hard")}
sd_qa = [("Is the large-print sudoku free?", f"Yes. {len(sd_extras)} free puzzles ({_lvn['Easy']} Easy, {_lvn['Medium']} Medium, {_lvn['Hard']} Hard), each a one-page PDF with the answer key."),
         ("How big are the numbers?", "Extra-large and bold (38 point), with thick lines around each 3 x 3 box, one puzzle per page."),
         ("Which level should I start with?", "Start with Easy: every square can be found with simple logic. Move to Medium when Easy feels quick. Hard is for experienced solvers.")]
faq_html, faq_ld = faq_block(sd_qa)
body = f"""<h1>Large-print sudoku for seniors, Easy to Hard</h1>
<p class="lead">7 books of 100 puzzles each: one puzzle per page, extra-large bold numbers, thick box lines, every solution in the back.
Each puzzle has exactly one answer, and its level is checked by a logic solver.</p>
<h2>Try one free</h2><div class="grid">{"".join(xcard(x) for x in sd_extras)}</div>
<h2 id="series">The series</h2><div class="grid">{"".join(sd_card(v, lv, lid) for v, lv, lid in SUDOKU)}</div>
<div class="box"><b>Which level?</b> Easy: every square can be found by simple logic, great for beginners. Medium: a few more logic steps,
never guessing. Hard: for experienced solvers. Volumes 3 and 6 move from one level to the next.</div>
{faq_html}{signup()}"""
write(path + "index.html", page(path, "Large Print Sudoku for Seniors: Free Printables, Easy to Hard",
      "Free printable large-print sudoku for seniors and adults: easy, medium and hard puzzles with big bold numbers, one per page, answer key included.",
      body, image="/img/cover-sudoku-1.jpg", img_wh=(340, 440), img_alt="Large print sudoku books", og_type="website",
      graph=[{"@type": "CollectionPage", "name": "Large-print sudoku for seniors", "url": url},
             item_list("Free large-print sudoku", [f"/free/{x['slug']}/" for x in sd_extras]), faq_ld],
      crumbs=[("Home", "/"), ("Sudoku", None)]))

# ---------- activity directors ----------
path = "activity-directors/"; url = BASE + "/" + path; urls.append(url)
body = f"""<h1>Large-print puzzles for memory care and activity directors</h1>
<p class="lead">Word searches and sudoku your residents can actually see: one puzzle per page, big bold letters and numbers, every answer in the back.</p>
<h2>Word search: the Activity Director Pack</h2>
<p>350 word searches across 7 themes, with a license to print for your whole facility. One purchase, no subscription.</p>
<p><a class="btn" href="{SHOP}/listing/{PACK}">See the Activity Director Pack ($19.99)</a><a class="btn alt" href="{SHOP}/listing/{SAMPLER}">Try the 10-puzzle sampler</a></p>
<div class="box"><b>Facility license:</b> print unlimited copies for the residents, participants or members of one facility, program or location
(senior living, memory care, adult day, church group, classroom).</div>
<div class="grid">{"".join(ws_book(k) for k in ORDER)}</div>
<h2>Sudoku for your number lovers</h2>
<p>7 books of 100 large-print sudoku, from Easy to Hard, so every resident finds the right level. Each printable PDF can be printed as many times as your group needs.</p>
<p><a class="btn alt" href="/sudoku/">See the sudoku books and free samples</a></p>
<div class="grid">{"".join(xcard(x) for x in sd_extras[:3])}</div>
<h2>Why residents can finish them</h2><ul>
<li>One puzzle per page: 21 pt bold grid letters, 38 pt sudoku numbers</li><li>Word search words only read forward, down or diagonally. Nothing backwards</li>
<li>Every puzzle checked by computer, and every answer is in the back</li>
<li>Themes people talk about: Christmas, Winter, Bible, Hymns, 1950s & 60s Memories, Garden, Cooking & Baking</li></ul>
<p>Planning for residents living with dementia? See our guide to <a href="/dementia-friendly-printables/">dementia-friendly printables</a>.</p>
{signup()}"""
write(path + "index.html", page(path, "Large Print Word Search for Memory Care & Activity Directors",
      "Large-print word searches and sudoku for senior living, memory care and adult day programs: one puzzle per page, 21 pt letters, a facility print license.",
      body, image="/img/cover-christmas.jpg", img_wh=(340, 440), img_alt="Large print word search books for activity directors", og_type="website",
      crumbs=[("Home", "/"), ("Activity directors", None)]))

# ---------- dementia-friendly printables (audience guide) ----------
path = "dementia-friendly-printables/"; url = BASE + "/" + path; urls.append(url)
d_qa = [("What makes a word search easier to do?",
         "Big letters, one puzzle per page, fewer words, familiar themes and words that never run backwards or upward. All of our puzzles follow those rules."),
        ("Which free printable should we start with?",
         "Try a theme with strong memories: the 1950s Soda Fountain puzzle, Amazing Grace or Deck the Halls. For number lovers, start with the easy sudoku."),
        ("Can we copy them for a group?", "Yes, the free printables can be copied for your group. The Activity Director Pack adds 350 puzzles with a facility print license."),
        ("Are these puzzles a treatment?", "No. They are a relaxing, social activity, not a medical product, and we make no health claims.")]
faq_html, faq_ld = faq_block(d_qa)
starts = ["nostalgia", "hymns", "christmas"]
body = f"""<h1>Dementia-friendly printable activities: large-print puzzles</h1>
<p class="lead">Free large-print word searches and sudoku that are easy to see and easy to start: big letters, nothing backwards, answer keys included. For memory care groups, day programs and caregivers at home.</p>
<h2>What makes a puzzle easier to enjoy</h2><ul>
<li><b>Big, bold letters.</b> Our grid letters are 21 point bold and word lists are 18 point.</li>
<li><b>One puzzle per page.</b> No crowded pages, plenty of white space.</li>
<li><b>Words never run backwards or up.</b> Only right, down and diagonally down-right.</li>
<li><b>Short word lists.</b> 10 to 12 words per puzzle.</li>
<li><b>Familiar themes.</b> Hymns, Bible stories, Christmas, gardens, kitchens and the 1950s spark conversation.</li>
<li><b>Answer key on page 2.</b> Helpers can give a hint without guessing.</li></ul>
<h2>Start with Extra Easy</h2><p>Our Extra Easy puzzles use a small 10 x 10 grid, just 6 to 8 short words, giant 34 pt letters, and words that only read across or down.</p>
<div class="grid">{"".join(xcard(x) for x in ee_extras)}</div>
<h2>More free printables to try</h2><div class="grid">{"".join(card(k) for k in starts)}{xcard(sd_extras[0])}</div>
<h2>Tips for a group session</h2><ul>
<li>Print one copy per person, plus one enlarged copy for the table to work on together.</li>
<li>Read the word list aloud first and talk about each word: who remembers a sock hop, a soda fountain or a favorite hymn?</li>
<li>Pairs work well: one person finds, the other circles.</li>
<li>Finishing isn't the goal. Stop while it's still fun.</li></ul>
{faq_html}
<p>More: <a href="/word-search/">all {WS_N} free word searches</a> · <a href="/sudoku/">free large-print sudoku</a> · <a href="/activity-directors/">the Activity Director Pack</a></p>
{signup()}"""
write(path + "index.html", page(path, "Dementia-Friendly Printable Activities: Large Print Puzzles (Free)",
      "Free large-print word searches and sudoku that are easy to see: big letters, nothing backwards, answer keys included. Printables for memory care and home.",
      body, image="/img/nostalgia-preview.jpg", img_alt="Large print 1950s word search for memory care", og_type="article",
      graph=[{"@type": "Article", "headline": "Dementia-friendly printable activities: large-print puzzles", "url": url,
              "publisher": {"@id": f"{BASE}/#org"}, "dateModified": TODAY}, faq_ld],
      crumbs=[("Home", "/"), ("Dementia-friendly printables", None)]))

# ---------- what font size is large print (answer page) ----------
path = "large-print-font-size/"; url = BASE + "/" + path; urls.append(url)
f_qa = [("What font size is large print?",
         "Usually 16 to 18 point or bigger. The American Printing House for the Blind (US) says a document is not large print unless it is at least 18 point; RNIB (UK) calls 16 to 18 point large print and anything bigger giant print."),
        ("What is the difference between enlarged print and large print?",
         "APH calls print between 14 and 16 point \"enlarged\" print and says it does not meet the large-print standard. Large print starts at 18 point."),
        ("What size is a large-print puzzle book?",
         "It varies a lot. Many books sold as large print use letters around 14 to 16 point. Our word search grids are 21 point bold with 18 point word lists, one puzzle per page."),
        ("What font is easiest to read in large print?",
         "Plain sans-serif fonts. APH lists APHont, Verdana, Tahoma and Helvetica among the acceptable fonts for large print.")]
faq_html, faq_ld = faq_block(f_qa)
body = f"""<h1>What font size is large print? 16, 18 or 21 point explained</h1>
<p class="lead"><b>Large print usually means 16 to 18 point or bigger.</b> In the US, the American Printing House for the Blind says a document isn't large print unless it is at least 18 point. In the UK, RNIB calls 16 to 18 point large print and anything bigger giant print.</p>
<h2>Print sizes compared</h2>
<table><tr><th>Size</th><th>What it's called</th><th>Where you see it</th></tr>
<tr><td>10 to 12 pt</td><td>Regular print</td><td>Most books, newspapers and forms</td></tr>
<tr><td>14 to 16 pt</td><td>"Enlarged" print (APH); 16 pt is large print in the UK (RNIB)</td><td>Many books sold as "large print"</td></tr>
<tr><td>18 pt and up</td><td>Large print (APH); giant print above 18 pt (RNIB)</td><td>Large-print documents and textbooks</td></tr>
<tr><td>21 pt bold</td><td>Our word search grid letters</td><td>Big Clear Puzzle Books, with 18 pt word lists</td></tr></table>
<h2>Why point size isn't the whole story</h2><ul>
<li><b>Font:</b> plain sans-serif letters read bigger than serif letters at the same size.</li>
<li><b>Weight:</b> bold letters are easier to pick out in a puzzle grid.</li>
<li><b>Space:</b> one puzzle per page with wide spacing helps as much as size.</li>
<li><b>Contrast:</b> black on white beats gray or colored text.</li></ul>
<h2>Test it at home</h2><p>Print one of our free puzzles and see if the letters are comfortable: <a href="/free/christmas-word-search-for-seniors/">large-print Christmas word search</a> or <a href="/free/large-print-sudoku-for-seniors/">large-print easy sudoku</a>.</p>
{faq_html}
<h2>Sources</h2><ul class="small">
<li><a href="https://www.aph.org/app/uploads/2022/04/Research-Based-Large-Print-Guidelines.pdf">American Printing House for the Blind: Research-Based Guidelines for the Development of Documents in Large Print</a></li>
<li><a href="https://www.rnib.org.uk/reading-services/newsagent/big-print-TV-and-radio-guides">RNIB: Large and giant print</a></li>
<li><a href="https://www.acb.org/large-print-guidelines">American Council of the Blind: Large Print Guidelines</a></li></ul>
{signup()}"""
write(path + "index.html", page(path, "What Font Size Is Large Print? 16, 18 or 21 Point Explained",
      "Large print usually means 16 to 18 point or bigger. See what APH and RNIB say, how puzzle books compare, and a free page to test-print at home.",
      body, image="/img/christmas-preview.jpg", img_alt="Large print word search with 21 point letters", og_type="article",
      graph=[{"@type": "Article", "headline": "What font size is large print? 16, 18 or 21 point explained", "url": url,
              "publisher": {"@id": f"{BASE}/#org"}, "dateModified": TODAY}, faq_ld],
      crumbs=[("Home", "/"), ("What font size is large print?", None)]))

BOOK_BLURB = {  # one line per book, from the Amazon descriptions
    "garden": "Spring flowers, summer blooms, the vegetable patch, herbs, garden tools and backyard birds.",
    "bible": "From Genesis to Revelation: Eden, Noah, Joseph, Moses and more. Names follow the King James Version.",
    "nostalgia": "Soda fountains, sock hops, drive-ins, rock and roll and fifties fashion: a trip down memory lane.",
    "christmas": "Deck the halls, trim the tree, the first Christmas, Santa's workshop, cookies and carols.",
    "winter": "Snowfall, building a snowman, hot drinks, ice skating and the sledding hill.",
    "hymns": "Amazing Grace, It Is Well with My Soul, Rock of Ages and more, all hymns published before 1929.",
    "cooking": "In the kitchen, baking day, bread making and family favorites.",
}

# ---------- books (all paperbacks + printables) ----------
path = "books/"; url = BASE + "/" + path; urls.append(url)
def book_card(k):
    b = books[k]
    amz = f'<a class="btn" href="https://www.amazon.com/dp/{b["asin"]}">Paperback on Amazon</a>' if b.get("asin") else '<p class="small">Paperback coming soon</p>'
    return (f'<div class="card"><img src="/img/cover-{k}.jpg" alt="Large Print Word Search for Seniors: {E(b["name"])} by Callan Brooks" loading="lazy" width="340" height="440">'
            f'<h3>{E(b["name"])}</h3><p>{E(BOOK_BLURB[k])}</p><p>50 puzzles · 80 pages · 8.5 x 11 in</p>{amz}'
            f'<p><a href="{SHOP}/listing/{b["listing"]}">Printable PDF on Etsy</a> · <a href="/free/{SEO[k][0]}/">Free sample puzzle</a></p></div>')
body = f"""<h1>Large print word search books by Callan Brooks</h1>
<p class="lead">The <b>Big Clear Puzzle Books</b> series: 50 puzzles per book, one big puzzle per 8.5 x 11 page, 21 pt bold grid letters and 18 pt word lists,
words that never run backwards, and every answer in the back. Paperbacks on Amazon, printable PDFs on Etsy.</p>
<p><a class="btn alt" href="{AMAZON_SERIES}">The whole series on Amazon</a><a class="btn alt" href="{AMAZON_AUTHOR}">Callan Brooks author page</a></p>
<h2>Word search paperbacks</h2><div class="grid">{"".join(book_card(k) for k in ORDER)}</div>
<h2>Large print sudoku</h2><p>7 books of 100 puzzles each, Easy to Hard, with extra-large numbers. Available now as printable PDFs; paperbacks are on the way.</p>
<div class="grid">{"".join(sd_card(v, lv, lid) for v, lv, lid in SUDOKU)}</div>
<div class="box"><b>For a whole facility?</b> The <a href="/activity-directors/">Activity Director Pack</a> has all 7 word search books (350 puzzles) with a facility print license.</div>
{signup()}"""
write(path + "index.html", page(path, "Large Print Word Search Books for Seniors by Callan Brooks",
      "The Big Clear Puzzle Books series by Callan Brooks: large print word search paperbacks for seniors on Amazon, plus printable PDFs and large print sudoku.",
      body, image="/img/cover-christmas.jpg", img_wh=(340, 440), img_alt="Large print word search books by Callan Brooks", og_type="website",
      graph=[{"@type": "CollectionPage", "name": "Big Clear Puzzle Books by Callan Brooks", "url": url}] + [book_ld(k) for k in ORDER if books[k].get("asin")],
      crumbs=[("Home", "/"), ("Books", None)]))

# ---------- home ----------
live = [k for k in ORDER if books[k].get("asin")]
paperbacks = (f"<h2>Paperbacks on Amazon</h2><p>Prefer a real book? Printed paperbacks by Callan Brooks, 8.5 x 11 in. A good gift. <a href=\"{AMAZON_SERIES}\">See the whole series on Amazon</a> or <a href=\"/books/\">browse all our books</a>.</p><p>"
              + "".join(f'<a class="btn alt" href="https://www.amazon.com/dp/{books[k]["asin"]}">{E(books[k]["name"])}</a>' for k in live)
              + "</p>") if live else ""
body = f"""<h1>Free large-print puzzles for seniors</h1>
<p class="lead">Big, clear word searches and sudoku that are easy to see and always right. Print free samples, then get the full books on Etsy or Amazon.</p>
<div class="series">
<a class="tile" href="/word-search/"><img src="/img/cover-christmas.jpg" alt="Large print word search books" width="340" height="440">
<span><b>Word Search</b>7 themed books, 50 puzzles each<br>{WS_N} free printables<em>Browse word searches →</em></span></a>
<a class="tile" href="/sudoku/"><img src="/img/cover-sudoku-1.jpg" alt="Large print sudoku books" width="340" height="440">
<span><b>Sudoku</b>7 books, Easy to Hard, 100 puzzles each<br>{len(sd_extras)} free printables<em>Browse sudoku →</em></span></a>
</div>
{signup()}
<h2 id="thanksgiving">This week: Thanksgiving</h2><div class="grid">{"".join(xcard(x) for x in seasonal)}</div>
<h2>Free word searches</h2><div class="grid">{"".join(card(o) for o in ORDER[:6])}</div>
<p><a class="btn alt" href="/word-search/">See all {WS_N} free word searches</a></p>
<h2>Free sudoku</h2><div class="grid">{"".join(xcard(x) for x in sd_extras[:3])}</div>
<p><a class="btn alt" href="/sudoku/">See the sudoku series</a></p>
{paperbacks}<h2>For activity directors and memory care</h2><p>Facility print license, word search and sudoku: <a href="/activity-directors/">see the activity director page</a>, or read our guide to <a href="/dementia-friendly-printables/">dementia-friendly printables</a>.</p>
<h2>What makes them different</h2><ul><li>One puzzle per page with extra-large bold letters and numbers (<a href="/large-print-font-size/">what counts as large print?</a>)</li><li>Word search words read forward, down or diagonally, never backwards</li>
<li>A computer checks every puzzle, and every answer is in the back</li></ul>"""
write("index.html", page("", "Free Large Print Word Search & Sudoku Printables for Seniors",
      "Free printable large-print word searches and sudoku for seniors, adults and memory care. 21 pt bold letters, one puzzle per page, answer key included.",
      body, image="/img/christmas-preview.jpg", img_alt="Large print Christmas word search page", og_type="website"))

# ---------- 404, headers, sitemap, robots ----------
body404 = """<h1>Sorry, we can't find that page</h1><p>The link may be old or mistyped. All of our free large-print puzzles are still here:</p>
<p><a class="btn" href="/word-search/">Free word searches</a><a class="btn" href="/sudoku/">Free sudoku</a><a class="btn alt" href="/">Home</a></p>
<h2>Popular free printables</h2><ul><li><a href="/free/christmas-word-search-for-seniors/">Large print Christmas word search</a></li>
<li><a href="/free/winter-word-search-for-seniors/">Large print winter word search</a></li><li><a href="/free/bible-word-search-large-print/">Large print Bible word search</a></li>
<li><a href="/free/1950s-word-search-for-seniors/">1950s word search for seniors</a></li><li><a href="/free/large-print-sudoku-for-seniors/">Easy large print sudoku</a></li>
<li><a href="/activity-directors/">For activity directors and memory care</a></li></ul>"""
write("404.html", page("404.html", "Page not found | Big Clear Puzzle Books", "Page not found.", body404, noindex=True))
write("_headers", "".join(f'/downloads/{pdf}\n  Link: <{BASE}/{p}>; rel="canonical"\n' for pdf, p in pdf_pages)
      + "/downloads/custom/*\n  X-Robots-Tag: noindex\n/downloads/packs/*\n  X-Robots-Tag: noindex\n")


def lastmod(u):
    rel = u[len(BASE) + 1:] + "index.html"
    try:
        d = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%cs", "--", rel], capture_output=True, text=True).stdout.strip()
    except Exception:
        d = ""
    return d or TODAY


def img_xml(u):
    return "".join(f"<image:image><image:loc>{BASE}{E(src)}</image:loc></image:image>" for src, alt in IMGS.get(u, [])[:20])


write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
      'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' +
      "".join(f"<url><loc>{u}</loc><lastmod>{lastmod(u)}</lastmod>{img_xml(u)}</url>\n" for u in urls) + "</urlset>\n")
write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
write(".nojekyll", "")
print("pages:", len(urls))
try:   # 2:3 Pinterest/og share images for free pages (needs Pillow; skipped quietly without it)
    if SHARE:
        r = subprocess.run(["python3", os.path.join(ROOT, "tools", "share_images.py")], input=json.dumps(SHARE), text=True, check=True, capture_output=True)
        print("share images:", r.stdout.strip())
except Exception as e:
    print("share images skipped:", e)
try:   # PDF title/author/links (idempotent): keeps new free PDFs search-friendly without a separate step
    subprocess.run(["python3", os.path.join(ROOT, "tools", "pdf_meta.py")], check=True, capture_output=True)
    print("pdf metadata: ok")
except Exception as e:
    print("pdf metadata skipped:", e)
