#!/usr/bin/env python3
"""Scraper fuer v3.verbranntezone.ch - Liest Detail-Seiten per ID-Iteration aus
und speichert die Daten als JSON in data/scraped/."""

import requests, json, os, re, time, sys, io

# Fix Windows console encoding
if sys.stdout and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer') and sys.stderr.buffer:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from html.parser import HTMLParser

BASE_URL = "https://v3.verbranntezone.ch"
LOGIN_URL = f"{BASE_URL}/index.php"
USER = "Dargoamarok"
PASS = "katerfelix"

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "scraped")
os.makedirs(OUT_DIR, exist_ok=True)

def log_progress(msg):
    """Schreibt Fortschritt in eine Textdatei (fuer Monitoring)."""
    with open("progress.txt", "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    print(msg)
    sys.stdout.flush()

# ─── HTML-zu-Text Parser ────────────────────────────────────────────────────
class TableParser(HTMLParser):
    """Extrahiert alle <td>-Inhalte aus HTML und baut Label-Value-Paare."""
    def __init__(self):
        super().__init__()
        self.in_td = False
        self.in_a = False
        self.current_text = ""
        self.cells = []
        self.current_href = ""
        self.hrefs = []  # parallel zu cells
        self.in_title = False
        self.title = ""
        # Track if we're inside a table at all
        self.table_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "table":
            self.table_depth += 1
        if tag == "td":
            self.in_td = True
            self.current_text = ""
            self.current_href = ""
        if tag == "a" and self.in_td:
            self.in_a = True
            self.current_href = attrs_dict.get("href", "")
        if tag == "title":
            self.in_title = True
            self.title = ""

    def handle_endtag(self, tag):
        if tag == "table":
            self.table_depth -= 1
        if tag == "td":
            self.in_td = False
            text = self.current_text.strip()
            self.cells.append(text)
            self.hrefs.append(self.current_href)
        if tag == "a":
            self.in_a = False
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_td:
            self.current_text += data
        if self.in_title:
            self.title += data

    def get_pairs(self):
        """Baut key-value Paare aus aufeinanderfolgenden Zellen."""
        pairs = {}
        i = 0
        while i < len(self.cells) - 1:
            key = self.cells[i].strip().rstrip(":")
            val = self.cells[i + 1].strip()
            if key and val and key != val:
                # Prüfe ob der Value ein Link enthält
                href = self.hrefs[i + 1]
                if href:
                    pairs[key] = {"text": val, "link": href}
                else:
                    pairs[key] = val
                i += 2
            elif key:
                # Einzelne Zelle (z.B. Section-Header) – überspringen
                i += 1
            else:
                i += 1
        return pairs

    def get_all_cells(self):
        return self.cells


def parse_page(html):
    """Parst eine Vorschau-Seite und gibt die Daten als Dict zurück."""
    # Extrahiere Titel
    # Neue Struktur: <div class='title'>Bunker <i>(ID: 1)</i></div>
    # Alte Struktur: <center><b>Name (ID: X)</b></center>
    extracted_name = None
    
    # Versuche neue Struktur
    name_match = re.search(r"<div class='title'>(.*?)(?:<i>|\(|<)", html, re.IGNORECASE | re.DOTALL)
    if not name_match:
        # Versuche alte Struktur oder allgemeingültiges b-tag im center
        name_match = re.search(r"<center>.*?<b>(.*?)(?:<i>|\(|<br>|<font|<line)", html, re.IGNORECASE | re.DOTALL)
    
    if name_match:
        extracted_name = name_match.group(1).strip().strip(":")
    else:
        # Letzter Versuch: Einfach alles im title div
        name_match = re.search(r"<div class='title'>(.*?)</div>", html, re.IGNORECASE | re.DOTALL)
        if name_match:
            # Entferne HTML-Tags falls vorhanden
            extracted_name = re.sub(r"<.*?>", "", name_match.group(1)).strip()

    parser = TableParser()
    parser.feed(html)
    
    result = {}
    if extracted_name:
        result["Name"] = extracted_name
    
    cells = parser.cells
    hrefs = parser.hrefs
    
    # Bekannte Labels, bei denen der Wert davor stehen kann (VZ Eigenheit)
    swapped_labels = ["Energiebedarf", "Arbeiter", "Wohnraum", "Lagerraumkapazität", "Bautyp", "Baukosten in Mips"]
    
    i = 0
    while i < len(cells):
        cell = cells[i].strip()
        if not cell or cell == "\xa0":
            i += 1
            continue
            
        # Wenn die Zelle ein bekanntes Label ist, aber der Wert in der Zelle DAVOR stand
        # (Passiert wenn die Tabelle unsauber geparst wird)
        if cell in swapped_labels and i > 0:
            prev_cell = cells[i-1].strip()
            if prev_cell and prev_cell not in result.values():
                result[cell] = prev_cell
                i += 1
                continue

        if i + 1 < len(cells):
            next_cell = cells[i + 1].strip()
            key = cell.rstrip(":")
            
            if next_cell and next_cell != "\xa0":
                href = hrefs[i + 1]
                val = next_cell
                
                # Wenn der Wert ein Link ist
                if href and ("vorschau" in href or "id=" in href):
                    val = {"text": next_cell, "link": href}
                
                # Speichern
                if key in result:
                    if isinstance(result[key], list):
                        result[key].append(val)
                    else:
                        result[key] = [result[key], val]
                else:
                    result[key] = val
                i += 2
            else:
                i += 1
        else:
            i += 1
            
    return result, extracted_name or parser.title.strip()


def is_valid_page(html):
    """Prüft ob die Seite gültige Daten enthält (nicht leer / nicht 404)."""
    if not html or len(html) < 200:
        return False
    # Prüfe auf typische "nicht gefunden" Muster
    lower = html.lower()
    if "nicht gefunden" in lower or "not found" in lower:
        return False
    if "<table" not in lower:
        return False
    return True


def scrape_category(session, name, url_template, max_id=2000, max_consecutive_empty=100):
    """Scrape eine Kategorie durch ID-Iteration."""
    log_progress(f"\n{'='*60}\nStarte Scraping: {name}\n{'='*60}")
    
    results = {}
    consecutive_empty = 0
    total_found = 0
    
    for id_num in range(1, max_id + 1):
        url = url_template.format(id=id_num)
        
        try:
            resp = session.get(url, timeout=15)
            
            current_url = resp.url
            if f"id={id_num}" not in current_url:
                if id_num > 1 and "id=1" in current_url:
                    log_progress(f"  -> Redirect auf ID 1 (Ende-Check) bei ID {id_num}")
                    break

            if resp.status_code != 200:
                log_progress(f"  [.] ID {id_num:>3}: Status {resp.status_code}")
                consecutive_empty += 1
            else:
                html = resp.text
                if not is_valid_page(html):
                    # log_progress(f"  [.] ID {id_num:>3}: Ungueltige Seite")
                    consecutive_empty += 1
                else:
                    data, title = parse_page(html)
                    if data:
                        # Stop-Condition: Bautyp == "FEHLER!"
                        bautyp = data.get("Bautyp", "")
                        if isinstance(bautyp, dict): bautyp = bautyp.get("text", "")
                        if "FEHLER!" in str(bautyp).upper():
                            log_progress(f"  -> 'FEHLER!' im Bautyp erkannt, stoppe bei ID {id_num}")
                            break

                        # Filter: Name darf nicht "unbekannt" sein
                        name_val = str(data.get("Name", data.get("name", ""))).lower()
                        is_unknown = "unbekannt" in name_val
                        has_name = len(name_val.strip()) > 1
                        
                        non_empty = sum(1 for v in data.values() if v and v != "" and v != "0")
                        
                        if non_empty >= 2 and has_name and not is_unknown:
                            data["_id"] = id_num
                            data["_title"] = title
                            results[id_num] = data
                            total_found += 1
                            consecutive_empty = 0
                            
                            display_name = data.get("Name", data.get("name", f"ID {id_num}"))
                            if isinstance(display_name, dict):
                                display_name = display_name.get("text", f"ID {id_num}")
                            log_progress(f"  [+] ID {id_num:>3}: {display_name}")
                        elif is_unknown:
                            log_progress(f"  [-] ID {id_num:>3}: Überspringe (Unbekannt)")
                            consecutive_empty = 0
                        else:
                            # log_progress(f"  [.] ID {id_num:>3}: Keine validen Daten")
                            consecutive_empty += 1
                    else:
                        consecutive_empty += 1
                
            if consecutive_empty >= max_consecutive_empty:
                log_progress(f"  -> {max_consecutive_empty} leere Seiten in Folge, stoppe bei ID {id_num}")
                break
                
        except Exception as e:
            log_progress(f"  [!] ID {id_num}: Fehler: {e}")
            consecutive_empty += 1
            
        time.sleep(1.0)
    
    log_progress(f"  Gefunden: {total_found} Einträge für '{name}'")
    return results


def main():
    with open("progress.txt", "w", encoding="utf-8") as f:
        f.write(f"--- SCRAPER START ({time.strftime('%Y-%m-%d %H:%M:%S')}) ---\n")
    log_progress("Starte Hauptprozess...")
    # ─── Konfiguration & Session ───────────────────────────────────────────────
    session = requests.Session()
    
    # Cookie-Injektion (Hybrid-Ansatz)
    # Nutze Umgebungsvariable oder manuell setzen
    manual_cookie = os.environ.get("VZ_COOKIE", "PHPSESSID=l1dmdgbmf3b1dorb1qupl3pu40; guidcookie=9e1424-af976d-69a1fff4")
    
    if manual_cookie:
        print("[INFO] Nutze manuellen Session-Cookie...")
        # Cookie-String parsen
        for item in manual_cookie.split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                session.cookies.set(k, v, domain="v3.verbranntezone.ch")
    else:
        # ─── Login (Legacy) ───────────────────────────────────────────────────────
        print("Logge ein...")
        # Login-Seite laden um ggf. CSRF-Token oder Cookies zu bekommen
        login_page = session.get(BASE_URL, timeout=15)
        
        # Login POST
        login_data = {
            "nickname": USER,
            "passwort": PASS,
            "anmelden": "Anmelden"
        }
        resp = session.post(LOGIN_URL, data=login_data, timeout=15, allow_redirects=True)
        
        # Prüfe ob Login erfolgreich
        if "Dargoamarok" in resp.text or "dargoamarok" in resp.text.lower():
            print("[OK] Login erfolgreich!")
        else:
            # Versuche alternative Login-URL
            resp = session.post(f"{BASE_URL}/login.php", data=login_data, timeout=15, allow_redirects=True)
            if "Dargoamarok" not in resp.text and "dargoamarok" not in resp.text.lower():
                print("[?] Login unklar - versuche trotzdem weiter...")
    
    # Teste ob Session funktioniert
    test_url = f"{BASE_URL}/gebaeudevorschau.php?id=1"
    test = session.get(test_url, timeout=15)
    if "Bunker" in test.text:
        print("[OK] Session aktiv - Daten sind erreichbar!")
    else:
        print("[FAIL] Session scheint nicht zu funktionieren!")
        print(f"  Status: {test.status_code}, Laenge: {len(test.text)}")
        return
    
    # ─── Scraping ──────────────────────────────────────────────────────────────
    categories = [
        ("gebaeude",     f"{BASE_URL}/gebaeudevorschau.php?id={{id}}",     1000),
        ("rohstoffe",    f"{BASE_URL}/rohstoffevorschau.php?id={{id}}",    1000),
        ("vorkommen",    f"{BASE_URL}/vorkommenvorschau.php?id={{id}}",    500),
        ("terrain",      f"{BASE_URL}/terrainvorschau.php?id={{id}}",      500),
        ("lebewesen",    f"{BASE_URL}/lebewesenvorschau.php?id={{id}}",    500),
        ("artikel",      f"{BASE_URL}/artikelvorschau.php?id={{id}}",      500),
        ("einheiten",    f"{BASE_URL}/einheitenvorschau.php?id={{id}}",    500),
        ("regierungen",  f"{BASE_URL}/regierungenvorschau.php?id={{id}}",  500),
    ]
    
    # Falls CLI-Argument angegeben, nur diese Kategorie scrapen
    limit_max_id = None
    if len(sys.argv) > 1:
        filter_cat = sys.argv[1].lower()
        if len(sys.argv) > 2:
            limit_max_id = int(sys.argv[2])
            
        categories = [c for c in categories if c[0] == filter_cat]
        if not categories:
            print(f"Unbekannte Kategorie: {filter_cat}")
            print(f"Verfügbar: gebaeude, rohstoffe, vorkommen, terrain, lebewesen, artikel, einheiten, regierungen")
            return
    
    all_data = {}
    
    for cat_name, url_template, default_max_id in categories:
        m_id = limit_max_id if limit_max_id else default_max_id
        data = scrape_category(session, cat_name, url_template, max_id=m_id)
        all_data[cat_name] = data
        
        # Sofort speichern nach jeder Kategorie
        out_file = os.path.join(OUT_DIR, f"{cat_name}.json")
        # Ensure data keys are strings (not ints) for JSON
        data_str_keys = {str(k): v for k, v in data.items()}
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data_str_keys, f, ensure_ascii=False, indent=2)
        print(f"  [SAVE] Gespeichert: {out_file}")
    
    # ─── Zusammenfassung ───────────────────────────────────────────────────────
    print("")
    print("=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    for cat_name in all_data:
        count = len(all_data[cat_name])
        print(f"  {cat_name:>15}: {count:>4} Einträge")
    
    total = sum(len(d) for d in all_data.values())
    print(f"  {'GESAMT':>15}: {total:>4} Einträge")
    print(f"\nAlle Daten gespeichert in: {OUT_DIR}")


if __name__ == "__main__":
    main()
