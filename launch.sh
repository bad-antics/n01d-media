#!/bin/bash
#
# ███╗   ██╗ ██████╗  ██╗██████╗       ███╗   ███╗███████╗██████╗ ██╗ █████╗ 
# ████╗  ██║██╔═████╗███║██╔══██╗      ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗
# ██╔██╗ ██║██║██╔██║╚██║██║  ██║█████╗██╔████╔██║█████╗  ██║  ██║██║███████║
# ██║╚██╗██║████╔╝██║ ██║██║  ██║╚════╝██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██║
# ██║ ╚████║╚██████╔╝ ██║██████╔╝      ██║ ╚═╝ ██║███████╗██████╔╝██║██║  ██║
# ╚═╝  ╚═══╝ ╚═════╝  ╚═╝╚═════╝       ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝
#
# N01D Media Suite Launcher
# Part of the NullSec Toolkit

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "███╗   ██╗ ██████╗  ██╗██████╗       ███╗   ███╗███████╗██████╗ ██╗ █████╗ "
echo "████╗  ██║██╔═████╗███║██╔══██╗      ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗"
echo "██╔██╗ ██║██║██╔██║╚██║██║  ██║█████╗██╔████╔██║█████╗  ██║  ██║██║███████║"
echo "██║╚██╗██║████╔╝██║ ██║██║  ██║╚════╝██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██║"
echo "██║ ╚████║╚██████╔╝ ██║██████╔╝      ██║ ╚═╝ ██║███████╗██████╔╝██║██║  ██║"
echo "╚═╝  ╚═══╝ ╚═════╝  ╚═╝╚═════╝       ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${GREEN}N01D Media Suite v1.0.0${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check/create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}[*] Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check/install dependencies
if [ ! -f "$VENV_DIR/.installed" ]; then
    echo -e "${YELLOW}[*] Installing dependencies...${NC}"
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r "$SCRIPT_DIR/requirements.txt"
    touch "$VENV_DIR/.installed"
    echo -e "${GREEN}[+] Dependencies installed${NC}"
fi

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}[!] FFmpeg not found. Encoding features will be limited.${NC}"
    echo -e "${YELLOW}    Install with: sudo apt install ffmpeg${NC}"
fi

# Check VLC
if ! command -v vlc &> /dev/null; then
    echo -e "${YELLOW}[!] VLC not found. Video playback will be limited.${NC}"
    echo -e "${YELLOW}    Install with: sudo apt install vlc${NC}"
fi

echo ""
echo -e "${GREEN}[+] Launching N01D Media...${NC}"
echo ""

# Launch application
python3 "$SCRIPT_DIR/n01d-media.py" "$@"
