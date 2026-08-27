# Add-ons Codes Exporter

An Anki 2.1+ add-on that extracts all your installed AnkiWeb add-on codes into a clean comma-separated or space-separated string for quick copying, backup, or transferring to another Anki setup.

## Features

- 📋 **Export All AnkiWeb Codes**: Scans installed add-ons and extracts their unique numeric AnkiWeb codes.
- ⚡ **Comma & Space Formats**: Provides both comma-separated (`12345, 67890`) and space-separated (`12345 67890`) strings.
- 🖱️ **1-Click Copy to Clipboard**: Dedicated copy buttons with visual feedback.
- 📑 **Installed Add-ons Summary**: Displays a list of all add-on names alongside their codes, plus any local/custom add-ons.
- ⌨️ **Keyboard Shortcut**: Press `Ctrl+Alt+E` (or `Cmd+Alt+E` on macOS) inside Anki to launch the exporter instantly.

## Installation

### Local Installation (for development/testing)
1. In Anki Desktop, go to **Tools -> Add-ons**.
2. Click **View Files** to open your local `addons21` directory.
3. Create a folder named `add-ons-codes-exporter` inside `addons21`.
4. Copy `__init__.py`, `exporter.py`, `config.json`, and `manifest.json` into that folder.
5. Restart Anki.

### Packaging for AnkiWeb / Sharing (`.ankiaddon`)
To build the `.ankiaddon` package:
```bash
zip -r add-ons-codes-exporter.ankiaddon __init__.py exporter.py config.json manifest.json README.md
```
Upload `add-ons-codes-exporter.ankiaddon` directly to [AnkiWeb](https://ankiweb.net/shared/addons/).

## Usage

1. Open Anki.
2. Go to **Tools -> Export Add-on Codes** (or press `Ctrl+Alt+E` / `Cmd+Alt+E`).
3. Click **Copy** next to your preferred format (comma-separated or space-separated).
4. Paste the codes into another Anki app (`Tools -> Add-ons -> Get Add-ons...`) or save them as a backup!

## License

MIT License
