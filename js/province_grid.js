// Province City Grid (15x15 Canvas)
let currentProvinceFields = [];
let selectedFieldIndex = -1;

async function loadProvinceCityGrid(provId) {
    try {
        const res = await fetch(`/api/province/${provId}/fields`);
        if (!res.ok) throw new Error("Fields load failed");
        currentProvinceFields = await res.json();
        
        const statusRes = await fetch(`/api/province/${provId}/city-status`);
        if (statusRes.ok) {
            const status = await statusRes.json();
            document.getElementById('city-level-name').textContent = `${status.size_level_name} (Stufe ${status.current_level})`;
            document.getElementById('next-city-building').textContent = status.next_building;
        }

        drawProvinceCityGrid();
    } catch (e) {
        console.error("City Grid Error:", e);
    }
}

function drawProvinceCityGrid() {
    const canvas = document.getElementById('provinceCityCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const cellSize = 30;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    currentProvinceFields.forEach((f, i) => {
        const x = f.x * cellSize;
        const y = f.y * cellSize;

        // Texture / Base Color
        if (f.type === "city") {
            ctx.fillStyle = "#444"; // Concrete
            ctx.fillRect(x, y, cellSize, cellSize);
            // Draw a pattern for concrete
            ctx.strokeStyle = "#555";
            ctx.strokeRect(x+2, y+2, cellSize-4, cellSize-4);
        } else {
            ctx.fillStyle = "#2d4a2d"; // Grass
            ctx.fillRect(x, y, cellSize, cellSize);
        }

        // Grid lines
        ctx.strokeStyle = "#222";
        ctx.strokeRect(x, y, cellSize, cellSize);

        // Building Icon
        if (f.occupied) {
            ctx.fillStyle = "white";
            ctx.font = "20px Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText("🏢", x + cellSize / 2, y + cellSize / 2);
        }

        // Selection highlight
        if (i === selectedFieldIndex) {
            ctx.strokeStyle = "white";
            ctx.lineWidth = 2;
            ctx.strokeRect(x + 2, y + 2, cellSize - 4, cellSize - 4);
            ctx.lineWidth = 1;
        }
    });
}

function selectField(idx) {
    selectedFieldIndex = idx;
    drawProvinceCityGrid();
    renderFieldInfo(currentProvinceFields[idx]);
}

async function renderFieldInfo(field) {
    const panel = document.getElementById('selected-field-info');
    if (!panel) return;

    if (field.occupied) {
        panel.innerHTML = `
            <h4>${field.occupied}</h4>
            <p>Typ: ${field.type === 'city' ? 'Stadtfeld' : 'Landfeld'}</p>
            <p>Position: ${field.x}, ${field.y}</p>
            <button class="btn-danger" onclick="demolishAtField(${field.id})">Gebäude Abreißen</button>
        `;
    } else {
        panel.innerHTML = `
            <h4>Freies Feld (${field.x}, ${field.y})</h4>
            <p>Typ: ${field.type === 'city' ? 'Stadtfeld' : 'Landfeld'}</p>
            <div id="build-options-list">Lade Bauoptionen...</div>
        `;
        loadBuildOptions(field);
    }
}

async function loadBuildOptions(field) {
    const container = document.getElementById('build-options-list');
    // Get all templates for now, filter in frontend or backend?
    // Let's use the existing API for available buildings
    try {
        const res = await fetch(`/api/player/${window.currentPlayerId}/buildings/available?province_id=${window.currentProvinzId}`);
        if (!res.ok) return;
        const buildings = await res.json();
        
        container.innerHTML = '';
        buildings.forEach(b => {
            // Check if allowed on this field type
            let allowed = false;
            if (b.bautyp === "Stadt" && field.type === "city") allowed = true;
            if (b.bautyp === "Land" && field.type === "land") allowed = true;
            if (b.bautyp === "Stadtausbau") allowed = true; // Special handling for Stadtausbau?

            if (allowed) {
                const btn = document.createElement('button');
                btn.className = "province-menu-item";
                btn.innerHTML = `<span>${b.name}</span> <small>${b.baukosten_mips} MIPS</small>`;
                btn.onclick = () => buildAtField(b.id, field.id);
                container.appendChild(btn);
            }
        });
    } catch (e) {
        container.innerHTML = "Fehler beim Laden.";
    }
}

async function buildAtField(templateId, fieldId) {
    try {
        const res = await fetch(`/api/province/${window.currentProvinzId}/build`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ template_id: templateId, field_id: fieldId })
        });
        const data = await res.json();
        if (res.ok) {
            showSnackbar("Gebäude errichtet!");
            loadProvinceCityGrid(window.currentProvinzId);
        } else {
            showSnackbar("Baufehler: " + data.detail);
        }
    } catch (e) {
        showSnackbar("Netzwerkfehler beim Bauen.");
    }
}

async function demolishAtField(fieldId) {
    if (!confirm("Gebäude wirklich abreißen? (50% Rückerstattung)")) return;
    try {
        const res = await fetch(`/api/province/${window.currentProvinzId}/demolish/${fieldId}`, {
            method: 'POST'
        });
        if (res.ok) {
            showSnackbar("Gebäude abgerissen.");
            loadProvinceCityGrid(window.currentProvinzId);
            selectedFieldIndex = -1;
            document.getElementById('selected-field-info').innerHTML = '<p>Wähle ein Feld im Grid aus...</p>';
        }
    } catch (e) {
        showSnackbar("Fehler beim Abreißen.");
    }
}

// Attach listener
window.addEventListener('load', () => {
    const canvas = document.getElementById('provinceCityCanvas');
    if (!canvas) return;

    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) / 30);
        const y = Math.floor((e.clientY - rect.top) / 30);
        const idx = y * 15 + x;
        if (idx >= 0 && idx < 225) selectField(idx);
    });
});
