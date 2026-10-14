#!/usr/bin/env python3
"""
Mertune Discovery Scraper — Ticketmaster Discovery API
Searches by LOCATION (not by venue), so it finds every ticketed event
in Florida, including last-minute games, festivals, and venues we've
never seen before. Runs inside the GitHub Action every 4 hours.

Env: TM_API_KEY (Ticketmaster consumer key)
Output: /tmp/mertune-deploy/discovery.json
"""
import json, os, ssl, sys, time, urllib.request, urllib.parse
from datetime import datetime, date, timedelta

API_KEY = os.environ.get('TM_API_KEY', '').strip()
BASE = 'https://app.ticketmaster.com/discovery/v2/events.json'
OUT_DIR = '/tmp/mertune-deploy'

# Florida metro centers to search (lat, lng, radius miles)
REGIONS = [
    ('Miami',        25.7617, -80.1918, 40),
    ('Orlando',      28.5383, -81.3792, 40),
    ('Tampa',        27.9506, -82.4572, 40),
    ('Jacksonville', 30.3322, -81.6557, 40),
    ('Tallahassee',  30.4383, -84.2807, 40),
    ('Fort Myers',   26.6406, -81.8723, 40),
    ('West Palm',    26.7153, -80.0534, 30),
    ('Pensacola',    30.4213, -87.2169, 40),
    ('Daytona',      29.2108, -81.0228, 30),
    ('Gainesville',  29.6516, -82.3248, 30),
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mertune/1.0'})
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        return json.loads(r.read().decode('utf-8'))

def fmt_date(ev):
    d = ev.get('dates', {}).get('start', {})
    ld, lt = d.get('localDate'), d.get('localTime')
    if not ld: return ''
    try:
        dt = datetime.strptime(ld, '%Y-%m-%d')
        s = dt.strftime('%B %d, %Y')
        if lt:
            t = datetime.strptime(lt[:5], '%H:%M')
            s += ' · ' + t.strftime('%-I:%M %p')
        return s
    except Exception:
        return ld

def search_region(name, lat, lng, radius, days=120):
    start = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    end = (datetime.utcnow() + timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    events, page = [], 0
    while page < 5:  # max 5 pages x 200 = 1000 events per region
        q = urllib.parse.urlencode({
            'apikey': API_KEY, 'latlong': f'{lat},{lng}', 'radius': radius, 'unit': 'miles',
            'startDateTime': start, 'endDateTime': end, 'size': 200, 'page': page,
            'sort': 'date,asc', 'countryCode': 'US', 'stateCode': 'FL',
        })
        try:
            data = fetch(f'{BASE}?{q}')
        except Exception as e:
            print(f'    {name} page {page}: {e}')
            break
        items = data.get('_embedded', {}).get('events', [])
        if not items: break
        for ev in items:
            venues = ev.get('_embedded', {}).get('venues', [{}])
            v = venues[0] if venues else {}
            loc = v.get('location', {})
            cls = (ev.get('classifications') or [{}])[0]
            price = (ev.get('priceRanges') or [{}])[0]
            events.append({
                'tm_id': ev.get('id'),
                'title': ev.get('name', '').strip(),
                'date': fmt_date(ev),
                'iso_date': ev.get('dates', {}).get('start', {}).get('localDate', ''),
                'url': ev.get('url', ''),
                'venue_name': v.get('name', ''),
                'venue_id': v.get('id', ''),
                'address': ', '.join(x for x in [v.get('address', {}).get('line1', ''), v.get('city', {}).get('name', ''), 'FL', v.get('postalCode', '')] if x),
                'lat': float(loc['latitude']) if loc.get('latitude') else None,
                'lng': float(loc['longitude']) if loc.get('longitude') else None,
                'segment': cls.get('segment', {}).get('name', ''),
                'genre': cls.get('genre', {}).get('name', ''),
                'min_price': price.get('min'),
                'max_price': price.get('max'),
                'region': name,
            })
        total_pages = data.get('page', {}).get('totalPages', 1)
        page += 1
        if page >= total_pages: break
        time.sleep(0.25)  # TM rate limit: 5 req/sec
    return events

def main():
    if not API_KEY:
        print('❌ TM_API_KEY not set'); sys.exit(1)
    print(f'🔎 Mertune Discovery — Ticketmaster — {datetime.now():%Y-%m-%d %H:%M}')
    all_ev, seen = [], set()
    for name, lat, lng, radius in REGIONS:
        evs = search_region(name, lat, lng, radius)
        new = [e for e in evs if e['tm_id'] not in seen]
        seen.update(e['tm_id'] for e in new)
        all_ev.extend(new)
        print(f'  {name:13s} {len(evs):4d} found, {len(new):4d} new')
        time.sleep(0.3)

    # Group by venue
    by_venue = {}
    for e in all_ev:
        if not e['lat'] or not e['url']: continue
        key = e['venue_id'] or e['venue_name']
        by_venue.setdefault(key, {'name': e['venue_name'], 'address': e['address'], 'lat': e['lat'], 'lng': e['lng'], 'segment': e['segment'], 'events': []})
        by_venue[key]['events'].append(e)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(f'{OUT_DIR}/discovery.json', 'w') as f:
        json.dump({'generated': datetime.now().isoformat(), 'total': len(all_ev), 'venues': by_venue}, f, indent=1)
    print(f'\n✅ {len(all_ev)} events across {len(by_venue)} venues → {OUT_DIR}/discovery.json')

if __name__ == '__main__':
    main()
