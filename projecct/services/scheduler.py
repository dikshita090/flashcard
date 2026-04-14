from datetime import datetime, timedelta


def apply_sm2(card: dict, quality: int) -> dict:
    quality = max(0, min(5, quality))
    repetitions = int(card["repetitions"])
    ease_factor = float(card["ease_factor"])
    interval_days = int(card["interval_days"])

    if quality < 3:
        repetitions = 0
        interval_days = 1
    else:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 3
        else:
            interval_days = round(interval_days * ease_factor)
        repetitions += 1

    ease_factor = max(
        1.3,
        ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )

    due_at = datetime.now() + timedelta(days=interval_days)
    success = quality >= 3
    review_count = int(card["review_count"]) + 1
    correct_count = int(card["correct_count"]) + (1 if success else 0)
    incorrect_count = int(card["incorrect_count"]) + (0 if success else 1)
    mastery_score = round((correct_count / review_count) * 100, 1) if review_count else 0

    return {
        "repetitions": repetitions,
        "ease_factor": ease_factor,
        "interval_days": interval_days,
        "due_at": due_at.isoformat(timespec="seconds"),
        "last_reviewed_at": datetime.now().isoformat(timespec="seconds"),
        "review_count": review_count,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "mastery_score": mastery_score,
    }
