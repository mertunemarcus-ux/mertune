#!/usr/bin/env python3
"""
Event poster fetcher — pulls the official poster from each event's own page
(venue website or Ticketmaster) via og:image / twitter:image.
Priority: venue website poster > Ticketmaster API artwork.
Results cached in scripts/posters_cache.json (committed) so each 4-hour run
only fetches new events. Max FETCH_LIMIT new fetches per run.
"""
import json, re, os, ssl, html as htmlmod, urllib.request
from datetime import datetime

APP_HTML = 'public/app.html'
CACHE = 'scripts/posters_cache.json'
FETCH_LIMIT = int(os.environ.get('POSTER_FETCH_LIMIT', '80'))
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
           'Accept': 'text/html,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.5'}
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

SKIP_HOSTS = ('seatgeek.com', 'vividseats.com', 'eventticketscenter.com', 'mlb.com', 'cruise-search')
BAD_IMG = ('logo', 'placeholder', 'default', 'favicon', 'sprite', '.svg')

def fetch_og(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
        raw = r.read(400_000).decode('utf-8', errors='ignore')
    for pat in (r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image'):
        m = re.search(pat, raw, re.I)
        if m:
            img = htmlmod.unescape(m.group(1)).strip()
            if img.startswith('//'): img = 'https:' + img
            if img.startswith('http') and not any(b in img.lower() for b in BAD_IMG):
                return img
    return ''

def main():
    h = open(APP_HTML).read()
    s = h.index('var EVENTS = '); e = h.index(';', s) + 1
    events = json.loads(h[s+13:e-1])
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

    fetched = hit = 0
    for vid, evs in events.items():
        for ev in evs:
            url = ev.get('url', '')
            if not url or url == '#' or any(k in url for k in SKIP_HOSTS): continue
            if url in cache:
                if cache[url]: ev['image'] = cache[url]; hit += 1
                continue
            if fetched >= FETCH_LIMIT: continue
            fetched += 1
            try:
                img = fetch_og(url)
            except Exception:
                img = ''
            cache[url] = img
            if img: ev['image'] = img; hit += 1

    json.dump(cache, open(CACHE, 'w'), indent=0)
    h = h[:s] + 'var EVENTS = ' + json.dumps(events, ensure_ascii=True) + ';' + h[e:]
    open(APP_HTML, 'w').write(h)
    total = sum(len(v) for v in events.values())
    with_img = sum(1 for v in events.values() for x in v if x.get('image'))
    print(f'🖼  posters: fetched {fetched} new pages, {hit} site posters applied · {with_img}/{total} events have a poster')

if __name__ == '__main__':
    main()
