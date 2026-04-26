# 📄 Abschnitt 2: Bevölkerung & Alterssystem

## 2.0 Überblick

Die Bevölkerung ist dynamisch und unterteilt in **drei Altersgruppen**. Nur Erwachsene produzieren Arbeitspunkte (AP), können in Gebäuden arbeiten oder zu Einheiten rekrutiert werden. Kinder und Rentner verbrauchen Ressourcen, sind aber keine Arbeitskräfte.

---

## 2.1 Altersgruppen & Lebenszyklus (AKTUALISIERT)

### 2.1.1 Altersphasen (mit Bildungseinfluss)

**Grunddauern mit Bildungseinfluss:**

| Phase | Basis | Mit Bildung (500) | AP-Produktion | Ressourcenverbrauch |
|-------|-----|-----------|---|---|
| **Kinder** | 1 Tag | 0.5 Tage (-50%) | ❌ 0 AP | ✅ Ja (Nahrung, Getränke) |
| **Erwachsene** | 6 Tage | 7.5 Tage (+25%) | ✅ 1 AP/Tag | ✅ Ja |
| **Rentner** | 2 Tage | 2 Tage | ❌ 0 AP | ✅ Ja |

**Bildungseinfluss auf Alterung (Lineare Skalierung):**
```javascript
function berechneAlterungsDauer(province, stufe) {
  const BASE_DAUER = { kind: 1, erwachsener: 6, rentner: 2 };
  let dauer = BASE_DAUER[stufe];
  
  // Lineare Reduktion: Bildung / 1000 (max. -50%)
  const reduktion = Math.min(bildungLevel / 1000, 0.5);
  
  if (stufe === 'kind') {
    dauer = baseDauer - reduktion; // 1.0 bis 0.5 Tage
  } else if (stufe === 'erwachsener') {
    dauer *= (1 + bildungBonus * 0.5); // +25% bei hoher Bildung
  }
  
  return Math.max(0.5, Math.min(10, dauer));
}

// Beispiel: Bildung = 500 → Kinderphase = 1 - (500/1000) = 0.5 Tage (-50%)
```

**Total-Zyklus:** 0.5 + 7.5 + 2 = **10 Tage** (hohe Bildung) vs. 9 Tage (Basis)

### 2.1.2 Zufällige Todesfälle (NEU)

**Altersabhängige Sterberaten:**

| Altersgruppe | Rate pro Tag |
|-------------|-|
| **Kinder** | 0.07% |
| **Erwachsene** | 0.1% |
| **Rentner** | 0.2% |

**Umsetzung:**
```javascript
function applyZufaelligeTodesfaelle(provinc) {
  const rate = { kind: 0.0007, erwachsene: 0.001, rentner: 0.002 };
  
  provinz.tode = {
    kind: Math.ceil(provinc.bevoelkerung.kinder * rate.kind),
    erwachsene: Math.ceil(provinc.bevoelkerung.erwachsene * rate.erwachsene),
    rentner: Math.ceil(provinc.bevoelkerung.rentner * rate.rentner)
  };
}
```

---

## 2.2 Bildung & Geburtenrate (AKTUALISIERT)

### Exponentielle Geburtenformel

```javascript
function berechneGeburten(provinc) {
  const BASE = 0.1;  // 10%
  const bildungLevel = provinz.bildungLevel;
  const bildungFaktor = Math.exp(-bildungLevel / 500);
  
  let rate = BASE * bildungFaktor;
  rate = Math.max(0.02, rate);  // Minimum 2%
  
  return Math.floor(provinc.bevoelkerung.erwachsene * rate);
}
```

**Beispieltabelle:**

| Bildung | Rate | Bei 100 Erwachsenen |
|---------|-----|-------------------|
| 50 | 9.05% | 9 Kinder/Tag |
| 150 | 7.41% | 7 Kinder/Tag |
| 500 | 3.68% | 4 Kinder/Tag |
| 1000 | 2.00% | 2 Kinder/Tag (Min) |

---

## 2.3-2.6 UI, Datenbank, Checkliste

*Restliche Abschnitte wie im Original dokumentiert*

---

**Status:** ✅ Aktualisiert mit Bildungseinfluss, Zufallstode, exponentieller Geburtenrate
