# Product Specification: Echo (Farm AI Agent)

## 1. Product Context & Overview
**Echo** is a comprehensive, highly intelligent, and autonomous AI assistant designed specifically for farm management. It serves as the primary operational brain for agricultural activities, functioning natively on the edge or via local infrastructure to track fields, monitor weather, schedule and trigger irrigation, manage fertilizer inventory, and synthesize daily operational reports. 

The system leverages large language models through **LangGraph** to maintain a stateful, agentic workflow. The current web experience uses Gemini for standard text requests and Gemini Live for low-latency voice interaction with native audio responses.

## 2. Agent Persona and Tone
- **Name:** Echo (frequently referred to or styled as "JARVIS" in specific desktop HUD implementations).
- **Tone:** Naturally professional, proactive, intelligent, and conversational.
- **Demeanor:** Affirmative and helpful. The agent acknowledges user requests explicitly ("Certainly," "I'll take care of that for you") before taking actions.
- **Natural Persona (STRICT):** Echo is forbidden from using technical jargon or computer-centric terminology. It never mentions "databases", "tables", "JSON", "transactions", or "API endpoints" in conversation. It reports results as a professional human assistant would (e.g., "I've processed that for you" instead of "Transaction recorded").
- **Interaction Model:** Seamlessly blends reactive command execution with autonomous voice / system interruptions when critical conditions arise.

## 3. Core Functionalities

### A. Reactive Activities (User-Driven)
These are actions directly requested by the user via voice or text chat. The agent interprets the intent, selects the appropriate tool, queries or updates the database, and responds.
- **Crop Management:** Users can ask the agent to add new crops, delete fields, or check the status of all active fields.
- **Irrigation History Tracking:** Users can query past watering activities (e.g., "When was the last time I watered the corn?" or "How long have I irrigated my crops?"). The agent looks up specific session durations and timestamps to provide factual updates.
- **Ambiguity Guard & Clarification:** For vague or incomplete requests (e.g., "Echo, can you check?"), the agent is programmed to ask follow-up questions for clarity rather than assuming user intent or calling tools prematurely.
- **Inventory Control:** Users can query the fertilizer stock, ask for crop-specific fertilizer recommendations, and instruct the agent to add or remove fertilizer from the database.
- **Weather Inquiries:** Real-time fetching of current weather and multi-day forecasts for the farm's location (e.g., Kanija Bhavan).
- **Manual Irrigation Control:** Users can instruct the agent to manually activate sprinkler systems for specific durations and delays. 
- **Reminders:** The agent can set personal or farm-related reminders explicitly requested by the user (e.g., "Remind me to check the tractors in 5 minutes").

### B. Proactive & Autonomous Activities (System-Driven)
Echo operates a background `APScheduler` (Farm Scheduler) that actively monitors the farm without user prompts. When specific conditions are met, the agent acts autonomously.
- **Weather Monitoring:** The system routinely fetches weather data. If rain is actively detected or forecasted within a critical window, the system adjusts irrigation recommendations.
- **Downtime Catch-up:** If the main processing cores go offline, the agent autonomously logs the downtime and backfills historical weather data when connectivity is restored to ensure continuous data integrity.
- **Irrigation Auditing:** The system proactively compares the daily irrigation schedule against current weather conditions. If a field is scheduled for watering but rain is forecasted, it generates a "SKIP" alert. If watering is needed and no rain is detected, it generates an active alert.
- **Alert Generation & UI Sync:** Autonomous system events create `WARNING`, `ERROR`, or `INFO` alerts that immediately populate in the visual HUDs.
- **Automated Daily Reporting & SMS:** Every day at exactly 17:00 (5:00 PM local time), Echo autonomously aggregates all active crops, irrigation history, inventory warnings, and the latest weather into a detailed daily text report. It then autonomously sends an SMS summary to the farmer's mobile device via Twilio.
- **Autonomous Verbal Announcements:** 
  - When the daily SMS report is sent, Echo will autonomously interrupt and speak via the UI: *"Sir, the daily report has been generated and sent via SMS. Please check your phone."*
  - When a configured system reminder triggers, Echo autonomously speaks to inform the user (e.g., *"Hi, you have a reminder - Irrigation Needed for Sugarcane."*)

## 4. User Interfaces
The product is presented through decoupled frontends:
1. **Desktop HUD (Jarvis UI):** A `CustomTkinter` desktop application designed for persistent monitoring. It features continuous background polling, real-time alert and reminder displays, an active typing indicator, and local TTS/STT (using `SpeechRecognition` and `pyttsx3`). It features highly tuned pause thresholds (2.5 seconds) to allow users to speak naturally without cutoff.
2. **Web HUD (React/Vite):** A cutting-edge, glassmorphic modern UI. It connects to the FastAPI backend over REST for text chat and over a proxied WebSocket (`/ws/live`) for Gemini Live voice sessions.
    - **Native Gemini Voice:** The web microphone streams PCM audio to Gemini Live and plays Gemini's returned 24 kHz PCM audio in the browser.
    - **Live Model Configuration:** Users can choose supported Gemini Live voices (`Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`) and language preferences from the settings panel.
    - **Usage and Error Visibility:** The header displays Gemini token usage metadata when available, and surfaces quota or Live session errors directly in the HUD.

## 5. Security and "Human-in-the-Loop"
Despite having autonomous capabilities, Echo adheres strictly to a **Human-in-the-loop** protocol for destructive or resource-intensive tasks. While the agent can *recommend* irrigation or *suggest* deleting a crop, it will always ask for final, explicit user confirmation before executing the command in the database or actuating physical sprinklers.
