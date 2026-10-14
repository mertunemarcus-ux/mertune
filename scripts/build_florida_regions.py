#!/usr/bin/env python3
"""
Build Florida Voronoi regions by grouping counties to nearest city.
Uses Florida county GeoJSON from a public source.
Outputs a clean GeoJSON with 7 regions, each a union of counties.
"""
import json, urllib.request, math

HEADERS = {'User-Agent': 'Mertune/1.0'}

CITIES = {
    'jacksonville': {'name': 'Jacksonville', 'lat': 30.3322, 'lng': -81.6557, 'color': '#E91E8C', 'live': False},
    'tallahassee':  {'name': 'Tallahassee',  'lat': 30.4518, 'lng': -84.2807, 'color': '#2196F3', 'live': False},
    'tampa':        {'name': 'Tampa',         'lat': 27.9506, 'lng': -82.4572, 'color': '#00BCD4', 'live': False},
    'orlando':      {'name': 'Orlando',       'lat': 28.5383, 'lng': -81.3792, 'color': '#4CAF50', 'live': False},
    'westpalm':     {'name': 'West Palm Beach','lat': 26.7153, 'lng': -80.0534, 'color': '#9C27B0', 'live': False},
    'fortmyers':    {'name': 'Fort Myers',    'lat': 26.6406, 'lng': -81.8723, 'color': '#FF9800', 'live': False},
    'miami':        {'name': 'Miami',         'lat': 25.7617, 'lng': -80.1918, 'color': '#FF3B30', 'live': True},
}

def dist(lat1, lng1, lat2, lng2):
    return math.sqrt((lat1-lat2)**2 + (lng1-lng2)**2)

def centroid(geom):
    coords = []
    if geom['type'] == 'Polygon':
        coords = geom['coordinates'][0]
    elif geom['type'] == 'MultiPolygon':
        coords = geom['coordinates'][0][0]
    if not coords:
        return 0, 0
    lats = [c[1] for c in coords]
    lngs = [c[0] for c in coords]
    return sum(lats)/len(lats), sum(lngs)/len(lngs)

def nearest_city(lat, lng):
    best, best_d = None, float('inf')
    for cid, c in CITIES.items():
        d = dist(lat, lng, c['lat'], c['lng'])
        if d < best_d:
            best_d = d
            best = cid
    return best

# Fetch Florida counties GeoJSON
url = 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'
print('Fetching Florida counties...')
req = urllib.request.Request(url, headers=HEADERS)
with urllib.request.urlopen(req, timeout=30) as r:
    all_counties = json.loads(r.read())

# Filter Florida (FIPS starts with 12)
fl_counties = [f for f in all_counties['features'] if f['id'].startswith('12')]
print(f'Found {len(fl_counties)} Florida counties')

# Assign each county to nearest city
groups = {cid: [] for cid in CITIES}
for county in fl_counties:
    lat, lng = centroid(county['geometry'])
    cid = nearest_city(lat, lng)
    groups[cid].append(county)
    print(f'  {county["properties"].get("NAME", county["id"])} -> {cid}')

# Build output features (keep individual counties per group, merged visually)
features = []
for cid, counties in groups.items():
    if not counties:
        continue
    city = CITIES[cid]
    # Use a GeometryCollection or MultiPolygon of all county polygons
    all_polys = []
    for c in counties:
        geom = c['geometry']
        if geom['type'] == 'Polygon':
            all_polys.append(geom['coordinates'])
        elif geom['type'] == 'MultiPolygon':
            all_polys.extend(geom['coordinates'])
    
    features.append({
        'type': 'Feature',
        'properties': {
            'id': cid,
            'name': city['name'],
            'live': city['live'],
            'color': city['color']
        },
        'geometry': {
            'type': 'MultiPolygon',
            'coordinates': all_polys
        }
    })

result = {'type': 'FeatureCollection', 'features': features}

# Save
out = '/tmp/florida_regions.json'
with open(out, 'w') as f:
    json.dump(result, f)
print(f'\nSaved to {out} ({len(features)} regions)')
for f in features:
    p = f['properties']
    print(f"  {p['name']}: {len(groups[p['id']])} counties")
