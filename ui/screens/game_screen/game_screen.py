# ui/screens/game_screen/game_screen.py
import pygame
from typing import Optional, Tuple
from core.card import CardType
from core.game_core import Game
from core.config import GameConfig
from ui.widgets.playmat import PlayerPlaymat
from ui.widgets.phase_indicator import PhaseIndicator
from ui.screens.game_screen.game_state import GameState
from ui.screens.game_screen.game_combat import CombatManager
from ui.screens.game_screen.game_ai import AIController
from ui.screens.game_screen.game_events import EventHandler
from ui.screens.game_screen.game_renderer import GameRenderer
from ui.widgets.stats_hud import StatsHUD
from ui.widgets.status_bar import StatusBar


class GameScreen:
    """Pantalla principal del juego (orquestador).

    Flujo de combate
    ────────────────
    Turno del JUGADOR
      declarar → clic en criaturas → SPACE confirma atacantes → IA bloquea auto → daño
      damage   → SPACE resuelve daño y avanza fase

    Turno de la IA
      La IA declara atacantes y queda en step 8 (espera).
      El juego activa la subfase "bloquear": el jugador puede bloquear.
      SPACE confirma bloqueos → subfase "damage".
      SPACE resuelve daño y avanza fase → IA detecta phase != "combate" y continúa.
    """

    def __init__(self, screen, fonts, game: Game):
        self.screen = screen
        self.fonts = fonts
        self.game = game
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        
        self.state = GameState()
        self.last_log_count = 0

        # Ancho del registro de combate (derecha de la pantalla)
        log_width = GameConfig.LOG_WIDTH
        playmat_width = W - log_width - 20
        
        # Altura de cada playmat (45% cada uno, 10% para la barra de fases)
        playmat_height = int((H - 60) * 0.48)
        phase_bar_height = int((H - 60) * 0.04)
        
        # Playmat del oponente (arriba)
        self.opponent_playmat = PlayerPlaymat(10, 10, 
                                            playmat_width, playmat_height, is_player=False)
        
        # Barra de fases (centro)
        phase_bar_y = 10 + playmat_height + 10
        self.phase_indicator = PhaseIndicator(20, phase_bar_y, playmat_width - 20, phase_bar_height)
        
        # Playmat del jugador (abajo)
        player_y = phase_bar_y + phase_bar_height + 10
        self.player_playmat = PlayerPlaymat(10, player_y, 
                                            playmat_width, playmat_height, is_player=True)

        phase_indicator_y = playmat_height + 15
        self.phase_indicator = PhaseIndicator(20, phase_indicator_y, playmat_width - 20, 50)
        self.positions = self._calculate_positions()
        self.buttons = {"phase": pygame.Rect(W - 160, H - 44, 150, 36)}

        self.combat_manager = CombatManager(game, self.state, self.game.add_log)
        self.ai_controller = AIController(
            game, self.combat_manager, self.game.add_log, self.state.rotate_card
        )
        self.event_handler = EventHandler(
            game, self.state, self.combat_manager, self.game.add_log, self.state.set_status
        )
        self.renderer = GameRenderer(screen, fonts)
        self.stats_hud = StatsHUD()
        self.status_bar_widget = StatusBar()

    def _calculate_positions(self) -> dict:
        pc = self.player_playmat.get_creatures_area()
        pl = self.player_playmat.get_lands_area()
        oc = self.opponent_playmat.get_creatures_area()
        ol = self.opponent_playmat.get_lands_area()
        return {
            "player_creatures": (pc.x + 10, pc.y + 45),
            "player_lands":     (pl.x + 10, pl.y + 45),
            "opp_creatures":    (oc.x + 10, oc.y + 45),
            "opp_lands":        (ol.x + 10, ol.y + 45),
        }

    # ------------------------------------------------------------------
    # Consultas de estado
    # ------------------------------------------------------------------

    def is_player_turn(self) -> bool:
        return self.game.active_player == 0

    def is_combat_phase(self) -> bool:
        return self.game.phase == "combate"

    def is_main_phase(self) -> bool:
        return self.game.phase in ("principal1", "principal2")

    def _player_can_act(self) -> bool:
        """True si el jugador puede pulsar SPACE/botón: su turno, o bloqueo durante turno IA."""
        if self.is_player_turn():
            return True
        if self.is_combat_phase() and self.state.combat_subphase in ("bloquear", "damage"):
            return True
        return False

    def _get_current_phase(self) -> str:
        if self.is_combat_phase():
            return {"declarar": "combate", "bloquear": "bloqueo", "damage": "daño"}.get(
                self.state.combat_subphase, "combate"
            )
        return self.game.phase

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def handle_event(self, event) -> Optional[str]:
        self.event_handler.set_card_rects(self.renderer.get_card_rects())
        player_graveyard_rect = self.player_playmat.graveyard_rect
        opponent_graveyard_rect = self.opponent_playmat.graveyard_rect
        self.event_handler.set_graveyard_rects(player_graveyard_rect, opponent_graveyard_rect)
        return self.event_handler.handle_event(
            event,
            self.is_player_turn(),
            self.is_combat_phase(),
            self.is_main_phase(),
            self.buttons["phase"],
            self._advance_player_phase,
            self._player_can_act,
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt_ms: int) -> Tuple:
        self.ai_controller.update(dt_ms, self.is_player_turn())

        # Cuando la IA ha declarado atacantes, activar subfase de bloqueo para el jugador
        if (not self.is_player_turn()
                and self.is_combat_phase()
                and self.game.attackers
                and self.state.combat_subphase == "declarar"):
            self.state.combat_subphase = "bloquear"
            self.state.temp_blockers.clear()
            self.state.selecting_blocker_for = None
            print("🔁 Subfase cambiada a BLOQUEAR (IA ataca)")
            self.state.set_status("⚔️ IA ataca — selecciona bloqueadores y pulsa ESPACIO", ticks=300)

        mouse_y = pygame.mouse.get_pos()[1]
        self.state.update_hand_positions(mouse_y, GameConfig.SCREEN_HEIGHT)
        self.state.sync_rotations_with_tapped()
        self.state.update_status(dt_ms)
        self.status_bar_widget.update(dt_ms)
        self.state.update_rotations()
        self.state.update_animations()
        for p in self.game.players:
            p.update_floating_mana()

        if len(self.game.log_messages) != self.last_log_count:
            self.last_log_count = len(self.game.log_messages)
            if self.state.log_auto_scroll:
                # Actualizar offset a máximo
                visible = (GameConfig.SCREEN_HEIGHT - 20 - 40) // 16  # aproximado, pero podemos recalcular en el renderer
                # Lo más simple: establecer un flag para que el render recalculé el offset.
                self.state.log_scroll_offset = 100000  # Luego se ajustará en render a max

        self.phase_indicator.update(self._get_current_phase(), self.game.active_player)
        self.game.players[0].is_active = self.is_player_turn()
        self.game.players[1].is_active = not self.is_player_turn()

        loser = self.game.check_game_over()
        if loser:
            winner = next(p for p in self.game.players if p is not loser)
            return winner, loser
        return None, None

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self):
        self.renderer.render(
            self.game, self.state,  # <-- state se pasa aquí
            self.player_playmat, self.opponent_playmat,
            self.phase_indicator, self.positions, self.buttons,
            self.is_player_turn(), self.is_combat_phase(),
            self.state.combat_subphase, self.state.pending_attackers,
            self.state.card_rotations,
        )
        self.stats_hud.draw(self.screen, self.fonts, self.game)
        self.status_bar_widget.draw(self.screen, self.fonts)

    # ------------------------------------------------------------------
    # Avance de fase
    # ------------------------------------------------------------------

    def _advance_player_phase(self):
        if self.is_combat_phase():
            sp = self.state.combat_subphase

            # TURNO JUGADOR — declarar atacantes
            if self.is_player_turn() and sp == "declarar":
                if self.state.pending_attackers:
                    for att in self.state.pending_attackers:
                        self.state.rotate_card(att, 90)
                    self.game.declare_attackers(self.state.pending_attackers)
                    self.state.pending_attackers.clear()
                    self.combat_manager.ai_declare_blockers_as_opponent()
                    self.state.combat_subphase = "damage"
                    self.state.set_status("Resolviendo daño...")
                else:
                    # Sin atacantes: saltar directamente al resto del turno
                    self.state.combat_subphase = "declarar"
                    self.game.advance_phase()
                    if not self.is_player_turn():
                        self.ai_controller.reset()
                return

            # TURNO JUGADOR — resolver daño
            if self.is_player_turn() and sp == "damage":
                self.game.deal_combat_damage()
                self.state.combat_subphase = "declarar"
                self.game.advance_phase()
                if not self.is_player_turn():
                    self.ai_controller.reset()
                return

            # TURNO IA — jugador confirma bloqueos
            if not self.is_player_turn() and sp == "bloquear":
                if self.state.temp_blockers:
                    self.game.declare_blockers(self.state.temp_blockers)
                    self.game.add_log(f"🛡️ Jugador bloquea {len(self.state.temp_blockers)} atacante(s)")
                    self.state.temp_blockers.clear()
                    self.state.selecting_blocker_for = None
                self.state.combat_subphase = "damage"
                self.state.set_status("Resolviendo daño... pulsa ESPACIO")
                return

            # TURNO IA — resolver daño
            if not self.is_player_turn() and sp == "damage":
                self.game.deal_combat_damage()
                self.state.combat_subphase = "declarar"
                self.game.advance_phase()  # La IA detectará phase != "combate" en step 8
                return

        # Fuera de combate
        self.game.advance_phase()
        self.state.selected_card = None
        if not self.is_player_turn():
            self.ai_controller.reset()

    # ------------------------------------------------------------------
    # Girar tierras
    # ------------------------------------------------------------------

    def _tap_all_lands(self):
        player = self.game.players[0]
        tapped = sum(
            1 for land in player.battlefield
            if not land.tapped and land.card_type == CardType.LAND
            and player.tap_land_for_mana(land)
            and self.state.rotate_card(land, 90) is None
        )
        if tapped:
            self.game.add_log(f"Giraste {tapped} tierra(s)")
        else:
            self.state.set_status("No hay tierras disponibles")
