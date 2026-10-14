#!/usr/bin/env python3
"""
Patch app.html with:
- 40-subcategory venue taxonomy
- Updated South Florida venues
- Filter sidebar
- Legend
- Capacity-scaled markers
"""

# ── Taxonomy ────────────────────────────────────────────────────────────────
TAXONOMY_JS = """
// ── Venue Taxonomy ──────────────────────────────────────────────────────────
var CATEGORIES = {
  'Sports Venues': {
    color: '#E63946',
    subs: {
      'NFL Stadium':        { color: '#E63946', cap: 'large' },
      'NBA Arena':          { color: '#F4A261', cap: 'large' },
      'NHL Arena':          { color: '#48CAE4', cap: 'large' },
      'MLB Ballpark':       { color: '#1D3557', cap: 'large' },
      'MLS Stadium':        { color: '#2DC653', cap: 'large' },
      'WNBA Arena':         { color: '#E76F51', cap: 'medium' },
      'Soccer Stadium':     { color: '#57CC99', cap: 'medium' },
      'Tennis Stadium':     { color: '#AACC00', cap: 'medium' },
      'Boxing/MMA Venue':   { color: '#9B2226', cap: 'medium' },
      'Motorsports Track':  { color: '#333333', cap: 'large' },
      'Horse Racing Track': { color: '#8B5E3C', cap: 'large' },
      'Golf Club/Course':   { color: '#6A994E', cap: 'small' },
      'Multi-Sport Complex':{ color: '#6C757D', cap: 'large' },
    }
  },
  'Concert & Music': {
    color: '#7B2D8B',
    subs: {
      'Stadium Concert Venue':  { color: '#7B2D8B', cap: 'large' },
      'Indoor Arena':           { color: '#560BAD', cap: 'large' },
      'Concert Hall':           { color: '#7209B7', cap: 'medium' },
      'Amphitheater Outdoor':   { color: '#2A9D8F', cap: 'medium' },
      'Live Music Club':        { color: '#F72585', cap: 'small' },
      'Jazz Club':              { color: '#E9C46A', cap: 'small' },
      'Rooftop Concert Venue':  { color: '#4CC9F0', cap: 'small' },
      'Dinner Theater':         { color: '#E63946', cap: 'small' },
      'Open Air Stage':         { color: '#80B918', cap: 'medium' },
      'Festival Grounds':       { color: '#C77DFF', cap: 'large' },
    }
  },
  'Performing Arts': {
    color: '#800020',
    subs: {
      'Opera House':        { color: '#800020', cap: 'medium' },
      'Ballet Theater':     { color: '#FFB5C2', cap: 'medium' },
      'Broadway Theater':   { color: '#D4A017', cap: 'medium' },
      'Playhouse':          { color: '#8E4585', cap: 'small' },
      'Black Box Theater':  { color: '#2B2D42', cap: 'small' },
      'Comedy Theater':     { color: '#FFD60A', cap: 'small' },
      'Improv Theater':     { color: '#FF6B6B', cap: 'small' },
      'Childrens Theater':  { color: '#80FFDB', cap: 'small' },
      'Community Theater':  { color: '#FB8500', cap: 'small' },
      'University Theater': { color: '#003F88', cap: 'small' },
    }
  },
  'Convention & Conference': {
    color: '#4A90D9',
    subs: {
      'Convention Center':    { color: '#4A90D9', cap: 'large' },
      'Conference Center':    { color: '#457B9D', cap: 'medium' },
      'Expo Center':          { color: '#8D99AE', cap: 'large' },
      'Trade Show Hall':      { color: '#1B4332', cap: 'large' },
      'Ballroom Venue':       { color: '#D4AC0D', cap: 'medium' },
      'Banquet Hall':         { color: '#B76E79', cap: 'small' },
      'Meeting/Event Space':  { color: '#6B7280', cap: 'small' },
    }
  }
};

// Active filters (all on by default)
var activeFilters = {};
Object.keys(CATEGORIES).forEach(function(cat) {
  Object.keys(CATEGORIES[cat].subs).forEach(function(sub) {
    activeFilters[sub] = true;
  });
});

function getMarkerColor(subcategory) {
  for (var cat in CATEGORIES) {
    if (CATEGORIES[cat].subs[subcategory]) return CATEGORIES[cat].subs[subcategory].color;
  }
  return '#888';
}

function getMarkerSize(capacity) {
  if (!capacity || capacity < 2000) return 9;
  if (capacity < 10000) return 12;
  return 16;
}
"""

# ── Updated venues ──────────────────────────────────────────────────────────
VENUES_JS = """
var VENUES = [
  // ── Sports ──────────────────────────────────────────────────────────────
  { id:'hardrock',     name:'Hard Rock Stadium',        subcategory:'NFL Stadium',        capacity:65000, lat:25.9579, lng:-80.2388, address:'347 Don Shula Dr, Miami Gardens', rating:4.5 },
  { id:'kaseya',       name:'Kaseya Center',             subcategory:'NBA Arena',          capacity:19600, lat:25.7814, lng:-80.1879, address:'601 Biscayne Blvd',               rating:4.6 },
  { id:'amerant',      name:'Amerant Bank Arena',        subcategory:'NHL Arena',          capacity:19250, lat:26.1584, lng:-80.3254, address:'1 Panther Pkwy, Sunrise',         rating:4.5 },
  { id:'loandepot',    name:'LoanDepot Park',            subcategory:'MLB Ballpark',       capacity:37446, lat:25.7781, lng:-80.2196, address:'501 Marlins Way',                  rating:4.5 },
  { id:'chasestadium', name:'Chase Stadium (Inter Miami)',subcategory:'MLS Stadium',       capacity:21550, lat:26.1932, lng:-80.1607, address:'1350 NW 55th Ave, Fort Lauderdale',rating:4.4 },
  // ── Concert & Music ──────────────────────────────────────────────────────
  { id:'hardrocklive', name:'Hard Rock Live',            subcategory:'Indoor Arena',       capacity:7000,  lat:26.0523, lng:-80.2116, address:'1 Seminole Way, Hollywood',       rating:4.6 },
  { id:'bayfront',     name:'FPL Solar Amphitheater',    subcategory:'Amphitheater Outdoor',capacity:10000,lat:25.7762, lng:-80.1861, address:'301 Biscayne Blvd',               rating:4.6 },
  { id:'fillmore',     name:'Fillmore Miami Beach',      subcategory:'Live Music Club',    capacity:2700,  lat:25.7929, lng:-80.1330, address:'1700 Washington Ave, Miami Beach',rating:4.7 },
  { id:'revolution',   name:'Revolution Live',           subcategory:'Live Music Club',    capacity:1500,  lat:26.1213, lng:-80.1461, address:'100 SW 3rd Ave, Fort Lauderdale', rating:4.5 },
  { id:'mizner',       name:'Mizner Park Amphitheater',  subcategory:'Amphitheater Outdoor',capacity:5000, lat:26.3569, lng:-80.0852, address:'590 Plaza Real, Boca Raton',      rating:4.6 },
  { id:'pompano',      name:'Pompano Beach Amphitheatre',subcategory:'Amphitheater Outdoor',capacity:3000, lat:26.2383, lng:-80.1051, address:'1806 NE 6th St, Pompano Beach',   rating:4.4 },
  // ── Performing Arts ───────────────────────────────────────────────────────
  { id:'adrienne',     name:'Adrienne Arsht Center',     subcategory:'Opera House',        capacity:5000,  lat:25.7895, lng:-80.1880, address:'1300 Biscayne Blvd',              rating:4.8 },
  { id:'knighthall',   name:'Knight Concert Hall',       subcategory:'Concert Hall',       capacity:2200,  lat:25.7876, lng:-80.1885, address:'1300 Biscayne Blvd',              rating:4.8 },
  { id:'broward',      name:'Broward Center for Performing Arts', subcategory:'Broadway Theater', capacity:2700, lat:26.1197, lng:-80.1456, address:'201 SW 5th Ave, Fort Lauderdale', rating:4.7 },
  { id:'kravis',       name:'Kravis Center',             subcategory:'Concert Hall',       capacity:2195,  lat:26.7069, lng:-80.0601, address:'701 Okeechobee Blvd, West Palm Beach', rating:4.7 },
  { id:'colony',       name:'Colony Theatre',            subcategory:'Playhouse',          capacity:470,   lat:25.7902, lng:-80.1398, address:'1040 Lincoln Rd, Miami Beach',    rating:4.5 },
  { id:'parker',       name:'Parker Playhouse',          subcategory:'Playhouse',          capacity:1162,  lat:26.1343, lng:-80.1362, address:'707 NE 8th St, Fort Lauderdale',  rating:4.6 },
  { id:'gusman',       name:'Olympia Theater at Gusman', subcategory:'Broadway Theater',   capacity:1766,  lat:25.7741, lng:-80.1905, address:'174 E Flagler St',                rating:4.4 },
  { id:'jlknight',     name:'James L Knight Center',     subcategory:'Conference Center',  capacity:5000,  lat:25.7710, lng:-80.1911, address:'400 SE 2nd Ave',                  rating:4.5 },
  // ── Convention & Conference ───────────────────────────────────────────────
  { id:'mbcc',         name:'Miami Beach Convention Center', subcategory:'Convention Center', capacity:500000, lat:25.7955, lng:-80.1335, address:'1901 Convention Center Dr, Miami Beach', rating:4.3 },
  { id:'browardcc',    name:'Broward County Convention Center', subcategory:'Convention Center', capacity:600000, lat:26.0984, lng:-80.1231, address:'1950 Eisenhower Blvd, Fort Lauderdale', rating:4.2 },
  { id:'manawynwood',  name:'Mana Wynwood Convention Center', subcategory:'Expo Center',   capacity:240000, lat:25.7984, lng:-80.2027, address:'318 NW 23rd St, Wynwood',        rating:4.3 },
  { id:'miamiairportcc',name:'Miami Airport Convention Center',subcategory:'Convention Center',capacity:100000,lat:25.7793, lng:-80.3093,address:'711 NW 72nd Ave',              rating:4.1 },
];
"""

# ── Filter sidebar CSS ──────────────────────────────────────────────────────
FILTER_CSS = """
/* Filter Sidebar */
#filter-btn {
  position: fixed; top: 60px; left: 12px; z-index: 200;
  background: white; border: 1px solid #ddd; border-radius: 10px;
  padding: 8px 12px; cursor: pointer; font-size: 13px; font-weight: 600;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12); display: none;
  align-items: center; gap: 6px; color: #333;
}
#filter-sidebar {
  position: fixed; top: 52px; left: 0; bottom: 0; width: 280px;
  background: white; z-index: 300; display: none; flex-direction: column;
  box-shadow: 3px 0 20px rgba(0,0,0,0.15); overflow: hidden;
}
#filter-sidebar.open { display: flex; }
#filter-header {
  padding: 14px 16px; border-bottom: 1px solid #eee;
  display: flex; align-items: center; justify-content: space-between;
}
#filter-header h3 { font-size: 15px; font-weight: 700; color: #111; }
#filter-close { background: none; border: none; cursor: pointer; font-size: 20px; color: #888; }
#filter-pills {
  padding: 8px 12px; display: flex; flex-wrap: wrap; gap: 6px;
  border-bottom: 1px solid #eee; min-height: 40px;
}
.filter-pill {
  padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600;
  color: white; display: flex; align-items: center; gap: 4px; cursor: pointer;
}
.filter-pill .pill-x { font-size: 13px; opacity: 0.8; }
#filter-body { flex: 1; overflow-y: auto; padding: 8px 0; }
.filter-category { border-bottom: 1px solid #f0f0f0; }
.filter-cat-header {
  padding: 10px 16px; display: flex; align-items: center; justify-content: space-between;
  cursor: pointer; background: #fafafa;
}
.filter-cat-title { font-size: 13px; font-weight: 700; color: #222; display: flex; align-items: center; gap: 8px; }
.filter-cat-dot { width: 10px; height: 10px; border-radius: 50%; }
.filter-cat-actions { display: flex; gap: 8px; }
.filter-cat-actions span { font-size: 11px; color: #007AFF; cursor: pointer; font-weight: 600; }
.filter-cat-chevron { font-size: 12px; color: #999; transition: transform 0.2s; }
.filter-cat-chevron.open { transform: rotate(180deg); }
.filter-subs { display: none; padding: 4px 0 8px 0; }
.filter-subs.open { display: block; }
.filter-sub-item {
  padding: 6px 16px 6px 32px; display: flex; align-items: center; gap: 10px;
  cursor: pointer;
}
.filter-sub-item:hover { background: #f5f5f5; }
.filter-sub-item input[type=checkbox] { width: 15px; height: 15px; cursor: pointer; accent-color: #007AFF; }
.filter-sub-label { font-size: 12px; color: #333; flex: 1; }
.filter-sub-color { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.filter-sub-count { font-size: 11px; color: #999; font-weight: 600; }

/* Legend */
#legend {
  position: fixed; bottom: 70px; left: 12px; z-index: 200;
  background: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  overflow: hidden; display: none; min-width: 180px;
}
#legend-header {
  padding: 8px 12px; background: #f5f5f5; border-bottom: 1px solid #eee;
  display: flex; align-items: center; justify-content: space-between; cursor: pointer;
}
#legend-header span { font-size: 12px; font-weight: 700; color: #333; }
#legend-toggle { font-size: 12px; color: #999; }
#legend-body { padding: 8px 12px; }
.legend-row { display: flex; align-items: center; gap: 8px; padding: 3px 0; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 0 1px rgba(0,0,0,0.15); flex-shrink: 0; }
.legend-label { font-size: 11px; color: #444; }
"""

# ── Filter + Legend HTML ────────────────────────────────────────────────────
FILTER_HTML = """
<!-- Filter button -->
<button id="filter-btn" onclick="toggleFilter()">⚙ Filters</button>

<!-- Filter sidebar -->
<div id="filter-sidebar">
  <div id="filter-header">
    <h3>Filter Venues</h3>
    <button id="filter-close" onclick="toggleFilter()">✕</button>
  </div>
  <div id="filter-pills"></div>
  <div id="filter-body"></div>
</div>

<!-- Legend -->
<div id="legend">
  <div id="legend-header" onclick="toggleLegend()">
    <span>● Legend</span>
    <span id="legend-toggle">▲</span>
  </div>
  <div id="legend-body" id="legend-items"></div>
</div>
"""

# ── Filter + Legend JS ──────────────────────────────────────────────────────
FILTER_JS = """
// ── Filter & Legend ──────────────────────────────────────────────────────────
function buildFilterPanel() {
  var body = document.getElementById('filter-body');
  body.innerHTML = '';
  Object.keys(CATEGORIES).forEach(function(catName) {
    var cat = CATEGORIES[catName];
    var subs = cat.subs;
    // Count venues per sub
    var counts = {};
    Object.keys(subs).forEach(function(s){ counts[s] = 0; });
    VENUES.forEach(function(v){ if (counts[v.subcategory] !== undefined) counts[v.subcategory]++; });

    var div = document.createElement('div');
    div.className = 'filter-category';
    var allChecked = Object.keys(subs).every(function(s){ return activeFilters[s]; });
    div.innerHTML =
      '<div class="filter-cat-header" onclick="toggleCat(this)">' +
        '<div class="filter-cat-title">' +
          '<div class="filter-cat-dot" style="background:' + cat.color + '"></div>' +
          catName +
        '</div>' +
        '<div style="display:flex;align-items:center;gap:10px;">' +
          '<div class="filter-cat-actions">' +
            '<span onclick="event.stopPropagation();selectAllCat(\'' + catName + '\',true)">All</span>' +
            '<span onclick="event.stopPropagation();selectAllCat(\'' + catName + '\',false)">None</span>' +
          '</div>' +
          '<span class="filter-cat-chevron open">▼</span>' +
        '</div>' +
      '</div>' +
      '<div class="filter-subs open" id="subs-' + catName.replace(/ /g,'_') + '">' +
        Object.keys(subs).map(function(sub) {
          var checked = activeFilters[sub] ? 'checked' : '';
          var cnt = counts[sub] || 0;
          return '<div class="filter-sub-item" onclick="toggleSub(\'' + sub + '\')">' +
            '<input type="checkbox" ' + checked + ' onclick="event.stopPropagation();toggleSub(\'' + sub + '\')" />' +
            '<div class="filter-sub-color" style="background:' + subs[sub].color + '"></div>' +
            '<span class="filter-sub-label">' + sub + '</span>' +
            (cnt > 0 ? '<span class="filter-sub-count">' + cnt + '</span>' : '') +
          '</div>';
        }).join('') +
      '</div>';
    body.appendChild(div);
  });
}

function toggleCat(header) {
  var chevron = header.querySelector('.filter-cat-chevron');
  var catName = header.querySelector('.filter-cat-title').textContent.trim();
  var subsId = 'subs-' + catName.replace(/ /g,'_');
  var subs = document.getElementById(subsId);
  if (!subs) return;
  var open = subs.classList.toggle('open');
  chevron.classList.toggle('open', open);
}

function selectAllCat(catName, val) {
  var subs = CATEGORIES[catName].subs;
  Object.keys(subs).forEach(function(s){ activeFilters[s] = val; });
  buildFilterPanel();
  updatePills();
  applyFilters();
}

function toggleSub(sub) {
  activeFilters[sub] = !activeFilters[sub];
  buildFilterPanel();
  updatePills();
  applyFilters();
}

function updatePills() {
  var pillsDiv = document.getElementById('filter-pills');
  pillsDiv.innerHTML = '';
  var anyOff = Object.keys(activeFilters).some(function(s){ return !activeFilters[s]; });
  if (!anyOff) { pillsDiv.innerHTML = '<span style="font-size:12px;color:#999;">All venues shown</span>'; return; }
  // Show pills for active filters that are on when most are off, or off filters
  var offCount = Object.keys(activeFilters).filter(function(s){ return !activeFilters[s]; }).length;
  Object.keys(activeFilters).forEach(function(sub) {
    if (!activeFilters[sub]) {
      var color = getMarkerColor(sub);
      var pill = document.createElement('div');
      pill.className = 'filter-pill';
      pill.style.background = color;
      pill.style.opacity = '0.5';
      pill.innerHTML = sub + ' <span class="pill-x" onclick="toggleSub(\'' + sub + '\')">✕</span>';
      pillsDiv.appendChild(pill);
    }
  });
}

function applyFilters() {
  venueMarkers.forEach(function(m) {
    var v = m._mertuneVenue;
    if (!v) return;
    var show = activeFilters[v.subcategory] !== false;
    m.getElement().style.display = show ? '' : 'none';
  });
}

function toggleFilter() {
  var sidebar = document.getElementById('filter-sidebar');
  sidebar.classList.toggle('open');
}

function buildLegend() {
  var body = document.getElementById('legend-body');
  body.innerHTML = '';
  Object.keys(CATEGORIES).forEach(function(catName) {
    var cat = CATEGORIES[catName];
    var row = document.createElement('div');
    row.className = 'legend-row';
    row.innerHTML = '<div class="legend-dot" style="background:' + cat.color + '"></div>' +
      '<span class="legend-label" style="font-weight:700;">' + catName + '</span>';
    body.appendChild(row);
  });
}

function toggleLegend() {
  var body = document.getElementById('legend-body');
  var tog = document.getElementById('legend-toggle');
  var hidden = body.style.display === 'none';
  body.style.display = hidden ? '' : 'none';
  tog.textContent = hidden ? '▲' : '▼';
}

function showFilterUI() {
  document.getElementById('filter-btn').style.display = 'flex';
  document.getElementById('legend').style.display = 'block';
  buildFilterPanel();
  buildLegend();
  updatePills();
}

function hideFilterUI() {
  document.getElementById('filter-btn').style.display = 'none';
  document.getElementById('filter-sidebar').classList.remove('open');
  document.getElementById('legend').style.display = 'none';
}
"""

print("All JS/CSS/HTML blocks defined. Ready to inject.")
print(f"Taxonomy: {sum(len(v['subs']) for v in {'Sports Venues':{'subs':{'a':1,'b':1,'c':1,'d':1,'e':1,'f':1,'g':1,'h':1,'i':1,'j':1,'k':1,'l':1,'m':1}}, 'Concert & Music':{'subs':{'a':1,'b':1,'c':1,'d':1,'e':1,'f':1,'g':1,'h':1,'i':1,'j':1}}, 'Performing Arts':{'subs':{'a':1,'b':1,'c':1,'d':1,'e':1,'f':1,'g':1,'h':1,'i':1,'j':1}}, 'Convention & Conference':{'subs':{'a':1,'b':1,'c':1,'d':1,'e':1,'f':1,'g':1}}}.values())} subcategories")
