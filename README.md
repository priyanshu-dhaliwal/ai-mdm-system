# 🛡️ AI-Powered MDM System

### Mobile Device Management for Android Fleets
**Kali Linux · Python 3 · Ollama AI (100% Free & Local)**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Kali Linux](https://img.shields.io/badge/Kali-Linux-557C94?style=for-the-badge&logo=kalilinux&logoColor=white)](https://kali.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/Ollama-AI%20Free-000000?style=for-the-badge)](https://ollama.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<br/>

> An advanced, AI-powered Mobile Device Management system built for Android fleets (20–100 devices).  
> Manage, monitor, and secure devices using **natural language commands** — all AI runs locally, no cloud, no API keys.

</div>

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Directory Structure](#-directory-structure)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [AI Model Setup](#-ai-model-setup)
- [Running the System](#-running-the-system)
- [Android Agent Deployment](#-android-agent-deployment)
- [Dashboard Guide](#-dashboard-guide)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Known Issues & Fixes](#-known-issues--fixes)
- [Tech Stack](#-tech-stack)
- [Legal Notice](#-legal-notice)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Natural Language Commands** | Control any device or fleet in plain English — powered by local Ollama LLM |
| 🔍 **Threat Analyzer** | 15+ detection rules mapped to **MITRE ATT&CK Mobile** framework |
| 📊 **Anomaly Detection** | Per-device **Isolation Forest** ML model detects behavioral anomalies |
| 🔒 **Policy Engine** | Auto-enforce security rules; AI generates policies from plain text |
| 🖥️ **Dual Dashboard** | **Textual** CLI dashboard + **Streamlit** web UI with Plotly charts |
| 📱 **Bulk ADB Installer** | Deploy agent to 20–100 devices in parallel via USB or WiFi ADB |
| 🚨 **Real-Time Alerts** | WebSocket-powered live alert feed with AI-generated explanations |
| 🔐 **JWT Authentication** | Secure token-based auth with bcrypt password hashing |
| 📄 **Threat Reports** | AI generates executive summaries + technical narratives per device |
| 🆓 **100% Free AI** | Ollama runs locally — no OpenAI key, no cloud costs, no data leaves your server |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      KALI LINUX SERVER                            │
│                                                                   │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │  Textual CLI │   │  Streamlit   │   │   Ollama AI Engine   │ │
│  │  Dashboard   │   │   Web UI     │   │  mistral / llama3    │ │
│  │  (port CLI)  │   │  :8501       │   │  :11434  (local)     │ │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬───────────┘ │
│         └──────────────────┼──────────────────────┘             │
│  ┌─────────────────────────▼──────────────────────────────────┐ │
│  │                 FastAPI Server  :8000                      │ │
│  │     REST API · WebSocket Hub · Policy Engine · AI Advisor  │ │
│  └──────────────────┬──────────────────────────────────────── ┘ │
│                     │                                            │
│  ┌──────────────────▼────────────────────────────────────────┐  │
│  │   SQLite DB  │  Isolation Forest ML  │   Alert Engine     │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬───────────────────────────────────┘
                               │  HTTPS + WebSocket (WSS)
                ┌──────────────┼──────────────┐
           ┌────▼─────┐  ┌────▼─────┐  ┌─────▼────┐
           │ Device 1 │  │ Device 2 │  │ Device N │
           │ Android  │  │ Android  │  │ Android  │
           │  Agent   │  │  Agent   │  │  Agent   │
           └──────────┘  └──────────┘  └──────────┘
```

---

## 📁 Directory Structure

```
mdm_full/
│
├── 📂 server/                        # FastAPI backend
│   ├── __init__.py
│   ├── main.py                       # Main server + WebSocket connection hub
│   ├── auth.py                       # JWT token creation & verification
│   ├── db.py                         # SQLAlchemy models (Device, Alert, Policy, Metrics)
│   └── policy_engine.py              # Automatic policy evaluation & enforcement
│
├── 📂 ai/                            # AI & ML modules
│   ├── __init__.py
│   ├── llm_engine.py                 # Ollama LLM async/sync wrapper
│   ├── nl_commander.py               # Natural language → structured device command
│   ├── anomaly_detector.py           # Per-device Isolation Forest anomaly detection
│   └── threat_analyzer.py           # MITRE ATT&CK threat analysis (15+ rules)
│
├── 📂 dashboard/                     # User interfaces
│   ├── __init__.py
│   ├── app.py                        # Textual TUI CLI dashboard (fixed for v8.x)
│   └── web_dashboard.py              # Streamlit web dashboard (8 pages)
│
├── 📂 agent/                         # Android device agent
│   ├── agent.py                      # Lightweight agent (deploy via ADB to Android)
│   └── bulk_installer.py             # Parallel ADB installer (USB + WiFi)
│
├── 📂 scripts/
│   └── setup.sh                      # One-shot Kali Linux setup script
│
├── 📂 config/
│   └── config.yaml                   # All system settings
│
├── 📂 certs/                         # Auto-generated TLS certs (after setup)
│   ├── cert.pem
│   └── key.pem
│
├── 📂 data/                          # Runtime data (auto-created)
│   ├── mdm.db                        # SQLite database
│   └── sessions/                     # Session logs
│
├── 📂 reports/                       # Generated threat reports
│
├── push_to_github.sh                 # One-click GitHub push script
└── requirements.txt                  # Python dependencies (Python 3.11–3.13 compatible)
```

---

## 📦 Requirements

### System
- **OS:** Kali Linux (recommended) or any Debian-based Linux
- **Python:** 3.11 or higher
- **RAM:** Minimum 8 GB (for Mistral 7B AI model)
- **Storage:** ~10 GB free (4 GB for AI model + project)
- **Android devices:** USB debugging enabled

### Python Packages
```
fastapi >= 0.110.0       # Web framework
uvicorn >= 0.27.0        # ASGI server
websockets >= 12.0       # Real-time device comms
sqlalchemy >= 2.0.0      # Database ORM
python-jose >= 3.3.0     # JWT authentication
passlib >= 1.7.4         # Password hashing
httpx >= 0.27.0          # Async HTTP client
numpy >= 1.26.4          # Numerical computing
scikit-learn >= 1.4.0    # Isolation Forest ML
textual >= 0.52.0        # CLI dashboard framework
rich >= 13.7.0           # Terminal formatting
streamlit >= 1.32.0      # Web dashboard
plotly >= 5.20.0         # Interactive charts
pandas >= 2.1.0          # Data manipulation
```

---

## 🚀 Installation

### Option A — One-Shot Setup (Recommended)

```bash
# Clone the project
git clone https://github.com/YOUR_USERNAME/ai-mdm-system.git
cd ai-mdm-system

# Run automated setup (installs everything)
chmod +x scripts/setup.sh
sudo ./scripts/setup.sh
```

The setup script automatically:
- Updates Kali Linux packages
- Installs Python3, ADB, Nmap, OpenSSL, SQLite3
- Installs Ollama (free local AI)
- Downloads Mistral 7B model
- Installs all Python packages
- Generates self-signed TLS certificates
- Initializes the SQLite database
- Configures UFW firewall rules (ports 8000, 8501)

---

### Option B — Manual Step-by-Step

#### 1. System Packages
```bash
sudo apt update && sudo apt install -y \
    python3 python3-pip python3-venv python3-dev \
    adb nmap openssl sqlite3 curl git build-essential
```

#### 2. Virtual Environment (prevents Kali conflicts)
```bash
cd ai-mdm-system
python3 -m venv venv --system-site-packages
source venv/bin/activate
```

#### 3. Python Packages
```bash
pip install -r requirements.txt
```

#### 4. Initialize Project
```bash
# Create package init files
touch server/__init__.py ai/__init__.py dashboard/__init__.py agent/__init__.py

# Create directories
mkdir -p data reports certs

# Initialize database
python3 -c "from server.db import init_db; init_db()"
```

#### 5. Generate TLS Certificates
```bash
openssl req -x509 -newkey rsa:4096 \
    -keyout certs/key.pem \
    -out certs/cert.pem \
    -days 365 -nodes \
    -subj "/CN=MDM-Server/O=MDM-Security/C=US"
```

---

## 🤖 AI Model Setup

The system uses **Ollama** — a free, local LLM runner. No API keys, no internet required during use.

### Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Pull a Model

| Model | RAM Required | Best For | Command |
|---|---|---|---|
| `phi3` | 4 GB | Low-spec machines | `ollama pull phi3` |
| `mistral` | 8 GB | **Default — recommended** | `ollama pull mistral` |
| `llama3` | 16 GB | Better reasoning | `ollama pull llama3` |
| `llama3:8b` | 16 GB | Smarter analysis | `ollama pull llama3:8b` |
| `codellama` | 8 GB | Code/script analysis | `ollama pull codellama` |

```bash
# Pull recommended model
ollama pull mistral

# Verify it downloaded
ollama list

# Test it works
ollama run mistral "Explain USB debugging risks on Android in 2 sentences"

# Check API is live
curl http://localhost:11434/api/tags
```

### Change Model
Edit `config/config.yaml`:
```yaml
ai:
  model: "llama3"    # Change this line
```

---

## ▶️ Running the System

> **Always activate your virtual environment first in every terminal:**
> ```bash
> source venv/bin/activate
> ```

Open **4 terminals** and run one command in each:

### Terminal 1 — AI Engine
```bash
ollama serve
```

### Terminal 2 — Backend API Server
```bash
python3 -m server.main

# Expected output:
# ✅ Database initialized at data/mdm.db
# INFO: Uvicorn running on http://0.0.0.0:8000
# INFO: WebSocket ready at ws://0.0.0.0:8000/ws/device/{device_id}
```

### Terminal 3 — CLI Dashboard (Textual TUI)
```bash
python3 -m dashboard.app

# Keyboard shortcuts:
# q     → Quit
# r     → Refresh
# Tab   → Switch panels
# Enter → Send AI command
```

### Terminal 4 — Web Dashboard (Streamlit)
```bash
streamlit run dashboard/web_dashboard.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --theme.base dark

# Then open in browser:
# Local:   http://localhost:8501
# Network: http://YOUR_KALI_IP:8501
```

---

## 📱 Android Agent Deployment

### Step 1 — Enable USB Debugging on Each Device
```
Settings → About Phone
  → Tap "Build Number" 7 times  (unlocks Developer Options)

Settings → Developer Options
  → USB Debugging: ON
  → (Optional) Wireless Debugging: ON
```

### Step 2 — Connect and Verify
```bash
# Connect via USB cable and accept RSA fingerprint popup on device
adb devices -l

# Expected:
# List of devices attached
# R58N21ABCDE   device   model:Pixel_7
```

### Step 3 — Deploy Agent

```bash
# List all connected devices
python3 agent/bulk_installer.py --list

# Install on ALL connected USB devices
python3 agent/bulk_installer.py \
    --server YOUR_KALI_IP \
    --port 8000 \
    --token demo_token

# Install on specific devices only
python3 agent/bulk_installer.py \
    --server 192.168.1.100 \
    --serials emulator-5554,R58N21ABCDE

# WiFi ADB — scan subnet and install wirelessly
python3 agent/bulk_installer.py \
    --server 192.168.1.100 \
    --wifi-scan 192.168.1.0/24

# Use 10 parallel workers for large fleets
python3 agent/bulk_installer.py \
    --server 192.168.1.100 \
    --workers 10

# Uninstall agent from all devices
python3 agent/bulk_installer.py --uninstall

# Save enrollment manifest to custom path
python3 agent/bulk_installer.py \
    --server 192.168.1.100 \
    --output /home/kali/fleet_enrollment.json
```

### WiFi ADB Setup (cable-free after initial setup)
```bash
# One-time per device (while USB still connected):
adb tcpip 5555
adb connect 192.168.1.DEVICE_IP:5555

# Disconnect USB — device now reachable wirelessly
```

### Testing Without Physical Devices
```bash
# Use Android emulator
sudo apt install qemu-kvm -y
emulator -avd Pixel_7_API_34

# Deploy to emulator
python3 agent/bulk_installer.py \
    --server localhost \
    --serials emulator-5554
```

---

## 🖥️ Dashboard Guide

### Web Dashboard Pages (Streamlit — port 8501)

| Page | Features |
|---|---|
| **📊 Overview** | KPI cards, risk bar chart, severity pie chart, live alert feed, battery heatmap |
| **📱 Fleet Manager** | Device cards with filters (status/group/risk), per-device action buttons |
| **🚨 Alerts** | Severity-filtered alert feed, AI analysis display, resolve/investigate actions |
| **🤖 AI Commander** | Chat-style NL command interface, AI policy generator, command history |
| **🔒 Policy Engine** | Policy table with toggles, create new policies via form |
| **🔍 Threat Analyzer** | Per-device deep scan, risk gauge, MITRE ATT&CK coverage, remediation steps |
| **📈 Analytics** | 30-day risk timeline, policy group comparison, alert category breakdown |
| **⚙️ Settings** | AI config, security toggles, server config, token management |

### AI Natural Language Command Examples
```
"Lock all rooted devices immediately"
"Disable WiFi on devices in the warehouse group"
"Reboot Device-003"
"Create a policy to block USB debugging on all devices"
"Enable airplane mode on devices connected to unknown WiFi"
"Push a security alert to the finance group"
"Get battery status for all offline devices"
```

---

## 🌐 API Reference

**Base URL:** `http://localhost:8000`  
**Auth Header:** `Authorization: Bearer demo_token`

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/devices` | List all fleet devices |
| `GET` | `/alerts?limit=50` | Get recent alerts |
| `GET` | `/stats` | Fleet health statistics |
| `POST` | `/ai/command` | Parse and execute NL command |
| `POST` | `/ai/policy` | Generate policy from description |
| `POST` | `/ai/threat-analyze` | Run full threat analysis |
| `WS` | `/ws/device/{id}` | Device WebSocket connection |

### Example Requests

```bash
# Get all devices
curl http://localhost:8000/devices \
    -H "Authorization: Bearer demo_token"

# Get fleet stats
curl http://localhost:8000/stats \
    -H "Authorization: Bearer demo_token"

# AI natural language command
curl -X POST http://localhost:8000/ai/command \
    -H "Authorization: Bearer demo_token" \
    -H "Content-Type: application/json" \
    -d '{"input": "Lock all rooted devices immediately", "devices": "all"}'

# Generate AI policy from description
curl -X POST http://localhost:8000/ai/policy \
    -H "Authorization: Bearer demo_token" \
    -H "Content-Type: application/json" \
    -d '{"text": "Block devices connecting to unknown WiFi networks and send an alert"}'

# Run threat analysis on a device
curl -X POST http://localhost:8000/ai/threat-analyze \
    -H "Authorization: Bearer demo_token" \
    -H "Content-Type: application/json" \
    -d '{
        "device_id":   "dev-001",
        "device_name": "Samsung-S23-Finance",
        "metrics": {
            "battery":          45,
            "cpu_usage":        78,
            "ram_usage":        62,
            "network_tx":       350,
            "is_rooted":        true,
            "usb_debugging":    true,
            "developer_mode":   false,
            "battery_drain_rate": 20,
            "wifi_ssid":        "FreeAirportWifi",
            "allowed_ssids":    ["CorpWifi", "MDM-SECURE"]
        },
        "app_list": [
            {"package": "com.spy.tracker", "name": "SpyTracker", "sideloaded": true}
        ]
    }'
```

---

## ⚙️ Configuration

Edit `config/config.yaml` to customize the system:

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  tls_cert: "./certs/cert.pem"
  tls_key:  "./certs/key.pem"

ai:
  ollama_host: "http://localhost:11434"
  model: "mistral"          # mistral | llama3 | phi3 | codellama
  temperature: 0.1          # Lower = more precise (0.0 – 1.0)
  max_tokens: 1000
  timeout: 60               # seconds

security:
  enrollment_token: "CHANGE_ME_IN_PRODUCTION"
  jwt_expire_hours: 8
  block_rooted_devices: true
  require_screen_lock: true
  min_battery_threshold: 10  # % below which alert fires

fleet:
  heartbeat_interval: 30    # seconds between device pings
  device_timeout: 90        # seconds before marked offline
  max_devices: 100

alerts:
  min_severity: "MEDIUM"    # LOW | MEDIUM | HIGH | CRITICAL
  slack_webhook: ""         # optional Slack integration
```

---

## 🐛 Known Issues & Fixes

### ❌ Issue 1 — scikit-learn build fails on Python 3.13

**Error:**
```
ERROR: Could not find a version that satisfies the requirement numpy==2.0.0rc1
ERROR: Failed to build 'scikit-learn' when installing build dependencies
```

**Root Cause:**  
Old `requirements.txt` used exact `==` pins with a yanked release candidate (`numpy==2.0.0rc1`) that no longer exists on PyPI. Python 3.13 also has no pre-built `scikit-learn==1.4.1` wheel, forcing a source build that fails.

**Fix ✅ (already applied in `requirements.txt`):**
```bash
# Use flexible >= pins — pip finds the right pre-built wheel automatically
pip install "numpy>=1.26.4" "scikit-learn>=1.4.0" --break-system-packages
```
Changed all `==` pins to `>=` in `requirements.txt`.

---

### ❌ Issue 2 — Cannot uninstall starlette (Debian-managed package)

**Error:**
```
× Cannot uninstall starlette 0.50.0
╰─> The package's contents are unknown: no RECORD file was found for starlette.
hint: The package was installed by debian. You should check if it can uninstall the package.
```

**Root Cause:**  
Kali Linux installs many Python packages via `apt` (Debian-managed). These packages have no `RECORD` file, so pip cannot track or uninstall them.

**Fix ✅ — Use virtual environment:**
```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```
The `--system-site-packages` flag inherits Kali's system packages without pip trying to reinstall or uninstall them.

---

### ❌ Issue 3 — Textual `Log` markup keyword removed in v8.x

**Error:**
```
TypeError: Log.__init__() got an unexpected keyword argument 'markup'

AlertPanel() compose() method returned an invalid result;
Log.__init__() got an unexpected keyword argument 'markup'
```

**Root Cause:**  
Textual 8.x split the `Log` widget into two separate widgets:
- `Log` — plain text only, no markup support
- `RichLog` — supports `markup=True`, `highlight=True`, rich formatting

**Fix ✅ (already applied in `dashboard/app.py`):**
```python
# ❌ BEFORE — broken on Textual 8.x
from textual.widgets import Log
yield Log(id="al", highlight=True, markup=True)
log.write_line("text with [bold]markup[/bold]")

# ✅ AFTER — fixed
from textual.widgets import RichLog
yield RichLog(id="al", highlight=True, markup=True)
log.write("text with [bold]markup[/bold]")
```

---

### ❌ Issue 4 — StatsPanel.refresh() conflicts with Textual 8.x internals

**Error:**
```
TypeError: StatsPanel.refresh() got an unexpected keyword argument 'layout'

NOTE: 1 of 4 errors shown. Run with textual run --dev to see all errors.
```

**Root Cause:**  
Textual 8.x calls `widget.refresh(layout=True)` internally during the mount phase. Our custom `refresh()` method intercepted this internal call and crashed because it doesn't accept a `layout` keyword argument.

Affected classes: `DeviceTable`, `AlertPanel`, `StatsPanel`

**Fix ✅ (already applied in `dashboard/app.py`):**
```python
# ❌ BEFORE — name collides with Textual's built-in refresh()
def on_mount(self):
    self.set_interval(5, self.refresh)      # ← crash on Textual 8.x

async def refresh(self):                    # ← conflicts with internal call
    ...fetch data...

# ✅ AFTER — unique method name, no conflict
def on_mount(self):
    self.set_interval(5, self.fetch_data)   # ← safe unique name

async def fetch_data(self):                 # ← no collision
    ...fetch data...
```

> **Rule for Textual 8.x:** Never name custom widget methods `refresh()`, `compose()`, `mount()`, or `on_mount()` as standalone data methods — these are reserved Textual lifecycle names.

---

### ⚠️ Issue 5 — Kali tool dependency conflict warnings (non-breaking)

**Warning output during install:**
```
ERROR: pip's dependency resolver does not currently take into account all packages...
theharvester 4.10.1 requires fastapi==0.129.2, but you have fastapi 0.118.0
mitmproxy 12.2.1 requires mitmproxy_rs<0.13, which is not installed.
flask-limiter 3.12 requires rich<14, but you have rich 14.x
faradaysec 5.19.0 requires bcrypt<5.0.0, but you have bcrypt 5.0.0
lsassy 3.1.11 requires netaddr<0.9.0, but you have netaddr 1.3.0
```

**Root Cause:**  
Kali Linux pre-installs many security tools (mitmproxy, theharvester, faradaysec, lsassy) with tightly pinned dependency versions. These conflict with MDM's more recent package versions.

**Impact:**  
⚠️ **These are warnings only** — MDM packages install and run correctly. However, some Kali tools may break if invoked after installing to system Python.

**Fix ✅ — Virtual environment isolation:**
```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
# MDM runs isolated — Kali tools remain untouched
```

---

## 🔬 Threat Detection Coverage

### MITRE ATT&CK Mobile Techniques Detected

| Technique ID | Name | Detection Rule |
|---|---|---|
| T1401 | Device Administrator Permissions | Root access detection |
| T1400 | Modify System Partition | Root + system partition check |
| T1406 | Obfuscated Files or Information | Developer mode / USB debug |
| T1516 | Input Injection | USB debugging enabled |
| T1407 | Download New Code at Runtime | Sideloaded / unknown apps |
| T1437 | Application Layer Protocol | High network TX anomaly |
| T1533 | Data from Local System | Data exfiltration indicators |
| T1521 | Encrypted Channel | Unusual outbound traffic |
| T1430 | Location Tracking | Battery drain + GPS activity |
| T1429 | Capture Audio | Background mic usage indicators |
| T1512 | Video Capture | Screen recording detection |
| T1513 | Screen Capture | Active screen recording |
| T1517 | Access Notifications | Accessibility service abuse |
| T1461 | Lockscreen Bypass | Multiple failed unlock attempts |
| T1412 | Capture SMS Messages | SMS send spike detection |

---

## 📊 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **AI Engine** | Ollama + Mistral 7B | Local LLM — free, private, offline |
| **ML Detection** | scikit-learn Isolation Forest | Per-device anomaly detection |
| **Threat Framework** | MITRE ATT&CK Mobile | Standardized threat mapping |
| **Backend API** | FastAPI + Uvicorn | High-performance async REST API |
| **Real-time Comms** | WebSockets | Live device ↔ server connection |
| **CLI Dashboard** | Textual 8.x + Rich | Terminal UI framework |
| **Web Dashboard** | Streamlit + Plotly | Browser-based monitoring UI |
| **Database** | SQLite + SQLAlchemy | Zero-config embedded database |
| **Authentication** | JWT + bcrypt (passlib) | Secure token-based auth |
| **Android Deployment** | ADB + asyncio | Parallel agent installation |
| **TLS** | OpenSSL (self-signed) | Encrypted comms |
| **OS** | Kali Linux | Penetration testing distribution |

---

## 🧪 Testing Environments (Free)

| Platform | URL | Cost | Best For |
|---|---|---|---|
| **Android Emulator** | developer.android.com | Free | Local testing |
| **HackTheBox** | hackthebox.com | Free tier | CTF & labs |
| **TryHackMe** | tryhackme.com | Free rooms | Learning |
| **VulnHub** | vulnhub.com | 100% free | Vulnerable VMs |
| **Metasploitable 3** | github.com/rapid7 | Free | Pentest practice |

```bash
# Quick local test with DVWA
docker run -d -p 80:80 vulnerables/web-dvwa

# Android emulator
emulator -avd Pixel_7_API_34 &
python3 agent/bulk_installer.py --server localhost --serials emulator-5554
```

---

## 🔒 Security Notes

- Change the default `enrollment_token` in `config.yaml` before production use
- TLS certs are self-signed — replace with trusted CA certs for production
- JWT secret is auto-generated at startup — persists only during session
- All AI inference runs **locally** — no device data is sent to external servers
- Database is unencrypted SQLite — encrypt at rest for sensitive deployments

---

## ⚠️ Legal Notice

> This tool is designed for **authorized Mobile Device Management only**.
>
> Only deploy the MDM agent on:
> - Devices you personally own
> - Devices you have **explicit written authorization** to manage
>
> Deploying MDM agents on devices without owner consent may be illegal under the Computer Fraud and Abuse Act (CFAA), Computer Misuse Act, and equivalent laws in your jurisdiction.
>
> **The authors assume no liability for unauthorized or illegal use.**

---

## 📄 License

```
MIT License — Copyright (c) 2025 MDM Project Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software to use, copy, modify, merge, publish, distribute, and/or
sublicense subject to the MIT License conditions.
```

---

<div align="center">

Built with 🛡️ for the security community · Kali Linux · Python 3 · Ollama

**⭐ Star this repo if it helped you!**

</div>
