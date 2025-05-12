"""
Whisper transcription + LangChain summarisation logic.
"""

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import os
import subprocess
import tempfile
from pathlib import Path
import requests
from sqlalchemy.orm import Session
import whisper
import json

from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.callbacks import get_openai_callback

from .db import SessionLocal
from .models import Recording, SummaryMetrics

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny.en")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o") # Or "gpt-3.5-turbo"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

model = whisper.load_model(WHISPER_MODEL)

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "./audio_cache"))
AUDIO_DIR.mkdir(exist_ok=True)


def download_file(url: str, dest: Path):
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(1024 * 1024):
            f.write(chunk)


def extract_audio(video_path: Path, audio_path: Path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(audio_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def transcribe(audio_path: Path) -> dict:
    return model.transcribe(str(audio_path))

def generate_summary(transcript_path: str, recording_id: int = None) -> str:
    # Read API key and model name at runtime to respect environment overrides
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL", OPENAI_MODEL)
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set. Cannot generate summary.")

    try:
        with open(transcript_path, 'r') as f:
            transcript_data = json.load(f)
        transcript_text = transcript_data.get("text", "")
        if not transcript_text.strip():
            return "Transcript was empty or contained no text."

        llm = ChatOpenAI(temperature=0, model_name=model_name, openai_api_key=api_key)

        # Split text into manageable documents for refine chain
        text_splitter = CharacterTextSplitter(chunk_size=8000, chunk_overlap=200) # Adjusted chunk_size for longer contexts
        texts = text_splitter.split_text(transcript_text)
        docs = [Document(page_content=t) for t in texts]

        # Initial prompt for the first chunk
        prompt_template = """Write a concise summary of the following meeting transcript:

{text}

CONCISE SUMMARY:"""
        prompt = PromptTemplate(template=prompt_template, input_variables=["text"])

        # Refine prompt for subsequent chunks, incorporating the request for 5 bullets and action items
        refine_template = (
            "Your job is to produce a final summary of a meeting transcript.\n"
            "We have provided an existing summary up to a certain point: {existing_answer}\n"
            "We have the opportunity to refine the existing summary"
            "(only if needed) with some more context below.\n"
            "------------\n"
            "{text}\n"
            "------------\n"
            "Given the new context, refine the original summary to cover the entire transcript.\n"
            "The final summary MUST be formatted as follows:\n"
            "1.  A section titled '**Key Decisions (5 bullet points):**' listing exactly five key decisions made."
            "    If fewer than five decisions are evident, note this explicitly.\n"
            "2.  A section titled '**Action Items:**' listing all actionable tasks, with assigned owners if mentioned.\n"
            "If the context isn't useful, return the original summary."
        )
        refine_prompt = PromptTemplate(
            input_variables=["existing_answer", "text"],
            template=refine_template,
        )
        chain = load_summarize_chain(
            llm,
            chain_type="refine",
            question_prompt=prompt,
            refine_prompt=refine_prompt,
            return_intermediate_steps=False, # Set to True to see intermediate steps
            input_key="input_documents",
            output_key="output_text",
        )
        # Use callback to capture token usage
        with get_openai_callback() as cb:
            result = chain({"input_documents": docs})
        summary_text = result["output_text"]
        # Record metrics if recording_id provided
        if recording_id is not None:
            try:
                session = SessionLocal()
                cost_per_token = float(os.getenv("OPENAI_COST_PER_TOKEN", "0"))
                session.add(SummaryMetrics(
                    recording_id=recording_id,
                    prompt_tokens=cb.prompt_tokens,
                    completion_tokens=cb.completion_tokens,
                    total_tokens=cb.total_tokens,
                    cost=cb.total_tokens * cost_per_token
                ))
                session.commit()
            except Exception as e:
                print(f"Failed to record metrics for {recording_id}: {e}")
                session.rollback()
            finally:
                session.close()
        return summary_text

    except FileNotFoundError:
        return "Error: Transcript file not found."
    except Exception as e:
        # Log the full error for debugging
        print(f"Error during summarization: {e}")
        return f"Error generating summary: {str(e)}"


def run_transcription_job():
    db: Session = SessionLocal()
    recs_to_process = db.query(Recording).filter_by(transcript_fetched=False).all()
    
    for rec in recs_to_process:
        print(f"Processing transcription for recording ID: {rec.id}, Meeting ID: {rec.meeting_id}")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                video_file = tmpdir_path / f"{rec.meeting_id}_meeting.mp4"
                print(f"Downloading video to {video_file} from {rec.recording_url}")
                download_file(rec.recording_url, video_file)

                audio_file = tmpdir_path / f"{rec.meeting_id}_audio.wav"
                print(f"Extracting audio to {audio_file}")
                extract_audio(video_file, audio_file)

                print(f"Transcribing audio file {audio_file}")
                transcript_result = transcribe(audio_file)
                
                out_path = AUDIO_DIR / f"{rec.meeting_id}.json"
                print(f"Saving transcript to {out_path}")
                with open(out_path, "w") as f:
                    json.dump(transcript_result, f, indent=2)

                rec.transcript_fetched = True
                rec.transcript_path = str(out_path)
                db.commit()
                print(f"Transcription successful for {rec.meeting_id}.")

                # Now, attempt to summarize
                print(f"Generating summary for {rec.meeting_id} using transcript {out_path}")
                summary_text = generate_summary(str(out_path), rec.id)
                rec.summary = summary_text
                db.commit()
                print(f"Summary generated for {rec.meeting_id}: {summary_text[:100]}...")

                # Publish summary to Slack and Confluence
                try:
                    from .publishers import publish_to_slack, publish_to_confluence
                    publish_to_slack(rec.meeting_id, summary_text)
                    print(f"Posted summary to Slack for {rec.meeting_id}")
                except Exception as e:
                    print(f"Failed to post to Slack for {rec.meeting_id}: {e}")

                try:
                    publish_to_confluence(rec.meeting_id, summary_text, rec.transcript_path)
                    print(f"Posted summary to Confluence for {rec.meeting_id}")
                except Exception as e:
                    print(f"Failed to post to Confluence for {rec.meeting_id}: {e}")

        except Exception as e:
            print(f"Failed to process {rec.meeting_id}: {e}")
            db.rollback() # Rollback all changes for this recording if any step failed
            
    # Separate loop for summaries if transcription was done previously but summarization failed or was skipped
    recs_to_summarize = db.query(Recording).filter(Recording.transcript_fetched==True, Recording.summary==None).all()
    for rec in recs_to_summarize:
        if not rec.transcript_path:
            print(f"Skipping summary for {rec.meeting_id}: transcript_path is missing.")
            continue
        
        print(f"Attempting to generate summary for previously transcribed recording: {rec.meeting_id}")
        try:
            summary_text = generate_summary(rec.transcript_path, rec.id)
            rec.summary = summary_text
            db.commit()
            print(f"Summary generated for {rec.meeting_id}: {summary_text[:100]}...")

            # Publish summary to Slack and Confluence
            try:
                from .publishers import publish_to_slack, publish_to_confluence
                publish_to_slack(rec.meeting_id, summary_text)
                print(f"Posted summary to Slack for {rec.meeting_id}")
            except Exception as e:
                print(f"Failed to post to Slack for {rec.meeting_id}: {e}")

            try:
                publish_to_confluence(rec.meeting_id, summary_text, rec.transcript_path)
                print(f"Posted summary to Confluence for {rec.meeting_id}")
            except Exception as e:
                print(f"Failed to post to Confluence for {rec.meeting_id}: {e}")
        except Exception as e:
            print(f"Failed to generate summary for {rec.meeting_id} during catch-up: {e}")
            db.rollback()
            
    db.close()