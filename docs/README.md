# N01D Media Documentation

## Overview

N01D Media is a media file analysis and steganography detection tool. Part of the N01D Suite, it analyzes images, audio, and video files for hidden data, metadata leaks, and suspicious modifications.

## Capabilities

- **Steganography Detection** — Detect hidden data in images, audio, video
- **Metadata Analysis** — Extract and analyze EXIF, XMP, IPTC data
- **LSB Analysis** — Least Significant Bit steganography detection
- **Spectral Analysis** — Audio spectrogram analysis for hidden messages
- **File Carving** — Extract embedded files from media containers

## Detection Methods

| Method | Media Type | Technique |
|--------|-----------|-----------|
| LSB Analysis | Images | Statistical analysis of pixel LSBs |
| Chi-Square | Images | Detect non-random LSB distributions |
| RS Analysis | Images | Regular-Singular group analysis |
| Phase Coding | Audio | Phase manipulation detection |
| Echo Hiding | Audio | Echo-based steganography |
| Metadata | All | Hidden data in file metadata |

## Usage

```bash
# Analyze an image for steganography
n01d-media analyze suspicious.png

# Extract metadata from all files in directory
n01d-media metadata --recursive ./evidence/

# Audio spectrogram analysis
n01d-media spectro audio.wav --output spectrogram.png
```

## Part of N01D Suite

See the [N01D Suite](https://github.com/bad-antics/n01d-suite) for the complete toolkit.
