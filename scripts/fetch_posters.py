#!/usr/bin/env python3
"""
Event poster fetcher — real posters from the venues' own websites first,
Ticketmaster artwork as fallback (TM gives team logos for sports games).

Two sources:
 1. Venue listing pages (SITE_INDEX): scrape <img src alt="More Info for X"> /
    <img alt="X"> pairs and fuzzy-match titles to our events.
 2. Each event's own page og:image / twitter:image (cached).
Cache: scripts/posters_cache.json
"""
import json, re, os, ssl, gzip, zlib, html as htmlmod, urllib.request, difflib

APP_HTML = 'public/app.html'
CACHE = 'scripts/posters_cache.json'
FETCH_LIMIT = int(os.environ.get('POSTER_FETCH_LIMIT', '80'))
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
           'Accept': 'text/html,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.5', 'Accept-Encoding': 'gzip, deflate'}
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

# venue id -> listing pages to index for posters
SITE_INDEX = {
    'kaseya':     ['https://www.kaseyacenter.com/events', 'https://www.kaseyacenter.com/events/all'],
    'amerant':    ['https://www.amerantbankarena.com/events', 'https://www.amerantbankarena.com/events/all'],
    'hardrock':   ['https://www.hardrockstadium.com/events/'],
    'broward':    ['https://www.browardcenter.org/events', 'https://www.browardcenter.org/events/all'],
    'parker':     ['https://www.parkerplayhouse.com/events', 'https://www.parkerplayhouse.com/events/all'],
    'adrienne':   ['https://www.arshtcenter.org/tickets/'],
    'fillmore':   ['https://www.fillmore-miami.com/shows'],
    'bayfront':   ['https://www.fplsolaramphitheaterbayfront.com/shows'],
    'revolution': ['https://www.jointherevolution.net/concerts/'],
    'jlknight':   ['https://jlkc.com'],
    'nustadium':  ['https://nustadium.com'],
    'loandepot':  ['https://www.mlb.com/marlins/ballpark/events'],
    'camping_world': ['https://www.campingworldstadium.com/events'],
    'raymond_james': ['https://raymondjamesstadium.com/events/'],
    'tiaa_bank':  ['https://www.everbankstadium.com/events'],
    'daytona_speedway': ['https://www.daytonainternationalspeedway.com/events/'],
}
SKIP_HOSTS = ('seatgeek.com', 'vividseats.com', 'eventticketscenter.com', 'cruise-search')
BAD_IMG = ('logo', 'placeholder', 'default', 'favicon', 'sprite', '.svg', 'blank', 'spacer', 'pixel')

def fetch(url, limit=600_000):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
        raw = r.read(limit); enc = (r.headers.get('Content-Encoding') or '').lower()
    if enc == 'gzip' or raw[:2] == b'\x1f\x8b':
        try: raw = gzip.decompress(raw)
        except Exception: raw = zlib.decompress(raw, 16 + zlib.MAX_WBITS)
    elif enc == 'deflate':
        raw = zlib.decompress(raw)
    return raw.decode('utf-8', errors='ignore')

def absolutize(img, base):
    img = htmlmod.unescape(img.strip())
    if img.startswith('//'): return 'https:' + img
    if img.startswith('/'):
        m = re.match(r'https?://[^/]+', base); return (m.group(0) if m else '') + img
    return img

def good_img(img):
    return img.startswith('http') and not any(b in img.lower() for b in BAD_IMG)

def index_site(vid, urls):
    """Return list of (title, image) from a venue's listing pages."""
    pairs = []
    for u in urls:
        try: page = fetch(u)
        except Exception: continue
        for m in re.finditer(r'<img[^>]+>', page, re.I):
            tag = m.group(0)
            src = re.search(r'(?:data-src|data-lazy-src|src)=["\']([^"\']+)', tag, re.I)
            alt = re.search(r'alt=["\']([^"\']*)', tag, re.I)
            if not src or not alt: continue
            img = absolutize(src.group(1), u)
            title = htmlmod.unescape(alt.group(1)).strip()
            title = re.sub(r'^(more info for|more info|buy tickets for|tickets for)\s*', '', title, flags=re.I).strip()
            if len(title) < 3 or not good_img(img): continue
            pairs.append((title, img))
    return pairs

def norm(s):
    s = s.lower().replace('&', 'and')
    s = re.sub(r'\b(the|vs\.?|v\.?|at|live|tour|presents?|in concert|miami|heat)\b', ' ', s)
    return re.sub(r'[^a-z0-9 ]+', ' ', s).split()

def best_match(title, pairs):
    t = set(norm(title)); best, score = '', 0
    for pt, img in pairs:
        p = set(norm(pt))
        if not t or not p: continue
        overlap = len(t & p) / max(1, min(len(t), len(p)))
        ratio = difflib.SequenceMatcher(None, title.lower(), pt.lower()).ratio()
        s = max(overlap, ratio)
        if s > score: best, score = img, s
    return best if score >= 0.6 else ''

def fetch_og(url):
    raw = fetch(url, 400_000)
    for pat in (r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image'):
        m = re.search(pat, raw, re.I)
        if m:
            img = absolutize(m.group(1), url)
            if good_img(img): return img
    return ''

def main():
    h = open(APP_HTML).read()
    s = h.index('var EVENTS = '); e = h.index(';', s) + 1
    events = json.loads(h[s+13:e-1])
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

    # 1) venue-site poster index
    site_hits = 0
    for vid, urls in SITE_INDEX.items():
        if vid not in events: continue
        pairs = index_site(vid, urls)
        if not pairs: continue
        n = 0
        for ev in events[vid]:
            img = best_match(ev['title'], pairs)
            if img: ev['image'] = img; ev['image_src'] = 'site'; n += 1
        site_hits += n
        print(f'  {vid:16s} {len(pairs):3d} site posters indexed → {n:2d}/{len(events[vid])} events matched')

    # 2) per-event page og:image (only where we still lack a site poster)
    fetched = og_hits = 0
    for vid, evs in events.items():
        for ev in evs:
            if ev.get('image_src') == 'site': continue
            url = ev.get('url', '')
            if not url or url == '#' or any(k in url for k in SKIP_HOSTS) or 'ticketmaster.com' in url: continue
            if url in cache:
                if cache[url]: ev['image'] = cache[url]; og_hits += 1
                continue
            if fetched >= FETCH_LIMIT: continue
            fetched += 1
            try: img = fetch_og(url)
            except Exception: img = ''
            cache[url] = img
            if img: ev['image'] = img; og_hits += 1

    for evs in events.values():
        for ev in evs: ev.pop('image_src', None)
    json.dump(cache, open(CACHE, 'w'), indent=0)
    h = h[:s] + 'var EVENTS = ' + json.dumps(events, ensure_ascii=True) + ';' + h[e:]
    open(APP_HTML, 'w').write(h)
    total = sum(len(v) for v in events.values())
    with_img = sum(1 for v in events.values() for x in v if x.get('image'))
    print(f'🖼  posters: {site_hits} from venue sites, {og_hits} from event pages ({fetched} new fetches) · {with_img}/{total} events have a poster')

if __name__ == '__main__':
    main()
