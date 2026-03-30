# Echo — Farm AI Agent

A highly intelligent, proactive farm management system powered by AI (`llama-3.3-70b`), designed to help farmers monitor field conditions, manage irrigation, and track inventory.

## 🌟 Core Features & capabilities
Echo operates via two primary modes: **Reactive** (executing commands) and **Proactive / Autonomous** (managing the farm automatically in the background). 

> 📘 **For full details on the agent's behavior, autonomous capabilities, and persona, see the [Product Specification](PRODUCT_SPECIFICATION.md) document.**

### 🤖 Reactive Activities
- **Intelligent Assistant:** Interprets voice and text requests using `llama-3.3-70b` (Groq/LangGraph).
- **CRUD Operations:** Instantly update crop layout, manage fields, and track fertilizer inventory via direct natural language queries.
- **Smart Analytics:** Answer complex queries regarding weather and schedules.

### ⚙️ Proactive & Autonomous Activities
- **Weather & Field Polling:** A background `farm_scheduler.py` thread checks real-time weather against daily irrigation schedules.
- **Smart SMS Reporting:** Aggregates a full farm system daily report at 5:00 PM and autonomously texts the farmer the summary via Twilio.
- **Autonomous Announcements:** Echo actively reaches out via TTS to announce critical system events, such as when SMS reports are sent or when a field critically requires irrigation.
- **Downtime Recovery:** Automatically logs offline periods and synthesizes historical catch-up records.

---

## 🛠️ Tech Stack & Architecture

### Intelligence & Logic
- **Brain**: `llama-3.3-70b` (Groq API) integrated via **LangGraph** for stateful, agentic workflows.
- **Tools**: Custom Python tools for database interaction, weather fetching, and irrigation control.
- **Weather API**: Integrated with OpenWeatherMap (or similar) to provide real-time forecasts for **Kanija Bhavan**.

### User Interfaces
Echo supports three distinct interfaces to suit different operational needs:

1. **Web HUD (Modern React) — *Recommended***
   - **Frontend**: React (Vite) with a premium glassmorphic HUD.
   - **Styling**: Vanilla CSS for smooth animations and hardware-accelerated effects.
   - **Speech (STT/TTS)**: Uses the **Web Speech API** for native browser-based voice recognition and natural voice synthesis.
   - **Hotkeys**: Press **'M'** to toggle the microphone.

2. **Desktop HUD (CustomTkinter)**
   - **Framework**: `customtkinter` for a modern, themed desktop experience.
   - **STT**: Uses the `SpeechRecognition` library with Google Speech Recognition.
   - **TTS**: Powered by `pyttsx3` for offline voice synthesis.

3. **Management UI (Streamlit)**
   - **Framework**: Streamlit for rapid data visualization and administrative control.

### Backend & Database
- **API Bridge**: FastAPI (`app_web.py`) connects the Web UI to the Python agent.
- **Database**: SQL Server via **SSMS** (SQL Server Management Studio) for robust farm data storage.
- **Scheduler**: Python `APScheduler` for proactive maintenance and daily reporting.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js & npm (for Web UI)
- SQL Server (backend database)
- API Keys: `GROQ_API_KEY`, `OPENWEATHER_API_KEY`, etc. in a `.env` file.

### Installation
1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the database schema using the tools in the `database/` folder.

---

## 🖥️ Running the Application

### Option A: Web UI (HUD)
1. **Start the Backend**:
   ```bash
   python app_web.py
   ```
2. **Start the Frontend**:
   ```bash
   cd ui_web
   npm install
   npm run dev
   ```
3. Open `http://localhost:5173`.

### Option B: Desktop HUD
```bash
python ui/chat_interface_2.py
```

### Option C: Management UI
```bash
streamlit run app.py
```
*(Ensure `ui/chat_interface.py` is enabled in `app.py`)*

---

## 📋 Logging & Diagnostics
- **`logs/YYYY-MM-DD.log`**: Detailed daily interaction logs including user input, tool execution, and token usage.
- **`agent_logs/`**: Logs specific to autonomous agent decisions and background calculations.
