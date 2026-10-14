#!/usr/bin/env python3
"""
Mertune Event Scraper — Commission-Eligible Events Only
Runs every 4 hours via cron to catch last-minute events.
"""

import json, re, os, urllib.request, urllib.parse, ssl
from datetime import datetime, date

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
        return r.read().decode('utf-8', errors='ignore')

def clean(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def is_future(date_str):
    if not date_str: return True
    c = date_str.split('·')[0].split('–')[0].split('-')[0].strip()
    for fmt in ['%B %d, %Y', '%b %d, %Y', '%b. %d, %Y', '%Y-%m-%d', '%B %Y']:
        try:
            return datetime.strptime(c.strip(), fmt).date() >= date.today()
        except: pass
    return True

def has_ticket(ev):
    url = ev.get('url', '')
    if not url or url == '#': return False
    ticket_domains = [
        'ticketmaster','seatgeek','stubhub','eventbrite','axs.com',
        'livenation','ticketweb','etix.com','fearticket','ticketsignup',
        'ticketspice','zentix','hauntpay','getyourguide','universe.com',
        'ncl.com','carnival.com','royalcaribbean','virginvoyages','msccruises',
        'buschgardens','universalorlando','seaworld','disneyworld',
        'mlb.com','kaseyacenter','hardrockstadium','amerantbankarena',
        'nustadium','fillmore','jointherevolution','browardcenter',
        'parkerplayhouse','arshtcenter','jlkc.com','fplsolaramphitheater',
        'thehorrorland','houseofhorrorcarnival','soundsofscreams',
        'screamageddon','sirhenryshauntedtrail','terroronthetimberfarm',
        '13thfloorjacksonville','hauntedswfl','calusanature','artinlee',
        'galaxyfrightnights','farmermikesevents','vividseats','americanarenas',
        'eventticketscenter','tonyrobbins.com','fiutickets','bluewahoos',
        'curebowl','axs.com','hsrrace','nascarracingexperience',
        'floridagators','seminoles.evenue','seatgeek','buccaneers.com',
        'fausports','ucfknights','morelifemvmt'
    ]
    return any(d in url.lower() for d in ticket_domains)

def filter_events(events):
    return [e for e in events
            if is_future(e.get('date',''))
            and has_ticket(e)
            and len(e.get('title','').strip()) > 3]

def scrape_json_ld(html, base_url=''):
    """Extract events from JSON-LD structured data."""
    events = []
    blocks = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
    for block in blocks:
        try:
            data = json.loads(block)
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get('@type') in ('Event', 'MusicEvent', 'SportsEvent', 'TheaterEvent'):
                    name = item.get('name','')
                    start = item.get('startDate','')
                    url = item.get('url', base_url)
                    if name and start:
                        try:
                            d = datetime.fromisoformat(start[:19])
                            date_str = d.strftime('%B %d, %Y · %-I:%M %p')
                        except:
                            date_str = start[:10]
                        ev = {'title': name, 'date': date_str, 'url': url or base_url}
                        img = item.get('image')
                        if isinstance(img, list): img = img[0] if img else ''
                        if isinstance(img, dict): img = img.get('url', '')
                        if isinstance(img, str) and img.startswith('http'): ev['image'] = img
                        events.append(ev)
        except: pass
    return events

def scrape_fillmore():
    events = []
    try:
        html = fetch('https://www.fillmore-miami.com/shows')
        # Try JSON-LD first
        events = scrape_json_ld(html, 'https://www.fillmore-miami.com/shows')
        # Fallback: regex on name/startDate
        if not events:
            blocks = re.findall(r'"name"\s*:\s*"([^"]+)".*?"startDate"\s*:\s*"([^"]+)".*?"url"\s*:\s*"([^"]+)"', html, re.DOTALL)
            skip = {'The Fillmore Miami Beach','The Fillmore Miami Beach at Jackie Gleason Theater','US'}
            for name, start, url in blocks[:35]:
                if name in skip or len(name) < 5: continue
                try:
                    d = datetime.fromisoformat(start[:19])
                    date_str = d.strftime('%B %d, %Y · %-I:%M %p')
                except:
                    date_str = start[:10]
                events.append({'title': name, 'date': date_str, 'url': url})
    except Exception as e:
        print(f'    fillmore error: {e}')
    return filter_events(events[:30])

def scrape_kaseya():
    events = []
    try:
        html = fetch('https://www.kaseyacenter.com/events')
        events = scrape_json_ld(html, 'https://www.kaseyacenter.com/events')
        if not events:
            # Try extracting event cards
            cards = re.findall(r'<h3[^>]*>(.*?)</h3>.*?<time[^>]*datetime="([^"]+)"', html, re.DOTALL)
            for title, dt in cards[:15]:
                title = clean(title)
                if len(title) < 3: continue
                events.append({'title': title, 'date': dt[:10], 'url': 'https://www.kaseyacenter.com/events'})
        if not events:
            # Scrape the Heat schedule page too
            html2 = fetch('https://www.kaseyacenter.com/events/miami-heat')
            events = scrape_json_ld(html2, 'https://www.kaseyacenter.com/events/miami-heat')
    except Exception as e:
        print(f'    kaseya error: {e}')
    return filter_events(events[:20])

def scrape_hardrock():
    events = []
    try:
        html = fetch('https://www.hardrockstadium.com/events/')
        events = scrape_json_ld(html, 'https://www.hardrockstadium.com/events/')
        if not events:
            blocks = re.findall(r'"name"\s*:\s*"([^"]+)".*?"startDate"\s*:\s*"([^"]+)".*?"url"\s*:\s*"([^"]+)"', html, re.DOTALL)
            for name, start, url in blocks[:15]:
                if len(name) < 3: continue
                events.append({'title': name, 'date': start[:10], 'url': url})
    except Exception as e:
        print(f'    hardrock error: {e}')
    return filter_events(events[:10])

def scrape_loandepot():
    events = []
    try:
        today = date.today()
        end = date(today.year, 12, 31)
        url = f'https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=146&startDate={today}&endDate={end}&gameType=R,P&hydrate=venue'
        data = json.loads(fetch(url))
        for day in data.get('dates', []):
            for game in day.get('games', []):
                if game.get('venue', {}).get('id') != 4169: continue
                away = game['teams']['away']['team']['name']
                gdate = game['gameDate'][:10]
                try:
                    from datetime import timezone
                    gtime = datetime.fromisoformat(game['gameDate'].replace('Z','+00:00'))
                    time_str = gtime.strftime('%-I:%M %p ET')
                except:
                    time_str = ''
                events.append({
                    'title': f'Miami Marlins vs {away}',
                    'date': f'{gdate} · {time_str}',
                    'url': f'https://www.mlb.com/gameday/{game["gamePk"]}'
                })
    except Exception as e:
        print(f'    loandepot error: {e}')
    return filter_events(events[:10])

def scrape_nustadium():
    events = []
    try:
        html = fetch('https://nustadium.com')
        events = scrape_json_ld(html, 'https://nustadium.com')
        if not events:
            blocks = re.findall(r'"name"\s*:\s*"([^"]+)".*?"startDate"\s*:\s*"([^"]+)".*?"url"\s*:\s*"([^"]+)"', html, re.DOTALL)
            for name, start, url in blocks[:10]:
                if len(name) < 3: continue
                events.append({'title': name, 'date': start[:10], 'url': url or 'https://nustadium.com'})
    except Exception as e:
        print(f'    nustadium error: {e}')
    return filter_events(events[:8])

def scrape_bayfront():
    events = []
    try:
        html = fetch('https://www.fplsolaramphitheaterbayfront.com/shows')
        events = scrape_json_ld(html, 'https://www.fplsolaramphitheaterbayfront.com/shows')
        if not events:
            blocks = re.findall(r'"name"\s*:\s*"([^"]+)".*?"startDate"\s*:\s*"([^"]+)"', html, re.DOTALL)
            skip = {'FPL Solar Amphitheater','Bayfront Park','US'}
            for name, start in blocks[:10]:
                if name in skip or len(name) < 5: continue
                events.append({'title': name, 'date': start[:10], 'url': 'https://www.fplsolaramphitheaterbayfront.com/shows'})
    except Exception as e:
        print(f'    bayfront error: {e}')
    return filter_events(events[:8])

def scrape_jlknight():
    events = []
    try:
        html = fetch('https://jlkc.com')
        events = scrape_json_ld(html, 'https://jlkc.com')
        if not events:
            # Extract from event listing
            titles = re.findall(r'<h3[^>]*class="[^"]*tribe-events-list-event-title[^"]*"[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.DOTALL)
            links = re.findall(r'href="(https://(?:jlkc\.com|ticketmaster\.com)/[^"]+)"', html)
            dates = re.findall(r'<abbr[^>]*class="[^"]*tribe-events-abbr[^"]*"[^>]*title="([^"]+)"', html)
            for i, title in enumerate(titles[:10]):
                title = clean(title)
                url = links[i] if i < len(links) else 'https://jlkc.com'
                date_str = dates[i] if i < len(dates) else ''
                if len(title) > 3:
                    events.append({'title': title, 'date': date_str, 'url': url})
    except Exception as e:
        print(f'    jlknight error: {e}')
    return filter_events(events[:10])

def scrape_revolution():
    events = []
    try:
        html = fetch('https://www.jointherevolution.net/concerts/')
        events = scrape_json_ld(html, 'https://www.jointherevolution.net/concerts/')
        if not events:
            titles = re.findall(r'class="tribe-event-url"[^>]*title="([^"]+)"', html)
            links = re.findall(r'class="tribe-event-url"[^>]*href="([^"]+)"', html)
            dates = re.findall(r'<abbr[^>]*title="([^"]+)"', html)
            for i, title in enumerate(titles[:15]):
                url = links[i] if i < len(links) else 'https://www.jointherevolution.net/concerts/'
                date_str = dates[i] if i < len(dates) else ''
                events.append({'title': title, 'date': date_str, 'url': url})
    except Exception as e:
        print(f'    revolution error: {e}')
    return filter_events(events[:12])

def scrape_broward():
    events = []
    try:
        html = fetch('https://www.browardcenter.org/events')
        events = scrape_json_ld(html, 'https://www.browardcenter.org/events')
        if not events:
            blocks = re.findall(r'"name"\s*:\s*"([^"]+)".*?"startDate"\s*:\s*"([^"]+)".*?"url"\s*:\s*"([^"]+)"', html, re.DOTALL)
            for name, start, url in blocks[:15]:
                if len(name) < 3: continue
                events.append({'title': name, 'date': start[:10], 'url': url})
    except Exception as e:
        print(f'    broward error: {e}')
    return filter_events(events[:10])

def scrape_parker():
    events = []
    try:
        html = fetch('https://www.parkerplayhouse.com/events')
        events = scrape_json_ld(html, 'https://www.parkerplayhouse.com/events')
        if not events:
            blocks = re.findall(r'"name"\s*:\s*"([^"]+)".*?"startDate"\s*:\s*"([^"]+)".*?"url"\s*:\s*"([^"]+)"', html, re.DOTALL)
            for name, start, url in blocks[:15]:
                if len(name) < 3: continue
                events.append({'title': name, 'date': start[:10], 'url': url})
    except Exception as e:
        print(f'    parker error: {e}')
    return filter_events(events[:10])

def scrape_amerant():
    events = []
    try:
        html = fetch('https://www.amerantbankarena.com/events')
        events = scrape_json_ld(html, 'https://www.amerantbankarena.com/events')
        if not events:
            blocks = re.findall(r'"name"\s*:\s*"([^"]+)".*?"startDate"\s*:\s*"([^"]+)".*?"url"\s*:\s*"([^"]+)"', html, re.DOTALL)
            for name, start, url in blocks[:15]:
                if len(name) < 3: continue
                events.append({'title': name, 'date': start[:10], 'url': url})
    except Exception as e:
        print(f'    amerant error: {e}')
    return filter_events(events[:10])

def scrape_adrienne():
    events = []
    try:
        html = fetch('https://www.arshtcenter.org')
        events = scrape_json_ld(html, 'https://www.arshtcenter.org')
        if not events:
            blocks = re.findall(r'"name"\s*:\s*"([^"]+)".*?"startDate"\s*:\s*"([^"]+)".*?"url"\s*:\s*"([^"]+)"', html, re.DOTALL)
            for name, start, url in blocks[:15]:
                if len(name) < 3 or 'arsht' in name.lower(): continue
                events.append({'title': name, 'date': start[:10], 'url': url})
    except Exception as e:
        print(f'    adrienne error: {e}')
    return filter_events(events[:10])

def main():
    print(f'🎟 Mertune Event Scraper — {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('   Scraping commission-eligible events (runs every 4 hours)...\n')

    scrapers = {
        'fillmore':   scrape_fillmore,
        'kaseya':     scrape_kaseya,
        'hardrock':   scrape_hardrock,
        'loandepot':  scrape_loandepot,
        'nustadium':  scrape_nustadium,
        'bayfront':   scrape_bayfront,
        'jlknight':   scrape_jlknight,
        'revolution': scrape_revolution,
        'broward':    scrape_broward,
        'parker':     scrape_parker,
        'amerant':    scrape_amerant,
        'adrienne':   scrape_adrienne,
    }

    result = {'venues': {}, 'generated': datetime.now().isoformat()}

    for vid, fn in scrapers.items():
        print(f'  Scraping {vid}...', end=' ', flush=True)
        try:
            evts = fn()
            result['venues'][vid] = evts
            print(f'{len(evts)} events ✅' if evts else '0 events (none found)')
        except Exception as e:
            result['venues'][vid] = []
            print(f'ERROR: {e}')

    total = sum(len(v) for v in result['venues'].values())
    print(f'\n✅ Total: {total} commission-eligible events')

    os.makedirs('/tmp/mertune-deploy', exist_ok=True)
    with open('/tmp/mertune-deploy/events.json', 'w') as f:
        json.dump(result, f, ensure_ascii=True, indent=2)

if __name__ == '__main__':
    main()
