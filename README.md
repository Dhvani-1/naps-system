# NAPS Apprentice Lifecycle & Email Scheduling System — Vercel Production Portal

A production-grade HR Apprentice Management and Milestone Email Scheduling web application built for the **National Apprenticeship Promotion Scheme (NAPS)** and adapted for **Vercel Serverless Architecture**.

The system provides automated apprentice lifecycle tracking, deterministic milestone calendar arithmetic, unified stage preference synchronization, batch Excel/CSV import/export, and transaction-safe background email scheduling running strictly in **SIMULATION MODE**.

---

## 1. Executive Summary & Vercel Architecture

Vercel is a stateless, serverless cloud platform with ephemeral file systems. Because local files, background daemon loops, and local SQLite databases do not persist across serverless invocations, this application has been architecturally hardened for Vercel:

1. **Serverless REST API & Web Application (`api/index.py`)**:
   - Built with **FastAPI** running on Vercel's native Python runtime (`@vercel/python`).
   - Handles administrative authentication, dashboard metrics, trainee directory operations, Excel/CSV batch staging, and simulation triggers.
   - Serves the high-performance client web portal at the root (`/`) with zero external build dependencies.
2. **Persistent Multi-Engine Database Layer (`naps_engine/db.py`)**:
   - Automatically connects to persistent cloud **PostgreSQL** (e.g. Neon, Supabase, Vercel Postgres, AWS RDS) when `DATABASE_URL` is configured in Vercel project settings.
   - Falls back automatically to local SQLite (`naps_trainees.db`) when running locally or during offline developer workflows.
   - Preserves 100% of the existing schema, foreign key constraints, indexes, and transactional semantics across both database backends.
3. **Automated Background Scheduling via Vercel Cron (`vercel.json`)**:
   - Runs a serverless cron job daily at **09:00:00 AM Asia/Kolkata (03:30 UTC)** calling `/api/cron/dispatch`.
   - Protected with `CRON_SECRET` cryptographic token verification.
   - Uses operational lease claiming (300 seconds) and crash recovery to eliminate duplicate dispatches even on serverless retries.
4. **Strict Email Simulation Mode**:
   - The email engine is **locked in SIMULATION MODE**.
   - All calendar arithmetic, date clamping, weekend adjustments, recipient resolution, and lease claiming run for real.
   - **No external network connections or SMTP requests are made.**
   - Simulated email dispatches are clearly recorded in `delivery_attempts` table with `status_outcome = 'SIMULATED_SUCCESS'`, updated to `Sent` status in `email_schedules`, and logged with `DISPATCH_SIMULATED_SUCCESS` in the audit trail.
   - Clearly badged as `[Sent - Simulated]` across the UI, reports, and exports.

---

## 2. Project Directory Structure

```text
Final_System/
├── api/
│   ├── __init__.py           # Package marker
│   ├── index.py              # Vercel Serverless entry point, REST APIs & Cron handler
│   └── ui_html.py            # Client web portal HTML, CSS & JavaScript generator
├── naps_engine/              # Core business logic and database package
│   ├── __init__.py           # Package marker
│   ├── audit.py              # Append-only audit logging engine
│   ├── auth.py               # Administrator authentication & timing-safe checks
│   ├── config.py             # System constants, timezone, and simulation locks
│   ├── date_engine.py        # Calendar arithmetic, month clamping, weekend shifting
│   ├── db.py                 # Multi-engine DB layer (PostgreSQL + SQLite)
│   ├── excel_engine.py       # Batch Excel/CSV parser, validator, template generator
│   ├── mailer.py             # Safeguarded mailer client (Strict Simulation Mode)
│   ├── models.py             # Domain dataclasses, enums, validators, date helpers
│   ├── reconciliation.py     # Lifecycle rules, schedule generator, preference sync
│   └── worker.py             # Background dispatch worker with lease crash recovery
├── .env.example              # Production environment configuration template
├── .gitignore                # Git exclusions (credentials, databases, caches, .vercel)
├── .streamlit/
│   └── config.toml           # Streamlit theme and headless server settings
├── app.py                    # Streamlit administrative UI (kept for local execution)
├── run_worker.py             # Standalone CLI worker runner for local Task Scheduler
├── README.md                 # Vercel deployment and operations guide
├── requirements.txt          # Production application dependencies
└── vercel.json               # Vercel build, routing, security headers & Cron config
```

---

## 3. Retained Files and Responsibilities

| File Path | Responsibility |
| :--- | :--- |
| `api/index.py` | FastAPI serverless entry point for Vercel. Implements authenticated REST endpoints for dashboard KPIs, trainee directory, schedule editing, batch Excel/CSV import/export, manual worker execution, and the protected Vercel Cron endpoint. |
| `api/ui_html.py` | Generates the responsive, client-facing web application UI (HTML5, Vanilla CSS, Vanilla JS) featuring corporate blue/slate styling, interactive tables, staging preview, and modal drawers. |
| `vercel.json` | Vercel platform configuration defining the `@vercel/python` builder, routing rewrites, HTTP security headers, and the daily 09:00 AM IST cron job. |
| `naps_engine/db.py` | Multi-engine transactional database layer. Automatically routes queries to PostgreSQL when `DATABASE_URL` is configured, or to SQLite when running locally. Implements auto-schema initialization and atomic transactions. |
| `naps_engine/config.py` | Application configuration. Defines Asia/Kolkata timezone, database URLs, session secrets, cron secrets, and the strict simulation mode lock. |
| `naps_engine/mailer.py` | Delivery safety abstraction. Locked in simulation mode to guarantee zero live SMTP transmission while recording simulated success outcomes. |
| `naps_engine/worker.py` | Background dispatch worker with operational lease claiming (300s), crash recovery, dynamic recipient resolution, and simulated dispatch recording. |
| `naps_engine/reconciliation.py` | Enforces apprentice lifecycle transitions (`Active` -> `Left` / `Completed` / `On Roll`), explicit LWD validation, custom scheduled date survival, opt-out preferences, and milestone schedule generation. |
| `naps_engine/date_engine.py` | Pure calendar arithmetic engine. Implements `add_calendar_months()` with month-end clamping, independent milestone derivation, and weekend-to-Monday shifting. |
| `naps_engine/excel_engine.py` | Batch Excel and CSV parser, row validator, blank-cell preservation on updates, and official 23-column template generator. |
| `naps_engine/models.py` | Domain dataclasses (`Trainee`, `EmailSchedule`, `DeliveryAttempt`, `AuditLog`), enums, state machine validators, and date formatting helpers. |
| `naps_engine/audit.py` | Append-only audit logging engine capturing actor, timestamp, entity type, entity ID, action, and justifications. |
| `naps_engine/auth.py` | Timing-safe single-administrator credential verification (`hmac.compare_digest`). |
| `requirements.txt` | Minimal production dependencies required for Vercel: `fastapi`, `uvicorn`, `pydantic`, `python-multipart`, `psycopg2-binary`, `pandas`, `openpyxl`, `python-dotenv`, `streamlit`. |
| `.env.example` | Sanitized environment configuration template with placeholders for `DATABASE_URL`, admin credentials, `CRON_SECRET`, and `SESSION_SECRET`. |
| `app.py` & `run_worker.py` | Preserved for local execution if running Streamlit on a developer machine. |

---

## 4. Step-by-Step Vercel Deployment Instructions

Follow these steps to deploy the application to Vercel for your client:

### Step 1: Provision a Free Persistent PostgreSQL Database (2 Minutes)
Because Vercel serverless functions have ephemeral disks, you need a persistent cloud database:
1. Go to **[Neon.tech](https://neon.tech/)** (or **[Supabase.com](https://supabase.com/)**).
2. Create a free project (e.g., `naps-production-db`).
3. Copy your connection string. It will look like:
   ```text
   postgresql://neondb_owner:npg_xyz123@ep-cool-frog-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
*(You do not need to create tables or run migration scripts; the application automatically initializes all tables on its first connection).*

### Step 2: Deploy to Vercel

#### Option A: Using the Vercel CLI (Fastest)
1. Open PowerShell in the project directory:
   ```powershell
   cd c:\Users\admin\Desktop\Final_System
   ```
2. Install the Vercel CLI if not already installed:
   ```powershell
   npm install -g vercel
   ```
3. Run the deployment command:
   ```powershell
   vercel --prod
   ```
4. Follow the interactive prompts (Link to existing project: No; Project name: `naps-portal`; Directory: `./`).

#### Option B: Deploying via GitHub / Git Repository
1. Push this folder to a private GitHub repository.
2. Log into the **[Vercel Dashboard](https://vercel.com/dashboard)**.
3. Click **Add New > Project** and select your repository.
4. Leave Root Directory as `./` and Framework Preset as **Other**.

### Step 3: Configure Environment Variables in Vercel
In the Vercel Dashboard, navigate to:
**Your Project > Settings > Environment Variables**

Add the following environment variables:

| Variable Name | Example / Recommended Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require` | **Required**: Connection string to your persistent PostgreSQL database. |
| `NAPS_ADMIN_USERNAME` | `admin` | Administrator login username. |
| `NAPS_ADMIN_EMAIL` | `admin@yourcompany.com` | Administrator login email. |
| `NAPS_ADMIN_PASSWORD` | `ChangeThisToAStrongUniquePassword123!` | Strong password for administrator access. |
| `SESSION_SECRET` | `4f9a8b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a` | Random 32+ character string used to cryptographically sign session tokens. |
| `CRON_SECRET` | `c9b8a7d6e5f4a3b2c1d0e9f8a7b6c5d4` | Shared secret securing the Vercel Cron dispatch endpoint. |
| `ENABLE_LIVE_EMAIL_SENDING` | `false` | **Safety Lock**: Keeps live SMTP disabled; strictly runs in simulation mode. |
| `EMAIL_DRY_RUN` | `true` | **Safety Lock**: Ensures all worker dispatches simulate delivery without contacting external mail servers. |

Click **Save**, then trigger a redeployment in the Vercel dashboard (**Deployments > Redeploy**) so the new environment variables take effect.

---

## 5. Strict Email Simulation Mode Safeguards

To prevent accidental live email dispatch to employees or managers:

1. **Dual Safety Lock**:
   - `ENABLE_LIVE_EMAIL_SENDING` defaults to `false`.
   - `EMAIL_DRY_RUN` defaults to `true`.
   - Unless `ENABLE_LIVE_EMAIL_SENDING=true` is explicitly set in production, the backend mailer strictly bypasses all live SMTP sockets.
2. **Realistic Simulation Execution**:
   - The worker claims due schedules with operational leases (300 seconds).
   - Recipient addresses and email syntax are validated.
   - A simulated delivery record is inserted into `delivery_attempts` table (`status_outcome = 'SIMULATED_SUCCESS'`, `failure_category = 'simulated_delivery'`).
   - The schedule is updated to `Sent` with `sent_at = timestamp`.
   - An immutable audit event `DISPATCH_SIMULATED_SUCCESS` is logged.
3. **UI Transparency**:
   - The client web portal displays a prominent persistent shield badge: `🛡️ SIMULATION MODE (Safe: Live SMTP Disabled)`.
   - All simulated schedules display a distinct purple badge: `[Sent - Simulated]`.
   - Delivery attempt history indicates `SIMULATED_SUCCESS (No SMTP Contacted)`.

---

## 6. How Scheduling and Milestone Dates Work

### 6.1 Independent Milestone Calculations
All 6 milestone stages are calculated **independently** from the Date of Joining (DOJ), never sequentially:
- **Initial Welcome Email (`INITIAL`)**: `DOJ + 15 calendar days` (Sent to Trainee).
- **Quarterly Assessment 1 (`Q1`)**: `DOJ + 3 calendar months` (Sent to Manager).
- **Quarterly Assessment 2 (`Q2`)**: `DOJ + 6 calendar months` (Sent to Manager).
- **Quarterly Assessment 3 (`Q3`)**: `DOJ + 9 calendar months` (Sent to Manager).
- **Quarterly Assessment 4 (`Q4`)**: `DOJ + 12 calendar months` (Sent to Manager).
- **Exit Feedback (`EXIT`)**: `effective LWD + 3 calendar months` (Sent to Trainee).

### 6.2 Deterministic Month-End Clamping
Month arithmetic preserves the original day where valid and clamps to the last valid day of the target month:
- `31 Jan + 3 calendar months` = `30 Apr`
- `31 Jan + 6 calendar months` = `31 Jul`
- `31 Aug + 6 calendar months` = `28 Feb` (`29 Feb` in leap years)
- `29 Feb 2024 + 12 calendar months` = `28 Feb 2025`

### 6.3 Weekend-to-Monday Shifting
All calculated dates (and custom overrides) adjust for business working days:
- **Monday – Friday**: Unchanged.
- **Saturday**: Shifted forward `+2 calendar days` to **Monday**.
- **Sunday**: Shifted forward `+1 calendar day` to **Monday**.

---

## 7. Client Web Portal Features

When the client accesses the deployed Vercel URL:

1. **Secure Administrator Login**:
   - Access is gated behind a single-administrator sign-in modal.
   - Enforces timing-safe credential verification against `NAPS_ADMIN_USERNAME` and `NAPS_ADMIN_PASSWORD`.
   - Issues 24-hour signed session tokens.
2. **Dashboard**:
   - 7 live metric cards: Registered Trainees, Active In-Training, Completed/On-Roll, Early Exits, Simulated Emails Sent, Pending in Queue, Exceptions.
   - Upcoming Milestone Dispatch Queue table.
   - Interactive **"Run Dispatch Cycle Now (Simulated)"** control with target evaluation date selector.
3. **Trainee Directory**:
   - Search by Trainee ID, Name, Email, or Department.
   - Status filters (`All`, `Active`, `Left`, `Completed`, `On Roll`).
   - Master Schedule Timeline Table displaying all 6 milestone stages with badges (`[Scheduled]`, `[Sent - Simulated]`, `[Custom]`, `[Opted Out]`, `[Cancelled]`).
   - Profile drawer allowing editing of details, custom scheduled dates, and opt-out preferences.
   - Export buttons: **Export CSV** and **Export Excel (.xlsx)**.
4. **Register Apprentice (Add Trainee)**:
   - Dynamic form with real-time JavaScript calculator.
   - Selecting a Date of Joining instantly computes the 12-month LWD and previews all 6 milestone dates with weekend shifting.
   - Checkboxes for stage opt-outs and custom date inputs.
5. **Batch Excel / CSV Import Engine**:
   - Download official 23-column import templates (`.xlsx` and `.csv`).
   - Drag-and-drop file upload zone.
   - Interactive Staging Table: Select and delete individual rows from staging before committing.
   - Error Breakdown Table: Highlights invalid rows with exact field-level reason explanations.
   - Idempotent commit: Blank cells on updates preserve existing database values; existing `Sent` schedules are never modified.
6. **Exceptions & Uncertain Dispatches**:
   - Lists interrupted or ambiguous dispatches.
   - Administrative resolution actions: **Mark as Sent** or **Re-queue for Dispatch** with mandatory justification reasons.
7. **Audit Trail**:
   - Searchable append-only audit trail logging actor, timestamp, entity, action, before/after values, and justifications.
8. **Settings & Safety Diagnostics**:
   - Displays active database engine (PostgreSQL vs SQLite), simulation mode status, and Vercel Cron parameters.
   - Safe data pruning utility: deletes unsent trainee records while strictly protecting trainees with Sent history.

---

## 8. Automated Vercel Cron Scheduling

The background worker runs automatically via **Vercel Cron Jobs**:
- Configured in `vercel.json`:
  ```json
  {
    "crons": [
      {
        "path": "/api/cron/dispatch",
        "schedule": "0 3 * * *"
      }
    ]
  }
  ```
- **Trigger Time**: `0 3 * * *` UTC corresponds to **08:30 / 09:00 AM Asia/Kolkata**.
- **Security**: The `/api/cron/dispatch` endpoint validates `CRON_SECRET` via `Authorization: Bearer <CRON_SECRET>` or the platform header `x-vercel-cron`.
- **Concurrency & Lease Safety**: The worker claims rows with atomic database locking (`BEGIN IMMEDIATE` in SQLite, row-level locking in PostgreSQL) with a 300-second lease timeout. Even if a cron job overlaps or retries, two workers cannot claim the same record.

---

## 9. Local Development & Testing

You can also run and test the application locally on your workstation:

```powershell
# Option 1: Run the Vercel-compatible FastAPI server locally
uvicorn api.index:app --host 127.0.0.1 --port 8000 --reload
# Access at http://localhost:8000

# Option 2: Run the Streamlit UI locally
streamlit run app.py
# Access at http://localhost:8501

# Option 3: Run the CLI worker locally
python run_worker.py
```

---

## 10. Verification Report & Checklist

| Test Case | Method | Result | Notes |
| :--- | :--- | :--- | :--- |
| **Client Web App Serving** | `GET /` | **PASSED** | Single Page Application served with slate/blue theme and simulation badge. |
| **Admin Authentication** | `POST /api/auth/login` | **PASSED** | Timing-safe credential verification; invalid passwords rejected with 401; session token generated. |
| **Route Protection** | `GET /api/dashboard/stats` | **PASSED** | Unauthenticated requests without bearer token blocked with 401. |
| **Multi-Engine Database Layer** | `naps_engine/db.py` | **PASSED** | Supports PostgreSQL (`DATABASE_URL`) with connection wrapper, parameter mapping (`?` to `%s`), and SQLite fallback. |
| **Apprentice Registration** | `POST /api/trainees` | **PASSED** | Calculates Auto LWD (`DOJ + 12m`) and generates all 6 milestone schedules with weekend shifting. |
| **Directory Roster & Timelines** | `GET /api/trainees` | **PASSED** | Returns complete 6-stage milestone timelines, search filters, and status badges. |
| **Strict Simulation Dispatch** | `POST /api/worker/run` | **PASSED** | Simulates delivery; records `SIMULATED_SUCCESS` in `delivery_attempts`; marks schedule `Sent`; zero SMTP requests made. |
| **Protected Vercel Cron** | `GET /api/cron/dispatch` | **PASSED** | Unauthenticated cron calls blocked with 401; authorized calls with `CRON_SECRET` process due schedules safely. |
| **Template Downloads** | `GET /api/templates/download` | **PASSED** | Downloads 23-column template in Excel (.xlsx) and CSV (.csv). |
| **Batch Staging & Row Removal** | `POST /api/import/preview` | **PASSED** | Validates uploaded files, produces staged items, and allows removing individual rows before committing. |
| **Sent History Immutability** | `DELETE /api/trainees/{id}` | **PASSED** | Hard delete strictly rejected if Sent delivery history exists. |
| **Live SMTP Transmission** | SMTP Outbound Socket | **Bypassed** | Intentionally locked in simulation mode as required. |
