// Admin City Grid Logic
let cityGrid = []; // Array of booleans (225)
let isDragging = false;
let currentMode = true; // true = selecting, false = deselecting
let cityConfigs = {}; // Cached configs per level

async function loadCityGridConfigs() {
    try {
        const res = await fetch('/api/admin/city-config?token=' + localStorage.getItem('token'));
        if (!res.ok) throw new Error("Could not load city configs");
        cityConfigs = await res.json();
        loadCityGridLevel(); // Initial draw
    } catch (e) {
        showSnackbar("Fehler beim Laden der Stadt-Konfig: " + e.message);
    }
}

function loadCityGridLevel() {
    const level = document.getElementById('city-grid-level-select').value;
    const unlocked = cityConfigs[level] || [];
    cityGrid = new Array(225).fill(false);
    unlocked.forEach(id => {
        if (id < 225) cityGrid[id] = true;
    });
    drawCityGrid();
}

function drawCityGrid() {
    const canvas = document.getElementById('cityGridCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const cellSize = 30;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    for (let i = 0; i < 225; i++) {
        const x = i % 15;
        const y = Math.floor(i / 15);
        
        ctx.strokeStyle = '#444';
        ctx.lineWidth = 1;
        ctx.strokeRect(x * cellSize, y * cellSize, cellSize, cellSize);
        
        if (cityGrid[i]) {
            ctx.fillStyle = '#cd853f'; // City tile
            ctx.fillRect(x * cellSize + 1, y * cellSize + 1, cellSize - 2, cellSize - 2);
        } else {
            ctx.fillStyle = '#2d4a2d'; // Grass tile
            ctx.fillRect(x * cellSize + 1, y * cellSize + 1, cellSize - 2, cellSize - 2);
        }
    }
}

async function saveCityGridLevel() {
    const level = parseInt(document.getElementById('city-grid-level-select').value);
    const unlocked_fields = [];
    cityGrid.forEach((val, idx) => {
        if (val) unlocked_fields.push(idx);
    });
    
    try {
        const res = await fetch('/api/admin/city-config?token=' + localStorage.getItem('token'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level, unlocked_fields })
        });
        if (!res.ok) throw new Error("Save failed");
        
        cityConfigs[level] = unlocked_fields;
        showSnackbar(`Konfiguration für Level ${level} gespeichert.`);
    } catch (e) {
        showSnackbar("Fehler beim Speichern: " + e.message);
    }
}

async function syncProvinceFields() {
    if (!confirm("Dies initialisiert die Grid-Felder für alle Provinzen in der DB, falls noch nicht vorhanden. Fortfahren?")) return;
    
    try {
        const res = await fetch('/api/admin/city-config/sync-provinces?token=' + localStorage.getItem('token'), {
            method: 'POST'
        });
        const data = await res.json();
        showSnackbar(`${data.provinces_initialized} Provinzen initialisiert.`);
    } catch (e) {
        showSnackbar("Sync Fehler: " + e.message);
    }
}

// Event Listeners for Canvas
window.addEventListener('load', () => {
    const canvas = document.getElementById('cityGridCanvas');
    if (!canvas) return;
    
    canvas.addEventListener('mousedown', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) / 30);
        const y = Math.floor((e.clientY - rect.top) / 30);
        const idx = y * 15 + x;
        
        if (idx >= 0 && idx < 225) {
            isDragging = true;
            currentMode = !cityGrid[idx];
            cityGrid[idx] = currentMode;
            drawCityGrid();
        }
    });
    
    canvas.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const rect = canvas.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) / 30);
        const y = Math.floor((e.clientY - rect.top) / 30);
        const idx = y * 15 + x;
        
        if (idx >= 0 && idx < 225) {
            cityGrid[idx] = currentMode;
            drawCityGrid();
        }
    });
    
    window.addEventListener('mouseup', () => {
        isDragging = false;
    });
});
