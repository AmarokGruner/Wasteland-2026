t = []
with open('admin.html', encoding='utf-8') as f:
    for i, l in enumerate(f):
        if 'loadTerrain' in l or 'editTerrain' in l or 'loadRegierungs' in l:
            t.append(f"{i+1}: {l.strip()}")
print('\n'.join(t))
