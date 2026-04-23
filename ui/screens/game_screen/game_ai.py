# ui/screens/game_screen/game_ai.py
import re
from core.card import CardType
from core.game_core import Game


class AIController:
    """Controla el turno de la IA.

    Pasos:
      0  mantenimiento → robo
      1  robo → principal1
      2  jugar tierra
      3  generar maná (tierras + habilidades de criaturas)
      4  lanzar criaturas
      5  lanzar hechizos de daño
      6  avanzar hasta combate
      7  declarar atacantes  (si los hay → step 8; si no → saltar a step 9)
      8  esperar a que el jugador resuelva bloqueo/daño
      9  fin de turno
    """

    AI_THINK_DELAY = 350
    MAX_CREATURES_PER_TURN = 2
    _DAMAGE_RE = re.compile(r'(\d+)\s*puntos?\s*de\s*da[ñn]o|hace\s*(\d+)', re.IGNORECASE)

    def __init__(self, game: Game, combat_manager, on_log, on_rotate_card):
        self.game = game
        self.combat_manager = combat_manager
        self.on_log = on_log
        self.on_rotate_card = on_rotate_card
        self.ai_timer = 0
        self.ai_step = 0
        self.ai_done = False

    def reset(self):
        self.ai_done = False
        self.ai_step = 0
        self.ai_timer = 0

    def update(self, dt_ms: int, is_player_turn: bool):
        if is_player_turn or self.ai_done:
            return
        self.ai_timer += dt_ms
        if self.ai_timer < self.AI_THINK_DELAY:
            return
        self.ai_timer = 0
        handlers = {
            0: self._step_mantenimiento,
            1: self._step_robo,
            2: self._step_jugar_tierra,
            3: self._step_generar_mana,
            4: self._step_lanzar_criaturas,
            5: self._step_lanzar_hechizos,
            6: self._step_avanzar_combate,
            7: self._step_declarar_atacantes,
            8: self._step_esperar_combate,
            9: self._step_fin_turno,
        }
        handler = handlers.get(self.ai_step)
        if handler:
            handler()

    def _next(self, steps=1):
        self.ai_step += steps

    def _step_mantenimiento(self):
        if self.game.phase == "mantenimiento":
            self.game.advance_phase()
        self._next()

    def _step_robo(self):
        if self.game.phase == "robo":
            self.game.advance_phase()
        self._next()

    def _step_jugar_tierra(self):
        ai = self.game.current_player()
        lands = [c for c in ai.hand if c.card_type == CardType.LAND]
        if lands and not ai.land_played_this_turn:
            ai.play_land(lands[0])
            self.on_log(f"IA juega {lands[0].name}")
        self._next()

    def _step_generar_mana(self):
        ai = self.game.current_player()
        for card in ai.battlefield:
            if card.tapped:
                continue
            if card.card_type == CardType.LAND:
                ai.tap_land_for_mana(card)
                self.on_rotate_card(card, 90)
            elif card.card_type == CardType.CREATURE:
                if ai.activate_creature_ability(card):
                    self.on_rotate_card(card, 90)
        self._next()

    def _step_lanzar_criaturas(self):
        ai = self.game.current_player()
        played = 0
        for c in [c for c in ai.hand if c.card_type == CardType.CREATURE]:
            if played >= self.MAX_CREATURES_PER_TURN:
                break
            if ai.can_pay_mana(c.mana_cost):
                ai.pay_mana(c.mana_cost)
                ai.hand.remove(c)
                ai.battlefield.append(c)
                has_haste = "prisa" in c.text.lower() or "haste" in c.text.lower()
                c.summoning_sickness = not has_haste
                self.on_log(f"IA lanza {c.name}")
                played += 1
        self._next()

    def _step_lanzar_hechizos(self):
        ai = self.game.current_player()
        for sp in [c for c in ai.hand if c.card_type in (CardType.INSTANT, CardType.SORCERY)]:
            if not ai.can_pay_mana(sp.mana_cost):
                continue
            m = self._DAMAGE_RE.search(sp.text)
            if m:
                dmg = int(m.group(1) or m.group(2))
                ai.pay_mana(sp.mana_cost)
                ai.hand.remove(sp)
                ai.graveyard.append(sp)
                self.game.players[0].take_damage(dmg)
                self.on_log(f"IA lanza {sp.name} → {dmg} daño al jugador")
        self._next()

    def _step_avanzar_combate(self):
        if self.game.phase != "combate":
            self.game.advance_phase()
        else:
            self._next()

    def _step_declarar_atacantes(self):
        if self.game.phase == "combate":
            ai = self.game.current_player()
            attackers = [
                c for c in ai.battlefield
                if c.card_type == CardType.CREATURE and c.can_attack()
            ]
            if attackers:
                for att in attackers:
                    self.on_rotate_card(att, 90)
                self.game.declare_attackers(attackers)
                self.on_log(f"⚔️ IA ataca con {len(attackers)} criatura(s) ⚔️")
                self._next()           # → step 8: esperar al jugador
            else:
                # Sin atacantes: avanzar la fase directamente y saltar step 8
                self.game.advance_phase()
                self._next(2)          # → step 9
        else:
            self._next()

    def _step_esperar_combate(self):
        """Espera a que el jugador resuelva bloqueo y daño.
        La IA solo avanza cuando el juego ya ha salido de la fase de combate."""
        if self.game.phase != "combate":
            self._next()

    def _step_fin_turno(self):
        while self.game.phase != "mantenimiento" or self.game.active_player != 0:
            self.game.advance_phase()
            if self.game.active_player == 0:
                break
        self.ai_done = True
        self.ai_step = 0
