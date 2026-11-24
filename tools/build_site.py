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
SD_TIP = {"Easy": "Pick a number and check each box: if only one square in a box can hold it, write it in.",
          "Medium": "Pencil in the possible numbers. If two squares in a row can only be the same two numbers, cross those numbers off the rest of the row.",
          "Hard": "Pencil in every square, then look for pairs, triples, and the X-Wing and XY-Wing patterns."}
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
CSS = """@font-face{font-family:"Bitter";src:url(/fonts/bitter-700.woff2) format("woff2");font-weight:700;font-display:swap}
:root{--paper:#fbf6ec;--card:#fffdf8;--ink:#1f1d1a;--soft:#4f483d;--navy:#1e3a5f;--navy2:#172d4a;--gold:#ffde73;--goldd:#e3b33f;--rule:#e6dbc4;--etsy:#a4401f;--amz:#1b2633;--green:#2f6b47;--focus:#0b5fff}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font-family:Verdana,Geneva,"DejaVu Sans",sans-serif;font-size:1.25rem;line-height:1.65;color:var(--ink);background:var(--paper)}
h1,h2,h3,.brand b,.tile b,.ft-brand b{font-family:Bitter,Georgia,"Times New Roman",serif;font-weight:700;color:var(--navy);letter-spacing:-.005em}
h1{font-size:2.75rem;line-height:1.15;margin:18px 0 12px}h2{font-size:2rem;line-height:1.2;margin:52px 0 14px}h3{line-height:1.25}
a{color:var(--navy);text-decoration-thickness:2px;text-underline-offset:3px}a:hover{color:var(--etsy)}
:focus-visible{outline:4px solid var(--focus);outline-offset:3px;border-radius:6px}
img{max-width:100%;height:auto}.w{max-width:1140px;margin:0 auto;padding:0 24px}
.lead{font-size:1.4375rem;color:var(--soft);max-width:44em}.small{font-size:1.0625rem}
.skip{position:absolute;left:-9999px;top:8px;z-index:20;background:var(--gold);color:var(--navy);padding:12px 18px;font-weight:bold;border-radius:8px}.skip:focus{left:12px}
/* top bar + header */
.topbar{background:var(--navy);color:#fff}.topbar .w{display:flex;justify-content:flex-end}
.util{display:flex;flex-wrap:wrap;gap:0 4px}.util a{display:inline-flex;align-items:center;min-height:44px;padding:4px 12px;color:#fff;font-size:1.0625rem;text-decoration:none}
.util a:hover{color:var(--gold);text-decoration:underline}.util .nav-pack{color:var(--gold);font-weight:bold}
.site-h{background:var(--card);border-bottom:1px solid var(--rule);box-shadow:0 4px 14px rgba(60,40,10,.05)}
.site-h .w{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px 28px;padding-top:16px;padding-bottom:16px}
.brand{display:flex;align-items:center;gap:14px;text-decoration:none;color:var(--navy)}
.brand img{width:66px;height:66px;border-radius:50%;box-shadow:0 0 0 3px var(--gold)}
.brand b{display:block;font-size:1.75rem;line-height:1.1}.brand small{display:block;font-size:1rem;color:var(--soft);margin-top:3px}
.main{display:flex;gap:8px}.main a{display:inline-flex;align-items:center;min-height:52px;padding:6px 20px;border-radius:12px;font-size:1.25rem;font-weight:bold;color:var(--navy);text-decoration:none;border:2px solid transparent}
.main a:hover{border-color:var(--rule);background:#f6eedc;color:var(--navy)}.main a[aria-current]{background:var(--navy);color:#fff}
.crumbs{font-size:1.0625rem;margin:22px 0 0;color:var(--soft)}.crumbs a{color:var(--navy)}
/* buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:12px;min-height:56px;padding:12px 26px;margin:8px 10px 8px 0;border-radius:12px;border:2px solid transparent;
 font-weight:bold;font-size:1.25rem;line-height:1.25;text-decoration:none;box-shadow:0 3px 0 rgba(0,0,0,.18);text-align:left}
.btn:active{transform:translateY(2px);box-shadow:none}.btn:hover{filter:brightness(1.07)}
.btn.dl{background:var(--gold);color:var(--navy);border-color:var(--goldd);font-size:1.5rem;min-height:70px;padding:14px 32px}
.btn.dl::before{content:"";flex:none;width:28px;height:28px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231e3a5f' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 3v12M6 10l6 6 6-6M4 20h16'/%3E%3C/svg%3E") no-repeat center/contain}
.btn.etsy{background:var(--etsy);color:#fff}.btn.amz{background:var(--amz);color:#fff}
.btn.etsy::before,.btn.amz::before{flex:none;font-size:0.875rem;letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:6px;font-weight:bold}
.btn.etsy::before{content:"Etsy";background:#fff;color:var(--etsy)}.btn.amz::before{content:"Amazon";background:#ffcf73;color:var(--amz)}
.btn.go{background:var(--navy);color:#fff}.btn.go2{background:var(--card);color:var(--navy);border-color:var(--navy);box-shadow:none}
.btn.etsy:hover,.btn.amz:hover,.btn.go:hover{color:#fff}.btn.dl:hover,.btn.go2:hover{color:var(--navy)}
/* hero (home) */
.hero{display:grid;grid-template-columns:1.15fr .85fr;gap:30px;align-items:center;padding:30px 0 10px}
.hero h1{font-size:3.5rem;line-height:1.06;margin:0 0 18px}.hero .lead{font-size:1.4375rem}
.hero-cta .btn{font-size:1.3125rem}.hero-art{position:relative;height:430px}
.hero-art img{position:absolute;border-radius:6px;box-shadow:0 18px 40px rgba(40,30,10,.22)}
.hero-art .c1{width:42%;left:0;top:70px;transform:rotate(-8deg)}.hero-art .c2{width:42%;right:0;top:56px;transform:rotate(7deg)}
.hero-art .c3{width:56%;left:22%;top:12px;border:1px solid var(--rule);background:#fff}
.why{background:var(--card);border:1px solid var(--rule);border-radius:18px;padding:6px 30px 18px;margin:26px 0}
.why h2{margin:20px 0 10px;font-size:1.625rem}.why ul{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(3,1fr);gap:18px 28px}
.why li,.ticks li{position:relative;padding-left:42px}
.why li::before,.ticks li::before{content:"";position:absolute;left:0;top:3px;width:28px;height:28px;border-radius:50%;background:var(--green) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12.5l4.5 4.5L19 7'/%3E%3C/svg%3E") no-repeat center/18px}
/* tiles */
.series{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:26px 0}
.tile{display:flex;gap:22px;align-items:center;background:var(--card);border:1px solid var(--rule);border-radius:18px;padding:22px;text-decoration:none;color:var(--ink);font-size:1.1875rem;box-shadow:0 3px 0 var(--rule)}
.tile:hover{border-color:var(--navy);color:var(--ink)}.tile img{width:140px;border-radius:4px;box-shadow:0 8px 18px rgba(0,0,0,.18)}
.tile b{display:block;font-size:2rem;margin-bottom:4px}.tile em{display:inline-block;margin-top:12px;font-style:normal;font-weight:bold;color:var(--navy);border-bottom:3px solid var(--gold)}
/* cards */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:24px;margin:20px 0}
.card{position:relative;background:var(--card);border:1px solid var(--rule);border-radius:16px;padding:14px 14px 16px;box-shadow:0 3px 0 var(--rule);transition:transform .15s}
.card:hover{transform:translateY(-3px);border-color:#cdbb95}.card:focus-within{outline:4px solid var(--focus);outline-offset:3px}
.card img{display:block;width:100%;aspect-ratio:1/1;object-fit:cover;object-position:top;border-radius:10px;border:1px solid #ece3cf;background:#fff}
.card.bk img{aspect-ratio:340/440;object-fit:contain;border:0;box-shadow:0 6px 14px rgba(0,0,0,.16)}
.card h3{font-size:1.375rem;margin:12px 0 4px}.card h3 a{text-decoration:none}.card h3 a:hover{text-decoration:underline}
.card.pz h3 a::after{content:"";position:absolute;inset:0;border-radius:16px}
.card p{margin:4px 0 0;font-size:1.0625rem;color:var(--soft)}.card .btn{display:flex;flex-direction:column;gap:4px;width:100%;font-size:1.125rem;min-height:52px;padding:10px 12px;margin:12px 0 8px;text-align:center}
/* free page */
.getit{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:40px;align-items:start;margin:22px 0 8px}
.getit .pv img{display:block;width:100%;border:1px solid var(--rule);border-radius:10px;background:#fff;box-shadow:0 14px 34px rgba(60,40,10,.13)}
.getit .act{background:var(--card);border:1px solid var(--rule);border-radius:18px;padding:26px 28px 14px;position:sticky;top:16px}
.box h2{margin-top:6px}
.dlrow{margin:0 0 12px}.dlrow .btn{width:100%;margin:0}
.ticks{list-style:none;padding:0;margin:8px 0 0}.ticks li{padding-top:10px;padding-bottom:10px;border-top:1px dashed var(--rule)}.ticks li::before{top:12px}
.strat figure{margin:14px 0 30px;background:#fff;border:1px solid var(--rule);border-radius:14px;padding:16px}.strat figure img{display:block;width:100%;height:auto;max-width:540px;margin:0 auto}.strat figure.row{overflow-x:auto}.strat figure.row img{max-width:780px;min-width:520px}.toc a{margin-right:18px}
.wl{margin-top:10px}.facts{font-size:1.125rem;color:var(--soft)}
.words{list-style:none;padding:0;margin:12px 0;display:flex;flex-wrap:wrap;gap:10px 12px;font-size:1.375rem;font-weight:bold;letter-spacing:.04em}
.words li{background:#fff;border:2px solid var(--rule);border-radius:10px;padding:8px 16px;white-space:nowrap}
.box{background:var(--card);border:1px solid var(--rule);border-left:8px solid var(--gold);border-radius:14px;padding:20px 26px;margin:28px 0}
.box.buy{border:2px solid var(--navy);border-top:10px solid var(--navy);padding:24px 28px;background:var(--card)}
.box.buy>b:first-child{display:block;font-family:Bitter,Georgia,serif;font-size:1.875rem;color:var(--navy);margin-bottom:6px}
.box.buy br{display:none}.box.buy .btn{display:flex;width:fit-content;max-width:100%;margin-top:14px}
.adline{font-size:1.1875rem}
/* faq, tables, signup */
.faq{margin-top:20px}.faq h3{font-size:1.375rem;margin:14px 0 0;padding:18px 24px 4px;background:var(--card);border:1px solid var(--rule);border-bottom:0;border-radius:14px 14px 0 0}
.faq p{margin:0;padding:0 24px 18px;background:var(--card);border:1px solid var(--rule);border-top:0;border-radius:0 0 14px 14px}
table{border-collapse:collapse;width:100%;background:var(--card);margin:18px 0}td,th{border:1px solid var(--rule);padding:12px 14px;text-align:left;vertical-align:top}th{background:#f3ead6}
.signup{background:var(--navy);color:#fff;border-radius:20px;padding:32px 34px;margin:52px 0}
.signup h2{color:#fff;margin:0 0 8px}.signup .small{color:#dbe3ee}.sf input{font-size:1.25rem}
.jump{font-size:0;display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}.jump a{font-size:1.125rem;display:inline-flex;align-items:center;min-height:48px;padding:6px 16px;background:var(--card);border:2px solid var(--rule);border-radius:999px;text-decoration:none;font-weight:bold}
.jump a:hover{border-color:var(--navy)}ul{padding-left:26px}
/* footer */
footer.site{margin-top:80px;background:var(--navy2);color:#fff;padding:44px 0 30px;font-size:1.125rem}
.ft{display:grid;grid-template-columns:1.3fr 1fr 1fr;gap:30px}.ft p{margin:0 0 10px}
.ft-brand{display:flex;align-items:center;gap:12px}.ft-brand img{border-radius:50%;background:#fff}.ft-brand b{color:#fff;font-size:1.5rem}
.ft-h{font-weight:bold;color:var(--gold);text-transform:uppercase;letter-spacing:.06em;font-size:1rem}
.ft ul{list-style:none;padding:0;margin:0}.ft li a{display:inline-block;padding:10px 0;color:#fff}.ft li a:hover{color:var(--gold)}
.ft-note{grid-column:1/-1;border-top:1px solid rgba(255,255,255,.22);padding-top:18px;font-size:1.0625rem;color:#d6dee9}
@media(max-width:860px){
 .topbar .w{padding:0 8px}.util{width:100%;display:grid;grid-template-columns:1fr 1.1fr .6fr}.util a{justify-content:center;text-align:center;font-size:0.9375rem;line-height:1.2;padding:4px 6px}
 .site-h .w{padding-top:12px;padding-bottom:12px}.brand img{width:52px;height:52px}.brand b{font-size:1.4375rem}.brand small{font-size:0.9375rem}
 .main{width:100%;display:grid;grid-template-columns:1.45fr 1fr 1fr;gap:8px}.main a{justify-content:center;white-space:nowrap;font-size:1.125rem;padding:6px 4px;border-color:var(--rule);background:#fff}
 h1{font-size:2.125rem}h2{font-size:1.6875rem;margin-top:42px}.lead{font-size:1.3125rem}
 .hero{grid-template-columns:1fr;padding-top:18px}.hero h1{font-size:2.5rem}.hero-art{height:240px;width:86%;max-width:360px;margin:0 auto}.getit .act{position:static}
 .why ul,.series{grid-template-columns:minmax(0,1fr)}.tile{padding:16px;gap:16px}.tile img{width:104px}.tile b{font-size:1.6875rem}
 .getit{grid-template-columns:1fr;gap:20px}.getit .act{order:-1;padding:20px 18px 8px}.getit .pv{max-width:460px}
 .ft{grid-template-columns:1fr}}
@media(max-width:380px){.main a{font-size:1rem}.brand b{font-size:1.25rem}}
@media(max-width:600px){td,th{overflow-wrap:anywhere;padding:8px;font-size:1.0625rem}
 .btn{width:100%;margin-right:0}.box{padding:18px}.box.buy{padding:20px 18px}.box.buy .btn{width:100%} .box.buy .btn{flex-direction:column;gap:6px;text-align:center}.signup{padding:24px 18px}.words{font-size:1.25rem;letter-spacing:.02em}.words li{padding:6px 12px}}
@media print{html{font-size:100%!important}body{background:#fff;color:#000;font-size:13pt}
 .topbar,.site-h,footer.site,.signup,.grid,.btn,.crumbs,.skip,.adline,.hero-art,.series,.jump,.buy{display:none!important}
 .free main>*:not(.getit){display:none!important}.free .getit{display:block;margin:0}.free .act{display:none}
 .free .pv img{width:100%;max-height:10in;object-fit:contain;border:0;box-shadow:none}
 h1,h2,h3{color:#000}a{color:#000;text-decoration:none}.card,.box,.faq h3,.faq p{box-shadow:none;border-color:#999}}

/* three home tiles */
.series{grid-template-columns:repeat(3,minmax(0,1fr))}.tile{flex-direction:column;align-items:flex-start;gap:14px}.tile img{width:118px}.tile b{font-size:1.875rem}
/* text-size control (A / A+ / A++), remembered on the device */
.topbar .w{justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0 12px}
.tsize{display:flex;align-items:center;gap:6px;color:#fff;font-size:1rem;padding:4px 0}
.tsize button{font:inherit;font-weight:bold;min-width:46px;min-height:40px;padding:0 8px;border:2px solid #fff;background:transparent;color:#fff;border-radius:8px;cursor:pointer}
.tsize button:nth-of-type(2){font-size:1.125rem}.tsize button:nth-of-type(3){font-size:1.25rem}
.tsize button[aria-pressed="true"]{background:var(--gold);border-color:var(--gold);color:var(--navy)}
html[data-ts="2"]{font-size:112.5%}html[data-ts="3"]{font-size:125%}
html[data-ts="2"] .main a,html[data-ts="3"] .main a{white-space:normal;text-align:center;line-height:1.15}
@media(max-width:860px){.series{grid-template-columns:minmax(0,1fr)}.tile{flex-direction:row;align-items:center}.tile img{width:96px}
 .tsize{width:100%;justify-content:center;border-top:1px solid rgba(255,255,255,.2)}}
/* phones: single-column list cards */
@media(max-width:600px){.grid{grid-template-columns:minmax(0,1fr);gap:12px}
 .card{display:grid;grid-template-columns:92px minmax(0,1fr);column-gap:14px;align-items:start;padding:10px}
 .card>*{grid-column:2}.card>a:first-child,.card>img:first-child{grid-column:1;grid-row:1/span 8}
 .card img{width:92px;aspect-ratio:765/990;object-fit:cover;object-position:top}.card.bk img{aspect-ratio:340/440;object-fit:contain}
 .card h3{font-size:1.3125rem;margin:4px 0 4px}.card p{font-size:1.0625rem}.card .btn{font-size:1.0625rem;margin:8px 0}}
@media print{.tsize{display:none!important}}
@media(max-width:860px){.ft,.getit{grid-template-columns:minmax(0,1fr)}.btn.dl{padding:12px 18px}}.ft a{overflow-wrap:anywhere}
.tsize{font-size:16px}.tsize button{font-size:16px;min-height:44px}.tsize button:nth-of-type(2){font-size:18px}.tsize button:nth-of-type(3){font-size:20px}

/* MailerLite embed */
.signup .ml-embedded{margin:16px 0 6px}
.signup #mlb2-48911036.ml-form-embedContainer,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form{width:100%!important;max-width:560px!important;margin:0!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-align-center,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-align-center{text-align:left!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper{width:100%!important;max-width:560px!important;background:#fffdf8!important;border:3px solid #ffde73!important;border-radius:16px!important;margin:0 auto!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody{padding:24px 24px 20px!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody h4,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody h4{font-family:Bitter,Georgia,"Times New Roman",serif!important;font-weight:700!important;font-size:1.625rem!important;line-height:1.2!important;color:#1e3a5f!important;margin:0 0 8px!important;text-align:left!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody p,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody p{font-family:Verdana,Geneva,"DejaVu Sans",sans-serif!important;font-size:1.125rem!important;line-height:1.5!important;color:#1f1d1a!important;text-align:left!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-successBody{padding:24px 24px 20px!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody h4,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-successBody h4{font-family:Bitter,Georgia,"Times New Roman",serif!important;font-weight:700!important;font-size:1.625rem!important;line-height:1.2!important;color:#1e3a5f!important;margin:0 0 8px!important;text-align:left!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-successBody p,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-successBody p{font-family:Verdana,Geneva,"DejaVu Sans",sans-serif!important;font-size:1.125rem!important;line-height:1.5!important;color:#1f1d1a!important;text-align:left!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input{font-family:Verdana,Geneva,"DejaVu Sans",sans-serif!important;font-size:1.25rem!important;line-height:1.3!important;color:#1f1d1a!important;background:#fff!important;min-height:56px!important;height:auto!important;padding:12px 16px!important;border:2px solid #4f483d!important;border-radius:10px!important;box-sizing:border-box!important;width:100%!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input::placeholder,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input::placeholder{color:#5f574b!important;opacity:1!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input:focus,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow input:focus{outline:4px solid #0b5fff!important;outline-offset:2px!important;border-color:#1e3a5f!important;box-shadow:none!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow.ml-error input,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-fieldRow.ml-error input{border-color:#b3261e!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-recaptcha,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-recaptcha{float:none!important;display:flex!important;justify-content:center!important;margin:14px 0 4px!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit{float:none!important;width:100%!important;margin:12px 0 0!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button.primary,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button.primary{width:100%!important;min-height:56px!important;height:auto!important;padding:12px 20px!important;font-family:Verdana,Geneva,"DejaVu Sans",sans-serif!important;font-size:1.25rem!important;font-weight:bold!important;line-height:1.25!important;background:#ffde73!important;color:#1e3a5f!important;border:2px solid #e3b33f!important;border-radius:12px!important;box-shadow:0 3px 0 rgba(0,0,0,.18)!important;cursor:pointer}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button.loading,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button.loading{width:100%!important;min-height:56px!important;height:auto!important;padding:12px 20px!important;font-family:Verdana,Geneva,"DejaVu Sans",sans-serif!important;font-size:1.25rem!important;font-weight:bold!important;line-height:1.25!important;background:#ffde73!important;color:#1e3a5f!important;border:2px solid #e3b33f!important;border-radius:12px!important;box-shadow:0 3px 0 rgba(0,0,0,.18)!important;cursor:pointer}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button.primary:hover,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button.primary:hover{background:#ffe68f!important;color:#1e3a5f!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button.primary:focus-visible,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedSubmit button.primary:focus-visible{outline:4px solid #fff!important;outline-offset:3px!important}
.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-embedPermissions{font-size:1rem!important;line-height:1.5!important;color:#1f1d1a!important}
@media(max-width:600px){.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody{padding:18px 16px 16px!important}}
.signup #mlb2-48911036.ml-form-embedContainer,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form{margin-left:auto!important;margin-right:auto!important}
@media screen and (max-width:480px){.signup #mlb2-48911036.ml-form-embedContainer,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form{display:block!important;width:100%!important;max-width:100%!important}.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper{display:block!important;max-width:100%!important}.signup #mlb2-48911036.ml-form-embedContainer .ml-form-embedWrapper .ml-form-embedBody .ml-form-recaptcha,.signup .ml-embedded .ml-form-embedContainer.ml-subscribe-form .ml-form-embedWrapper .ml-form-embedBody .ml-form-recaptcha{width:100%!important;height:62px!important;overflow:visible!important;justify-content:center!important}.signup .ml-form-recaptcha .g-recaptcha{transform:scale(.78)!important;-webkit-transform:scale(.78)!important;transform-origin:50% 0!important;-webkit-transform-origin:50% 0!important}}
@media print{.signup{display:none!important}}"""
HEAD_EXTRA = """<link rel="preload" href="/fonts/bitter-700.woff2" as="font" type="font/woff2" crossorigin><script>try{document.documentElement.dataset.ts=localStorage.getItem("bcpb-ts")||"1"}catch(e){}</script>"""

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



# ===== design-review: presentation helpers (markup around content only; no SEO text changes) =====
def restyle(s):
    """Give every button a kind so Download / Etsy / Amazon / internal links look different."""
    def f(m):
        cls, href = m.group(1), m.group(2)
        kind = ("dl" if href.startswith("/downloads/") else "etsy" if href.startswith(SHOP) else
                "amz" if "amazon.com" in href else ("go" if cls == "btn" else "go2"))
        return f'<a class="btn {kind}" href="{href}"'
    s = re.sub(r'<a class="(btn(?: alt)?)" href="([^"]+)"', f, s)
    return s.replace('<div class="box"><b>Want more?</b>', '<div class="box buy"><b>Want more?</b>')


def nav_html(path, crumbs):
    sec = "/" + path
    if crumbs and len(crumbs) > 1 and crumbs[1][1]: sec = crumbs[1][1]
    def a(href, label, cls=""):
        c = f' class="{cls}"' if cls else ""
        cur = ' aria-current="page"' if href == sec else ""
        return f'<a{c} href="{href}"{cur}>{label}</a>'
    main = '<nav class="main" aria-label="Main">' + a("/word-search/", "Word Search") + a("/sudoku/", "Sudoku") + a("/books/", "Books") + "</nav>"
    util = ('<nav class="util" aria-label="More">' + a("/activity-directors/", "Activity directors") + a("/#signup", "Free monthly pack", "nav-pack")
            + a(SHOP, "Shop", "nav-shop") + "</nav>")
    return main, util


def footer_html():
    return f"""<footer class="site"><div class="w ft">
<div class="ft-about"><p class="ft-brand"><img src="/img/icon.png" alt="" width="56" height="56" data-pin-nopin="true"><b>Big Clear Puzzle Books</b></p>
<p>Large-print word searches and sudoku that are easy to see and always right.</p></div>
<div><p class="ft-h">Shop &amp; follow</p><ul><li><a href="{SHOP}">Etsy shop</a></li><li><a href="{AMAZON_AUTHOR}">Paperbacks by Callan Brooks on Amazon</a></li>
<li><a href="https://www.pinterest.com/bigclearpuzzlebooks/">Pinterest</a></li><li><a href="mailto:hello@bigclearpuzzlebooks.com">hello@bigclearpuzzlebooks.com</a></li></ul></div>
<div><p class="ft-h">Guides</p><ul><li><a href="/books/">All our books</a></li><li><a href="/dementia-friendly-printables/">Dementia-friendly printables</a></li>
<li><a href="/large-print-font-size/">What font size is large print?</a></li><li><a href="/activity-directors/">For activity directors</a></li></ul></div>
<p class="ft-note">Free printables are for personal, family, classroom and activity-group use. Please share the link, not the file.</p>
</div></footer>"""

TSIZE = ('<div class="tsize" role="group" aria-label="Text size"><span>Text size</span><button type="button" data-s="1" aria-pressed="true">A</button>'
         '<button type="button" data-s="2" aria-pressed="false">A+</button><button type="button" data-s="3" aria-pressed="false">A++</button></div>'
         '<script>(function(){var d=document.documentElement;function a(v){d.dataset.ts=v;document.querySelectorAll(".tsize button").forEach(function(b){b.setAttribute("aria-pressed",b.dataset.s==v)});'
         'try{localStorage.setItem("bcpb-ts",v)}catch(e){}}a(d.dataset.ts||"1");document.addEventListener("click",function(e){var b=e.target.closest(".tsize button");if(b)a(b.dataset.s)})})()</script>')
def shell_top(path, crumbs):
    main, util = nav_html(path, crumbs)
    return (f'<a class="skip" href="#main">Skip to main content</a><div class="topbar"><div class="w">{TSIZE}{util}</div></div>'
            f'<header class="site-h"><div class="w"><a class="brand" href="/"><img src="/img/icon.png" alt="" data-pin-nopin="true" width="66" height="66">'
            f'<span><b>Big Clear Puzzle Books</b><small>Easy to see and always right</small></span></a>{main}</div></header>')


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
    body = restyle(body)
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
{ld(SITE_LD)}{page_ld}{ML_SCRIPT}{PIN_SCRIPT}{HEAD_EXTRA}<style>{CSS}</style></head><body class="{'free' if path.startswith('free/') else 'pg'}">
{shell_top(path, crumbs)}
<main class="w" id="main">{crumbs_html(crumbs) if crumbs else ""}{body}</main>
{footer_html()}
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
    return (f'<div class="card pz"><a href="/free/{slug}/"><img src="/img/{k}-preview.jpg" alt="Free large print {E(b["name"])} word search: {E(b["puzzle_title"][3:])}" '
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
    return (f'<div class="card pz"><a href="/free/{x["slug"]}/"><img src="/img/{x["key"]}-preview.jpg" alt="{E(xalt(x))}" '
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
<div class="getit"><div class="pv"><img src="/img/{k}-preview.jpg" alt="Large print {E(TEXT_NAME[k])} word search “{E(puzzle)}” with answer key" width="765" height="990"></div>
<div class="act"><p class="dlrow"><a class="btn" href="/downloads/{b['pdf']}" download>Download the free PDF</a></p>
<ul class="ticks"><li>Extra-large letters: 21 pt bold grid, 18 pt word list</li>
<li>Words read forward, down or diagonally. Nothing backwards</li><li>Puzzle on page 1, solution on page 2</li><li>US Letter (8.5 x 11 in), prints on A4 too</li></ul></div></div>
<section class="wl"><h2>{E(puzzle)}: puzzle 1 of the {E(b['name'])} book</h2>{words_block(words)}<p>{E(USE_TIP[k])}</p></section>
<div class="box"><b>Want more?</b> This puzzle comes from the full <b>{E(b['name'])}</b> book: 50 large-print puzzles, one per page, with every solution.
<br><a class="btn alt" href="{SHOP}/listing/{b['listing']}">Get all 50 puzzles (printable PDF)</a>{extra}</div>
<p class="adline">Running activities for a whole community? The <a href="/activity-directors/">Activity Director Pack</a> has all 7 books (350 puzzles) with a facility license.</p>
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
        bullets = "<li>Extra-large bold numbers, thick 3 x 3 box lines</li><li>Difficulty checked by a logic solver</li><li>Puzzle on page 1, solution on page 2</li><li>US Letter (8.5 x 11 in), prints on A4 too</li>"
        detail = (f'<h2>About this puzzle</h2><p class="facts">9 x 9 sudoku · {lv} level · exactly one solution · solvable by logic, never guessing</p>'
                  f'<p>Fill every row, column and 3 x 3 box with the numbers 1 to 9. {"Start with a row or box that is almost full." if lv == "Easy" else "Look for the square with the fewest possible numbers, then work outward."}</p>')
        detail += (f'<div class="box"><b>Stuck?</b> {E(SD_TIP[lv])} '
                   f'<a href="/sudoku/strategies/#{lv.lower()}">See the {lv.lower()} strategies, with pictures</a></div>')
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
        bullets = "<li>Giant letters: 34 pt bold grid, 26 pt word list</li><li>Small 10 x 10 grid with 6 to 8 short words</li><li>Words read only across or down. Never diagonal, never backwards</li><li>Puzzle on page 1, solution on page 2</li><li>US Letter (8.5 x 11 in), prints on A4 too</li>"
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
        bullets = "<li>Extra-large letters: 21 pt bold grid, 18 pt word list</li><li>Words read forward, down or diagonally. Nothing backwards</li><li>Puzzle on page 1, solution on page 2</li><li>US Letter (8.5 x 11 in), prints on A4 too</li>"
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
<div class="getit"><div class="pv"><img src="/img/{x['key']}-preview.jpg" alt="{E(xalt(x))}" width="765" height="990"></div>
<div class="act"><p class="dlrow"><a class="btn" href="/downloads/{x['pdf']}" download>Download the free PDF</a></p><ul class="ticks">{bullets}</ul></div></div>
<section class="wl">{detail}</section>{more}
<p class="adline">Running activities for a whole community? The <a href="/activity-directors/">Activity Director Pack</a> has 350 word searches with a facility license.</p>
{faq_html}{signup()}<h2>{more_title}</h2><div class="grid">{grid}</div>"""
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
    return (f'<div class="card bk"><a href="{href}"><img src="/img/cover-sudoku-{v}.jpg" alt="Large Print Sudoku for Seniors volume {v}, {lv}" '
            f'loading="lazy" width="340" height="440"></a><h3>Volume {v}: {lv}</h3><p>100 puzzles · <a href="{href}">Printable PDF</a>{amz}</p></div>')


def ws_book(k, up="/"):
    b = books[k]; slug = SEO[k][0]
    amz = f' · <a href="https://www.amazon.com/dp/{b["asin"]}">Paperback</a>' if b.get("asin") else ""
    return (f'<div class="card bk"><a href="/free/{slug}/"><img src="/img/cover-{k}.jpg" alt="Large Print Word Search for Seniors: {E(b["name"])}" '
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
<div class="box"><b>New to sudoku, or stuck on a hard one?</b> Our illustrated guide shows the 8 strategies every puzzle needs, from Easy to Hard.
<br><a class="btn alt" href="/sudoku/strategies/">Read the sudoku strategies</a></div>
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

# ---------- sudoku strategies (illustrated guide; diagrams from the factory's sudoku_strategies.py) ----------
path = "sudoku/strategies/"; url = BASE + "/" + path; urls.append(url); pdf_pages.append(("large-print-sudoku-solving-strategies.pdf", path))
ST_ALT = {
 "only-place": "Sudoku grid: the 5s in rows 2 and 3 and column 2 leave one empty square for 5 in the top-left box",
 "only-number": "Sudoku grid: the center square's row, column and box hold 1 to 8, so it must be 9",
 "pointing": "Sudoku grid with pencil marks for 4: the top-left box's 4 must be in the middle row, so 4 is crossed off the rest of that row",
 "naked-pair": "Sudoku row with pencil marks: two squares can only be 2 or 7, so 2 and 7 are crossed off the other squares",
 "hidden-pair": "Sudoku row with pencil marks: 3 and 6 fit only in the same two squares, so the other numbers in those squares are crossed off",
 "naked-triple": "Sudoku row with pencil marks: three squares share only 2, 5 and 8, so those numbers are crossed off the rest of the row",
 "x-wing": "Sudoku grid with pencil marks for 7 forming a rectangle in rows 2 and 7, so 7 is crossed off the rest of those two columns",
 "xy-wing": "Sudoku grid with an XY-Wing: squares A (3 or 7), B (3 or 9) and C (7 or 9) mean square D cannot be 9"}
def fig(k, row=False):
    return f'<figure{" class=" + chr(34) + "row" + chr(34) if row else ""}><img src="/img/strategies/{k}.svg" alt="{E(ST_ALT[k])}" width="548" height="{68 if row else 548}" loading="lazy" data-pin-nopin="true"></figure>'
st_qa = [("What is the best strategy for solving sudoku?",
          "Start with the two simple strategies: look for the only place a number can go in a box, row or column, and for a square where only one number fits. They solve every easy puzzle and find most numbers in harder ones."),
         ("Do you ever need to guess in sudoku?",
          "Not in a well-made puzzle. Every puzzle in our books can be solved with the eight strategies on this page, with no guessing."),
         ("What strategies do hard sudoku puzzles need?",
          "Pencil marks plus pairs, triples, the X-Wing and the XY-Wing. The XY-Wing is the one most hard puzzles in our books need."),
         ("What are pencil marks in sudoku?",
          "Small numbers written in the corner of an empty square to show which numbers could still go there. You cross them off as strategies rule them out.")]
faq_html, faq_ld = faq_block(st_qa)
body = f"""<h1>Sudoku strategies: how to solve easy, medium and hard sudoku</h1>
<p class="lead">Eight solving strategies, each shown on a big, clear example grid. Start with the first two: they solve every easy puzzle.
Every puzzle in our books can be solved with these eight, with no guessing.</p>
<div class="box"><b>Print the whole guide.</b> All eight strategies in large print, 7 pages, free.
<br><a class="btn" href="/downloads/large-print-sudoku-solving-strategies.pdf" download>Download the free strategy guide (PDF)</a></div>
<p class="toc"><b>Jump to:</b> <a href="#easy">Easy</a><a href="#medium">Medium</a><a href="#hard">Hard</a><a href="#stuck">When you're stuck</a></p>
<div class="strat">
<h2 id="easy">Easy puzzles: two strategies</h2>
<h3>1. Only one place for a number</h3><p>Every box needs a 5. Find the 5s already in the puzzle and follow their rows and columns (shaded).
They rule out two rows and one column of the top-left box, and the 8 fills another square. Only one square is left, so the 5 goes there.</p>{fig("only-place")}
<h3>2. Only one number fits</h3><p>Pick an empty square and look at its row, its column and its box (shaded). Together they already hold 1, 2, 3, 4, 5, 6, 7 and 8.
The only number missing is 9, so 9 goes in that square.</p>{fig("only-number")}
<h3>Helpful habits</h3><ul><li>Start with the number you see most often in the puzzle.</li><li>Check one number at a time across all nine boxes.</li>
<li>Use a pencil, and keep an eraser handy.</li><li>Stuck? Switch to a different number or a different box.</li></ul>
<h2 id="medium">Medium puzzles: pencil marks and pairs</h2>
<h3>Pencil marks</h3><p>Write the numbers that could go in each empty square in small print in the corner. When a strategy rules a number out, cross it off.
When only one is left, that's your answer. Fill them in one box at a time, and each time you write in an answer, erase that number from the pencil marks in its row, column and box.</p>
<h3>3. Naked pair</h3><p>Two squares in this row can only be 2 or 7 (outlined). One will be 2 and the other 7, so no other square in the row can be 2 or 7. Cross them off.</p>{fig("naked-pair", True)}
<h3>4. Hidden pair</h3><p>In this row, 3 and 6 each fit in only two squares, and they're the same two squares (outlined). Those squares must hold the 3 and the 6,
so cross off every other number in them.</p>{fig("hidden-pair", True)}
<h3>5. Pointing pair</h3><p>Pencil marks for 4 are shown. In the top-left box, the 4 in the third column rules out that column, so this box's 4 must go in the middle row,
in one of the two outlined squares. Either way, the 4 is in that row, so cross 4 off the rest of the row.</p>{fig("pointing")}
<p>It works the other way too: if, inside one row or column, a number's only spots all sit in the same box, cross that number off the rest of that box.</p>
<h2 id="hard">Hard puzzles: triples and wings</h2>
<h3>6. Naked triple</h3><p>Three squares share just three numbers between them: 2, 5 and 8 (outlined). Those three squares will use up the 2, the 5 and the 8,
so cross 2, 5 and 8 off the rest of the row. It works even when a square shows only two of the three numbers.</p>{fig("naked-triple", True)}
<p><b>Hidden triple:</b> if three numbers each fit in only the same three squares of a row, column or box, those squares must hold those three numbers. Cross off everything else in them.</p>
<h3>7. X-Wing</h3><p>Pencil marks for 7 are shown. In the 2nd row and the 7th row, 7 fits in only two squares, and they line up in the same two columns (outlined).
However the 7s fall, they use up both columns, so cross 7 off everywhere else in those two columns.</p>{fig("x-wing")}
<p><b>Swordfish:</b> the X-Wing idea with three rows and three columns. You'll rarely need it.</p>
<h3>8. XY-Wing</h3><p>Square A can only be 3 or 7. If A is 3, then B must be 9. If A is 7, then C must be 9. Either way, B or C is a 9.
Square D sees both B and C, so D can't be 9. Cross the 9 off D. Most hard puzzles in our books need this one.</p>{fig("xy-wing")}
<h2 id="stuck">When you're stuck</h2><ul><li>Go back to strategies 1 and 2. They find most numbers, even in hard puzzles.</li>
<li>Make sure every empty square has up-to-date pencil marks.</li><li>Take a break. Fresh eyes spot the next number.</li>
<li>Peek at one square in the solution, then carry on.</li></ul>
</div>
<h2>Practice with a free puzzle</h2><div class="grid">{"".join(xcard(x) for x in sd_extras)}</div>
<div class="box"><b>Want 100 at a time?</b> Every <a href="/sudoku/#series">Large Print Sudoku for Seniors</a> book starts with the strategies for its level, and every puzzle in it can be solved with them.</div>
{faq_html}{signup()}"""
write(path + "index.html", page(path, "Sudoku Strategies: How to Solve Easy to Hard Sudoku (Large Print)",
      "Eight sudoku strategies on big, clear example grids: only one place, naked and hidden pairs, X-Wing and XY-Wing. Free large-print printable guide.",
      body, image="/img/sudoku-strategies-preview.jpg", img_alt="Large print sudoku solving strategies guide, page 1", og_type="article",
      graph=[{"@type": "Article", "headline": "Sudoku strategies: how to solve easy, medium and hard sudoku", "url": url,
              "publisher": {"@id": f"{BASE}/#org"}, "dateModified": TODAY, "image": f"{BASE}/img/sudoku-strategies-preview.jpg"},
             doc_ld("Large print sudoku solving strategies guide", url, "/img/sudoku-strategies-preview.jpg", "large-print-sudoku-solving-strategies.pdf",
                    "sudoku strategies, how to solve sudoku, large print, seniors", series=False), faq_ld],
      crumbs=[("Home", "/"), ("Sudoku", "/sudoku/"), ("Strategies", None)]))

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
    return (f'<div class="card bk"><img src="/img/cover-{k}.jpg" alt="Large Print Word Search for Seniors: {E(b["name"])} by Callan Brooks" loading="lazy" width="340" height="440">'
            f'<h3>{E(b["name"])}</h3><p>{E(BOOK_BLURB[k])}</p><p>50 puzzles · 80 pages · 8.5 x 11 in</p>{amz}'
            f'<p><a href="{SHOP}/listing/{b["listing"]}">Printable PDF on Etsy</a> · <a href="/free/{SEO[k][0]}/">Free sample puzzle</a></p></div>')
body = f"""<h1>Large print word search books by Callan Brooks</h1>
<p class="lead">The <b>Big Clear Puzzle Books</b> series: 50 puzzles per book, one big puzzle per 8.5 x 11 page, 21 pt bold grid letters and 18 pt word lists,
words that never run backwards, and every answer in the back. Paperbacks on Amazon, printable PDFs on Etsy.</p>
<p><a class="btn alt" href="{AMAZON_SERIES}">The whole series on Amazon</a><a class="btn alt" href="{AMAZON_AUTHOR}">Callan Brooks author page</a></p>
<h2>Word search paperbacks</h2><div class="grid">{"".join(book_card(k) for k in ORDER)}</div>
<h2>Large print sudoku</h2><p>7 books of 100 puzzles each, Easy to Hard, with extra-large numbers and <a href="/sudoku/strategies/">illustrated solving strategies</a> at the front. Available now as printable PDFs; paperbacks are on the way.</p>
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
H_LEAD = '<p class="lead">Big, clear word searches and sudoku that are easy to see and always right. Print free samples, then get the full books on Etsy or Amazon.</p>'
H_TILES = (f'<a class="tile" href="/word-search/"><img src="/img/cover-christmas.jpg" alt="Large print word search books" width="340" height="440">'
           f'<span><b>Word Search</b>7 themed books, 50 puzzles each<br>{WS_N} free printables<em>Browse word searches →</em></span></a>'
           f'<a class="tile" href="/sudoku/"><img src="/img/cover-sudoku-1.jpg" alt="Large print sudoku books" width="340" height="440">'
           f'<span><b>Sudoku</b>7 books, Easy to Hard, 100 puzzles each<br>{len(sd_extras)} free printables<em>Browse sudoku →</em></span></a>')
H_SEASON = f'<h2 id="thanksgiving">This week: Thanksgiving</h2><div class="grid">{"".join(xcard(x) for x in seasonal)}</div>'
H_WS = (f'<h2>Free word searches</h2><div class="grid">{"".join(card(o) for o in ORDER[:6])}</div>'
        f'<p><a class="btn alt" href="/word-search/">See all {WS_N} free word searches</a></p>')
H_SD = (f'<h2>Free sudoku</h2><div class="grid">{"".join(xcard(x) for x in sd_extras[:3])}</div>'
        f'<p><a class="btn alt" href="/sudoku/">See the sudoku series</a></p>')
H_AD = ('<h2>For activity directors and memory care</h2><p>Facility print license, word search and sudoku: <a href="/activity-directors/">see the activity director page</a>, '
        'or read our guide to <a href="/dementia-friendly-printables/">dementia-friendly printables</a>.</p>')
H_WHY = ('<h2>What makes them different</h2><ul><li>One puzzle per page with extra-large bold letters and numbers (<a href="/large-print-font-size/">what counts as large print?</a>)</li>'
         '<li>Word search words read forward, down or diagonally, never backwards</li>\n<li>Solutions included for every word search and sudoku puzzle</li></ul>')
H_BOOKS = ('<a class="tile" href="/books/"><img src="/img/cover-nostalgia.jpg" alt="" width="340" height="440" data-pin-nopin="true">'
           '<span><b>Books</b>Paperbacks on Amazon, printable PDFs on Etsy.<em>All our books →</em></span></a>')
body = f"""<section class="hero"><div><h1>Free large-print puzzles for seniors</h1>{H_LEAD}
<p class="hero-cta"><a class="btn" href="/word-search/">Free word searches</a><a class="btn alt" href="/sudoku/">Free sudoku</a></p></div>
<div class="hero-art" aria-hidden="true"><img class="c1" src="/img/cover-hymns.jpg" alt="" width="340" height="440" data-pin-nopin="true"><img class="c2" src="/img/cover-sudoku-1.jpg" alt="" width="340" height="440" data-pin-nopin="true"><img class="c3" src="/img/christmas-preview.jpg" alt="" width="765" height="990" data-pin-nopin="true"></div></section>
<section class="why">{H_WHY}</section>
<div class="series">{H_TILES}{H_BOOKS}</div>
{H_SEASON}
{signup()}
{H_WS}
{H_SD}
{paperbacks}<section class="box">{H_AD}</section>"""
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
      + "/downloads/custom/*\n  X-Robots-Tag: noindex\n/downloads/packs/*\n  X-Robots-Tag: noindex\n/fonts/*\n  Cache-Control: public, max-age=31536000, immutable\n")


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
