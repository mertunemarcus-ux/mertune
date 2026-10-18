#!/usr/bin/env python3
"""
Merge Ticketmaster discovery results into app.html EVENTS.
- Matches TM venues to map venues by name keywords (multi-hall venues roll up).
- API events replace stale scraped events for matched venues; hand-curated
  non-Ticketmaster events (SeatGeek, venue sites) are kept if still upcoming.
- Never deletes a venue; unmatched venues keep their existing events.
"""
import json, re, os
from datetime import datetime, date

APP_HTML = 'public/app.html'
DISC = '/tmp/mertune-deploy/discovery.json'

# map venue id -> list of lowercase substrings that identify its TM venue name(s)
MATCH = {
    'kaseya':       ['kaseya center'],
    'hardrock':     ['hard rock stadium'],
    'amerant':      ['amerant bank arena'],
    'loandepot':    ['loandepot park'],
    'nustadium':    ['nu stadium'],
    'bayfront':     ['fpl solar amphitheater'],
    'fillmore':     ['fillmore miami beach'],
    'revolution':   ['revolution live'],
    'adrienne':     ['arsht center', 'knight concert hall', 'ziff ballet opera house', 'thomson plaza'],
    'broward':      ['broward center', 'au-rene', 'amaturo'],
    'parker':       ['wells hall at the parker', 'parker playhouse'],
    'jlknight':     ['james l knight', 'james l. knight'],
    'pitbull_stadium': ['pitbull stadium'],
    'daytona_speedway': ['daytona international speedway'],
    'fbc_mortgage': ['fbc mortgage stadium', 'acrisure bounce house'],
    'fau_stadium':  ['flagler credit union stadium', 'fau stadium'],
    'camping_world': ['camping world stadium'],
    'raymond_james': ['raymond james stadium'],
    'tiaa_bank':    ['everbank stadium', 'tiaa bank field'],
    'ben_hill':     ['ben hill griffin'],
    'doak_campbell': ['doak campbell', 'doak s. campbell'],
    'bragg_memorial': ['bragg memorial'],
    'hhn_orlando':  ['halloween horror nights'],
    'hardrock_live': ["hard rock live"],
    'kia_center': ["kia center"],
    'dr_phillips': ["dr. phillips performing arts center"],
    'house_of_blues': ["house of blues orlando"],
    'disney_world': ["walt disney world"],
    'icon_park': ["icon park"],
    'addition_arena': ["addition financial arena"],
    'plaza_live': ["plaza live - orlando"],
    'funny_bone_orl': ["funny bone comedy club - orlando"],
    'inter_co': ["inter.co stadium"],
    'straz_center': ["david a. straz center - carol morsani hall"],
    'yuengling_center': ["yuengling center"],
    'ritz_ybor': ["the ritz ybor"],
    'hardrock_tampa': ["seminole hard rock tampa event center"],
    'funny_bone_tpa': ["funny bone comedy club - tampa"],
    'tampa_theatre': ["tampa theater"],
    'mahaffey': ["mahaffey theater"],
    'jannus_live': ["jannus live"],
    'ruth_eckerd': ["ruth eckerd hall"],
    'capitol_theatre': ["bilheimer capitol theatre"],
    'baycare_sound': ["the baycare sound"],
    'kravis_center': ["kravis center - dreyfoos hall"],
    'aventura_arts': ["aventura arts & cultural center"],
    'watsco_center': ["watsco center at the university of miami"],
    'liv_miami': ["liv nightclub miami"],
    'just_the_funny': ["just the funny"],
    'miniaci': ["rose & alfred miniaci performing arts center"],
    'culture_room': ["culture room"],
    'war_memorial': ["war memorial auditorium-fl"],
    'mizner_studio': ["the studio at mizner park"],
    'coral_springs': ["coral springs center"],
    'sofi_center': ["sofi center"],
    'homestead_speedway': ["homestead miami speedway"],
    'delray_tennis': ["delray beach tennis center"],
    'banyan_live': ["the banyan live"],
    'vystar_arena': ["vystar veterans memorial arena"],
    'florida_theatre': ["florida theatre jacksonville"],
    'comedy_zone_jax': ["comedy zone - jacksonville"],
    'ponte_vedra': ["ponte vedra concert hall"],
    'tucker_center': ["donald l. tucker center"],
    'exactech_arena': ["exactech arena at the stephen c. o'connell center"],
    'hertz_arena': ["hertz arena"],
    'bb_mann': ["barbara b. mann performing arts hall"],
    'alico_arena': ["alico arena"],
    'caloosa_sound': ["caloosa sound amphitheater"],
    'artis_naples': ["hayes hall"],
    'asolo_rep': ["asolo repertory theatre"],
    'pensacola_bay': ["pensacola bay center"],
    'saenger_pcola': ["pensacola saenger theatre"],
    'vinyl_music_hall': ["vinyl music hall"],
    'peabody_daytona': ["the peabody daytona beach"],
    'ocean_center': ["ocean center"],
    'athens_theatre': ["athens theatre"],
}

def iso_future(iso):
    try: return datetime.strptime(iso, '%Y-%m-%d').date() >= date.today()
    except: return True

def text_future(ds):
    if not ds: return True
    c = ds.split('·')[0].split('–')[0].strip()
    for fmt in ['%B %d, %Y', '%Y-%m-%d', '%B %Y', '%b %d, %Y']:
        try: return datetime.strptime(c, fmt).date() >= date.today()
        except: pass
    return True

def main():
    if not os.path.exists(DISC):
        print('no discovery.json — skipping merge'); return
    disc = json.load(open(DISC))['venues']
    html = open(APP_HTML).read()
    s = html.index('var EVENTS = '); e = html.index(';', s) + 1
    events = json.loads(html[s+13:e-1])

    # bucket TM events by map venue id
    api = {}
    for v in disc.values():
        n = v['name'].lower().strip()
        for vid, keys in MATCH.items():
            if any(k in n for k in keys):
                api.setdefault(vid, []).extend(v['events'])
                break

    report = []
    for vid, evs in api.items():
        evs = [x for x in evs if x['url'] and iso_future(x['iso_date'])]
        evs.sort(key=lambda x: (x['iso_date'], x['date']))
        seen, merged = set(), []
        for x in evs:
            key = (x['title'].lower(), x['iso_date'])
            if key in seen: continue
            seen.add(key)
            ev = {'title': x['title'], 'date': x['date'], 'url': x['url']}
            if x.get('image'): ev['image'] = x['image']
            if x.get('min_price'): ev['price'] = f"From ${x['min_price']:.0f}"
            merged.append(ev)
        # keep hand-curated non-TM events still upcoming (e.g. SeatGeek, venue site)
        keep = [o for o in events.get(vid, [])
                if 'ticketmaster.com' not in o.get('url','') and text_future(o.get('date',''))
                and (o['title'].lower(), ) not in {(m['title'].lower(),) for m in merged}]
        before = len(events.get(vid, []))
        events[vid] = (merged + keep)[:40]
        report.append((vid, before, len(merged), len(keep)))

    html = html[:s] + 'var EVENTS = ' + json.dumps(events, ensure_ascii=True) + ';' + html[e:]
    open(APP_HTML, 'w').write(html)
    for vid, b, m, k in sorted(report): print(f'  {vid:18s} {b:3d} → {m:3d} TM + {k:2d} kept')
    print(f'✅ merged {len(report)} venues · total events now {sum(len(v) for v in events.values())}')

if __name__ == '__main__':
    main()
