# 🛡️ AI-Powered MDM System
### Mobile Device Management for Android Fleets | Kali Linux | Python 3 | 100% Free AI

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![Kali Linux](https://img.shields.io/badge/Kali-Linux-557C94?logo=kalilinux)](https://kali.org)
[![Ollama](https://img.shields.io/badge/AI-Ollama%20Free-black)](https://ollama.com)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)

---

## 📁 Directory Structure

```
ai-mdm-system/
├── server/           # FastAPI backend (main.py, auth.py, db.py, policy_engine.py)
├── ai/               # AI modules (llm_engine, nl_commander, anomaly_detector, threat_analyzer)
├── dashboard/        # app.py (Textual CLI) + web_dashboard.py (Streamlit)
├── agent/            # agent.py (Android) + bulk_installer.py (ADB deployer)
├── scripts/          # setup.sh (one-shot installer)
├── config/           # config.yaml
└── requirements.txt
```

---

## ⚡ Quick Start

### 1. Clone
```bash
git clone https://github.com/priyanshu-dhaliwal/ai-mdm-system.git
cd ai-mdm-system
```

### 2. One-Shot Setup
```bash
chmod +x scripts/setup.sh && sudo ./scripts/setup.sh
```

### 3. Virtual Environment (prevents Kali conflicts)
```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Init Project
```bash
touch server/__init__.py ai/__init__.py dashboard/__init__.py agent/__init__.py
mkdir -p data reports certs
python3 -c "from server.db import init_db; init_db()"
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem \
    -days 365 -nodes -subj "/CN=MDM-Server"
```

---

## 🤖 AI Model Setup (Free — No API Key)

```bash
curl -fsSL https://ollama.com/install.sh | sh

ollama pull mistral    # 8GB RAM  — RECOMMENDED
ollama pull phi3       # 4GB RAM  — lightweight
ollama pull llama3     # 16GB RAM — smarter

ollama list
```

---

## ▶️ Running the System

```bash
# Activate venv in every terminal
source venv/bin/activate

# Terminal 1 — AI Engine
ollama serve

# Terminal 2 — Backend API
python3 -m server.main

# Terminal 3 — CLI Dashboard
python3 -m dashboard.app

# Terminal 4 — Web Dashboard
streamlit run dashboard/web_dashboard.py --server.port 8501
# Open: http://localhost:8501
```

---

## 📱 Deploy Agent to Android

```bash
# Enable USB debugging on device:
# Settings → About Phone → tap Build Number 7x → Developer Options → USB Debugging ON

python3 agent/bulk_installer.py --list
python3 agent/bulk_installer.py --server YOUR_KALI_IP --port 8000
python3 agent/bulk_installer.py --server YOUR_KALI_IP --wifi-scan 192.168.1.0/24
python3 agent/bulk_installer.py --uninstall
```

---

## 🌐 API Reference

```bash
# Get all devices
curl http://localhost:8000/devices -H "Authorization: Bearer demo_token"

# AI natural language command
curl -X POST http://localhost:8000/ai/command \
  -H "Authorization: Bearer demo_token" \
  -H "Content-Type: application/json" \
  -d '{"input": "Lock all rooted devices", "devices": "all"}'

# Threat analysis
curl -X POST http://localhost:8000/ai/threat-analyze \
  -H "Authorization: Bearer demo_token" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"dev-001","device_name":"Test","metrics":{"is_rooted":true,"usb_debugging":true,"network_tx":350}}'
```

---

## 🐛 Issues & Fixes

### ❌ Issue 1 — scikit-learn fails on Python 3.13
```
ERROR: Could not find a version that satisfies the requirement numpy==2.0.0rc1
ERROR: Failed to build scikit-learn
```
**Cause:** Pinned RC version no longer exists on PyPI.  
**Fix:**
```bash
pip install "numpy>=1.26.4" "scikit-learn>=1.4.0" --break-system-packages
```
> Already fixed in `requirements.txt` — uses `>=` flexible pins instead of `==`.

---

### ❌ Issue 2 — starlette cannot be uninstalled
```
× Cannot uninstall starlette 0.50.0
╰─> no RECORD file was found for starlette
hint: The package was installed by debian.
```
**Cause:** Kali installed starlette via `apt` — pip cannot modify Debian-managed packages.  
**Fix:**
```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```

---

### ❌ Issue 3 — Textual Log markup error
```
TypeError: Log.__init__() got an unexpected keyword argument 'markup'
```
**Cause:** Textual 8.x removed `markup=` param from `Log`. Replaced with `RichLog`.  
**Fix** (already applied in `dashboard/app.py`):
```python
# BEFORE (broken)
from textual.widgets import Log
yield Log(id="al", highlight=True, markup=True)
log.write_line("text")

# AFTER (fixed)
from textual.widgets import RichLog
yield RichLog(id="al", highlight=True, markup=True)
log.write("text")
```

---

### ❌ Issue 4 — StatsPanel refresh() conflict
```
TypeError: StatsPanel.refresh() got an unexpected keyword argument 'layout'
```
**Cause:** Textual 8.x calls `widget.refresh(layout=True)` internally during mount. Custom `refresh()` methods intercept it.  
**Fix** (already applied):
```python
# BEFORE (broken) — conflicts with Textual internals
async def refresh(self): ...
self.set_interval(5, self.refresh)

# AFTER (fixed) — unique method name
async def fetch_data(self): ...
self.set_interval(5, self.fetch_data)
```
> **Rule:** Never name Textual widget methods `refresh()`, `compose()`, or `mount()`.

---

### ⚠️ Issue 5 — Kali tool dependency warnings (non-breaking)
```
theharvester 4.10.1 requires fastapi==0.129.2, but you have fastapi 0.118.0
mitmproxy 12.2.1 requires mitmproxy_rs<0.13
flask-limiter 3.12 requires rich<14
```
**Cause:** Kali pre-installs security tools with conflicting pinned deps. These are warnings only.  
**Fix:** Use virtual environment — already handled in Issue 2.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│               KALI LINUX SERVER                      │
│  Textual CLI ── Streamlit Web ── Ollama AI (Free)   │
│               FastAPI :8000                          │
│    SQLite DB ── Isolation Forest ── Alert Engine    │
└──────────────────────┬──────────────────────────────┘
                       │ WebSocket + HTTPS
              ┌────────┼────────┐
         [Device 1] [Device 2] [Device N]
          Android    Android    Android
           Agent      Agent      Agent
```

---

## ⚠️ Legal Notice
Only deploy on devices you own or have **written authorization** to manage.

## 📦 Stack
FastAPI · Ollama · scikit-learn · Textual · Streamlit · Plotly · SQLite · JWT · ADB
