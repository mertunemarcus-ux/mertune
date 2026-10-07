#!/usr/bin/env python3
"""
GitHub Actions deploy script.
Injects scraped events into app.html.
Vercel deploy is handled by the GitHub Action itself.
"""
import json, os
from datetime import datetime, date

APP_HTML = 'public/app.html'
EVENTS_JSON = '/tmp/mertune-deploy/events.json'

def is_future(ds):
    if not ds: return True
    c = ds.split('·')[0].split('–')[0].strip()
    for fmt in ['%B %d, %Y', '%Y-%m-%d', '%B %Y']:
        try:
            return datetime.strptime(c.strip(), fmt).date() >= date.today()
        except: pass
    return True

print(f"Injecting events — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Load scraped events
try:
    with open(EVENTS_JSON) as f:
        scraped = json.load(f)
    scraped_venues = scraped.get('venues', {})
    print(f"  Scraped: {sum(len(v) for v in scraped_venues.values())} events")
except Exception as e:
    print(f"  No scraped events: {e}")
    scraped_venues = {}

# Load current app.html
with open(APP_HTML) as f:
    html = f.read()

marker = 'var EVENTS = '
start = html.index(marker)
end = html.index(';', start) + 1
current = json.loads(html[start+len(marker):end-1])

# Merge scraped into current
for vid, evts in scraped_venues.items():
    if evts:
        current[vid] = [e for e in evts if is_future(e.get('date',''))]

# Filter past events from all venues
for vid in list(current.keys()):
    current[vid] = [e for e in current[vid] if is_future(e.get('date',''))]

total = sum(len(v) for v in current.values())
print(f"  Total: {total} upcoming events across {len([v for v in current.values() if v])} venues")

# Inject
events_js = json.dumps(current, ensure_ascii=True)
html = html[:start] + marker + events_js + ';' + html[end:]

with open(APP_HTML, 'w') as f:
    f.write(html)

# Also copy to vercel deploy dir
os.makedirs('/tmp/vercel-mertune', exist_ok=True)
with open('/tmp/vercel-mertune/index.html', 'w') as f:
    f.write(html)

print(f"✅ app.html updated!")
