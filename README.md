# Antone AI - Storage Assistant 

ANTONE is an AI-powered, real-time chat assistant custom-built for self-storage operations. It combines a high-performance backend telemetry system with a responsive user frontend, offering users the ability to query real-time vacancy catalogs, browse pricing structures, and handle multi-turn context-aware conversations seamlessly. It is based on Tenant Inc chat assistant ALITA.

## 🚀 Architecture & Technical Highlights
* **Persistent Conversational Memory:** Implements the modern `google-genai` SDK using `client.chats.create` workflows to handle stateful, multi-turn dialogue tracking natively.
* **Streamlit Interface:** A wide-layout reactive frontend split between interactive assistant chat windows and a dynamic live management operations dashboard.
* **FastAPI Backend Data Integration:** Connects dynamically to backend API infrastructure to securely query inventory counts, pricing spectrum bounds, and JWT-authenticated tenant active subleases/payment ledgers.
* **Dockerized Microservices:** Fully containerized setup leveraging volume mounts for instant environment mirroring and accelerated local development loops.

---

## 🛠️ Project Structure
```text
Antone-agent/
├── app.py                  # Streamlit Frontend UI & Gemini Chat Engine
├── requirements.txt        # Verified project package dependencies
├── Dockerfile.frontend     # Frontend service container configuration
├── Dockerfile.backend      # Backend service container configuration
├── docker-compose.yml      # Orchestration layer mapping system microservices
└── .gitignore              # Restricts runtime caches and environment secrets

⚙️ Quick Start Installation

Prerequisites
•	Docker Desktop installed on your machine.
•	A Gemini API Key from Google AI Studio.

1. Configure Local Application Secrets
Create a directory named .streamlit in the root folder and add a secrets.toml file to inject your credentials securely without leaking them to source control:

# .streamlit/secrets.toml
GEMINI_API_KEY = "YOUR_ACTUAL_GEMINI_API_KEY_HERE"

2. Launch the Application Container Ecosystem
Spin up the complete system (FastAPI backend service layer + Streamlit interactive chat window) with a single orchestrated build command:

docker compose up --build

Once execution finishes tracking, open your browser and navigate to:
•	Streamlit UI Portal: http://localhost:8501

Interactive Flows to Try
•	Multi-Turn Context: Ask "Do you have any units available in Irvine?" followed directly by "What sizes are they?" to watch Antone track context across state transitions.
•	Live System Metrics: Query "What is the cost of your cheapest unit?" to view real-time calculations drawn straight from live active catalog payloads.
•	Secure Tenant Ledgers: Switch navigating pages inside the sidebar to register or authenticate. Ask "Show me my active invoices" to test JWT authorization tokens injection.

