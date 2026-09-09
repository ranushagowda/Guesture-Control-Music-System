# 🎵 Gesture Music Controller

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Add your `.mp3`, `.wav`, or `.ogg` songs into the `Song/` folder.

3. Run the app:
```
python main.py
```

---

## Gesture Controls

| Gesture | Action |
|---|---|
| ✋ All 5 fingers open | Pause / Resume |
| ☝️ Index finger only | Volume Up |
| 👍 Thumb only | Volume Down |
| 🤘 Ring finger bent (index+middle up) | Next Song (random) |

---

## Windows
- **Main Window** — Live camera feed with gesture overlay + controls
- **Car Interior Window** — Ambient car dashboard that changes color with volume/music

---

## Notes
- Ambient color shifts from cool blue (low volume) → warm orange/red (high volume)
- Songs play randomly on startup and on "Next Song" gesture
- Cooldown prevents accidental repeated triggers
