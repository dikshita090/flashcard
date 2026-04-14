from services.deck_service import get_due_cards
from services.scheduler import apply_sm2
from services.storage import get_connection


def build_review_context(config, deck_id: int | None):
    card = get_due_cards(config, deck_id)
    if not card:
        return {"card": None, "deck_id": deck_id}
    return {"card": card, "deck_id": deck_id}


def submit_review_result(config, card_id: int, rating: int) -> None:
    connection = get_connection(config["DATABASE_PATH"])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
    card = cursor.fetchone()
    if not card:
        connection.close()
        return

    update = apply_sm2(card, rating)
    cursor.execute(
        """
        UPDATE cards
        SET repetitions = ?, ease_factor = ?, interval_days = ?, due_at = ?,
            last_reviewed_at = ?, review_count = ?, correct_count = ?,
            incorrect_count = ?, mastery_score = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            update["repetitions"],
            update["ease_factor"],
            update["interval_days"],
            update["due_at"],
            update["last_reviewed_at"],
            update["review_count"],
            update["correct_count"],
            update["incorrect_count"],
            update["mastery_score"],
            update["last_reviewed_at"],
            card_id,
        ),
    )
    connection.commit()
    connection.close()
