# GOTC Calculator

A Streamlit app with multiple calculators for player planning in Game of Thrones Conquest (GOTC).

## Features
- Stats Calculator: compute offensive/defensive values and compare against maxed references.
- Dragon vs Dragon Calculator: estimate dragon duel damage and dragon healing gold cost.
- Battle Simulator: estimate troop losses in rally/reinforcement scenarios.
- Wall Damage Calculator: estimate wall damage and break thresholds.

## Prerequisites
- Python 3.10+ (recommended)
- `pip`

## Setup
1. Clone the repository:
```bash
git clone https://github.com/felipeccalegari/GOTC_Calculator.git
cd GOTC_Calculator
```

2. (Recommended but not mandatory) Create and activate a virtual environment:
```bash
python -m venv .venv
```

Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Run The App
```bash
streamlit run landing.py
```

By default, Streamlit opens on:
- Local: `http://localhost:8501`
- Network (LAN): `http://<your-ip>:8501`

## Project Structure
- `landing.py`: app entry page
- `pages/1_Dragon_Vs_Dragon.py`: dragon duel calculator
- `pages/2_Stats_Calculator.py`: stats calculator
- `pages/3_Battle_Simulator.py`: battle simulation
- `pages/4_Wall_Damage.py`: wall damage calculator
- `data/`: JSON data tables used by calculators

## Notes And Disclaimer
- Results are estimates based on simplified formulas and available game data.
- This project is an auxiliary planning tool and is not affiliated with WB Games.
- All game rights and intellectual property belong to their respective owners.

## Troubleshooting
- If Streamlit does not open automatically, manually open `http://localhost:8501`.
- If phone/LAN access fails, confirm:
  - same Wi-Fi network
  - router client isolation is disabled
  - Windows firewall allows inbound TCP `8501`
