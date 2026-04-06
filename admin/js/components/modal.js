// Generic Modal Handler für Admin-CRUD-Operationen
// Extrahiert aus admin.html für bessere Wartbarkeit

export const GenericModal = {
    /**
     * Öffnet ein generisches Modal basierend auf Entity-Konfiguration
     */
    open(mode, entityType, data = null, entityConfig) {
        const config = entityConfig[entityType];
        if (!config) {
            console.error(`Entity ${entityType} not found in config`);
            return;
        }
        
        const modal = document.getElementById('genericModal');
        if (!modal) {
            console.error('GenericModal element not found');
            return;
        }
        
        modal.querySelector('h3').textContent = mode === 'create'
            ? `Neuer ${config.label}`
            : `${config.label} bearbeiten`;
        
        const form = document.getElementById('genericForm');
        form.dataset.mode = mode;
        form.dataset.entity = entityType;
        form.dataset.endpoint = config.endpoint;
        form.dataset.id = data ? (data.id ?? '') : '';
        
        // Build form HTML
        form.innerHTML = this.buildFormHTML(config, data) +
            `<div style="margin-top:16px"><button type="submit" class="btn btn-primary">Speichern</button></div>`;
        
        modal.classList.add('active');
    },
    
    /**
     * Schließt das generische Modal
     */
    close() {
        const modal = document.getElementById('genericModal');
        if (modal) {
            modal.classList.remove('active');
        }
    },
    
    /**
     * Erzeugt Formular-HTML basierend auf Entity-Konfiguration
     */
    buildFormHTML(config, data = null) {
        return config.fields.map(f => {
            const val = data ? (data[f.name] ?? '') : '';
            let input = '';
            const readonly = f.readonly ? 'readonly style="opacity:0.6"' : '';
            
            if (f.type === 'select') {
                const opts = Array.isArray(f.options)
                    ? f.options.map(o => {
                        const v = typeof o === 'object' ? o.v : o;
                        const l = typeof o === 'object' ? o.label : o;
                        return `<option value="${v}" ${String(val) === String(v) ? 'selected' : ''}>${l}</option>`;
                    }).join('')
                    : '';
                input = `<select name="${f.name}" ${readonly}>${opts}</select>`;
            } else if (f.type === 'textarea') {
                input = `<textarea name="${f.name}" ${readonly}>${val}</textarea>`;
            } else if (f.type === 'json') {
                const jsonVal = typeof val === 'object' ? JSON.stringify(val, null, 2) : (val || '{}');
                input = `<textarea name="${f.name}" class="json-editor" ${readonly}>${jsonVal}</textarea>`;
            } else if (f.type === 'dynamic-list') {
                // Will be handled by DynamicList component
                input = `<div class="dynamic-list-container" data-name="${f.name}" data-type="${f.listType}"></div>
                         <button type="button" class="btn btn-secondary btn-sm" style="margin-top:4px" onclick="addDynamicListRow(this)">+ Hinzufügen</button>`;
            } else if (f.type === 'color') {
                input = `<input type="color" name="${f.name}" value="${val || '#444444'}" ${readonly}>`;
            } else {
                const step = f.step ? `step="${f.step}"` : '';
                input = `<input type="${f.type}" name="${f.name}" value="${val}" 
                        ${f.required ? 'required' : ''} ${step} ${readonly}>`;
            }
            
            // Image preview for bild_url
            if (f.name === 'bild_url' || f.name === 'bild') {
                const currentImg = val 
                    ? `<img src="${val}" style="display:block; max-width:100px; margin-top:8px; border:1px solid #555;" id="preview_${f.name}">` 
                    : `<img src="" style="display:none; max-width:100px; margin-top:8px; border:1px solid #555;" id="preview_${f.name}">`;
                input += currentImg;
            }
            
            return `<div class="form-group"><label>${f.label}</label>${input}</div>`;
        }).join('');
    },
    
    /**
     * Zeigt ein Bild-Vorschau wenn URL geändert wird
     */
    setupImagePreview(fieldName) {
        setTimeout(() => {
            const inp = document.querySelector(`input[name="${fieldName}"]`);
            if (inp) {
                inp.addEventListener('input', (e) => {
                    const img = document.getElementById(`preview_${fieldName}`);
                    if (img) {
                        img.src = e.target.value;
                        img.style.display = e.target.value ? 'block' : 'none';
                    }
                });
            }
        }, 100);
    }
};

// Convenience function für showCreateModal
export function showCreateModal(type, entityConfig) {
    if (entityConfig[type]) {
        window.openGenericModal('create', type, null, entityConfig);
        return true;
    }
    return false;
}
