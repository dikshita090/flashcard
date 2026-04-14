import re
from collections import Counter

from models.flashcard import Flashcard
from services.ai_client import generate_cards_with_llm


def build_flashcards(base_dir, text: str, title: str, provider: str) -> list[Flashcard]:
    ai_cards = generate_cards_with_llm(base_dir, text, title, provider)
    if ai_cards:
        return [
            Flashcard(
                question=card["question"].strip(),
                answer=card["answer"].strip(),
                explanation=card.get("explanation", "").strip(),
                card_type=card.get("card_type", "concept").strip(),
                difficulty_hint=card.get("difficulty_hint", "medium").strip(),
                source_excerpt=card.get("source_excerpt", "").strip(),
                tags=", ".join(card.get("tags", [])),
            )
            for card in ai_cards
        ]
    return build_offline_flashcards(text, title)


def build_offline_flashcards(text: str, title: str) -> list[Flashcard]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.split()) > 12]
    sentences = []
    for paragraph in paragraphs:
        parts = re.split(r"(?<=[.!?])\s+", paragraph)
        sentences.extend([part.strip() for part in parts if len(part.split()) > 7])

    keywords = extract_keywords(text, limit=12)
    cards: list[Flashcard] = []

    for keyword in keywords[:6]:
        supporting = next((s for s in sentences if keyword.lower() in s.lower()), "")
        if supporting:
            cards.append(
                Flashcard(
                    question=f"What is the significance of {keyword} in {title}?",
                    answer=supporting,
                    explanation="Review the surrounding context and connect it to the main topic.",
                    card_type="concept",
                    difficulty_hint="medium",
                    source_excerpt=supporting[:220],
                    tags=keyword,
                )
            )

    for sentence in sentences[:12]:
        cards.append(
            Flashcard(
                question=build_question_from_sentence(sentence),
                answer=sentence,
                explanation="Use this card for active recall of a key statement from the source.",
                card_type=guess_card_type(sentence),
                difficulty_hint="medium",
                source_excerpt=sentence[:220],
                tags=", ".join(keywords[:3]),
            )
        )
        if len(cards) >= 18:
            break

    unique_cards = []
    seen_questions = set()
    for card in cards:
        if card.question not in seen_questions:
            seen_questions.add(card.question)
            unique_cards.append(card)
    if unique_cards:
        return unique_cards[:18]

    fallback_answer = text.strip().replace("\n", " ")[:280] or "Add an API key to enable stronger card generation."
    return [
        Flashcard(
            question=f"What is the central idea of {title}?",
            answer=fallback_answer,
            explanation="This fallback card is shown because the PDF had very little extractable text.",
            card_type="concept",
            difficulty_hint="medium",
            source_excerpt=fallback_answer,
            tags=title,
        )
    ]


def extract_keywords(text: str, limit: int = 10) -> list[str]:
    words = re.findall(r"\b[A-Za-z][A-Za-z\-]{3,}\b", text)
    stopwords = {
        "that", "with", "from", "this", "were", "have", "their", "there", "which",
        "about", "into", "than", "them", "they", "when", "what", "where", "while",
        "your", "will", "such", "also", "these", "those", "because", "being",
    }
    counter = Counter(word for word in words if word.lower() not in stopwords)
    return [word for word, _ in counter.most_common(limit)]


def build_question_from_sentence(sentence: str) -> str:
    cleaned = sentence.strip().rstrip(".")
    if cleaned.lower().startswith(("if ", "when ", "why ", "how ")):
        return cleaned + "?"
    if " is " in cleaned:
        subject = cleaned.split(" is ", 1)[0]
        return f"What is true about {subject.strip()}?"
    if " are " in cleaned:
        subject = cleaned.split(" are ", 1)[0]
        return f"What should you remember about {subject.strip()}?"
    return f"What key idea is described by this statement: '{cleaned[:70]}'?"


def guess_card_type(sentence: str) -> str:
    lowered = sentence.lower()
    if any(token in lowered for token in ["defined", "means", "refers to", "is called"]):
        return "definition"
    if any(token in lowered for token in ["for example", "for instance", "consider"]):
        return "example"
    if any(token in lowered for token in ["unless", "except", "however", "edge"]):
        return "edge_case"
    if any(token in lowered for token in ["because", "therefore", "leads to", "causes"]):
        return "relationship"
    return "concept"
