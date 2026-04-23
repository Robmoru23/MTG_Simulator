# ui/screens/game_screen/game_combat.py
from typing import Dict
from core.card import Card, CardType
from core.game_core import Game


class CombatManager:
    """Lógica auxiliar de combate: bloqueo automático de la IA."""

    def __init__(self, game: Game, state, on_log):
        self.game = game
        self.state = state
        self.on_log = on_log

    def _build_blockers_map(self, defender_index: int) -> Dict[Card, Card]:
        """Asigna un bloqueador por atacante (greedy) para el jugador `defender_index`."""
        available = [
            c for c in self.game.players[defender_index].battlefield
            if c.card_type == CardType.CREATURE and c.can_block()
        ]
        result: Dict[Card, Card] = {}
        used: set = set()
        for att in self.game.attackers:
            for blk in available:
                if blk not in used:
                    result[att] = blk
                    used.add(blk)
                    break
        return result

    def ai_declare_blockers_as_opponent(self):
        """IA (jugador 1) bloquea los atacantes del jugador humano."""
        if not self.game.attackers:
            return
        bmap = self._build_blockers_map(1)
        if bmap:
            self.game.declare_blockers(bmap)
            self.on_log(f"🛡️ IA bloquea {len(bmap)} atacante(s)")

    def player_declare_blockers_auto(self):
        """Bloqueo automático greedy para el jugador humano (jugador 0)."""
        if not self.game.attackers:
            return
        bmap = self._build_blockers_map(0)
        if bmap:
            self.game.declare_blockers(bmap)
            self.on_log(f"🛡️ Jugador bloquea {len(bmap)} atacante(s) (auto)")
