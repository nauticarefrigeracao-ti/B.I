Assets usage for app_streamlit.py

Place logo and favicon images under the `assets/` folder at the project root.

Recommended files:
- assets/favicon.png  — 64x64 PNG or 32x32, used as the browser favicon when available.
- assets/logo_center.png — Square logo used in the app header. Recommended 86x86 or 160x160 for better retina display. SVG preferred if available.

Notes:
- Paths are referenced relative to the app root; Streamlit will serve files from the working directory.
- If `assets/logo_center.png` is not present, the app falls back to an inline SVG mark.
- If you want a different placement for the logo, open `app_streamlit.py` and search for `logo_center.png` to adjust the markup.
