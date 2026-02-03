# N01D Media Suite

```
███╗   ██╗ ██████╗  ██╗██████╗       ███╗   ███╗███████╗██████╗ ██╗ █████╗ 
████╗  ██║██╔═████╗███║██╔══██╗      ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗
██╔██╗ ██║██║██╔██║╚██║██║  ██║█████╗██╔████╔██║█████╗  ██║  ██║██║███████║
██║╚██╗██║████╔╝██║ ██║██║  ██║╚════╝██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██║
██║ ╚████║╚██████╔╝ ██║██████╔╝      ██║ ╚═╝ ██║███████╗██████╔╝██║██║  ██║
╚═╝  ╚═══╝ ╚═════╝  ╚═╝╚═════╝       ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝
```

**Unified Media Player, Editor & Encoder** - Part of the NullSec Toolkit

A modern, cyberpunk-styled media suite for handling video, audio, images, and PDFs with a unified interface.

## Features

### 🎬 Video Player
- VLC-powered playback for all major formats
- Timeline scrubbing and navigation
- Screenshot capture at any frame
- Video trimming with FFmpeg
- Volume control and playback speed

### 🎵 Audio Player
- Waveform visualization
- Support for MP3, WAV, FLAC, OGG, M4A
- Metadata display (bitrate, sample rate, channels)
- Audio trimming and conversion

### 🖼️ Image Editor
- View PNG, JPG, WebP, GIF, BMP, TIFF
- **Adjustments**: Brightness, Contrast, Saturation, Sharpness
- **Filters**: Blur, Sharpen, Grayscale, Sepia, Invert, Edge Detect
- **Transform**: Rotate, Flip, Resize
- Undo/Redo history
- Export to multiple formats

### 📄 PDF Viewer
- Fast rendering with PyMuPDF
- Page thumbnails sidebar
- Document outline/bookmarks
- Text search
- Zoom controls

### ⚙️ Media Encoder
- Convert between video formats (MP4, MKV, WebM, AVI, MOV, GIF)
- Convert between audio formats (MP3, AAC, FLAC, WAV, OGG, Opus)
- Convert between image formats (PNG, JPEG, WebP, BMP, TIFF)
- Batch processing
- Quality presets (ultrafast → veryslow)
- Custom resolution, bitrate, and framerate

## Installation

### Prerequisites

```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv ffmpeg vlc

# Arch Linux
sudo pacman -S python python-pip ffmpeg vlc
```

### Quick Start

```bash
# Clone or navigate to the n01d-media directory
cd /path/to/n01d-media

# Run the launcher (handles venv and deps automatically)
./launch.sh
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python3 n01d-media.py
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open file |
| `Ctrl+S` | Save file |
| `Ctrl+Q` | Quit |
| `F11` | Toggle fullscreen |
| `Space` | Play/Pause (video/audio) |
| `←/→` | Skip backward/forward |

## Supported Formats

### Video
- MP4, MKV, AVI, MOV, WebM, M4V, WMV, FLV

### Audio
- MP3, WAV, FLAC, OGG, M4A, AAC, WMA, Opus

### Images
- PNG, JPG/JPEG, WebP, GIF, BMP, TIFF, SVG

### Documents
- PDF

## Dependencies

| Package | Purpose |
|---------|---------|
| customtkinter | Modern GUI framework |
| Pillow | Image processing |
| pygame | Audio playback |
| PyMuPDF | PDF rendering |
| python-vlc | Video playback |
| FFmpeg | Media encoding (system) |

## Project Structure

```
n01d-media/
├── n01d-media.py      # Main application
├── launch.sh          # Launcher script
├── requirements.txt   # Python dependencies
├── README.md          # This file
├── core/
│   ├── theme.py       # N01D color theme
│   ├── status_bar.py  # Status bar component
│   └── file_browser.py # File browser widget
├── modules/
│   ├── video_player.py  # Video module
│   ├── audio_player.py  # Audio module
│   ├── image_editor.py  # Image module
│   ├── pdf_viewer.py    # PDF module
│   └── encoder.py       # Encoder module
├── assets/            # Icons and resources
└── themes/            # Additional themes
```

## Theme

N01D Media uses a cyberpunk/hacker aesthetic with:
- Dark backgrounds (`#0d1117`)
- Neon green accent (`#00ff9f`)
- Cyan highlights (`#00d4ff`)
- JetBrains Mono font

## License

Part of the NullSec Toolkit - For authorized use only.

## Credits

- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Video playback via [VLC](https://www.videolan.org/)
- PDF rendering via [PyMuPDF](https://pymupdf.readthedocs.io/)
- Media encoding via [FFmpeg](https://ffmpeg.org/)
