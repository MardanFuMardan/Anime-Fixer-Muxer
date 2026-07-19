# Phoenix Muxer

Phoenix Muxer is a batch subtitle standardizer and FFmpeg muxer specifically designed for anime releases.

## Features
- **Batch Folder Queue Processing**: Process multiple anime season folders in a single run.
- **Standalone Subtitle Standardizer**: Dedicated tab to clean and standardize `.ass` files in-place without muxing.
- **ASS Subtitle Standardization**: Automatically strips competitor branding, rewrites `[Script Info]` headers (with correct `PlayDepth` and custom `PlayRes`), and fixes bolding for specific fonts like "Bahij Greta Arabic".
- **Automatic Japanese Audio Track Detection**: Scans and defaults to the best stereo Japanese audio track using FFprobe.
- **Episode Number Matching**: Intelligently pairs video files with subtitle files based on episode numbers extracted from filenames using robust regex.
- **FFmpeg Muxing with Resume Support**: Securely muxes streams together and skips files that have already been processed to allow safe resumption.
- **Disk Space Validation**: Pre-flight checks ensure enough disk space is available before processing a batch.
- **Drag & Drop Folder Support**: Add folders and subtitle files seamlessly by dragging them into the UI.
- **Dark/Light Theme Toggle**: Choose between a futuristic OLED dark mode or a light mode, with UI configurations persisting between sessions.
- **Multi-threaded Processing**: Uses a concurrent `ThreadPoolExecutor` to speed up processing of episodes.
- **Dry-run Preview Mode**: Safely preview video-subtitle pairings before committing to batch operations.
- **Output Integrity Checking**: Validates generated `.mkv` files with FFprobe post-muxing to ensure no streams are missing.

## Requirements
- Python 3.x
- Required Python Packages (from `requirements.txt`):
  - `customtkinter`
  - `tkinterdnd2`
- FFmpeg tools: `ffmpeg.exe` and `ffprobe.exe` must be downloaded and placed manually inside the `tools/` subdirectory within the project folder.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/MardanFuMardan/Anime-Fixer-Muxer.git
   cd Anime-Fixer-Muxer
   ```
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Download FFmpeg and FFprobe binaries for your OS, and place `ffmpeg.exe` and `ffprobe.exe` into the `tools/` directory.

## How to Run
Execute the main application script:
```bash
python main.py
```
*(If the repository provides a `setup_and_run.bat` or `run.bat` file, you may use that to automatically install dependencies and launch the app).*

## Folder Structure Expected by the App
For the batch muxer to pair files properly, your anime folders must follow this structure:
- **Root Folder**: Contains the raw video files (`.mkv`, `.mp4`).
- **`subs/` Directory**: Must exist inside the root folder and contain the corresponding `.ass` subtitle files.
- **Output**: Once processed, muxed files will be generated in a newly created `Phoenix_Output/` directory within each respective root folder.

## Known Limitations
- **Filename Patterns**: Episode number extraction heavily relies on common naming conventions (`E01`, `EP01`, `- 01`, `[01]`). If the extractor fails, you may need to define a custom regex pattern in the UI.
- **Embedded Title Numbers**: Titles containing embedded 4-digit numbers (e.g. years like "1874" or codes) have been mitigated, but complex unconventional titles might still require custom regex anchoring.
- **Japanese Audio Only**: The audio detection logic hardcodes prioritization for Japanese audio streams (`jpn`, `ja`, `japanese`).
- **ASS Subtitles Only**: The standardizer and matching logic expects subtitles in `.ass` format.
- **OS Dependency**: Certain UI actions, such as "Open Output", rely on Windows-specific `os.startfile()` commands and may not work natively on Linux/macOS.

## Contributing / Reporting Issues
If you encounter a bug or have a feature request, please report it by opening an Issue on the [GitHub Issues](https://github.com/MardanFuMardan/Anime-Fixer-Muxer/issues) page.
