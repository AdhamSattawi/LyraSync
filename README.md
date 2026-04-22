# LyraSync: Asynchronous Applied AI Pipeline

An event-driven backend service that processes unstructured audio data from field environments, utilizes Large Language Models (LLMs) for intent classification and data extraction, and synchronously updates relational databases.

## 🔒 Repository Status & Source Code Visibility

This repository serves as the **Public Architectural Overview** for the LyraSync pipeline. 

While the full core source code, proprietary agentic workflows, and production deployment configurations are currently hosted in a **private repository**, this part is open-source. This decision was made to protect the intellectual property, custom LLM system prompts, and security architecture of the commercial MVP.

## 🏗️ System Architecture & Tech Stack

This project is built with a focus on resilient cloud infrastructure, strict data typing, and secure secret management.

* **Core Logic:** Python, FastAPI
* **AI / ML Integration:** OpenAI API (Whisper for STT, GPT-5.4-nano for Agentic data extraction)
* **External Webhooks:** Twilio API (Asynchronous event handling)
* **Database:** PostgreSQL (Relational schema mapping)
* **DevOps & Deployment:** Docker, Azure App Service, 1Password (Secrets)

## ⚙️ How It Works (The Data Flow)

1. **Ingestion:** An asynchronous Twilio webhook receives an audio payload from the field.
2. **Transcription:** The payload is securely routed to the Whisper model for high-fidelity Speech-to-Text (STT) conversion.
3. **Agentic Processing:** The transcribed text is passed to GPT-5.4-nano with strict system prompts to classify the user's intent (e.g., "Log Invoice", "Update Inventory") and extract specific data points into a validated JSON schema.
4. **Database Execution:** The structured JSON is mapped to strictly typed SQL models and injected into the PostgreSQL database.
5. **Confirmation:** A synchronous success state is returned to the user via the Twilio API.

## 🧠 Engineering Focus

I built Lyra to master the complexities of modern cloud deployments and Applied AI. My core focus during this build was:
* **Webhook Security & Error Handling:** Ensuring dropped packets or malformed audio files from the field do not crash the main server loop.
* **Containerization:** Writing robust Dockerfiles to ensure the local FastAPI environment matches the Azure App Service production environment identically.
* **Cost Optimization & Routing:** Managing API rate limits and structuring LLM prompts to minimize token usage while maintaining high accuracy.
