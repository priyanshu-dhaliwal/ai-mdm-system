#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#  MDM System — One-Shot Setup Script for Kali Linux
#  Run: chmod +x scripts/setup.sh && sudo ./scripts/setup.sh
# ═══════════════════════════════════════════════════════════════════════════════
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

banner() {
echo -e "${RED}${BOLD}"
echo " ███╗   ███╗██████╗ ███╗   ███╗"
echo " ████╗ ████║██╔══██╗████╗ ████║"
echo " ██╔████╔██║██║  ██║██╔████╔██║"
echo " ██║╚██╔╝██║██║  ██║██║╚██╔╝██║"
echo " ██║ ╚═╝ ██║██████╔╝██║ ╚═╝ ██║"
echo " ╚═╝     ╚═╝╚═════╝ ╚═╝     ╚═╝"
echo -e "  AI-Powered MDM Setup — Kali Linux${NC}"
echo ""
}

step()  { echo -e "${CYAN}[*] $1${NC}"; }
ok()    { echo -e "${GREEN}[✓] $1${NC}"; }
warn()  { echo -e "${YELLOW}[!] $1${NC}"; }
die()   { echo -e "${RED}[✗] $1${NC}"; exit 1; }

banner

# ── 1. System Update ──────────────────────────────────────────────────────────
step "Updating Kali Linux packages..."
apt update -y && apt upgrade -y
ok "System updated"

# ── 2. System Dependencies ────────────────────────────────────────────────────
step "Installing system dependencies..."
apt install -y \
    python3 python3-pip python3-dev \
    adb android-tools-adb \
    nmap \
    openssl \
    sqlite3 \
    curl wget git \
    build-essential \
    2>/dev/null || warn "Some packages may already be installed"
ok "System dependencies installed"

# ── 3. Ollama (Free Local AI) ─────────────────────────────────────────────────
step "Installing Ollama (free local LLM)..."
if command -v ollama &> /dev/null; then
    ok "Ollama already installed: $(ollama --version)"
else
    curl -fsSL https://ollama.com/install.sh | sh
    ok "Ollama installed"
fi

# ── 4. Pull AI Model ──────────────────────────────────────────────────────────
step "Pulling Mistral AI model (this takes a few minutes on first run)..."
ollama pull mistral &
OLLAMA_PID=$!
echo -e "${YELLOW}  Model download started in background (PID: $OLLAMA_PID)${NC}"
echo -e "${YELLOW}  You can continue setup — model will be ready before first use${NC}"

# ── 5. Python Dependencies ────────────────────────────────────────────────────
step "Installing Python packages..."
pip3 install -r requirements.txt --break-system-packages --quiet
ok "Python packages installed"

# ── 6. TLS Certificates ───────────────────────────────────────────────────────
step "Generating TLS certificates..."
mkdir -p certs
if [ ! -f certs/cert.pem ]; then
    openssl req -x509 -newkey rsa:4096 \
        -keyout certs/key.pem \
        -out    certs/cert.pem \
        -days   365 \
        -nodes  \
        -subj "/CN=MDM-Server/O=MDM-Security/C=US" 2>/dev/null
    ok "TLS certificates generated: certs/cert.pem + certs/key.pem"
else
    ok "TLS certificates already exist"
fi

# ── 7. Project Directories ────────────────────────────────────────────────────
step "Creating project directories..."
mkdir -p data/sessions reports
ok "Directories ready"

# ── 8. Database Init ──────────────────────────────────────────────────────────
step "Initializing SQLite database..."
python3 -c "
import sys; sys.path.insert(0,'.')
from server.db import init_db
init_db()
"
ok "Database initialized at data/mdm.db"

# ── 9. __init__.py files ──────────────────────────────────────────────────────
step "Creating Python package init files..."
touch server/__init__.py ai/__init__.py dashboard/__init__.py agent/__init__.py
ok "Package files created"

# ── 10. ADB setup ─────────────────────────────────────────────────────────────
step "Setting up ADB server..."
adb start-server 2>/dev/null || warn "ADB start failed (normal if no device connected)"
ok "ADB ready"

# ── 11. Firewall rules ────────────────────────────────────────────────────────
step "Configuring firewall rules..."
if command -v ufw &>/dev/null; then
    ufw allow 8000/tcp comment "MDM API Server"  2>/dev/null || true
    ufw allow 8501/tcp comment "MDM Web Dashboard" 2>/dev/null || true
    ok "Firewall rules added (8000, 8501)"
else
    warn "ufw not found — manually allow ports 8000 and 8501 if needed"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✅ MDM System Setup Complete!${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}📌 NEXT STEPS:${NC}"
echo ""
echo -e "  ${BOLD}1. Start Ollama AI (Terminal 1):${NC}"
echo -e "     ${YELLOW}ollama serve${NC}"
echo ""
echo -e "  ${BOLD}2. Start MDM Server (Terminal 2):${NC}"
echo -e "     ${YELLOW}python3 -m server.main${NC}"
echo ""
echo -e "  ${BOLD}3. Launch CLI Dashboard (Terminal 3):${NC}"
echo -e "     ${YELLOW}python3 -m dashboard.app${NC}"
echo ""
echo -e "  ${BOLD}4. Launch Web Dashboard (Terminal 4):${NC}"
echo -e "     ${YELLOW}streamlit run dashboard/web_dashboard.py --server.port 8501${NC}"
echo -e "     ${CYAN}Open browser: http://localhost:8501${NC}"
echo ""
echo -e "  ${BOLD}5. Deploy to Android devices (Terminal 5):${NC}"
echo -e "     ${YELLOW}python3 agent/bulk_installer.py --list${NC}"
echo -e "     ${YELLOW}python3 agent/bulk_installer.py --server YOUR_IP${NC}"
echo ""
echo -e "${YELLOW}⚠️  Only test on devices you own or have written authorization for!${NC}"
echo ""
