#!/usr/bin/env python3
"""
Deploy script for Mertune.
1. Scrapes latest events from all venues
2. Filters out past events
3. Injects into app.html
4. Deploys to Vercel (permanent, no bandwidth limits)
Run nightly at 1am via cron job.
"""

import json, os, re, subprocess, sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(__file__))

APP_HTML = os.path.expanduser('~/Projects/mertune/public/app.html')
DEPLOY_DIR = '/tmp/vercel-mertune'

def filter_past_events(events_by_venue):
    """Remove all events that have already passed."""
    today = date.today()
    
    def parse_date(ds):
        if not ds: return None
        clean = ds.split('·')[0].split('–')[0].split('-')[0].strip()
        for fmt in ['%B %d, %Y', '%B %d %Y', '%B %Y']:
            try:
                return datetime.strptime(clean.strip(), fmt).date()
            except:
                pass
        return None

    cleaned = {}
    for vid, evts in events_by_venue.items():
        future = []
        for ev in evts:
            # Skip junk entries
            title = ev.get('title', '')
            if not title or len(title) < 3 or '{{' in title or '//# sourceURL' in title:
                continue
            # Keep if future or undated
            d = parse_date(ev.get('date', ''))
            if d is None or d >= today:
                ev['date'] = ev.get('date', '').split('\r')[0].strip()[:60]
                future.append(ev)
        cleaned[vid] = future
    return cleaned

# Step 1: Scrape
print(f"Step 1: Scraping events — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
try:
    from scrape_events import main as scrape
    scrape()
    with open('/tmp/mertune-deploy/events.json') as f:
        scraped = json.load(f)
    scraped_venues = scraped.get('venues', {})
    print(f"  Scraped {sum(len(v) for v in scraped_venues.values())} raw events")
except Exception as e:
    print(f"  Scraper error: {e} — using existing events")
    scraped_venues = {}

# Step 2: Load current events from app.html
print("Step 2: Loading current events...")
with open(APP_HTML) as f:
    html = f.read()

marker = 'var EVENTS = '
start = html.index(marker)
end = html.index(';', start) + 1
current_events = json.loads(html[start+len(marker):end-1])

# Merge scraped into current (scraped wins for venues it covers)
for vid, evts in scraped_venues.items():
    if evts:
        current_events[vid] = evts

# Step 3: Filter past events
print("Step 3: Filtering past events...")
clean_events = filter_past_events(current_events)
total = sum(len(v) for v in clean_events.values())
print(f"  {total} upcoming events across {len([v for v in clean_events.values() if v])} venues:")
for vid, evts in clean_events.items():
    if evts:
        print(f"    {vid}: {len(evts)} events")
    else:
        print(f"    {vid}: ⚠️ NO EVENTS — needs scraper update")

# Step 4: Inject into app.html
print("Step 4: Injecting into app.html...")
events_js = json.dumps(clean_events, ensure_ascii=True)
html = html[:start] + marker + events_js + ';' + html[end:]

# Save to source
with open(APP_HTML, 'w') as f:
    f.write(html)

# Save to deploy dir
os.makedirs(DEPLOY_DIR, exist_ok=True)
with open(f'{DEPLOY_DIR}/index.html', 'w') as f:
    f.write(html)
print("  Saved to app.html and deploy dir")

# Step 5: Deploy to Vercel
print("Step 5: Deploying to Vercel...")
result = subprocess.run(
    ['vercel', '--prod', '--yes'],
    cwd=DEPLOY_DIR,
    capture_output=True, text=True
)
print(result.stdout[-300:] if result.stdout else '')
if result.returncode != 0:
    # Retry once -- Vercel occasionally returns transient "Not authorized"
    print(f"  Deploy failed ({result.stderr[-120:].strip()}), retrying once...")
    result = subprocess.run(['vercel', '--prod', '--yes'], cwd=DEPLOY_DIR, capture_output=True, text=True)
if result.returncode == 0:
    # Point mertune-map.vercel.app at the fresh deployment
    m = re.search(r'https://vercel-mertune-[a-z0-9]+-mertune\.vercel\.app', result.stdout or '')
    if m:
        subprocess.run(['vercel', 'alias', 'set', m.group(0), 'mertune-map.vercel.app'],
                       cwd=DEPLOY_DIR, capture_output=True, text=True)
    print("✅ Deployed to https://mertune-map.vercel.app")
else:
    print(f"❌ Vercel deploy failed: {result.stderr[-200:]}")
    sys.exit(1)
