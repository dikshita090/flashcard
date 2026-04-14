from services.deck_service import get_stats, list_decks


def build_dashboard_context(config):
    return {
        "stats": get_stats(config),
        "recent_decks": list_decks(config)[:5],
    }
