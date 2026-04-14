from dataclasses import dataclass


@dataclass
class Flashcard:
    question: str
    answer: str
    explanation: str
    card_type: str
    difficulty_hint: str
    source_excerpt: str
    tags: str
