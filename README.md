# Neon Vault 🟣⚡

A fast-paced **cyberpunk 2D platformer** built with Python and Pygame.
Race through 10 neon-drenched levels, collect energy crystals, and escape through the **Glitch Gate**!

## 🎮 Features

- **10 hand-crafted levels** with increasing difficulty
- **Double Jump** + **Dash** mechanics
- **Moving platforms** (horizontal & vertical)
- **Laser traps** that blink on/off
- **Speedrun timer** with personal best tracking
- Full neon cyberpunk visual style — no external assets needed
- Smooth camera follow and player trail effect

## 🕹️ Controls

| Key | Action |
|-----|--------|
| ← / → | Move |
| Space | Jump (press again in air for Double Jump) |
| Z or Left Shift | Dash |
| R | Restart current level |
| Esc | Back to menu |

## 🎯 Objective

Collect **all crystals** in the level → the **Glitch Gate** unlocks → reach the gate to advance.
Fall into the void = instant death. ⚠️

## 🚀 How to Run

1. Make sure Python 3.8+ is installed.
2. Install dependencies:
   ```bash
   pip install pygame-ce
   ```
   > **Note:** Uses `pygame-ce` (Community Edition) which supports Python 3.12+.
3. Run the game:
   ```bash
   python main.py
   ```

## 🛠️ Built With

- **Python 3**
- **Pygame**
- Zero external assets — all graphics drawn procedurally with Pygame primitives

## 📁 Project Structure

```
NeonVault/
├── main.py       # Entry point
├── game.py       # Game loop, state machine, rendering
├── sprites.py    # Player, Platform, Crystal, Laser, GlitchDoor
├── levels.py     # All 10 level maps
├── settings.py   # Constants, colours, physics values
└── README.md
```

---

*Can you clear all 10 vaults without dying? 🏆*
