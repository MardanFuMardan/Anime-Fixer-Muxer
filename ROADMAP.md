# Roadmap

This file tracks planned features and improvements for future development.
Contributors and future agents should update this file whenever a new idea is proposed or a planned item is completed.

## Planned Features
- [ ] Cross-platform compatibility (removing `os.startfile` dependency).
- [ ] Advanced audio track selection (allow user to pick preferred language from a dropdown instead of hardcoding Japanese).
- [ ] Auto-download missing FFmpeg binaries on first run.

## Completed
- [x] Multi-threaded episode processing (ThreadPoolExecutor)
- [x] Dry-run / preview mode showing video-subtitle match table
- [x] Configurable episode-number regex in settings UI
- [x] Output integrity check via ffprobe after muxing
- [x] Progress bar widget (CTkProgressBar) instead of text-only label
- [x] Futuristic UI overhaul (v3.0 theme)
- [x] Smarter episode-number extraction to avoid false positives from titles containing embedded numbers (e.g. "1874", "9004-tai")
- [x] Standalone Subtitle Standardizer tab for in-place subtitle processing.

## Notes for Future Agents
- Always verify current main.py content before editing — do not assume previous instructions were applied without checking file diffs.
- Any regex change to extract_episode_number must be tested against known edge cases: titles with embedded years, titles with numeric codes, and normal E01/EP01 formats.
- Keep CHANGELOG.md updated with every merged feature or fix.
