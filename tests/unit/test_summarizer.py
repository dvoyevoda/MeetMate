import pytest
import os
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# Ensure app modules can be imported
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.summarizer import generate_summary, AUDIO_DIR

# Create a dummy transcript file for testing
DUMMY_TRANSCRIPT_CONTENT = {
    "text": "This is a test transcript. It contains several key points. First, we decided to test the summarizer. Second, action item for Bob is to write more tests. Third, everyone agreed this meeting was productive."
}
DUMMY_TRANSCRIPT_ID = "test_transcript_123"
TRANSCRIPT_FILE_PATH = AUDIO_DIR / f"{DUMMY_TRANSCRIPT_ID}.json"

@pytest.fixture(scope="module", autouse=True)
def setup_dummy_transcript():
    AUDIO_DIR.mkdir(exist_ok=True)
    with open(TRANSCRIPT_FILE_PATH, 'w') as f:
        json.dump(DUMMY_TRANSCRIPT_CONTENT, f)
    yield
    os.remove(TRANSCRIPT_FILE_PATH)

@patch('app.summarizer.ChatOpenAI')
@patch.dict(os.environ, {"OPENAI_API_KEY": "fake_api_key", "OPENAI_MODEL": "gpt-test"})
def test_generate_summary_success(MockChatOpenAI):
    # Mock the LangChain chain and its invoke/call method
    mock_llm_instance = MockChatOpenAI.return_value
    mock_chain = MagicMock()
    mock_chain.return_value = {"output_text": "**Key Decisions (5 bullet points):**\n- Test summarizer.\n- Bob to write tests.\n- Meeting productive.\n- (No other decisions noted)\n- (No other decisions noted)\n\n**Action Items:**\n- Bob: Write more tests."}
    
    # To mock load_summarize_chain, we need to patch it where it's looked up
    with patch('app.summarizer.load_summarize_chain', return_value=mock_chain) as mock_load_chain:
        summary = generate_summary(str(TRANSCRIPT_FILE_PATH))

        assert "**Key Decisions (5 bullet points):**" in summary
        assert "**Action Items:**" in summary
        assert "Bob to write tests." in summary
        mock_load_chain.assert_called_once()
        # Check if the LLM instance (created by ChatOpenAI) was used by the chain
        assert mock_load_chain.call_args[0][0] == mock_llm_instance

@patch.dict(os.environ, {"OPENAI_API_KEY": ""}) # Simulate missing API key
def test_generate_summary_no_api_key():
    with pytest.raises(ValueError, match="OPENAI_API_KEY not set"): #Updated to ValueError based on implementation
        generate_summary(str(TRANSCRIPT_FILE_PATH))

def test_generate_summary_file_not_found():
    # Set a valid API key for this test case, as we are testing file not found, not auth.
    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake_api_key"}):
        summary = generate_summary("non_existent_file.json")
        assert summary == "Error: Transcript file not found."

def test_generate_summary_empty_transcript():
    EMPTY_TRANSCRIPT_ID = "empty_transcript_test"
    empty_transcript_path = AUDIO_DIR / f"{EMPTY_TRANSCRIPT_ID}.json"
    with open(empty_transcript_path, 'w') as f:
        json.dump({"text": " "}, f) # Transcript with only whitespace
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake_api_key"}):
        summary = generate_summary(str(empty_transcript_path))
        assert summary == "Transcript was empty or contained no text."
    os.remove(empty_transcript_path)

@patch('app.summarizer.ChatOpenAI')
@patch.dict(os.environ, {"OPENAI_API_KEY": "fake_api_key", "OPENAI_MODEL": "gpt-test"})
def test_generate_summary_llm_error(MockChatOpenAI):
    mock_llm_instance = MockChatOpenAI.return_value
    mock_chain = MagicMock()
    mock_chain.side_effect = Exception("LLM service unavailable")

    with patch('app.summarizer.load_summarize_chain', return_value=mock_chain):
        summary = generate_summary(str(TRANSCRIPT_FILE_PATH))
        assert "Error generating summary: LLM service unavailable" in summary 