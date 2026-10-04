from app.services.prompts import NOT_FOUND, SYSTEM_PROMPT, build_prompt
from app.services.vector_store import RetrievedChunk


def chunk(text, page, filename="notes.pdf"):
    return RetrievedChunk(document_id="doc-1", filename=filename, page=page, text=text, distance=0.1)


CHUNKS = [chunk("Precision measures exactness.", 12), chunk("Recall measures coverage.", 13)]


def test_system_prompt_defines_the_not_found_sentinel():
    assert NOT_FOUND in SYSTEM_PROMPT


def test_chunks_are_numbered_with_filename_and_page():
    prompt = build_prompt("What is precision?", CHUNKS)

    assert "[1] (notes.pdf, page 12) Precision measures exactness." in prompt
    assert "[2] (notes.pdf, page 13) Recall measures coverage." in prompt


def test_question_comes_after_the_context():
    prompt = build_prompt("What is precision?", CHUNKS)

    assert prompt.index("CONTEXT:") < prompt.index("QUESTION:")
    assert prompt.endswith("What is precision?")


def test_no_conversation_section_without_history():
    prompt = build_prompt("What is precision?", CHUNKS)

    assert "CONVERSATION SO FAR" not in prompt


def test_history_is_included_with_speaker_labels():
    history = [("user", "What is a confusion matrix?"), ("assistant", "A table of outcomes. [1]")]

    prompt = build_prompt("Explain that more simply", CHUNKS, history)

    assert "User: What is a confusion matrix?" in prompt
    assert "Assistant: A table of outcomes. [1]" in prompt
    assert prompt.index("CONVERSATION SO FAR") < prompt.index("CONTEXT:")