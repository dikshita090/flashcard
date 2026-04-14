from datetime import datetime
from pathlib import Path
from uuid import uuid4

from agents.flashcard_agent import build_flashcards
from services.pdf_service import derive_title, extract_pdf_text
from services.storage import get_connection


def create_deck_from_pdf(config, title: str, subject: str, provider: str, uploaded_file) -> int:
    upload_folder: Path = config["UPLOAD_FOLDER"]
    source_name = Path(uploaded_file.filename).name
    unique_name = f"{uuid4().hex}_{source_name}"
    saved_path = upload_folder / unique_name
    uploaded_file.save(saved_path)

    text = extract_pdf_text(saved_path)
    if not text.strip():
        raise ValueError("The PDF did not contain readable text. Please try a text-based PDF.")
    deck_title = title or derive_title(source_name)
    cards = build_flashcards(config["BASE_DIR"], text, deck_title, provider)
    now = datetime.now().isoformat(timespec="seconds")

    connection = get_connection(config["DATABASE_PATH"])
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO decks (title, subject, source_filename, provider, source_text, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (deck_title, subject, source_name, provider, text, now, now),
    )
    deck_id = cursor.lastrowid

    for card in cards:
        cursor.execute(
            """
            INSERT INTO cards (
                deck_id, question, answer, explanation, card_type, difficulty_hint,
                source_excerpt, tags, created_at, updated_at, due_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                deck_id,
                card.question,
                card.answer,
                card.explanation,
                card.card_type,
                card.difficulty_hint,
                card.source_excerpt,
                card.tags,
                now,
                now,
                now,
            ),
        )

    connection.commit()
    connection.close()
    return int(deck_id)


def list_decks(config, query: str = ""):
    connection = get_connection(config["DATABASE_PATH"])
    cursor = connection.cursor()
    pattern = f"%{query.lower()}%"
    cursor.execute(
        """
        SELECT
            decks.*,
            COUNT(cards.id) AS card_count,
            SUM(CASE WHEN datetime(cards.due_at) <= datetime('now') THEN 1 ELSE 0 END) AS due_count,
            ROUND(AVG(cards.mastery_score), 1) AS mastery_average
        FROM decks
        LEFT JOIN cards ON cards.deck_id = decks.id
        WHERE LOWER(decks.title) LIKE ? OR LOWER(COALESCE(decks.subject, '')) LIKE ?
        GROUP BY decks.id
        ORDER BY datetime(decks.updated_at) DESC
        """,
        (pattern, pattern),
    )
    rows = cursor.fetchall()
    connection.close()
    return rows


def find_deck(config, deck_id: int):
    connection = get_connection(config["DATABASE_PATH"])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM decks WHERE id = ?", (deck_id,))
    row = cursor.fetchone()
    connection.close()
    return row


def get_deck_cards(config, deck_id: int):
    connection = get_connection(config["DATABASE_PATH"])
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT *
        FROM cards
        WHERE deck_id = ?
        ORDER BY datetime(due_at) ASC, id ASC
        """,
        (deck_id,),
    )
    rows = cursor.fetchall()
    connection.close()
    return rows


def get_due_cards(config, deck_id: int | None = None):
    connection = get_connection(config["DATABASE_PATH"])
    cursor = connection.cursor()
    params = []
    where = "WHERE datetime(cards.due_at) <= datetime('now')"
    if deck_id is not None:
        where += " AND cards.deck_id = ?"
        params.append(deck_id)
    cursor.execute(
        f"""
        SELECT cards.*, decks.title AS deck_title
        FROM cards
        JOIN decks ON decks.id = cards.deck_id
        {where}
        ORDER BY datetime(cards.due_at) ASC, cards.mastery_score ASC, cards.id ASC
        LIMIT 1
        """,
        params,
    )
    row = cursor.fetchone()
    connection.close()
    return row


def get_stats(config):
    connection = get_connection(config["DATABASE_PATH"])
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) AS count FROM decks")
    deck_count = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) AS count FROM cards")
    card_count = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) AS count FROM cards WHERE datetime(due_at) <= datetime('now')")
    due_count = cursor.fetchone()["count"]
    cursor.execute("SELECT ROUND(AVG(mastery_score), 1) AS mastery FROM cards")
    mastery = cursor.fetchone()["mastery"] or 0

    connection.close()
    return {
        "deck_count": deck_count,
        "card_count": card_count,
        "due_count": due_count,
        "mastery": mastery,
    }


def delete_deck(config, deck_id: int) -> None:
    connection = get_connection(config["DATABASE_PATH"])
    cursor = connection.cursor()
    cursor.execute("DELETE FROM cards WHERE deck_id = ?", (deck_id,))
    cursor.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
    connection.commit()
    connection.close()
