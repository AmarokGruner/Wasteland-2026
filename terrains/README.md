# Terrain Bilder (30x30 PNG)

Platzhalter für Terrain-Grafiken. Jede Datei sollte 30x30 Pixel groß sein.

## Benötigte Dateien:

- ocean.png (Ozean - Blau)
- desert.png (Wüste - Sandfarben)
- grass.png (Grasland - Grün)
- mountain.png (Gebirge - Grau)
- forest.png (Wald - Dunkelgrün)
- wasteland.png (Ödland - Braun)
- radioactive.png (Verstrahlt - Giftgrün)
- ruins.png (Ruinen - Grau mit Rot)
- bunker.png (Bunker - Metallisch)
- city.png (Stadt - Grau)

## Erstellen:
Nutze ein Grafikprogramm oder generiere einfache Farbflächen:
```python
from PIL import Image
img = Image.new('RGB', (30, 30), color='#1a4d7a')  # Ozean
img.save('ocean.png')
```
