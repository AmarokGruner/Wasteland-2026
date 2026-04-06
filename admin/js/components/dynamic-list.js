// Dynamic List Handler für Admin-Formulare
// Handhabt dynamische Feldlisten (z.B. Terrain-Aufwertungen, Gebäude-Effekte)
// Extrahiert aus admin.html für bessere Wartbarkeit

export const DynamicList = {
    /**
     * Fügt eine neue Zeile zu einer dynamischen Liste hinzu
     */
    addRow(container, listType) {
        const select = document.createElement('select');
        select.className = 'dynamic-select';
        
        // Populate select options based on listType
        if (listType === 'terrain-percent' || listType === 'building-percent') {
            // Get terrain/building options
            select.innerHTML = getTerrainSelectOptions();
        } else if (listType === 'terrain-list') {
            select.innerHTML = getTerrainSelectOptions();
        }
        
        const valueInput = document.createElement('input');
        if (listType === 'terrain-list') {
            valueInput.type = 'text';
            valueInput.placeholder = 'Terrain ID';
        } else {
            valueInput.type = 'number';
            valueInput.placeholder = 'Wert (%)';
            if (listType === 'terrain-percent' || listType === 'building-percent') {
                valueInput.step = '1';
            }
        }
        valueInput.className = 'dynamic-value';
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-danger btn-sm';
        removeBtn.style.marginLeft = '8px';
        removeBtn.textContent = 'X';
        removeBtn.onclick = () => container.removeChild(row);
        
        const row = document.createElement('div');
        row.className = 'dynamic-row';
        row.style.cssText = 'display: flex; gap: 8px; margin-top: 8px; align-items: center;';
        
        row.appendChild(select);
        row.appendChild(valueInput);
        row.appendChild(removeBtn);
        
        container.appendChild(row);
    },
    
    /**
     * Rendert alle Zeilen für eine dynamische Liste aus Daten
     */
    renderFromData(container, listType, data) {
        container.innerHTML = '';
        
        if (listType === 'terrain-percent' || listType === 'building-percent') {
            Object.entries(data || {}).forEach(([key, value]) => {
                this.renderTerrainPercentRow(container, key, value);
            });
        } else if (listType === 'terrain-list') {
            (Array.isArray(data) ? data : []).forEach(key => {
                this.renderTerrainListRow(container, key);
            });
        }
    },
    
    /**
     * Rendert eine Terrain-Prozent-Zeile
     */
    renderTerrainPercentRow(container, key, value) {
        const row = document.createElement('div');
        row.className = 'dynamic-row';
        row.style.cssText = 'display: flex; gap: 8px; margin-top: 8px; align-items: center;';
        
        const select = document.createElement('select');
        select.className = 'dynamic-select';
        select.innerHTML = getTerrainSelectOptions();
        select.value = key;
        
        const valueInput = document.createElement('input');
        valueInput.type = 'number';
        valueInput.className = 'dynamic-value';
        valueInput.placeholder = 'Wert (%)';
        valueInput.value = value;
        valueInput.style.cssText = 'width: 100px;';
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-danger btn-sm';
        removeBtn.style.marginLeft = '8px';
        removeBtn.textContent = 'X';
        removeBtn.onclick = () => row.remove();
        
        row.appendChild(select);
        row.appendChild(valueInput);
        row.appendChild(removeBtn);
        container.appendChild(row);
    },
    
    /**
     * Rendert eine Terrain-Liste-Zeile
     */
    renderTerrainListRow(container, key) {
        const row = document.createElement('div');
        row.className = 'dynamic-row';
        row.style.cssText = 'display: flex; gap: 8px; margin-top: 8px; align-items: center;';
        
        const select = document.createElement('select');
        select.className = 'dynamic-select';
        select.innerHTML = getTerrainSelectOptions();
        select.value = key;
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-danger btn-sm';
        removeBtn.style.marginLeft = '8px';
        removeBtn.textContent = 'X';
        removeBtn.onclick = () => row.remove();
        
        row.appendChild(select);
        row.appendChild(removeBtn);
        container.appendChild(row);
    },
    
    /**
     * Sammelt alle Werte aus einer dynamischen Liste
     */
    collectValues(container, listType) {
        const rows = container.querySelectorAll('.dynamic-row');
        
        if (listType === 'terrain-percent' || listType === 'building-percent') {
            const obj = {};
            rows.forEach(row => {
                const key = row.querySelector('.dynamic-select').value;
                const val = parseInt(row.querySelector('.dynamic-value').value) || 0;
                if (key) obj[key] = val;
            });
            return obj;
        } else if (listType === 'terrain-list') {
            const arr = [];
            rows.forEach(row => {
                const key = row.querySelector('.dynamic-select').value;
                if (key) arr.push(key);
            });
            return arr;
        }
        
        return [];
    }
};

// Helper: Erzeuge Terrain-Select-Options
function getTerrainSelectOptions() {
    // This should be loaded from API or cached data
    // For now, return empty - will be populated when needed
    if (window.terrainOptions) {
        return window.terrainOptions;
    }
    return '<option value="">-- Wählen --</option>';
}

// Exportiere global accessible Funktion für onclick-Handler
window.addDynamicListRow = function(button) {
    const container = button.previousElementSibling;
    if (!container) return;
    
    const listType = container.dataset.type;
    DynamicList.addRow(container, listType);
};
