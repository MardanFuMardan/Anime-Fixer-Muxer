# Contributing Guide

Thank you for investing your time in contributing to the Phoenix Muxer project!

## How to Propose a New Feature
1. Open a new issue describing your proposed feature or the bug you've found before submitting a Pull Request.
2. Outline the expected behavior and any UI changes necessary.

## Commit Guidelines
- Commit messages should be clear, concise, and scoped.
- We recommend using conventional commit prefixes: `feat:`, `fix:`, `style:`, `docs:`, or `refactor:`.
- Example: `feat: add robust batch processing cancel mechanism`

## Documentation Updates
When your feature or fix is ready to be merged:
- You **must** update `CHANGELOG.md` reflecting your additions, fixes, or changes under the correct section.
- You **must** update `ROADMAP.md` if you have completed a planned feature or if a new feature is proposed.

## Regex Validation Rule
Any changes made to the `extract_episode_number()` function or its regular expressions **must** be validated against known filename edge cases prior to committing. 

Always test your changes against:
- Titles with embedded years (e.g., "Meiji Gekken 1874 - 01 [1080p].mkv")
- Titles with numeric codes (e.g., "9004-tai - 05 [720p].mkv")
- Normal explicit markers (e.g., "Anime EP01 [1080p].mkv" or "Anime E01 [1080p].mkv")
- Cases where the user provides a custom regex in the UI.

Please include proof of these passing tests (or a small script check) before merging.
