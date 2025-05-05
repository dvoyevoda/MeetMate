# MeetMate

**AI-Powered Meeting Summarizer**

---

> **Note:** This project is a work in progress and not yet production-ready.

---

## 🚀 Project Goals
MeetMate is a cross‑platform bot that:
- **Captures** audio/video from Zoom and Google Meet calls
- **Transcribes** meetings using OpenAI Whisper
- **Summarizes** with GPT‑4o (via LangChain) into concise bullet points and action items
- **Delivers** digests to Slack channels/threads and Confluence pages
- **Monitors** latency, token cost, and summary quality
- **Packages** everything in Docker for easy deployment

## 🏗️ Current Status
- Project is in early development
- Core scaffolding and infrastructure are being set up
- Major features are in progress (see [Project_Outline.md](Project_Outline.md) for roadmap)

## 📦 Tech Stack
- **FastAPI** (Python async backend)
- **OpenAI Whisper** (speech-to-text)
- **LangChain + GPT-4o** (summarization)
- **Slack API & Confluence REST** (publishing digests)
- **Streamlit** (metrics dashboard)
- **Postgres & S3/local FS** (storage)
- **Docker** (containerization)

## 📋 Features (Planned)
- [ ] Zoom & Google Meet integration
- [ ] Automated transcription
- [ ] GPT-4o/LangChain summarization
- [ ] Slack & Confluence publishing
- [ ] Cost/latency metrics dashboard
- [ ] Automated tests and CI

See [Project_Outline.md](Project_Outline.md) for full roadmap and architecture details.

---

## 📢 License
MIT (see LICENSE file)
