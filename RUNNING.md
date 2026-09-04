# Running Phase 1

## Local desktop app

Python 3.10+ and Tkinter are required. From this directory:

```text
python -m sovereign_ai
```

On first launch, create an administrator with a username and password of at least 8 characters. The application creates `data/sovereign.db` and stores uploaded files under `data/files`.

For local chat with Bionic Studio, enable its Local Model API and use the default URL `http://localhost:1234/v1`. Set `LOCAL_MODEL` to the model ID shown by Bionic Studio, or leave it as-is and choose a model from the sidebar when the API is connected. If the local API is unavailable, the app still starts and reports the model backend as offline.

Phase 3 accelerators are listed in `requirements.txt`. Install them with `python -m pip install -r requirements.txt` for Turbovec, machine-readable PDF parsing, local OCR, and image handling. OCR also requires a local Tesseract installation; no cloud OCR is used.

## Docker

```text
docker compose up --build
```

The compose file persists application data in the `sovereign_data` volume. Tkinter needs a desktop display; on Linux, allow the container to access the X display with `xhost +local:docker` before starting it. On Windows and macOS, running the local Python command is the simplest desktop path.

Docker runs the local API on `http://localhost:8000`. The API exposes `/api/setup`, `/api/login`, `/api/logout`, `/api/health`, `/api/models`, `/api/conversations`, `/api/files`, `/api/knowledge/documents`, `/api/knowledge/search`, and `/api/knowledge/ask`. Protected routes use the bearer token returned by `/api/login`.

## Checks

```text
python -m unittest discover -s tests -v
python -m compileall -q sovereign_ai
```
