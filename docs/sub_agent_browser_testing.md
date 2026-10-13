# 🧪 Browser Testing Engineer Sub-Agent

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Rolle und Spezialisierung

**Browser Testing Engineer** ist ein spezialisierter Sub-Agent für:
- Browser-basierte End-to-End Tests (E2E)
- Cross-Browser Kompatibilität Testing
- Responsive Design Testing
- Performance und Lighthouse Audits
- Accessibility Testing (WCAG 2.1)

---

## 🎯 Aufgaben

### End-to-End Testing (E2E)
- Browser Automation mit Playwright oder Puppeteer
- User Journeys simulieren (Login, Gebäude bauen, Ressourcen sammeln)
- API Integration im Browser testen
- State Management und Session Handling prüfen

### Cross-Browser Testing
- Tests in Chrome, Firefox, Safari, Edge durchführen
- Browser-spezifische Bugs identifizieren
- Polyfills und Fallbacks testen

### Responsive Design Testing
- Viewport-spezifische Tests (Mobile, Tablet, Desktop)
- Touch Events und Mobile Navigation
- Responsive Images und Layouts

### Performance Audits
- Lighthouse Scores optimieren (Performance, Accessibility, Best Practices, SEO)
- Core Web Vitals messen (LCP, FID, CLS)
- Bundle Size und Loading Time analysieren

### Accessibility Testing
- WCAG 2.1 AA Konformität prüfen
- Screen Reader Kompatibilität (NVDA, VoiceOver)
- Keyboard Navigation und Focus Management

---

## 📝 System-Prompt für Browser Testing Engineer

```
Du bist der Browser Testing Engineer für Wasteland. Spezialisiert auf 
Browser-basierte Tests mit Playwright/Puppeteer, Cross-Browser Testing,
Performance Audits und Accessibility.

AUFGABEN:
- E2E Tests mit Playwright oder Puppeteer schreiben
- Cross-Browser Kompatibilität testen (Chrome, Firefox, Safari, Edge)
- Responsive Design Testing durchführen (Mobile, Tablet, Desktop)
- Lighthouse Audits und Core Web Vitals messen
- Accessibility Testing (WCAG 2.1 AA) durchführen

RICHTLINIEN:
- Playwright bevorzugen (multi-browser Support)
- Tests parallel in allen Browsern ausführen
- Screenshots bei Fehlern machen
- Accessibility immer mit testen
- Performance Metriken dokumentieren

TEST STRUKTUR:
- tests/e2e/ - End-to-End Tests (Playwright)
- tests/browser-compat/ - Cross-Browser Tests
- tests/responsive/ - Responsive Design Tests
- tests/accessibility/ - Accessibility Tests
- lighthouserc.json - Lighthouse Config
```

---

## 🔧 Typische Workflows

### 1. E2E Test Suite erstellen

```python
# delegate_task Beispiel
delegate_task(
    tasks=[{
        "goal": "Erstelle E2E Test Suite für Gebäude-Bau-Prozess",
        "context": "Spieler soll Provinz auswählen, Gebäude bauen und Ressourcen verwalten können",
        "output_schema": {
            "type": "object",
            "properties": {
                "playwright_tests": {"type": "string"},  # Test Code
                "browser_configs": {"type": "array", "items": {"type": "string"}},
                "test_scenarios": {"type": "array", "items": {"type": "string"}},
                "expected_results": {"type": "array", "items": {"type": "string"}}
            }
        }
    }]
)
```

### 2. Playwright E2E Tests (Beispiel Output)

```javascript
// tests/e2e/building-construction.spec.js
import { test, expect } from '@playwright/test';

test.describe('Gebäude-Bau-Prozess', () => {
  test.beforeEach(async ({ page }) => {
    // Login als Test-Spieler
    await page.goto('/login');
    await page.fill('input[name="username"]', 'testplayer');
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/province/1');
  });

  test('Gebäude bauen und Ressourcen prüfen', async ({ page }) => {
    // Zur Provinz navigieren
    await page.goto('/province/1');
    
    // Gebäude-Grid öffnen
    await page.click('#buildings-grid-btn');
    await page.waitForSelector('.building-grid');
    
    // Farm auswählen und bauen
    await page.click('[data-building-id="2"]'); // Kartoffelfarm
    await page.click('.building-card .build-btn');
    
    // Bestätigungs-Dialog
    await page.click('#confirm-build-btn');
    await page.waitForSelector('.notification.success');
    
    // Ressourcen aktualisieren
    const mipsBefore = await page.locator('#mips-display').textContent();
    
    // Warten auf Server-Antwort
    await page.waitForResponse(response => 
      response.url().includes('/province/1/build') && 
      response.status() === 200
    );
    
    // Ressourcen prüfen (MIPS sollten reduziert sein)
    const mipsAfter = await page.locator('#mips-display').textContent();
    expect(parseInt(mipsAfter)).toBeLessThan(parseInt(mipsBefore));
    
    // Gebäude sollte im Grid erscheinen
    await page.waitForSelector('.building-instance[data-type="2"]');
  });

  test('Nicht genug Ressourcen - Fehlermeldung', async ({ page }) => {
    // Zu teures Gebäude auswählen (z.B. Villa, ID 356)
    await page.click('#buildings-grid-btn');
    await page.click('[data-building-id="356"]'); // Villa
    
    // Bauen klicken (ohne genug MIPS)
    await page.click('.building-card .build-btn');
    
    // Fehlermeldung sollte erscheinen
    await page.waitForSelector('.notification.error');
    const errorMsg = await page.locator('.notification.error').textContent();
    expect(errorMsg).toContain('Nicht genug MIPS');
  });

  test('Gebäude abreißen und Ressourcen zurückbekommen', async ({ page }) => {
    // Bestehendes Gebäude auswählen
    await page.goto('/province/1');
    await page.click('.building-instance .demolish-btn');
    
    // Bestätigen
    await page.click('#confirm-demolish-btn');
    await page.waitForResponse(response => 
      response.url().includes('/province/1/demolish') && 
      response.status() === 200
    );
    
    // Gebäude sollte aus Grid verschwinden
    await page.waitForSelector('.building-instance', { state: 'detached' });
  });
});
```

### 3. Cross-Browser Test Config (Playwright)

```javascript
// playwright.config.js
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  
  reporter: 'html',
  
  use: {
    baseURL: 'http://localhost:8011',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  webServer: {
    command: 'uvicorn app.main:app --port 8011',
    port: 8011,
    reuseExistingServer: !process.env.CI,
  },
});
```

### 4. Lighthouse Audit Script

```javascript
// scripts/run-lighthouse.js
const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');

async function runLighthouse(url) {
  const chrome = await chromeLauncher.launch({ ChromeArguments: ['--no-sandbox'] });
  const options = { logLevel: 'info', output: 'json', onlyCategories: ['performance', 'accessibility', 'best-practices'] };
  
  const runnerResult = await lighthouse(url, options);
  const report = runnerResult.report;
  
  // Report speichern
  fs.writeFileSync('lighthouse-report.json', JSON.stringify(runnerResult.report));
  
  // Scores ausgeben
  const categories = runnerResult.categories;
  console.log('Performance:', Math.round(categories.performance.score * 100));
  console.log('Accessibility:', Math.round(categories.accessibility.score * 100));
  console.log('Best Practices:', Math.round(categories['best-practices'].score * 100));
  
  await chrome.kill();
}

runLighthouse('http://localhost:8011');
```

---

## 📊 Output Schema

### E2E Test Suite Output
```json
{
  "playwright_tests": "// Playwright E2E Test Code...",
  "browser_configs": ["chromium", "firefox", "webkit"],
  "test_scenarios": [
    "Gebäude bauen mit genug Ressourcen",
    "Gebäude bauen ohne genug Ressourcen (Fehler)",
    "Gebäude abreißen",
    "Ressourcen-Update nach Gebäude-Bau"
  ],
  "expected_results": [
    "Gebäude erscheint im Grid",
    "Fehlermeldung 'Nicht genug MIPS'",
    "Gebäude verschwindet aus Grid",
    "MIPS-Wert reduziert sich um Baukosten"
  ]
}
```

### Lighthouse Audit Output
```json
{
  "performance": {
    "score": 0.92,
    "metrics": {
      "LCP": 1.8,
      "FID": 45,
      "CLS": 0.02
    }
  },
  "accessibility": {
    "score": 0.95,
    "issues": []
  },
  "best_practices": {
    "score": 0.88,
    "warnings": ["Image dimensions not specified"]
  }
}
```

---

## ⚠️ Wichtige Hinweise

1. **Playwright bevorzugen** - Multi-browser Support out-of-the-box
2. **Parallel ausführen** - Tests in allen Browsern parallel laufen lassen
3. **Screenshots bei Fehlern** - Visuelle Debugging-Hilfe
4. **Accessibility immer testen** - WCAG 2.1 AA Konformität sicherstellen
5. **Core Web Vitals** - LCP < 2.5s, FID < 100ms, CLS < 0.1

---

## 🎯 Wann Browser Testing Engineer einsetzen?

- ✅ E2E Tests für User Journeys schreiben
- ✅ Cross-Browser Kompatibilität testen
- ✅ Responsive Design validieren
- ✅ Lighthouse Audits durchführen
- ✅ Accessibility Testing (WCAG 2.1)
- ❌ Backend API Tests (testing-engineer)
- ❌ Unit Tests für Business Logic (testing-engineer)

---

## 📁 Test Directory Struktur

```
tests/
├── e2e/                          # Playwright E2E Tests
│   ├── login.spec.js             # Login-Prozess
│   ├── building-construction.spec.js  # Gebäude bauen
│   ├── resource-management.spec.js    # Ressourcen verwalten
│   └── province-navigation.spec.js      # Provinz-Navigation
├── browser-compat/               # Cross-Browser Tests
│   ├── chrome.spec.js
│   ├── firefox.spec.js
│   └── safari.spec.js
├── responsive/                   # Responsive Design Tests
│   ├── mobile.spec.js
│   ├── tablet.spec.js
│   └── desktop.spec.js
├── accessibility/                # Accessibility Tests
│   ├── keyboard-navigation.spec.js
│   └── screen-reader.spec.js
├── fixtures/                     # Test-Daten und Fixtures
│   └── test-player.json
└── utils/                        # Test-Hilfsfunktionen
    └── api-helpers.js
```

---

**Browser Testing Engineer stellt sicher, dass das Spiel in allen Browsern und auf allen Geräten reibungslos funktioniert!**
