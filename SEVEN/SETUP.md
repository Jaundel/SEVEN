# SEVEN Setup

Quick setup guide for running SEVEN with local AI inference.

## 1. Install Prerequisites
- **Python 3.12.10** and **Git**
- **Lemonade Server** (official AMD installer)
- Launch Lemonade Server after installation

## 2. Clone and Setup
```bash
git clone https://github.com/<your-org>/SEVEN.git
cd SEVEN
python -m venv .venv
.venv\Scripts\activate              # Windows
pip install -r requirements.txt
```

## 3. Download a Model
1. Open Lemonade Server (system tray icon)
2. Download a small model (1B-3B parameters recommended)
   - Examples: Llama 3.2 1B, Phi 3.5 Mini
3. Note the exact model name displayed

## 4. Configure Environment
Create `.env` file in the SEVEN directory:
```bash
LEMONADE_MODEL=<your-model-name>
LEMONADE_BASE_URL=http://localhost:8000/api/v1

# Optional: Cloud keys for complex queries
GROQ_API_KEY=your_key
OPENAI_API_KEY=your_key
```

## 5. Test and Run
Test local model first:
```bash
python SEVEN/local_model.py "What is 2+2?"
```

If successful, run SEVEN:
```bash
python SEVEN/main.py
```

## Troubleshooting
- **422 errors** → Check model name matches Lemonade Server exactly
- **Connection refused** → Start Lemonade Server
- **DLL errors** → Reinstall Lemonade Server
