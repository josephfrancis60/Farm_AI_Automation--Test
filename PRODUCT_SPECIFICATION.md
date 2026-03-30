# Product Specification: Echo (Farm AI Agent)

## 1. Product Context & Overview
**Echo** is a comprehensive, highly intelligent, and autonomous AI assistant designed specifically for farm management. It serves as the primary operational brain for agricultural activities, functioning natively on the edge or via local infrastructure to track fields, monitor weather, schedule and trigger irrigation, manage fertilizer inventory, and synthesize daily operational reports. 

The system leverages large language models natively via Groq (specifically utilizing endpoints like Llama 3) orchestrating logic through **LangGraph** to maintain a stateful, agentic workflow. Echo interacts with users via modern graphical UIs enriched with Speech-To-Text (STT) and Text-To-Speech (TTS) capabilities.

## 2. Agent Persona and Tone
- **Name:** Echo (frequently referred to or styled as "JARVIS" in specific desktop HUD implementations).
- **Tone:** Naturally professional, proactive, intelligent, and conversational.
- **Demeanor:** Affirmative and helpful. The agent acknowledges user requests explicitly ("Certainly," "I'll take care of that for you") before taking actions.
- **Interaction Model:** Seamlessly blends reactive command execution with autonomous voice / system interruptions when critical conditions arise.

## 3. Core Functionalities

### A. Reactive Activities (User-Driven)
These are actions directly requested by the user via voice or text chat. The agent interprets the intent, selects the appropriate tool, queries or updates the database, and responds.
- **Crop Management:** Users can ask the agent to add new crops, delete fields, or check the status of all active fields (e.g., "What crops are growing right now?").
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
2. **Web HUD (React/Vite):** A cutting-edge, glassmorphic modern UI capable of running in a browser. It utilizes the native Web Speech API for continuous transcript streaming.

## 5. Security and "Human-in-the-Loop"
Despite having autonomous capabilities, Echo adheres strictly to a **Human-in-the-loop** protocol for destructive or resource-intensive tasks. While the agent can *recommend* irrigation or *suggest* deleting a crop, it will always ask for final, explicit user confirmation before executing the command in the database or actuating physical sprinklers.
