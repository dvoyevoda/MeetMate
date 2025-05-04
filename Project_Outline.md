# MeetMate – AI Meeting Summarizer  
*A cross‑platform bot that records Zoom / Google Meet calls, transcribes them with Whisper, produces GPT‑4o summaries, and posts digests to Slack & Confluence.*

---

## 0 | High‑level Goals
- **Capture** audio/video from major meeting platforms.  
- **Transcribe** reliably with OpenAI Whisper.  
- **Summarise** into 5 bullets + action items via GPT‑4o / LangChain.  
- **Deliver** digests to Slack (channel or thread) and Confluence (new page).  
- **Monitor** latency, token cost, and ROUGE‑L summary quality.  
- **Package** everything in Docker; support one‑click deploy on Fly.io / Render.

---

## 1 | System Architecture

### 1.1 Component Diagram

| Layer | Key Services | Notes |
|-------|--------------|-------|
| **Capture** | Zoom Recording Webhook, Google Meet “conferenceRecords” API | Poll recording URLs every 60 s. |
| **Backend API** | **FastAPI** (`/webhook`, `/health`) | Async, high‑throughput. |
| **Transcription** | **Whisper** (local or OpenAI endpoint) | Multilingual, accurate. |
| **Summariser** | LangChain `map_reduce` / `refine` chain | Works with GPT‑4o or gpt‑3.5‑turbo. |
| **Publishers** | Slack Incoming Webhook / Bolt app; Confluence REST API | Slack for chat, Confluence for archives. |
| **Dashboards** | Streamlit | Cost & latency charts. |
| **Storage** | Postgres (metadata) • S3 or local FS (audio cache) | Purge audio after transcription for privacy. |

### 1.2 Data Flow
1. Meeting ends → recording‑ready webhook fires.  
2. FastAPI receives URL, downloads `.mp4`.  
3. Whisper transcribes to JSON (speaker turns included).  
4. LangChain summarises → returns bullets & action items.  
5. Slack webhook posts digest; Confluence REST creates page with full transcript.  
6. Metrics (tokens, seconds) logged; Streamlit dashboard refreshes.

---

## 2 | Tech‑Stack Rationale

| Concern | Choice | Reason |
|---------|--------|--------|
| API Server | **FastAPI** | Modern async, auto‑docs, high perf. |
| Speech‑to‑Text | **Whisper** | State‑of‑the‑art, local or cloud. |
| Summarisation | **LangChain** | Ready‑made summary chains & memory. |
| Messaging | **Slack Webhooks / Bolt** | Native formatting, threading. |
| Knowledge Base | **Confluence REST** | Many companies already use Confluence. |
| Evaluation | **ROUGE‑L** via `rouge-score` | Standard summary metric. |
| Cost Tracking | **OpenAI Usage API** | Easy $/token monitoring. |
| UI | **Streamlit** | Fast dashboards without JS. |

---

## 3 | Development Phases & Tasks

### Phase 1 — Scaffold
1. `git init meetmate`.  
2. Create `Dockerfile`, `docker-compose.yml` (FastAPI, Postgres).  
3. Add basic FastAPI root route + `/health`.

### Phase 2 — Capture & Webhooks
1. Register Zoom Server‑to‑Server app → handle recording‑completed webhook.  
2. Enable Google Meet API → poll `conferenceRecords.transcripts`.  
3. Store recording URL & metadata in Postgres.

### Phase 3 — Transcription
1. Download `.mp4` → extract audio track.  
2. Run Whisper (`tiny.en` local for dev; OpenAI Whisper in prod).  
3. Save JSON transcript; purge original audio for privacy.

### Phase 4 — Summarisation
1. Implement LangChain `RefineDocumentsChain` with GPT‑4o.  
2. Prompt template: “Return **five** bullet decisions and an **Action Items** list.”  
3. Unit‑test summaries on 3 sample recordings.

### Phase 5 — Publish Integrations
1. Slack: create Incoming Webhook; post Markdown digest.  
2. Confluence: POST a new page with transcript + summary.  
3. Add retry / back‑off logic to handle 429s.

### Phase 6 — Metrics & Dashboard
1. Log `prompt_tokens`, `completion_tokens`, `$cost`.  
2. Build Streamlit dashboard (cost / day line chart, latency bar chart).  
3. Alert via Slack DM if cost > $5 / day.

### Phase 7 — Testing & Hardening
1. **Unit Tests**: FastAPI endpoints (`pytest` + `httpx`).  
2. **Integration Tests**: mock Zoom payload → end‑to‑end summary.  
3. **Quality Eval**: compute ROUGE‑L against human summaries.  
4. **Security**: validate HMAC headers; store secrets in `.env`.

---

## 4 | File / Repo Layout

meetmate/
├── app/
│   ├── main.py        # FastAPI routes
│   ├── tasks.py       # background jobs / Celery optional
│   └── summarizer.py  # Whisper + LangChain logic
├── dashboards/
│   └── cost_dashboard.py
├── tests/
│   ├── unit/
│   └── integration/
├── Dockerfile
├── docker-compose.yml
├── README.md
└── .github/
└── workflows/ci.yml

---

## 5 | Stretch Enhancements

| Feature | Benefit |
|---------|---------|
| Voice diarisation (speaker labels) | Attribute remarks to speakers. |
| Auto‑language detection | Whisper language ID → correct model. |
| Slack slash command `/summarize-latest` | Ad‑hoc summary on demand. |
| GDPR purge job | Auto‑delete transcripts after 30 days. |
| Hallucination guard | Reject summaries with > 10 % unmatched text. |

---

## 6 | Project Milestones & Deliverables

| **Stage** | **Deliverable** |
|-----------|-----------------|
| **Stage 1** | Live FastAPI endpoint (`/health`) + repo scaffold committed. |
| **Stage 2** | Recording webhook received and saved to Postgres. |
| **Stage 3** | Local `.mp4` → JSON transcript pipeline operational. |
| **Stage 4** | GPT‑4o summary function returns 5 bullets & action items. |
| **Stage 5** | Digest posting to Slack and Confluence verified end‑to‑end. |
| **Stage 6** | Streamlit dashboard shows cost & latency metrics. |
| **Stage 7** | All tests pass; demo video & complete README published.

---

## 7 | README Checklist
- ✅ 30‑second product pitch  
- ✅ Quick‑start (`docker compose up`)  
- ✅ `.env.example` with all required keys  
- ✅ Architecture diagram (PNG)  
- ✅ Testing guide (`pytest -q`)  
- ✅ Demo GIF + Loom walkthrough link  

---