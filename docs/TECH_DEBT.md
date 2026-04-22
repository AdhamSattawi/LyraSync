# LyraSync — Technical Debt & Post-MVP Backlog

This document is the **single source of truth** for all planned, pending, and deferred work. It is cross-referenced with `STRATEGIC_PLAN.md`.

---

## 🛑 Tier 1 — Critical Issues (Fix Before Anything Else)

### [TEST-03] Database Integration Tests (Real DB)
- **Description:** Current tests use `AsyncMock`. Need to verify actual SQL execution and constraints using a test database (e.g., SQLite in-memory or a separate Postgres instance).

---

## 🏗️ Tier 2 — Unfinished MVP Features

### [MVP-02] End-to-End Simulation Script
- **Fix:** Create `scripts/simulate_flow.py` to test entire workflows from webhook receipt to PDF generation without using a real phone.

---

## ⚡ High Priority (Security / Reliability)

### [PERF-04] Redis Backend for Rate Limiting
- **Fix:** Configure `Limiter` to use Redis for multi-instance support.

---

## ✅ Completed / Resolved
- `[DONE] [SCALE-03]` Parallel Audio Transcription (Implemented `asyncio.gather` for chunk processing).
- `[DONE] [INFRA-02]` Health Monitoring (Added `/health` endpoint).
- `[DONE] [SCALE-01]` Subscription Enforcement (Implemented expiration gating in `AgentDispatcher`).
- `[DONE] [BUG-06]` Webhook Composite PK Conflict (Fixed `ProcessedWebhook` primary key).
- `[DONE] [BUG-05]` Missing `ProfileService` Import (Resolved startup NameError).
- `[DONE] [INFRA-01]` Webhook Idempotency (Implemented `ProcessedWebhook` tracking).
- `[DONE] [USER-01]` User Mapping (Verified unique phone lookups).
- `[DONE] [ERROR-01]` Graceful Voice Recovery (Integrated into `AgentDispatcher`).
- `[DONE] [API-01]` Management Endpoints (Profile/Business PUT/GET).
- `[DONE] [BUG-04]` Runtime Crash in Audio Transcription.
- `[DONE] [PERF-05]` Connection Exhaustion (NullPool -> QueuePool).
- `[DONE] [INFRA-05]` Missing Environment Variables in Docker.
- `[DONE] [QUALITY-06]` Management API Layer Violation (DI implemented).
- `[DONE] [TEST-04]` Service-Layer Unit Tests (Reached 60%+ coverage target).
- `[DONE] [DATA-01]` Database Schema synchronized.
- `[DONE] [SEC-03]` Environment Secret Management.
- `[DONE] [SEC-01/02]` Webhook Signature & JWT Auth.
- `[DONE] [STORAGE-01]` Azure Blob Storage.
- `[DONE] [DOC-01]` ADR Documentation (001-031).
- `[DONE] [PERF-02/03]` Message Audit Log & Basic Rate Limiting.

---

## 🚀 Future Roadmap (Post-MVP)
- [ARCH-01] AI Orchestration Layer (LangChain/State Machines).
- [BILLING-01] Tiered Subscription Logic.
- [LANGUAGE-01] Full RTL Support in Dashboard.
- [TRANSCRIPTION-01] Advanced Audio Denoising.
