# Arena Trainer

Kleines, eigenständiges Reflex-Trainingstool (Ausweichen, Zielen/Vorhalten,
Super-Timing), inspiriert von Arena-Shooter-Mechaniken. Kein offizieller
Bezug zu Supercell/Brawl Stars, keine Spieldateien werden verändert.

## Steuerung

- **WASD / Pfeiltasten** — bewegen, feindlichen Projektilen ausweichen
- **Maus + Klick** — auf das bewegliche Ziel schießen (Vorhalten nötig, da
  die Schüsse eine Flugzeit haben)
- **Leertaste** — bei vollem Super-Balken einen Super-Blast auslösen
  (räumt alle Projektile weg, kurze Unverwundbarkeit, Bonuspunkte)

Schwierigkeit (Spawnrate & Projektilgeschwindigkeit der Gegner) steigt mit
der Überlebenszeit.

## Browser-Version

Einfach öffnen, kein Build nötig:

```
web/index.html
```

## Python-Version

```
cd python
pip install -r requirements.txt
python trainer.py
```
