from services.deck_service import find_deck, get_deck_cards, list_decks


def build_deck_list_context(config, query: str):
    return {"decks": list_decks(config, query), "query": query}


def build_deck_detail_context(config, deck_id: int):
    deck = find_deck(config, deck_id)
    cards = get_deck_cards(config, deck_id)
    due_cards = [card for card in cards if card["interval_days"] <= 0 or card["mastery_score"] < 70]
    return {
        "deck": deck,
        "cards": cards,
        "summary": {
            "card_count": len(cards),
            "due_count": len(due_cards),
            "mastered_count": len([card for card in cards if card["mastery_score"] >= 80]),
        },
    }
