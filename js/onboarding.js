// ============================================================
// onboarding.js – Willkommensscreen & Tutorial-System
// ============================================================

(function () {
  'use strict';

  // Tutorial-Texte
  const TUTORIAL_STEPS = [
    {
      title: "Deine erste Provinz",
      text: "Das ist deine erste Provinz in der Verbrannten Zone. Klicke auf sie auf der Weltkarte, um sie zu verwalten.",
      highlightBtn: null
    },
    {
      title: "Lager prüfen",
      text: "Öffne das <strong>Provinzlager</strong> (Seitenmenü), um deine Startvorräte zu prüfen. Du hast Getreide, Wasser, Bauholz und Stein erhalten.",
      highlightBtn: "menu-btn-lager"
    }
  ];

  const TUTORIAL_MAX_STEP = TUTORIAL_STEPS.length; // ≥ TUTORIAL_MAX_STEP → Tutorial abgeschlossen

  // ── Haupt-Einstiegspunkt ─────────────────────────────────────
  async function checkOnboarding() {
    const playerId = window.currentPlayerId;
    if (!playerId) return;

    try {
      const res = await gameFetch(`${APIBASE}/player/${playerId}/provinzen`);
      if (!res.ok) return;
      const data = await res.json();
      const provinzen = data.provinzen || [];

      if (provinzen.length === 0) {
        // Neuer Spieler → Welcome-Screen
        showWelcomeScreen();
      } else {
        // Bestehender Spieler → Tutorial-Status prüfen
        checkTutorial(token, playerId);
      }
    } catch (e) {
      console.warn('[Onboarding] Prüfung fehlgeschlagen:', e.message);
    }
  }

  // ── Welcome-Screen ───────────────────────────────────────────
  function showWelcomeScreen() {
    const overlay = document.getElementById('welcome-overlay');
    if (overlay) overlay.style.display = 'flex';
  }

  function hideWelcomeScreen() {
    const overlay = document.getElementById('welcome-overlay');
    if (overlay) overlay.style.display = 'none';
  }

  async function doSpawn() {
    const token = AuthService.getAccessToken();
    const playerId = window.currentPlayerId;

    const btn = document.getElementById('btn-spawn');
    if (btn) { btn.disabled = true; btn.textContent = 'Starte...'; }

    try {
      const res = await gameFetch(`${APIBASE}/player/${playerId}/spawn`, {
        method: 'POST'
      });
      const data = await res.json();

      if (res.ok) {
        hideWelcomeScreen();
        // Weltkarte aktualisieren & Provinz öffnen
        if (typeof window.loadWorldMap === 'function') loadWorldMap();
        if (typeof window.switchView === 'function') {
          window.switchView('province', data.world_x, data.world_y);
        }
        // Tutorial starten
        setTimeout(() => showTutorialStep(0), 800);
      } else {
        alert('Fehler beim Spawn: ' + (data.detail || JSON.stringify(data)));
        if (btn) { btn.disabled = false; btn.textContent = 'Welt betreten'; }
      }
    } catch (e) {
      console.error('[Onboarding] Spawn fehlgeschlagen:', e);
      alert('Server nicht erreichbar: ' + e.message);
      if (btn) { btn.disabled = false; btn.textContent = 'Welt betreten'; }
    }
  }

  // ── Tutorial ─────────────────────────────────────────────────
  async function checkTutorial(playerId) {
    try {
      const res = await gameFetch(`${APIBASE}/player/${playerId}/tutorial`);
      if (!res.ok) return;
      const data = await res.json();
      const step = data.tutorial_step;
      if (step >= 0 && step < TUTORIAL_MAX_STEP) {
        setTimeout(() => showTutorialStep(step), 500);
      }
    } catch (e) {
      console.warn('[Onboarding] Tutorial-Check fehlgeschlagen:', e.message);
    }
  }

  function showTutorialStep(step) {
    if (step >= TUTORIAL_MAX_STEP) {
      hideTutorial();
      return;
    }
    const info = TUTORIAL_STEPS[step];
    const overlay = document.getElementById('tutorial-overlay');
    const title = document.getElementById('tutorial-title');
    const text = document.getElementById('tutorial-text');
    const progress = document.getElementById('tutorial-progress');
    if (!overlay) return;

    if (title) title.textContent = info.title;
    if (text) text.innerHTML = info.text;
    if (progress) progress.textContent = `Schritt ${step + 1} / ${TUTORIAL_MAX_STEP}`;

    overlay.style.display = 'flex';

    // Highlight-Effekt (optional)
    if (info.highlightBtn) {
      const el = document.getElementById(info.highlightBtn);
      if (el) {
        el.classList.add('tutorial-highlight');
        setTimeout(() => el.classList.remove('tutorial-highlight'), 3000);
      }
    }
  }

  function hideTutorial() {
    const overlay = document.getElementById('tutorial-overlay');
    if (overlay) overlay.style.display = 'none';
  }

  async function advanceTutorial() {
    const playerId = window.currentPlayerId;

    try {
      const res = await gameFetch(`${APIBASE}/player/${playerId}/tutorial/advance`, {
        method: 'POST'
      });
      const data = await res.json();
      if (res.ok) {
        showTutorialStep(data.tutorial_step);
      }
    } catch (e) {
      console.warn('[Onboarding] Tutorial-Advance fehlgeschlagen:', e.message);
      hideTutorial();
    }
  }

  // ── Exports ──────────────────────────────────────────────────
  window.checkOnboarding = checkOnboarding;
  window.doSpawn = doSpawn;
  window.advanceTutorial = advanceTutorial;
  window.hideTutorial = hideTutorial;

})();
