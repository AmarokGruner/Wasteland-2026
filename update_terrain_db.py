import sqlite3
import json

# Farben-Mapping (analog zu terrain-types.js, plus Defaults für neue)
FALLBACK_COLORS = {
    'ozean': '#1a4d7a',
    'wüste': '#d4a76a',
    'grasland': '#5a8c3a',
    'gebirge': '#888888',
    'wald': '#2d5016',
    'ödland': '#3a2a1a',

    # Typische Farbwerte für die deutschen Bezeichnungen
    'brachland': '#8B7355',
    'brachhügel': '#705b42',
    'brachgebirge': '#5c4933',
    'brachfelsland': '#4f3e2a',

    'grasland': '#4CAF50',
    'grashügel': '#388E3C',
    'grasgebirge': '#2E7D32',
    'grasfelsland': '#1B5E20',

    'grünland': '#8BC34A',
    'grünhügel': '#689F38',
    'grüngebirge': '#558B2F',
    'grünfelsland': '#33691E',
    
    'weideland': '#CDDC39',
    'weidefelsland': '#AFB42B',

    'steppe': '#DCE775',
    'stepphügel': '#C0CA33',
    'steppgebirge': '#AFB42B',
    'steppfelsland': '#9E9D24',

    'savanne': '#FFEB3B',
    'savannenhügel': '#FBC02D',
    'savannengebirge': '#F57F17',
    'savannenfelsland': '#F9A825',

    'pampa': '#FFC107',
    'pampafelsland': '#FF8F00',
    'pampagebirge': '#FFB300',

    'wüste': '#FF9800',
    'eiswüste': '#B2EBF2',
    'steinwüste': '#BCAAA4',
    'sanddünen': '#FFE082',

    'ödland': '#795548',
    'ödhügel': '#6D4C41',
    'ödgebirge': '#5D4037',
    'ödfelsland': '#4E342E',

    'wald': '#1B5E20',
    'regenwald': '#004D40',
    'dschungel': '#00695C',
    'hochnebelwald': '#00796B',

    'sumpfland': '#827717',
    'tropensumpf': '#9E9D24',

    'felsgebirge': '#757575',
    'plateau': '#BDBDBD'
}

# Dateinamen Mapping aus worldmap.js
TERRAIN_FILENAME_MAP_RAW = {
    'ocean':     'Ozean',
    'grass':     'Grasland',
    'forest':    'Wald',
    'mountain':  'Grasgebirge',
    'desert':    'Wueste',
    'wasteland:': 'Oedland',
    'player':    'Grasland',

    'brachfelsland':   'Brachfelsland',
    'brachgebirge':    'Brachgebirge',
    'brachhügel':      'Brachhuegel',
    'brachland':       'Brachland',
    'dschungel':       'Dschungel',
    'eiswüste':        'Eiswueste',
    'felsgebirge':     'Felsgebirge',
    'grasfelsland':    'Grasfelsland',
    'grasgebirge':     'Grasgebirge',
    'grashügel':       'Grashuegel',
    'grasland':        'Grasland',
    'grünfelsland':    'Gruenfelsland',
    'grüngebirge':     'Gruengebirge',
    'grünhügel':       'Gruenhuegel',
    'grünland':        'Gruenland',
    'hochnebelwald':   'Hochnebelwald',
    'ozean':           'Ozean',
    'pampa':           'Pampa',
    'pampafelsland':   'Pampafelsland',
    'pampagebirge':    'Pampagebirge',
    'plateau':         'Plateau',
    'regenwald':       'Regenwald',
    'sanddünen':       'Sandduenen',
    'savanne':         'Savanne',
    'savannenfelsland':'Savannenfelsland',
    'savannengebirge': 'Savannengebirge',
    'savannenhügel':   'Savannenhuegel',
    'steppe':          'Steppe',
    'steppfelsland':   'Steppfelsland',
    'steppgebirge':    'Steppgebirge',
    'stepphügel':      'Stepphuegel',
    'sumpfland':       'Sumpfland',
    'tropensumpf':     'Tropensumpf',
    'wald':            'Wald',
    'weidefelsland':   'Weidefelsland',
    'weideland':       'Weideland',
    'wüste':           'Wueste',
    'ödfelsland':      'Oedfelsland',
    'ödgebirge':       'Oedgebirge',
    'ödhügel':         'Oedhuegel',
    'ödland':          'Oedland',
}

db = sqlite3.connect('verbrannte_zone.db')
c = db.cursor()

# Spalten hinzufügen, falls noch nicht vorhanden
columns = [x[1] for x in c.execute('PRAGMA table_info(world_terrain)').fetchall()]
if 'fallback_color' not in columns:
    c.execute('ALTER TABLE world_terrain ADD COLUMN fallback_color TEXT DEFAULT "#8B7355"')
if 'filename' not in columns:
    c.execute('ALTER TABLE world_terrain ADD COLUMN filename TEXT DEFAULT ""')

db.commit()

# Alle Terrains holen
terrains = c.execute('SELECT id, name FROM world_terrain').fetchall()

for t_id, t_name in terrains:
    key = t_name.strip().lower()
    
    # Filename extrahieren 
    filename = TERRAIN_FILENAME_MAP_RAW.get(key, '')
    if not filename:
        # Fallback aus worldmap.js logik
        filename = t_name.replace('ä', 'ae').replace('Ä', 'Ae').replace('ö', 'oe').replace('Ö', 'Oe').replace('ü', 'ue').replace('Ü', 'Ue').replace('ß', 'ss').replace(' ', '')
        
    color = FALLBACK_COLORS.get(key, '#8B7355') # Default braun/grau
    
    c.execute('UPDATE world_terrain SET fallback_color=?, filename=? WHERE id=?', (color, filename, t_id))
    print(f"Updated {t_name}: {filename}.gif / {color}")

db.commit()
db.close()
print("Done!")
