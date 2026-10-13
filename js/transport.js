// ============================================================
// Warentransport – Verbrannte Zone
// ============================================================

const KARREN_KAPAZITAET = 100; // Platz-Einheiten pro Handelskarren (sync mit Backend)

// ── State ────────────────────────────────────────────────────
let _transportLocalLager = [];    // [{ressource_id, ressource_name, typ, platzbedarf, menge}]
let _transportKapazitaet = 1000;  // eigene Max-Kapazität
let _transportProvinzen = [];     // [{id, world_x, world_y, name, ...}]
let _transportTargetLager = [];   // Lager des Ziels
let _transportTargetKap = 0;     // max Kapazität Ziel
let _transportTargetBelegt = 0;  // belegter Platz Ziel

// ── Haupt-Loader ─────────────────────────────────────────────
async function loadTransportView() {
    const localList = document.getElementById('transport-local-list');
    const targetSelect = document.getElementById('transport-target-prov');
    const resSelect = document.getElementById('transport-res-select');
    const amountInput = document.getElementById('transport-amount');

    if (!window.currentProvinzId) {
        localList.innerHTML = '<p style="color:var(--text-muted)">Keine Provinz-ID. Bitte Provinz zuerst beanspruchen.</p>';
        return;
    }

    localList.innerHTML = '<p style="color:var(--text-muted)">Lade Lager...</p>';

    try {
        // 1. Eigenes Lager laden
        const lagerUrl = `${window.APIBASE}/player/${window.currentPlayerId}/provinzen/${window.currentProvinzId}/lager`;
        const lagerRes = await gameFetch(lagerUrl);
        if (!lagerRes.ok) throw new Error(`Lager: HTTP ${lagerRes.status}`);
        const lagerData = await lagerRes.json();

        _transportLocalLager = lagerData.eintraege || [];
        _transportKapazitaet = lagerData.kapazitaet || 1000;

        // Lokales Lager rendern
        renderLocalLager();

        // Ressource-Dropdown befüllen – nur Ressourcen mit menge > 0 und NICHT Handelskarren (id=1)
        resSelect.innerHTML = '<option value="">Bitte wählen...</option>';
        _transportLocalLager
            .filter(e => e.ressource_id !== 1 && e.menge > 0)
            .forEach(e => {
                const opt = document.createElement('option');
                opt.value = e.ressource_id;
                opt.textContent = `${e.ressource_name} (${e.menge.toLocaleString('de-DE')} vorhanden)`;
                opt.dataset.platzbedarf = e.platzbedarf;
                opt.dataset.menge = e.menge;
                resSelect.appendChild(opt);
            });

        // 2. Alle Provinzen für Ziel-Dropdown laden
        const provUrl = `${window.APIBASE}/player/${window.currentPlayerId}/provinzen`;
        const provRes = await gameFetch(provUrl);
        if (!provRes.ok) throw new Error(`Provinzen: HTTP ${provRes.status}`);
        const provData = await provRes.json();

        _transportProvinzen = (provData.provinzen || []).filter(p => p.id !== window.currentProvinzId);

        targetSelect.innerHTML = '<option value="">Ziel auswählen...</option>';
        _transportProvinzen.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name || `Provinz (${p.world_x},${p.world_y})`;
            targetSelect.appendChild(opt);
        });

        // 3. Event-Listener einrichten (idempotent via replacer)
        resSelect.onchange = onTransportResChange;
        amountInput.oninput = onTransportAmountChange;
        targetSelect.onchange = onTransportTargetChange;

        // Reset
        amountInput.value = 0;
        amountInput.max = 0;
        updateCartInfo(0, 0);

    } catch (err) {
        console.error('Transport-View Fehler:', err);
        localList.innerHTML = `<p style="color:var(--accent-danger)">⚠️ ${err.message}</p>`;
    }
}

// ── Lokales Lager rendern ────────────────────────────────────
function renderLocalLager() {
    const container = document.getElementById('transport-local-list');
    if (_transportLocalLager.length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted)">Lager ist leer.</p>';
        return;
    }

    let html = '<table class="lager-tabelle"><thead><tr><th>Ressource</th><th style="text-align:right">Menge</th></tr></thead><tbody>';
    _transportLocalLager.forEach(item => {
        html += `<tr>
      <td>${item.ressource_name} <span class="lager-typ">${item.typ || ''}</span></td>
      <td class="lager-menge">${item.menge.toLocaleString('de-DE')}</td>
    </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

// ── Ressource-Wechsel ────────────────────────────────────────
function onTransportResChange() {
    const resSelect = document.getElementById('transport-res-select');
    const amountInput = document.getElementById('transport-amount');

    const option = resSelect.selectedOptions[0];
    if (!option || !option.value) {
        amountInput.value = 0;
        amountInput.max = 0;
        updateCartInfo(0, 0);
        return;
    }

    const maxMenge = parseInt(option.dataset.menge, 10) || 0;
    amountInput.max = maxMenge;
    amountInput.value = 0;
    updateCartInfo(0, parseInt(option.dataset.platzbedarf, 10) || 1);
}

// ── Mengen-Änderung ──────────────────────────────────────────
function onTransportAmountChange() {
    const resSelect = document.getElementById('transport-res-select');
    const amountInput = document.getElementById('transport-amount');

    const option = resSelect.selectedOptions[0];
    if (!option || !option.value) return;

    let menge = parseInt(amountInput.value, 10) || 0;
    const maxMenge = parseInt(option.dataset.menge, 10) || 0;
    if (menge > maxMenge) { menge = maxMenge; amountInput.value = menge; }
    if (menge < 0) { menge = 0; amountInput.value = 0; }

    const platzbedarf = parseInt(option.dataset.platzbedarf, 10) || 1;
    updateCartInfo(menge, platzbedarf);
}

// ── Karren-Info updaten ──────────────────────────────────────
function updateCartInfo(menge, platzbedarf) {
    const platzGesamt = menge * platzbedarf;
    const karrenBen = Math.ceil(platzGesamt / KARREN_KAPAZITAET);

    // Handelskarren im Lager (ID=1)
    const karrenItem = _transportLocalLager.find(e => e.ressource_id === 1);
    const karrenVorhanden = karrenItem ? karrenItem.menge : 0;

    document.getElementById('transport-carts-needed').textContent = karrenBen;
    document.getElementById('transport-carts-avail').textContent = karrenVorhanden;

    const cartsEl = document.getElementById('transport-carts-needed');
    if (karrenBen > karrenVorhanden) {
        cartsEl.style.color = '#ff4444';
    } else {
        cartsEl.style.color = '#48bb78';
    }
}

// ── Ziel-Provinz gewechselt ──────────────────────────────────
async function onTransportTargetChange() {
    const targetSelect = document.getElementById('transport-target-prov');
    const capText = document.getElementById('target-cap-text');
    const capFill = document.querySelector('#transport-target-cap .cap-bar-fill');
    const targetList = document.getElementById('transport-target-list');

    const zielId = parseInt(targetSelect.value, 10);
    if (!zielId) {
        capText.textContent = '0 / 0';
        if (capFill) capFill.style.width = '0%';
        targetList.innerHTML = '<p style="color:var(--text-muted)">Zeigt Bestand nach Auswahl...</p>';
        return;
    }

    targetList.innerHTML = '<p style="color:var(--text-muted)">Lade Ziel-Lager...</p>';

    try {
        const url = `${window.APIBASE}/player/${window.currentPlayerId}/provinzen/${zielId}/lager`;
        const res = await gameFetch(url);
        if (!res.ok) throw new Error(`Ziel-Lager: HTTP ${res.status}`);
        const data = await res.json();

        _transportTargetLager = data.eintraege || [];
        _transportTargetKap = data.kapazitaet || 1000;

        // Belegter Platz berechnen
        _transportTargetBelegt = _transportTargetLager.reduce((sum, e) => sum + (e.menge * (e.platzbedarf || 1)), 0);

        // Kapazitätsbalken
        const freierPlatz = _transportTargetKap - _transportTargetBelegt;
        const prozent = Math.min(100, Math.round((_transportTargetBelegt / _transportTargetKap) * 100));
        capText.textContent = `${_transportTargetBelegt.toLocaleString('de-DE')} / ${_transportTargetKap.toLocaleString('de-DE')} (frei: ${freierPlatz.toLocaleString('de-DE')})`;
        if (capFill) {
            capFill.style.width = `${prozent}%`;
            capFill.style.background = prozent > 80 ? '#ff4444' : prozent > 50 ? '#ffaa00' : '#48bb78';
        }

        // Ziel-Lager-Tabelle
        if (_transportTargetLager.length === 0) {
            targetList.innerHTML = '<p style="color:var(--text-muted)">Ziel-Lager ist leer.</p>';
        } else {
            let html = '<table class="lager-tabelle"><thead><tr><th>Ressource</th><th style="text-align:right">Menge</th></tr></thead><tbody>';
            _transportTargetLager.forEach(item => {
                html += `<tr>
          <td>${item.ressource_name} <span class="lager-typ">${item.typ || ''}</span></td>
          <td class="lager-menge">${item.menge.toLocaleString('de-DE')}</td>
        </tr>`;
            });
            html += '</tbody></table>';
            targetList.innerHTML = html;
        }
    } catch (err) {
        console.error('Ziel-Lager Fehler:', err);
        targetList.innerHTML = `<p style="color:var(--accent-danger)">⚠️ ${err.message}</p>`;
    }
}

// ── Transport senden ─────────────────────────────────────────
async function sendTransport() {
    const resSelect = document.getElementById('transport-res-select');
    const amountInput = document.getElementById('transport-amount');
    const targetSelect = document.getElementById('transport-target-prov');

    const ressourceId = parseInt(resSelect.value, 10);
    const menge = parseInt(amountInput.value, 10);
    const zielId = parseInt(targetSelect.value, 10);

    if (!ressourceId || !menge || !zielId) {
        alert('Bitte Ressource, Menge und Ziel auswählen.');
        return;
    }
    if (menge <= 0) {
        alert('Menge muss > 0 sein.');
        return;
    }

    // Karren-Check Frontend
    const option = resSelect.selectedOptions[0];
    const platzbedarf = parseInt(option.dataset.platzbedarf, 10) || 1;
    const karrenBen = Math.ceil((menge * platzbedarf) / KARREN_KAPAZITAET);
    const karrenItem = _transportLocalLager.find(e => e.ressource_id === 1);
    const karrenVorhanden = karrenItem ? karrenItem.menge : 0;

    if (karrenBen > karrenVorhanden) {
        alert(`Nicht genug Handelskarren! Benötigt: ${karrenBen}, Vorhanden: ${karrenVorhanden}`);
        return;
    }

    try {
        const url = `${window.APIBASE}/player/${window.currentPlayerId}/provinzen/${window.currentProvinzId}/transport`;
        const res = await gameFetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nach_provinz_id: zielId,
                ressource_id: ressourceId,
                menge: menge
            })
        });

        const data = await res.json();

        if (!res.ok) {
            alert(`Fehler: ${data.detail || JSON.stringify(data)}`);
            return;
        }

        alert(`✅ ${data.message}`);

        // View neu laden
        loadTransportView();

    } catch (err) {
        console.error('Transport senden Fehler:', err);
        alert('Verbindung fehlgeschlagen: ' + err.message);
    }
}

// ── Exports ──────────────────────────────────────────────────
if (typeof window !== 'undefined') {
    window.loadTransportView = loadTransportView;
    window.sendTransport = sendTransport;
}
