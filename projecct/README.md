# The Flashcard Engine

A Python Flask app that converts PDFs into flashcard decks, then schedules review with spaced repetition.

## Folder structure

- `main.py`: local entrypoint for running the app
- `app.py`: Flask app factory
- `agents/`: flashcard-generation logic
- `components/`: view-model builders for dashboard, deck pages, and review
- `models/`: dataclasses
- `services/`: PDF parsing, storage, deck logic, AI provider clients, SM-2 scheduler
- `templates/`: HTML pages
- `static/`: CSS and JavaScript
- `data/`: SQLite database and uploaded PDFs
- `.env/`: API key template for Groq or Gemini

## Setup

```bash
cd projecct
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Open `http://127.0.0.1:5000`

## API keys

Edit `.env/.env.example` and add one of these:

- `GROQ_API_KEY=your_key_here`
- `GEMINI_API_KEY=your_key_here`

If you leave keys blank, the app still works with an offline flashcard builder.
