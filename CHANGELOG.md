# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- Multi-tab layout supporting both Muxing and Standalone Subtitle Standardization.
- Standalone Subtitle Standardizer workflow for in-place `.ass` processing.
- Custom regex support for overriding default episode number detection.
- Dry-run preview mode showing video-subtitle match table.
- Output integrity check via ffprobe after muxing.
- Progress bar widget (CTkProgressBar).
- Futuristic UI overhaul (v3.0 theme) with OLED dark mode and crimson accents.
- Drag-and-drop support for adding anime folders via tkinterdnd2.
- Multi-threaded processing capabilities via ThreadPoolExecutor.
- Real-time ETA display and progress reporting.
- Robust batch processing cancel mechanism with cleanup.
- Disk space pre-flight validation.
- Config.json save/load mechanism for resolution settings.

### Changed
- Sort video files by episode number before processing.
- Setup UI layout tightened to reduce empty space and improve density.
- Audio selection logic adjusted to prefer stereo over other formats (e.g., 5.1).

### Fixed
- Year misdetection bug preventing title years (e.g., 1874) from being identified as episode numbers.
- TkinterDnD.Tk unknown option '-fg_color' crash.
- FFmpeg 'Stream type specified multiple times' error.
- Encoding fallback chain added for subtitle files (utf-8-sig, cp1256, latin-1).
- Thread-safe folder queue removals.
- Missing empty commit logic on GitHub deployments.
