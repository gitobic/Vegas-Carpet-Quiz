# Vegas Carpet Quiz - Project Documentation

## Overview
A Streamlit-based quiz app where users identify Las Vegas casino/hotel locations by their carpet patterns. Features 556 carpet images with configurable quiz length and difficulty.

## Tech Stack
- **Framework**: Streamlit (Python)
- **Deployment**: Streamlit Community Cloud
- **Data**: Static images + text metadata files

## Project Structure
```
├── app.py                 # Main Streamlit application
├── carpets/               # 556 carpet images + .txt descriptions
│   ├── [facility]-[type]-[space].jpg
│   └── [facility]-[type]-[space].txt
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── requirements.txt       # Python dependencies
└── README.md
```

## Data Format

### Image Naming Convention
Files follow the pattern: `[facility]-[type]-[space].jpg`

- **facility**: Casino/hotel name (e.g., `aria`, `bellagio`, `mgm-grand`)
- **type**: Area category (one of 8 values): `amenity`, `buffet`, `casino`, `convention`, `hotel`, `lounge`, `restaurant`, `retail`
- **space**: Specific location (e.g., `gaming_floor01`, `lobby_bar`)

### Parsing Strategy
The 8 types are a fixed set. To parse filenames reliably (handling multi-word facilities like "green-valley-ranch"):
1. Split filename on `-`
2. Scan left-to-right for first occurrence of a known type
3. Everything before = facility, the match = type, everything after = space

### Description Files
Each `.jpg` has a matching `.txt` with location/date info:
```
aria-casino-baccarat.txt → "Baccarat February 2022"
```

## Quiz Modes

### Easy Mode
- Identify the facility only
- 4 multiple choice options
- 1 point per correct answer

### Hard Mode (Two-Step)
- Step 1: Identify the facility (4 options)
- Step 2: Identify the area type (8 options)
- Must get BOTH correct to score 1 point

## Session State
Key variables in `st.session_state`:
- `config`: Quiz settings (question_count, difficulty)
- `quiz_questions`: List of selected CarpetImage objects
- `current_index`: Current question (0-based)
- `score`: Running score
- `high_scores`: Dict mapping (difficulty, count) → best score
- `hard_step`: 'facility' or 'type' for two-step mode

## Running Locally
```bash
uv run streamlit run app.py
```

## Deployment
Push to GitHub, connect repo to Streamlit Community Cloud.

## Credits
- Carpet photography: Brent Maynard (https://www.brentmaynard.com/casino-carpet.html)
- App development: T. Gossen and Claude (Anthropic)
