// buildings-data.js
// Verbrannte Zone – Gebäude-Client
// Lädt Daten dynamisch vom API-Endpoint GET /gebaeude
// Fallback: statischer Cache für Offline-Betrieb
// Stand: 2026-02-23 | Version: 2.0

const BuildingsAPI = (() => {

  // Interner Cache – wird beim ersten Aufruf befüllt
  let _cache = null;
  const API_URL = "/world/buildings";

  // --------------------------------------------------------
  // Hauptfunktion: Datenbank laden (einmalig, dann gecacht)
  // --------------------------------------------------------
  async function load() {
    if (_cache) return _cache;
    try {
      const response = await fetch(API_URL);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      _cache = await response.json();
      console.log(`✅ BuildingsAPI: ${_cache.length} Gebäude geladen`);
    } catch (err) {
      console.warn("⚠️ BuildingsAPI: API nicht erreichbar, nutze statischen Fallback", err);
      _cache = BUILDINGS_FALLBACK;
    }
    return _cache;
  }

  // --------------------------------------------------------
  // Hilfsfunktionen (alle async, nutzen internen Cache)
  // --------------------------------------------------------

  async function getAll() {
    return await load();
  }

  async function getById(id) {
    const db = await load();
    return db.find(b => b.id === id) || null;
  }

  async function getByCategory(kategorie) {
    const db = await load();
    return db.filter(b => b.kategorie.toLowerCase() === kategorie.toLowerCase());
  }

  async function getBuildable() {
    const db = await load();
    return db.filter(b => b.baubar === true);
  }

  async function getEfficiency(buildingId, terrain) {
    const building = await getById(buildingId);
    if (!building) return 0;
    for (const [pct, terrains] of Object.entries(building.terrain_effektivitaet)) {
      if (terrains.includes(terrain)) return parseInt(pct);
    }
    return 0;
  }

  async function getForTerrain(terrain, minEfficiency = 100) {
    const db = await load();
    const result = [];
    for (const b of db) {
      const eff = await getEfficiency(b.id, terrain);
      if (eff >= minEfficiency) result.push({ ...b, efficiency: eff });
    }
    return result.sort((a, b) => b.efficiency - a.efficiency);
  }

  // Cache leeren (z.B. nach Admin-Änderungen)
  function clearCache() {
    _cache = null;
    console.log("🔄 BuildingsAPI: Cache geleert");
  }

  return { load, getAll, getById, getByCategory, getBuildable,
           getEfficiency, getForTerrain, clearCache };

})();

// --------------------------------------------------------
// Statischer Fallback (identisch zur letzten buildings-data.js)
// Wird nur genutzt wenn API nicht erreichbar ist
// --------------------------------------------------------
const BUILDINGS_FALLBACK = [
  { id:1,  name:"Bunker",          kategorie:"Start",     baubar:true, arbeiter:10, wohnraum:100, lagerkapazitaet:20000, tech_level:0,  baukosten_mips:0,    symbol_emoji:"🏢", produktion:[{rohstoff:"Wasser",menge:50}],                              terrain_effektivitaet:{"100":["Grasland","Wald","Steppe","Savanne","Sumpfland"]} },
  { id:2,  name:"Feldweg",         kategorie:"Weg",       baubar:true, arbeiter:0, wohnraum:0, lagerkapazitaet:0, tech_level:0, baukosten_mips:50, symbol_emoji:"🛤️", produktion:[], terrain_effektivitaet:{} },
  { id:3,  name:"Feldwegkreuzung", kategorie:"Weg",       baubar:true, arbeiter:0, wohnraum:0, lagerkapazitaet:0, tech_level:0, baukosten_mips:80, symbol_emoji:"🛤️", produktion:[], terrain_effektivitaet:{} },
  { id:4,  name:"Kiesweg",         kategorie:"Weg",       baubar:true, arbeiter:0, wohnraum:0, lagerkapazitaet:0, tech_level:0, baukosten_mips:100, symbol_emoji:"🛤️", produktion:[], terrain_effektivitaet:{} },
  { id:5,  name:"Kieskreuzung",    kategorie:"Weg",       baubar:true, arbeiter:0, wohnraum:0, lagerkapazitaet:0, tech_level:0, baukosten_mips:150, symbol_emoji:"🛤️", produktion:[], terrain_effektivitaet:{} },
  { id:6,  name:"Kartoffelfarm",   kategorie:"Farm",      baubar:true,  arbeiter:10, wohnraum:0,   lagerkapazitaet:0,     tech_level:0,  baukosten_mips:0,    symbol_emoji:"🌿", produktion:[{rohstoff:"Kartoffeln",menge:40}],                          terrain_effektivitaet:{"100":["Grasland","Steppe"]} },
  { id:7,  name:"Sojafarm",        kategorie:"Farm",      baubar:true,  arbeiter:10, wohnraum:0,   lagerkapazitaet:0,     tech_level:25, baukosten_mips:0,    symbol_emoji:"🌿", produktion:[{rohstoff:"Sojabohnen",menge:25}],                         terrain_effektivitaet:{"100":["Sumpfland"]} },
  { id:8,  name:"Imkerei",         kategorie:"Abbau",     baubar:true,  arbeiter:2,  wohnraum:0,   lagerkapazitaet:0,     tech_level:0,  baukosten_mips:0,    symbol_emoji:"🐝", produktion:[{rohstoff:"Honig",menge:8},{rohstoff:"Wachs",menge:2}],    terrain_effektivitaet:{"100":["Grasfelsland","Grashügel","Grasland","Wald"]} },
  { id:9,  name:"Dattelnplantage", kategorie:"Farm",      baubar:true,  arbeiter:4,  wohnraum:0,   lagerkapazitaet:0,     tech_level:0,  baukosten_mips:0,    symbol_emoji:"🌿", produktion:[{rohstoff:"Datteln",menge:16}],                            terrain_effektivitaet:{"100":["Pampa","Savanne"]} },
  { id:10, name:"Orangenplantage", kategorie:"Farm",      baubar:true,  arbeiter:10, wohnraum:0,   lagerkapazitaet:0,     tech_level:0,  baukosten_mips:0,    symbol_emoji:"🌿", produktion:[{rohstoff:"Orangen",menge:40}],                          terrain_effektivitaet:{"100":["Grünland","Regenwald","Weideland"]} },
  { id:11, name:"Apfelplantage",   kategorie:"Farm",      baubar:true,  arbeiter:6,  wohnraum:0,   lagerkapazitaet:0,     tech_level:0,  baukosten_mips:0,    symbol_emoji:"🌿", produktion:[{rohstoff:"Äpfel",menge:24}],                              terrain_effektivitaet:{"100":["Grasland","Wald"]} },
  { id:14, name:"Palmenplantage",  kategorie:"Farm",      baubar:true,  arbeiter:15, wohnraum:0,   lagerkapazitaet:0,     tech_level:35, baukosten_mips:0,    symbol_emoji:"🌴", produktion:[{rohstoff:"Kokosnuss",menge:32}],                       terrain_effektivitaet:{"100":["Dschungel","Regenwald"]} },
  { id:15, name:"Holzfäller",      kategorie:"Abbau",     baubar:true,  arbeiter:6,  wohnraum:0,   lagerkapazitaet:0,     tech_level:0,  baukosten_mips:0,    symbol_emoji:"🪓", produktion:[{rohstoff:"Bauholz",menge:12}],                            terrain_effektivitaet:{"100":["Sumpfland","Wald"]} },
  { id:16, name:"Steinmetz",       kategorie:"Abbau",     baubar:true,  arbeiter:8,  wohnraum:0,   lagerkapazitaet:0,     tech_level:0,  baukosten_mips:0,    symbol_emoji:"🔨", produktion:[{rohstoff:"Stein",menge:5},{rohstoff:"Kies",menge:2}],     terrain_effektivitaet:{"100":["Brachfelsland","Felsgebirge","Grasfelsland","Grasgebirge"]} },
  { id:22, name:"Tabakplantage",   kategorie:"Farm",      baubar:true,  arbeiter:15, wohnraum:0,   lagerkapazitaet:0,     tech_level:5,  baukosten_mips:5000, symbol_emoji:"🌿", produktion:[{rohstoff:"Tabak",menge:6}],                               terrain_effektivitaet:{"100":["Grünfelsland","Grünhügel","Grünland","Weideland"]} },
  { id:23, name:"Hanfplantage",    kategorie:"Farm",      baubar:true,  arbeiter:15, wohnraum:0,   lagerkapazitaet:0,     tech_level:10, baukosten_mips:6000, symbol_emoji:"🌿", produktion:[{rohstoff:"Hanf",menge:8}],                                terrain_effektivitaet:{"100":["Sumpfland"]} },
  { id:24, name:"Kräutergarten",   kategorie:"Farm",      baubar:true,  arbeiter:5,  wohnraum:0,   lagerkapazitaet:0,     tech_level:0,  baukosten_mips:0,    symbol_emoji:"🌱", produktion:[{rohstoff:"Kräuter",menge:12}],                          terrain_effektivitaet:{"100":["Grünland","Sumpfland","Tropensumpf","Wald","Weideland"]} },
  { id:27, name:"Ziegenfarm",      kategorie:"Tierzucht", baubar:true,  arbeiter:4,  wohnraum:0,   lagerkapazitaet:0,     tech_level:15, baukosten_mips:0,    symbol_emoji:"🐐", produktion:[{rohstoff:"Ziegen",menge:1},{rohstoff:"Milch",menge:10}],  terrain_effektivitaet:{"100":["Savanne","Savannenfelsland","Savannenhügel"]} }
];

// Beim Laden automatisch starten
BuildingsAPI.load();
