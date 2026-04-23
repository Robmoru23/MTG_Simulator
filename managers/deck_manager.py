# managers/deck_manager.py
import json
import os
import logging
from copy import copy
from typing import List, Dict, Optional
from core.card import Card, ALL_CARDS, CARDS_BY_NAME

logger = logging.getLogger(__name__)


class Deck:
    """Representa un mazo de cartas."""

    def __init__(self, name: str, cards: List[Card]):
        self.name = name
        self.cards = cards

    def get_card_names(self) -> List[str]:
        return [card.name for card in self.cards]

    def get_card_count(self) -> int:
        return len(self.cards)

    def get_card_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for card in self.cards:
            counts[card.name] = counts.get(card.name, 0) + 1
        return counts


class DeckManager:
    """Gestiona la creación, carga y guardado de mazos."""

    DECKS_DIR = "decks"

    def __init__(self):
        os.makedirs(self.DECKS_DIR, exist_ok=True)

    def save_deck(self, deck: Deck) -> bool:
        deck_data = {"name": deck.name, "cards": deck.get_card_names()}
        try:
            with open(self._get_filename(deck.name), "w", encoding="utf-8") as f:
                json.dump(deck_data, f, indent=2, ensure_ascii=False)
            return True
        except OSError as e:
            logger.error("Error guardando mazo '%s': %s", deck.name, e)
            return False

    def load_deck(self, name: str) -> Optional[Deck]:
        filename = self._get_filename(name)
        if not os.path.exists(filename):
            return None
        try:
            with open(filename, "r", encoding="utf-8") as f:
                deck_data = json.load(f)

            cards = []
            for card_name in deck_data["cards"]:
                if card_name in CARDS_BY_NAME:
                    cards.append(copy(CARDS_BY_NAME[card_name]))
                else:
                    logger.warning("Carta '%s' no encontrada en la base de datos", card_name)

            return Deck(deck_data["name"], cards)
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.error("Error cargando mazo '%s': %s", name, e)
            return None

    def list_decks(self) -> List[str]:
        if not os.path.exists(self.DECKS_DIR):
            return []
        return sorted(
            f[:-5] for f in os.listdir(self.DECKS_DIR) if f.endswith(".json")
        )

    def delete_deck(self, name: str) -> bool:
        filename = self._get_filename(name)
        if os.path.exists(filename):
            os.remove(filename)
            return True
        return False

    def _get_filename(self, name: str) -> str:
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-")
        return os.path.join(self.DECKS_DIR, f"{safe_name}.json")
