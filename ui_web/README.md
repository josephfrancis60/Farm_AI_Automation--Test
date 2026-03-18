# JARVIS Farm AI - Web UI (React)

This is a modern, premium HUD for the Farm AI Agent.

## Prerequisites
- Node.js (v16+)
- Python (v3.9+) with `fastapi`, `uvicorn`, and `pydantic` installed.
- The existing Farm AI Agent environment.

## Running the Application

### 1. Start the Backend
From the root directory:
```powershell
python app_web.py
```
This starts the FastAPI server at `http://localhost:8000`.

### 2. Start the Frontend
From the `ui_web` directory:
```powershell
# Install dependencies first (one time)
npm install

# Run the dev server
npm run dev
```
Open `http://localhost:5173` in your browser.

## Features
- **Premium HUD**: Glassmorphic design with neon accents.
- **Voice-to-Text**: Click the mic or press 'M' to speak.
- **Text-to-Speech**: Echo speaks his replies using your browser's TTS.
- **Live Alerts**: Filtered alerts and reminders update in the side panel.
