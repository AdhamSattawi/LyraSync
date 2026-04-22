# Architecture Decision Records (ADR) - Lyra (LyraSync)

This document records the core architectural decisions made during the development of the Lyra (LyraSync) Voice-to-CRM backend platform.

---

## ADR 001: Adoption of Clean Architecture (N-Layer Design)

**Context**: 
Lyra needs a highly maintainable, scalable, and testable codebase that can adapt to rapid changes in AI capabilities and third-party APIs without requiring complete rewrites of the business logic.

**Decision**: 
Adopt a strict Clean Architecture (N-Layer) separating the application into distinct domains:
*   `api/`: Routers and webhooks (presentation layer).
*   `core/`: Configuration and global exception handling.
*   `domain/`: Database ORM models (SQLAlchemy) and DTO validation schemas (Pydantic).
*   `infrastructure/`: Wrappers/Adapters for external systems (OpenAI APIs, Document Generators, Databases).
*   `services/`: The core business logic and orchestration layer.

**Consequences**: 
*   **Positive**: High separation of concerns. The AI models, databases, or web framework can be swapped or tested in complete isolation.
*   **Negative**: Introduces boilerplate code upfront compared to heavily coupled Django or bare FastAPI implementations.

---

## ADR 002: Core Technology Stack Selection

**Context**: 
The platform handles high-concurrency webhook events (WhatsApp) requiring robust asynchronous non-blocking boundaries, strong static typing, and high performance.

**Decision**: 
The core backend stack is standardized as:
*   **Python 3.11+**
*   **FastAPI** (for high-performance async routing)
*   **Pydantic V2** (for rigorous input/output data validation and DTOs)
*   **SQLAlchemy 2.0 with asyncpg** (for asynchronous relational database interactions)
*   **Alembic** (for database migrations)

**Consequences**: 
Ensures entirely non-blocking execution inside the main event loop, significantly increasing concurrent webhook throughput.

---

## ADR 003: AI Infrastructure - Managed APIs over Local Models

**Context**: 
The application must transcribe short, often noisy, multilingual WhatsApp voice notes (Hebrew, Arabic, English technical terms) and extract highly structured JSON data. Hosting powerful open-source models (like `insanely-fast-whisper`) locally requires maintaining expensive dedicated GPU infrastructure with high idle costs.

**Decision**: 
Rely strictly on managed OpenAI API services for the primary MVP AI pipeline:
*   **Transcription (`AudioTranscriber`)**: Use `whisper-1` (OpenAI API) for its low cost ($0.006/min) and robust multilingual noise-reduction features without hardware overhead.
*   **Extraction (`LLMExtractor`)**: Use `gpt-5.4-nano` (or equivalent high-speed/low-cost reasoning models) combined with rigorous **Structured Outputs** (Pydantic schemas) to guarantee the output matches the required backend types.

**Consequences**: 
Massively lowers the initial cloud computing burn rate. It heavily couples the AI processing reliability to OpenAI's uptime.

---

## ADR 004: The "AI Router" (Intent Classification Workflow)

**Context**: 
The original naive approach attempted to use a single LLM call to both understand what the user wants and extract the invoice fields. As the application shifted from an "Invoice Generator" to a "Voice CRM," this proved unscalable (e.g., handling "create a job" vs. "update a client address").

**Decision**: 
Implement a two-step "AI Router" via an `AgentDispatcher`:
1.  **Intent Classification**: A fast LLM call strictly using a `CommandIntent` schema (with "Chain of Thought" reasoning) to classify the user's root action (e.g., `CREATE_JOB`, `UPDATE_CLIENT`).
2.  **Specialized Extraction**: Based on the classified intent, the audio transcript is passed back to the LLM with a highly targeted schema (e.g., `JobCreate`) to extract exact data.

**Consequences**: 
Removes Pydantic inheritance traps (e.g., LLM failing when unsure how to fill irrelevant inherited fields), reduces hallucinations, and scales infinitely for new voice commands.

---

## ADR 005: Line-Item Architecture & Templating System

**Context**: 
A single flat `payment` float on the `Job` model fails real-world business compliance for quotes and invoices where multiple items (parts, labor, call-out fee) need itemized breakdown.

**Decision**: 
*   Strip the `payment` column from the `Job` model.
*   Implement a separate `JobItem` model linked via a One-to-Many relationship to `Job`.
*   Establish a `DocumentTemplate` and `JobDocument` architecture to decouple raw line items from the PDF output, allowing the same job data to dynamically generate a "Quote", "Service Agreement", or "Invoice" based on the business lifecycle.

**Consequences**: 
Increres the complexity of SQLAlchemy database read/writes and LLM extraction schemas, but achieves commercial production compliance.

---

## ADR 006: Multi-Tenant Readiness via Business Profiles

**Context**: 
Tying company attributes directly to a `User` entity causes friction when businesses expand or require localized defaults (currencies, time zones). 

**Decision**: 
Introduce a `BusinessProfile` model between the `User` and `Job`/`Client` entities. This profile houses critical localization anchors like `country`, `timezone`, and `currency_code`.

**Consequences**: 
Allows a single tradesman account to seamlessly manage multiple company brands or regions in the future.

---

## ADR 007: Asynchronous PDF Generation

**Context**: 
PDF generation utilizing `WeasyPrint` is a heavily CPU-bound synchronous process that will freeze the FastAPI asyncio event loop, causing webhook timeouts.

**Decision**: 
Wrap all `WeasyPrint` (or similar synchronous C-dependent libraries) operations with `asyncio.to_thread()`.

**Consequences**: 
Offloads high-load HTML-to-PDF rendering to isolated worker threads, maintaining concurrent responsiveness for the webhooks.

---

## ADR 008: Strict Pydantic V2 "Extra Data" Policy

**Context**: 
When strictly parsing LLM outputs using schema validators, language models occasionally hallucinate helpful but undefined metadata keys (e.g. `{"confidence": 98}`). Standard validation drops the request, crashing the ingestion pipeline.

**Decision**: 
All Pydantic models utilized in the `LLMExtractor` layer must explicitly define `model_config = ConfigDict(extra='ignore')`.

**Consequences**: 
Guarantees robust and fault-tolerant parsing on unpredictable AI JSON outputs.

---

## ADR 009: Strict Session & UUID State Management 

**Context**: 
Using sequential integer primary keys introduces endpoint security vulnerabilities (IDOR). Handling complex transactions requires guarantees that database IDs exist before child relationship commits.

**Decision**: 
*   Use `UUID` exclusively for primary keys throughout PostgreSQL.
*   Enforce a mandatory `await session.flush()` step to secure generated DB UUIDs prior to performing any child `session.add()` relational linkages (e.g., JobLine items to Jobs) before the final `await session.commit()`.

**Consequences**: 
Ensures absolute structural integrity across parent/child database insertion blocks while safeguarding REST API perimeters.

---

## ADR 010: Database Session Extent and Object Decoupling

**Context**: 
Passing ORM models retrieved in one session (e.g., within `AgentDispatcher`) into another session managed by a different service (e.g., `JobService`) introduces a `DetachedInstanceError` risk whenever lazy-loaded relationships are accessed on those detached models.

**Decision**: 
Enforce strict session boundaries by passing only plain Python values like primary keys (e.g., `UUID`) across service boundaries, rather than full ORM models. Services are responsible for re-querying the entities they require within their own local session scope.

**Consequences**: 
Eliminates detached entity risks and safely handles async session boundaries, adhering strictly to Clean Architecture object boundaries.

---

## ADR 011: LLM Schema Decoupling for Specialized Extraction

**Context**: 
The LLM ingestion pipeline was failing because the `JobCreate` schema inherited internal application fields (e.g., `raw_data`, `parsed_data`, `status`) that an LLM cannot logically extract from voice transcripts.

**Decision**: 
Decouple internal DB creation schemas from LLM extraction schemas. Introduce independent extraction schemas (e.g., `JobExtract`) optimized exclusively for extracting data from speech, separate from domain creation schemas (e.g., `JobCreate`) used in business logic.

**Consequences**: 
Increases the overall schema count but drastically reduces system-breaking validation errors by ensuring the LLM is only ever prompted to fill fields it can realistically extract.

---

## ADR 012: Whisper Vocabulary Priming (Hybrid Layer)

**Context**: 
The speech-to-text engine (OpenAI Whisper) struggles with niche or highly specialized tradesman vocabulary (e.g., parsing "PEX pipe" as "pecks pipe"). LLM Post-processing the transcript natively impacts latency and increases token cost per request.

**Decision**: 
Implement a two-layer "Hybrid" vocabulary priming architecture leveraging Whisper's native `prompt` parameter:
*   **Static Layer:** Load available, profession-specific terminology text files (e.g., `plumber.txt`, `electrician.txt`).
*   **Dynamic Layer:** Dynamically query and merge the user's most frequently used terms over time based on past inputs (`JobItem` descriptions).

**Consequences**: 
Provides highly accurate technical transcriptions with zero added system latency or secondary API request costs, gracefully resolving the Whisper cold-start problem.

---

## ADR 013: PostgreSQL for Conversation State Management

**Context**: 
The webhook-driven workflow required a short-term memory layer to perform gracefully when dealing with missing mandatory intent fields (e.g., knowing an unstructured WhatsApp reply is a response to "What type of job is this?").

**Decision**: 
Implement a `ConversationState` table directly inside PostgreSQL over introducing an external in-memory queue like Redis. 

**Consequences**: 
Maintains a simplified infrastructure with zero new dependencies, effectively delivering transactional consistency with core CRM data while fully supporting the expected single-business request loads entirely well beyond the MVP stage. If concurrent webhook volume exceeds PostgreSQL's connection pool limits in the future, this state management layer will need to be migrated to an in-memory datastore like Redis.

---

## ADR 014: AI Evolution to a Vertical "Secretary" (Predefined Query Engine)

**Context**: 
The strategic vision for the product expanded from a rigid Voice-to-CRM automation pipeline into a conversational AI capable of answering business intelligence questions (e.g., "How much revenue this month?").

**Decision**: 
Expand the Intent classification router inside `AgentDispatcher` to include query categories (e.g., `QUERY_BUSINESS`, `QUERY_CLIENTS`). To maintain system safety, use LLMs to extract parameters to place into predefined, safe SQL templates (Option A) rather than allowing direct generative raw SQL access to the PostgreSQL database layout.

**Consequences**: 
Enables a conversational interface driving rich intelligence without exposing the app to generative SQL injection risks, establishing Lyra strictly as a vertical tool specialized and highly robust within its domain.

---

## ADR 015: Multi-User SMB Architecture

**Context**: 
The original naive model mapped one phone number directly to one `BusinessProfile`. This fails for small-to-medium businesses (SMBs) where a single business entity has multiple employees (e.g., an owner and three technicians) interacting with Lyra via different devices.

**Decision**: 
Implement a strict hierarchy: `BusinessProfile` -> `User` -> Webhook events.
*   Add a `User` model with defined roles (`ADMIN`, `OWNER`, `EMPLOYEE`, `INDEPENDENT`).
*   Shift the Foreign Key mapping so `User` belongs to `BusinessProfile`.
*   Directly tie conversational context (`ConversationState`) and system action logging (`created_by_id`) to the specific `User` rather than the overarching `BusinessProfile`.

**Consequences**: 
*   **Positive**: Supports teams, enables accountability audits (knowing *who* drafted a quote), and scales correctly to multi-tenant team structures.
*   **Negative**: Increases lookup query complexity in the `AgentDispatcher` (requiring targeted joins) over standard single-entity parsing.

---

## ADR 016: Integer-based Financial Representation and Currency Standardization

**Context**: 
Storing monetary values as `Float` introduces floating-point precision errors during aggregations and tax calculations. Additionally, storing raw totals without explicit currency types prevents global scalability (e.g., distinguishing between ILS, GBP, or USD).

**Decision**: 
*   Refactor all database financial columns (`unit_price`, `total_price`) to `Integer`.
*   Store all money in its smallest fractional monetary unit (e.g., cents, pence, agorot).
*   Centralize `currency_code` and `timezone` on the `Job` model (the document boundary) and inherit defaults from the `BusinessProfile`.
*   Enforce Pydantic validation using explicit field descriptions instructing the LLM to process captured fiat values into standard integer sizes.

**Consequences**: 
*   **Positive**: Eradicates mathematical rounding bugs. Guarantees global formatting compatibility. 
*   **Negative**: Requires mathematical data transformations at the service and UI boundaries prior to human readability.

---

## ADR 017: Immutable Audit Trails & Compliance

**Context**: 
Under strict business bookkeeping and tax laws (such as Israel's "עוסק פטור" and UK accounting standards), a finalized financial document (invoice) cannot be simply deleted or casually overwritten with a SQL `UPDATE` or `DELETE` statement.

**Decision**: 
*   Implement strict "Soft Deletes" utilizing boolean flags (`is_deleted`) to prevent permanent database row destruction.
*   Enforce `Status` enumerations (`DRAFT`, `SENT`, `PAID`, `VOIDED`) on Documents/Jobs.
*   Architect the service layer to "lock" any mutation on a `Job` once it hits a finalized status. Subsequent administrative changes require issuing a formal linked revision ("Credit Note") rather than quietly modifying the origin document.

**Consequences**: 
*   **Positive**: Delivers full legal accounting compliance, establishing trust.
*   **Negative**: Bloats the database over time with voided/soft-deleted rows and increases validation conditionals within the service layer.

---

## ADR 018: Intent Handler Registry Pattern

**Context**: 
The `AgentDispatcher` was rapidly turning into a "God Class" (anti-pattern) as new conversational intents were added. It imported dozens of Pydantic schemas, injected almost every service in the repository, and was forcing double-executions against the OpenAI API by blurring business logic with string parsing.

**Decision**: 
*   Implement the **Command (Handler Registry) Pattern**.
*   Extract every intent into its own isolated `IntentHandler` subclass (e.g., `DraftQuoteHandler`).
*   Each Handler declares its own `IntentType`, `extraction_schema`, and `system_prompt`.
*   The `AgentDispatcher` acts natively as an execution engine. It loops through injected handlers to find a match, manages conversational state (missing LLM fields), and passes the validated Pydantic DTO directly to the `handler.execute()` method.

**Consequences**: 
*   **Positive**: Completely isolates services from LLM logic. The `AgentDispatcher` is now Closed for Modification but Open for Extension (**OCP** of SOLID). Adding a new feature only requires creating a single isolated Handler file. System imports are heavily optimized.
*   **Negative**: Scatters action flows across many separate Handler files, increasing the overhead to trace exactly where a route is executed for developers unfamiliar with Registry patterns.

---

## ADR 019: Ledger Architecture and Invoice Numbering

**Context**: 
The system required a mechanism to track incoming payments and outgoing expenses to act as a fully functional Business Ledger. Concurrently, a severe schema bug was identified where `Job.invoice_number` was utilizing a global PostgreSQL `autoincrement` sequence. In a multi-tenant SaaS environment, a global sequence causes sequential collisions (e.g., Business A gets Invoice #1, Business B receives Invoice #2), violating basic accounting workflows where each business has its own independent numbering schema.

**Decision**: 
*   **Transaction Entity**: Create an isolated `Transaction` model linking exclusively to a `business_id` (and optionally a `job_id`), categorized strictly via `TransactionType` (INCOME vs EXPENSE).
*   **Server-Side Aggregation**: Instead of iterating over vast arrays of ledger objects in Python memory, `TransactionRepository.get_balance()` utilizes optimized PostgreSQL native SQL aggregates (`func.sum` with `GROUP BY type`) to compute real-time cash flow.
*   **Revert Invoice Sequence**: Reverted `Job.invoice_number` to a manually-managed `String` column, breaking its dependency on the PostgreSQL global auto-increment sequence and opening it up to string-based tenant formatting (e.g. `INV-2401`).
*   **Command Integration**: Added schema-enforced Pydantic extraction for Logging Incomes/Expenses, wired natively into the `AgentDispatcher` via the new Handler Registry pattern.

**Consequences**: 
*   **Positive**: Guarantees distinct data separation for B2B tenants. High-performance O(1) balance calculations regardless of history size.
*   **Negative**: Requires `JobService` to manually query the max invoice number per tenant and assign the sequential integer programmatically at creation time, adding a slight performance overhead.

---

## ADR 020: Platform-Agnostic Messaging Layer (Adapter Pattern)

**Context**: 
The system needed to receive messages from WhatsApp via Twilio and route them into the `AgentDispatcher`. The naive solution would be to read Twilio's form fields directly inside the webhook route, which would permanently couple the entire system to a single messaging provider. As the product targets international markets, supporting multiple messaging platforms (e.g., Telegram, Signal, Meta Messenger) is an explicit future requirement.

**Decision**: 
*   **Abstract Base Class**: Defined `BaseMessageAdapter` (`app/infrastructure/adapters/base_adapter.py`) with two abstract `async` methods: `parse_incoming(request) -> IncomingMessage` and `send_reply(to_phone, text)`.
*   **Normalized Contract**: Created a platform-agnostic Pydantic DTO (`IncomingMessage`) in `app/domain/schemas/messaging_schemas.py`. This is the only object the `AgentDispatcher` ever interacts with — it has no awareness of Twilio or any specific platform.
*   **First Concrete Adapter**: `TwilioWhatsappAdapter` implements the base class: parsing Twilio's Form fields, stripping `"whatsapp:"` prefixes, downloading media files via `httpx` with Twilio Basic Auth, and delegating `send_reply` to the Twilio REST SDK via `asyncio.to_thread` (preventing event loop blocking from a synchronous SDK).
*   **Webhook Router**: `POST /api/v1/webhooks/twilio/whatsapp` injects both the adapter and dispatcher via FastAPI Dependency Injection, ensuring the webhook is a thin orchestrator with zero business logic.
*   **Audio Cleanup**: A `finally` block inside the webhook guarantees temp audio files are deleted from `/tmp/` regardless of whether transcription succeeds or fails.

**Consequences**: 
*   **Positive**: Adding a second platform (e.g., Telegram) requires only one new Adapter file and one new route — no changes to `AgentDispatcher`, handlers, or services. The `IncomingMessage` schema acts as a stable contract across the entire system.
*   **Negative**: Each new platform requires implementing both `parse_incoming` and `send_reply`, which may have wildly different authentication schemes (API keys, webhooks, OAuth2). This complexity is intentional but real.

---

## ADR 021: Argon2 for Secure Password Hashing

**Context**: 
Bcrypt, while robust, has a fundamental 72-byte limit on plaintext input and is increasingly susceptible to brute-force attacks via specialized hardware (FPGAs/ASICs). Password security is paramount for a multi-tenant CRM.

**Decision**: 
Transition to **Argon2id** (via `argon2-cffi` and `passlib`) as the primary hashing algorithm for all user credentials.

**Consequences**: 
*   **Positive**: Eradicates the 72-byte length limit (enabling long passphrases). Provides significantly higher resistance to GPU/ASIC cracking due to its memory-hard nature.
*   **Negative**: Requires the `cffi` system bindings for compilation but is highly optimized for performance on modern CPUs.

---

## ADR 022: Automated Business Onboarding & Country Defaults

**Context**: 
Manual database seeding is non-scalable, inconsistent, and prevents automated SaaS tenant acquisition. Additionally, manually setting currencies and time zones for every user is error-prone.

**Decision**: 
Implement a dedicated `POST /admin/setup` route that handles the atomic registration of a `BusinessProfile` and its first `OWNER` user. Use a centralized `COUNTRY_DEFAULTS` mapping to automatically configure `currency_code`, `timezone`, and `phone_country_code` based on the legal jurisdiction of the business.

**Consequences**: 
*   **Positive**: Guarantees data consistency for new tenants. Simplifies the onboarding experience. Centralizes regional formatting logic in a maintainable Python utility.
*   **Negative**: Requires ongoing maintenance of the `COUNTRY_DEFAULTS` map as the platform expands into new territories.

---

## ADR 023: Async Eager Loading & Post-Commit Refresh Pattern

**Context**: 
Async SQLAlchemy strictly forbids "lazy-loading" of relationships (e.g., `job.items`) during Pydantic serialization, causing `MissingGreenlet` runtime crashes. Furthermore, database objects expire immediately after `session.commit()`, rendering server-side values (like `updated_at` or `invoice_number`) inaccessible.

**Decision**: 
Enforce a dual-layer loading strategy for all asynchronous interactions:
1.  **Read Operations:** Every Repository query returning an object intended for Pydantic serialization **must** use `selectinload()` for all accessed relationships.
2.  **Write Operations:** Every Service method that modifies an object and returns a schema **must** call `await session.refresh(obj)` (and specific attributes) immediately following `session.commit()`.

**Consequences**: 
*   **Positive**: Completely eliminates the leading cause of async ORM runtime errors in the codebase. Guarantees that API responses always reflect the absolute latest server-persisted state.
*   **Negative**: Introduces additional "refresh" database round-trips for write operations, though negligible compared to the stability gains.

---

## ADR 024: Twelve-Factor Configuration and Secret Management

**Context**:
As Lyra moved toward CI/CD and containerized deployment, local `.env` usage and occasional hardcoded credentials risked violating Twelve-Factor principles and increased the chance of secret leakage.

**Decision**:
Enforce strict runtime configuration injection across all environments:
*   No credentials, tokens, or private keys are committed to the repository.
*   All sensitive values are supplied via environment variables at process start.
*   Local development uses **1Password CLI** (`op run --env-file=...`) to inject secrets.
*   Cloud deployment uses **Azure Key Vault** as the source of truth for production secrets.
*   Compose configurations use required-variable guards (e.g., `${VAR:?missing VAR}`) so startup fails fast when critical secrets are missing.

**Consequences**:
*   **Positive**: Aligns with Twelve-Factor config doctrine, reduces secret exposure risk, and standardizes secure onboarding.
*   **Negative**: Adds operational dependency on secret tooling (1Password/Azure) and requires disciplined environment setup in CI and local shells.

---

## ADR 025: Container Runtime and Healthcheck Contract

**Context**:
Container startup failures and drift between dev/prod execution patterns can cause non-deterministic deployments (wrong app entrypoint, blocked startup on DB timing, or invalid health probes).

**Decision**:
Standardize a container runtime contract for Lyra services:
*   Run FastAPI with `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000`.
*   Keep application containers non-root during runtime.
*   Define explicit service healthchecks and use readiness gating (`depends_on` with `condition: service_healthy`) for local orchestration.
*   Health probes must target implemented routes and matching database names.

**Consequences**:
*   **Positive**: Improves reliability of local stacks and CI smoke environments, reducing false failures and startup races.
*   **Negative**: Requires stricter maintenance of compose/runtime definitions whenever routes, database names, or startup behavior change.

---

## ADR 026: Environment Separation Policy (Local, CI, Production)

**Context**:
As Lyra scales to team development and cloud deployment, unmanaged differences between local, CI, and production configuration can create hidden bugs and unsafe operational behavior.

**Decision**:
Define explicit configuration boundaries by environment:
*   **Local**: Docker Compose plus 1Password-injected runtime environment variables.
*   **CI**: Ephemeral secrets injection during pipeline execution; no long-lived plaintext secrets in repository or build artifacts.
*   **Production**: Azure-hosted runtime with Key Vault-backed secret provisioning and no developer-local secret files.
*   Shared rule: all environments use the same required settings contract (`DATABASE_URL`, OpenAI, Twilio, admin key), differing only in secret source.

**Consequences**:
*   **Positive**: Reduces environment drift, improves auditability, and makes deployment behavior predictable across stages.
*   **Negative**: Increases initial platform configuration effort and requires documentation discipline to keep environment contracts synchronized.

---

## ADR 027: Polymorphic Document Orchestration & Provider Pattern

**Context**: 
Initial implementations of document generation (e.g., Invoices) were tightly coupled to specific business logic (tax calculations, line item formatting) within a single service. As the platform scales to support Quotes, Contracts, and custom reports, this approach would lead to code duplication and a fragile "god service."

**Decision**: 
Implement a **Provider Pattern** for document generation:
1.  **Orchestrator**: A generic `DocumentService` that handles the common "Mechanical" tasks: fetching templates, rendering HTML (Jinja2), generating PDFs (WeasyPrint), and managing storage.
2.  **Context Builders**: Specialized classes (e.g., `InvoiceContextBuilder`, `QuoteContextBuilder`) that handle the "Business" tasks: fetching specific data and transforming it into a standard rendering context.
3.  **Registry**: Link document types in the `document_templates` table to their respective builders at runtime.

**Consequences**: 
*   **Positive**: High scalability—adding a new document type (e.g., "Contract") requires only one new builder class, leaving the core engine untouched. Promotes Single Responsibility Principle (SRP).
*   **Negative**: Increases the number of classes in the service layer. Requires a registry or factory to map template types to builders.

---

## ADR 028: Persistent Object Storage (Adapter Pattern)

**Context**: 
In containerized environments (Docker, Azure App Service), the local filesystem is ephemeral. Storing generated PDFs and incoming audio files on disk leads to permanent data loss upon container restart. Furthermore, generating public links for WhatsApp requires a secure mechanism for remote file access.

**Decision**: 
Implement a decoupled `StorageService` interface (`app/infrastructure/storage/storage_service.py`) using the Adapter Pattern:
*   **Production**: Use `AzureBlobAdapter` to persist files in Azure Blob Storage.
*   **Local/Dev**: Use `LocalStorageAdapter` for zero-cost development.
*   **Security**: Implement Shared Access Signature (SAS) token generation within the Azure adapter to provide time-limited (e.g., 24h) secure URLs to users.

**Consequences**: 
*   **Positive**: Guarantees 99.9% data durability. Enables horizontal scaling of the API layer without shared disk dependencies.
*   **Negative**: Introduces dependency on Azure Storage SDKs and requires managing SAS token lifecycles for long-term audit access.

---

## ADR 029: Comprehensive Communication Audit Logging

**Context**: 
The initial "Voice-to-CRM" pipeline processed messages in real-time but left no trace of the raw input or the exact AI response. This made debugging hallucinations, reproducing user errors, and meeting legal data retention requirements impossible.

**Decision**: 
Establish a mandatory **Message Audit Log** architecture:
*   Create a `Message` model linked to `User` and `BusinessProfile`.
*   The Webhook layer is responsible for logging the `INCOMING` message (including storage URLs for audio) before processing.
*   The Webhook layer captures the `OUTGOING` response and persists it to the database asynchronously.

**Consequences**: 
*   **Positive**: Provides a definitive "Source of Truth" for every user interaction. Enables future fine-tuning of LLMs using real-world production datasets.
*   **Negative**: Increases database write volume and storage size.

---

## ADR 030: Stateless Management API Security (JWT)

**Context**: 
While Twilio webhooks are secured via signature validation, the new Management REST API (clients, jobs, analytics) requires a different security model for human users and future frontend dashboards. 

**Decision**: 
Adopt **JWT (JSON Web Tokens)** for all non-webhook REST endpoints:
*   Use `python-jose` for secure token signing and verification.
*   Implement `OAuth2PasswordBearer` flow for token exchange.
*   Enforce a `get_current_user` dependency across all management routes to ensure data isolation by `business_id`.

**Consequences**: 
*   **Positive**: Enables a secure, stateless, and scalable authentication model. Preparers the platform for a React/Mobile frontend.
*   **Negative**: Requires clients to manage token storage and refresh logic.

---

## ADR 031: Inbound Webhook Rate Limiting

**Context**: 
Every incoming WhatsApp voice note triggers expensive downstream AI calls (OpenAI Whisper + GPT-4o). An accidental loop or a malicious flood of messages could result in significant API billing spikes and resource exhaustion.

**Decision**: 
Implement **Rate Limiting** at the presentation layer using `slowapi`:
*   Apply a `@limiter.limit("10/minute")` decorator to the Twilio webhook endpoint.
*   Key the limit by the sender's remote IP address (or phone number).
*   Register a global `RateLimitExceeded` handler to return standard 429 status codes.

**Consequences**: 
*   **Positive**: Protects the project budget from runaway costs and secures the system against volumetric DoS attacks.
*   **Negative**: May occasionally block high-velocity legitimate users (e.g., a power-user sending many short voice notes in rapid succession).

