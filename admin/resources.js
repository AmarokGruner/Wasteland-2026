(() => {
  const apiBase = '/api';
  let fields = [];
  let buildings = [];
  let currentResource = null;

  async function loadFields() {
    const res = await fetch(apiBase + '/resources/fields');
    fields = await res.json();
  }

  async function loadBuildings() {
    const res = await fetch(apiBase + '/buildings');
    buildings = await res.json();
  }

  async function loadResources() {
    const res = await fetch(apiBase + '/resources');
    return await res.json();
  }

  function renderTable(results) {
    const thead = document.getElementById('thead');
    const tbody = document.getElementById('tbody');
    thead.innerHTML = '';
    tbody.innerHTML = '';
    // simple fixed columns for now
    thead.innerHTML = '<tr><th>ID</th><th>Name</th><th>Typ</th><th>Produktionswert</th><th>Aktionen</th></tr>';
    results.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${r.id}</td><td>${r.name || ''}</td><td>${r.type || ''}</td><td>${r.production_value ?? ''}</td>`;
      const td = document.createElement('td');
      const btn = document.createElement('button');
      btn.textContent = 'Bearbeiten';
      btn.dataset.id = r.id;
      btn.addEventListener('click', () => openEditor(r));
      td.appendChild(btn);
      tr.appendChild(td);
      tbody.appendChild(tr);
    });
  }

  async function openEditor(resource) {
    currentResource = resource ? resource : null;
    const modal = document.getElementById('editorModal');
    const form = document.getElementById('editorForm');
    form.innerHTML = '';
    // title
    document.getElementById('modalTitle').textContent = resource ? 'Resource bearbeiten' : 'Neue Resource';
    // build fields
    const fieldsToRender = fields;
    const idField = document.createElement('input');
    idField.type = 'hidden';
    idField.name = 'id';
    if (resource && resource.id) idField.value = resource.id;
    form.appendChild(idField);
    fieldsToRender.forEach(f => {
      const wrapper = document.createElement('div');
      wrapper.style.gridColumn = 'span 2';
      const label = document.createElement('label');
      label.textContent = f.label || f.name;
      wrapper.appendChild(label);
      let input;
      const val = resource ? resource[f.name] : undefined;
      switch (f.type) {
        case 'string':
        case 'number':
        case 'text':
          if (f.type === 'text') {
            input = document.createElement('textarea');
            input.name = f.name;
            input.value = val ?? '';
          } else {
            input = document.createElement('input');
            input.type = f.type === 'number' ? 'number' : 'text';
            input.name = f.name;
            input.value = val ?? '';
          }
          input.style.width = '100%';
          wrapper.appendChild(input);
          break;
        case 'enum':
          input = document.createElement('select');
          input.name = f.name;
          (f.options || []).forEach(opt => {
            const o = document.createElement('option');
            o.value = opt;
            o.textContent = opt;
            if (val === opt) o.selected = true;
            input.appendChild(o);
          });
          wrapper.appendChild(input);
          break;
        case 'relation':
          input = document.createElement('select');
          input.name = f.name;
          input.multiple = true;
          buildings.forEach(b => {
            const o = document.createElement('option');
            o.value = b.id; o.textContent = b.name;
            if (Array.isArray(val) && val.includes(b.id)) o.selected = true;
            input.appendChild(o);
          });
          wrapper.appendChild(input);
          break;
        default:
          input = document.createElement('input');
          input.name = f.name; input.value = val ?? '';
          wrapper.appendChild(input);
      }
      form.appendChild(wrapper);
    });
    modal.style.display = 'flex';
  }

  function closeEditor() {
    const modal = document.getElementById('editorModal');
    modal.style.display = 'none';
  }

  async function saveResource() {
    const form = document.getElementById('editorForm');
    const formData = new FormData(form);
    const payload = { name: formData.get('name'), type: formData.get('type'),
      production_value: formData.get('production_value') ? Number(formData.get('production_value')) : undefined,
      land_transport_cost: formData.get('land_transport_cost') ? Number(formData.get('land_transport_cost')) : undefined,
      water_transport_cost: formData.get('water_transport_cost') ? Number(formData.get('water_transport_cost')) : undefined,
      air_transport_cost: formData.get('air_transport_cost') ? Number(formData.get('air_transport_cost')) : undefined,
      description: formData.get('description'),
      consumption_per_1000_per_day: formData.get('consumption_per_1000_per_day') ? Number(formData.get('consumption_per_1000_per_day')) : undefined,
      consumes_buildings: formData.getAll('consumes_buildings') || [],
      produces_buildings: formData.getAll('produces_buildings') || []
    };
    const id = formData.get('id');
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/resources/${id}` : '/api/resources';
    const resp = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!resp.ok) {
      alert('Fehler beim Speichern');
      return;
    }
    closeEditor();
    await loadAndRender();
  }

  async function loadAndRender() {
    const resources = await loadResources();
    renderTable(resources);
  }

  document.addEventListener('DOMContentLoaded', async () => {
    // wires
    document.getElementById('btnNew').addEventListener('click', () => openEditor(null));
    document.getElementById('btnSave').addEventListener('click', saveResource);
    document.getElementById('btnCancel').addEventListener('click', () => closeEditor());
    document.getElementById('modalClose').addEventListener('click', () => closeEditor());
    // init
    await loadFields();
    await loadBuildings();
    const resources = await loadResources();
    renderTable(resources);
  });
})();
