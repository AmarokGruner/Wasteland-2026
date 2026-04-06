// Entity Configuration für Admin-CRUD-Operationen
// Extrahiert aus admin.html für bessere Wartbarkeit

export const ENTITY_CONFIG = {
    ressourcen: {
        label: 'Rohstoff',
        endpoint: 'rohstoffe',
        fields: [
            { name: 'name', label: 'Name', type: 'text', required: true },
            { name: 'typ', label: 'Typ', type: 'select', options: ['Baurohstoff', 'Industriegut', 'Nahrung', 'Getränk', 'Verbrauchsgut', 'Genussgut', 'Tier', 'Waffentyp', 'Transport'] },
            { name: 'produktionswert', label: 'Produktionswert', type: 'number' },
            { name: 'platz_land', label: 'Platz Land', type: 'number' },
            { name: 'platz_wasser', label: 'Platz Wasser', type: 'number' },
            { name: 'platz_luft', label: 'Platz Luft', type: 'number' },
            { name: 'beschreibung', label: 'Beschreibung', type: 'textarea' },
        ]
    },
    vorkommen: {
        label: 'Vorkommen',
        endpoint: 'vorkommen',
        fields: [
            { name: 'name', label: 'Name', type: 'text', required: true },
            { name: 'typ', label: 'Typ', type: 'select', options: ['geologisch', 'Oberfläche', 'unt. Seen'] },
            { name: 'tech', label: 'Tech-Level', type: 'number' },
            { name: 'suchkosten', label: 'Suchkosten (MIPS)', type: 'number' },
            { name: 'beschreibung', label: 'Beschreibung', type: 'textarea' },
            { name: 'findwahrscheinlichkeit', label: 'Fundwahrsch.', type: 'dynamic-list', listType: 'terrain-percent' },
        ]
    },
    gebaeude_felder: {
        label: 'Gebäude-Feld',
        endpoint: 'gebaeude_felder',
        fields: [
            { name: 'id', label: 'ID', type: 'text', readonly: true },
            { name: 'name', label: 'Name', type: 'text', required: true },
            { name: 'beschreibung', label: 'Beschreibung', type: 'textarea' },
            { name: 'groesse_px', label: 'Größe (px)', type: 'number' },
            { name: 'ist_baubar', label: 'Baubar', type: 'select', options: [{ v: '1', label: 'Ja' }, { v: '0', label: 'Nein' }] },
            { name: 'farbe_leer', label: 'Farbe (leer)', type: 'color' },
        ]
    },
    terrain: {
        label: 'Terrain',
        endpoint: 'terrain',
        fields: [
            { name: 'id', label: 'ID', type: 'number', readonly: true },
            { name: 'name', label: 'Name', type: 'text', required: true },
            { name: 'startgebiet', label: 'Startgebiet', type: 'select', options: [{ v: 1, label: 'Ja' }, { v: 0, label: 'Nein' }] },
            { name: 'playable', label: 'Spielbar', type: 'select', options: [{ v: 1, label: 'Ja' }, { v: 0, label: 'Nein' }] },
            { name: 'color', label: 'Farbe (Hex)', type: 'color' },
            { name: 'icon', label: 'Icon (Emoji)', type: 'text' },
            { name: 'regen_pct', label: 'Regen %', type: 'number' },
            { name: 'aufwertungen_json', label: 'Aufwertungen', type: 'dynamic-list', listType: 'terrain-list' },
            { name: 'abwertungen_json', label: 'Abwertungen', type: 'dynamic-list', listType: 'terrain-list' },
            { name: 'beschreibung', label: 'Beschreibung', type: 'textarea' },
            { name: 'bild_url', label: 'Bild URL', type: 'text' },
            { name: 'gebaeude_effektivitaet_json', label: 'Gebäude-Eff.', type: 'dynamic-list', listType: 'building-percent' },
        ]
    },
    artikel: {
        label: 'Artikel',
        endpoint: 'artikel',
        fields: [
            { name: 'name', label: 'Name', type: 'text', required: true },
            { name: 'spezies', label: 'Spezies', type: 'text' },
            { name: 'einheittext', label: 'Einheittext', type: 'text' },
            { name: 'modultyp', label: 'Modultyp', type: 'text' },
            { name: 'zugehoerig', label: 'Zugehörig', type: 'text' },
            { name: 'bautyp', label: 'Bautyp', type: 'text' },
            { name: 'produktionspunkte', label: 'Produktionspunkte', type: 'number' },
            { name: 'rohstoffbedarf', label: 'Rohstoffbedarf', type: 'json' },
            { name: 'modulgroesse', label: 'Modulgröße', type: 'number' },
            { name: 'auswirkung_einheitenwerte', label: 'Einheitenwerte-Effekt', type: 'json' },
            { name: 'transportkapazitaet', label: 'Transportkapazität', type: 'json' },
            { name: 'platzbedarf', label: 'Platzbedarf', type: 'json' },
            { name: 'beschreibung', label: 'Beschreibung', type: 'textarea' },
            { name: 'kategorie', label: 'Kategorie', type: 'text' },
            { name: 'preis_mips', label: 'Preis (MIPS)', type: 'number' },
            { name: 'preis_muenzen', label: 'Preis (Münzen)', type: 'number' },
            { name: 'gewicht', label: 'Gewicht', type: 'number' },
            { name: 'haltbarkeit', label: 'Haltbarkeit', type: 'number' },
        ]
    },
    einheiten: {
        label: 'Einheiten-Typ',
        endpoint: 'einheiten',
        fields: [
            { name: 'name', label: 'Name', type: 'text', required: true },
            { name: 'kategorie', label: 'Kategorie', type: 'text' },
            { name: 'kosten_mips', label: 'Kosten (MIPS)', type: 'number' },
            { name: 'kosten_muenzen', label: 'Kosten (Münzen)', type: 'number' },
            { name: 'bevoelkerung_count', label: 'Bevölkerung', type: 'number' },
            { name: 'bewaffnung', label: 'Bewaffnung', type: 'text' },
            { name: 'transport_kapazitaet', label: 'Transport-Kapazität', type: 'number' },
            { name: 'geschwindigkeit', label: 'Geschwindigkeit', type: 'number' },
            { name: 'spezies', label: 'Spezies', type: 'text' },
            { name: 'einheitenklasse', label: 'Klasse', type: 'text' },
            { name: 'fortbewegung', label: 'Fortbewegung', type: 'select', options: ['Boden', 'Luft', 'See', 'Untersee'] },
            { name: 'nahkampf_staerke', label: 'Nahkampf-Stärke', type: 'number' },
        ]
    },
    lebewesen: {
        label: 'Lebewesen',
        endpoint: 'lebewesen',
        fields: [
            { name: 'name', label: 'Name', type: 'text', required: true },
            { name: 'typ', label: 'Typ', type: 'text' },
            { name: 'staerke', label: 'Stärke', type: 'number' },
            { name: 'gesundheit', label: 'Gesundheit', type: 'number' },
            { name: 'bevoelkerung_kosten', label: 'Bevölk.-Kosten', type: 'number' },
            { name: 'beschreibung', label: 'Beschreibung', type: 'textarea' },
        ]
    },
    regierungsformen: {
        label: 'Regierungsform',
        endpoint: 'regierungsformen',
        fields: [
            { name: 'name', label: 'Name', type: 'text', required: true },
            { name: 'formtyp', label: 'Formtyp', type: 'text' },
            { name: 'techlevel', label: 'Techlevel', type: 'number' },
            { name: 'ausbauwert_regierungssitz', label: 'erf. Ausbau Regierungssitz', type: 'number' },
            { name: 'kulturverbreitung', label: 'Kulturverbreitung (Faktor)', type: 'number', step: 0.01 },
            { name: 'grundmoral', label: 'Grundmoral', type: 'number' },
            { name: 'forschungsfortschritt', label: 'Forschungsfortschritt (Faktor)', type: 'number', step: 0.01 },
            { name: 'produktivitaet', label: 'Produktivität (Faktor)', type: 'number', step: 0.01 },
            { name: 'wachstum', label: 'Wachstum (Faktor)', type: 'number', step: 0.01 },
            { name: 'finanzen', label: 'Finanzen (Faktor)', type: 'number', step: 0.01 },
            { name: 'sicherheit', label: 'Innere Sicherheit (Faktor)', type: 'number', step: 0.01 },
            { name: 'moralmalus_armee_aussen', label: 'Moralmalus Armee außerhalb', type: 'number' },
            { name: 'entfernungsmalus', label: 'Entfernungsmalus (Faktor)', type: 'number', step: 0.01 },
            { name: 'lebensmittelbedarf', label: 'Lebensmittelbedarf (Faktor)', type: 'number', step: 0.01 },
            { name: 'verbrauchsgutbedarf', label: 'Verbrauchsgutbedarf (Faktor)', type: 'number', step: 0.01 },
            { name: 'streikbereitschaft', label: 'Streikbereitschaft (Faktor)', type: 'number', step: 0.01 },
            { name: 'auswanderbereitschaft', label: 'Auswanderbereitschaft (Faktor)', type: 'number', step: 0.01 },
            { name: 'milizen', label: 'Milizen (Faktor)', type: 'number', step: 0.01 },
            { name: 'fremdkultur_verlust', label: 'An Fremdkultur verlieren', type: 'select', options: [{ val: 0, lab: 'Nein' }, { val: 1, lab: 'Ja' }] },
            { name: 'aufstand', label: 'Aufstand möglich', type: 'select', options: [{ val: 0, lab: 'Nein' }, { val: 1, lab: 'Ja' }] },
            { name: 'krieg_moeglich', label: 'Kann Kriege beginnen', type: 'select', options: [{ val: 0, lab: 'Nein' }, { val: 1, lab: 'Ja' }] },
            { name: 'provinzanzahl_bis_malus', label: 'Anzahl Provinzen bis Malus', type: 'number' },
            { name: 'malus_beschreibung', label: 'Malus-Beschreibung', type: 'text' },
            { name: 'beschreibung', label: 'Beschreibung', type: 'textarea' },
            { name: 'boni', label: 'Boni (JSON)', type: 'json' },
            { name: 'voraussetzungen', label: 'Voraussetzungen (JSON)', type: 'json' },
        ]
    },
    spieler: {
        label: 'Spieler',
        endpoint: 'players',
        fields: [
            { name: 'id', label: 'ID', type: 'number', readonly: true },
            { name: 'username', label: 'Username', type: 'text', readonly: true },
            { name: 'mips', label: 'MIPS', type: 'number' },
            { name: 'muenzen', label: 'Münzen', type: 'number' },
        ]
    }
};
