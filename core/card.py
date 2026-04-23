# core/card.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class Color(Enum):
    WHITE = "W"
    BLUE = "U"
    BLACK = "B"
    RED = "R"
    GREEN = "G"
    COLORLESS = "C"


class CardType(Enum):
    CREATURE = "Criatura"
    SORCERY = "Conjuro"
    INSTANT = "Instantáneo"
    LAND = "Tierra"
    ENCHANTMENT = "Encantamiento"
    ARTIFACT = "Artefacto"
    PLANESWALKER = "Planeswalker"


# Mapa centralizado: palabra clave en nombre de tierra -> color de maná
LAND_MANA_MAP: dict = {
    "mountain": "R", "montaña": "R",
    "plains":   "W", "llanura": "W",
    "forest":   "G", "bosque":  "G",
    "island":   "U", "isla":    "U",
    "swamp":    "B", "pantano": "B",
}


def land_mana_color(land_name: str) -> str:
    """Devuelve el color de maná que produce una tierra básica, o 'C'."""
    name_lower = land_name.lower()
    for keyword, color in LAND_MANA_MAP.items():
        if keyword in name_lower:
            return color
    return "C"


@dataclass
class Card:
    name: str
    mana_cost: str
    colors: List[Color]
    card_type: CardType
    text: str
    image_path: Optional[str] = None
    power: Optional[int] = None
    toughness: Optional[int] = None

    # Estado de juego (mutable por instancia)
    tapped: bool = False
    summoning_sickness: bool = True
    damage: int = 0

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def can_attack(self) -> bool:
        """Verifica si la criatura puede atacar (considerando prisa)"""
        if self.tapped:
            return False
        if self.summoning_sickness:
            # Verificar si tiene prisa
            if "prisa" in self.text.lower() or "haste" in self.text.lower():
                return True
            return False
        return True

    def can_block(self) -> bool:
        return not self.tapped


# ============================================================
# PLANTILLAS  (usar siempre copy.copy() antes de añadir al mazo)
# ============================================================

Plains = Card(name="Plains", mana_cost="", colors=[Color.COLORLESS],
              card_type=CardType.LAND, text="",
              image_path="assets/cards_imgs/364_Plains.png")

Island = Card(name="Island", mana_cost="", colors=[Color.COLORLESS],
              card_type=CardType.LAND, text="",
              image_path="assets/cards_imgs/368_Island.png")

Swamp = Card(name="Swamp", mana_cost="", colors=[Color.COLORLESS],
             card_type=CardType.LAND, text="",
             image_path="assets/cards_imgs/372_Swamp.png")

Mountain = Card(name="Mountain", mana_cost="", colors=[Color.COLORLESS],
                card_type=CardType.LAND, text="",
                image_path="assets/cards_imgs/376_Mountain.png")

Forest = Card(name="Forest", mana_cost="", colors=[Color.COLORLESS],
              card_type=CardType.LAND, text="",
              image_path="assets/cards_imgs/380_Forest.png")

Suntail_Hawk = Card(
    name="Suntail Hawk", 
    mana_cost="{W}", 
    colors=[Color.WHITE],
    card_type=CardType.CREATURE, 
    text="Vuela. (Esta criatura solo puede ser bloqueada por criaturas con Vuela o Alcance.)",
    image_path="assets/cards_imgs/50_Suntail_Hawk.png",
    power=1, 
    toughness=1
)

Cloud_Sprite = Card(
    name="Cloud Sprite", 
    mana_cost="{U}", 
    colors=[Color.BLUE],
    card_type=CardType.CREATURE, 
    text="Vuela. (Esta criatura solo puede ser bloqueada por criaturas con Vuela o Alcance.)\nCloud Sprite solo puede bloquear a criaturas con Vuela.",
    image_path="assets/cards_imgs/75_Cloud_Sprite.png",
    power=1, 
    toughness=1
)

Festering_Goblin = Card(
    name="Festering Goblin", 
    mana_cost="{B}", 
    colors=[Color.BLACK],
    card_type=CardType.CREATURE, 
    text="Cuando Festering Goblin vaya al cementerio desde el campo de batalla, la criatura objetivo obtiene -1/-1 hasta el final del turno.",
    image_path="assets/cards_imgs/143_Festering_Goblin.png",
    power=1, 
    toughness=1
)

Spark_Elemental = Card(
    name="Spark Elemental", 
    mana_cost="{R}", 
    colors=[Color.RED],
    card_type=CardType.CREATURE, 
    text="Arrolla, Prisa. (Puede atacar y girar en el turno en que entra al campo de batalla.)\nAl final del turno, sacrifica Spark Elemental.",
    image_path="assets/cards_imgs/237_Spark_Elemental.png",
    power=3, 
    toughness=1
)

Llanowar_Elves = Card(
    name="Llanowar Elves", 
    mana_cost="{G}", 
    colors=[Color.GREEN],
    card_type=CardType.CREATURE, 
    text="{T}: Agrega {G} a tu reserva de maná.",
    image_path="assets/cards_imgs/274_Llanowar_Elves.png",
    power=1, 
    toughness=1
)

ALL_CARDS = [
    Plains, Island, Swamp, Mountain, Forest,
    Suntail_Hawk, Cloud_Sprite, Festering_Goblin, Spark_Elemental, Llanowar_Elves,
]

CARDS_BY_NAME = {card.name: card for card in ALL_CARDS}
