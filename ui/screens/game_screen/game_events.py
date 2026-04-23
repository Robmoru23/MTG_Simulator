# ui/screens/game_screen/game_events.py
import pygame
from typing import Optional, List, Callable
from core.card import Card, CardType, land_mana_color
from core.game_core import Game
from core.config import GameConfig


class EventHandler:
    """Maneja los eventos de entrada del usuario."""

    def __init__(self, game: Game, state, combat_manager, on_log, on_set_status):
        self.game = game
        self.state = state
        self.combat_manager = combat_manager
        self.on_log = on_log
        self.on_set_status = on_set_status
        self.card_rects = []

    def set_card_rects(self, rects):
        self.card_rects = rects

    def handle_event(self, event, is_player_turn: bool, is_combat_phase: bool,
                     is_main_phase: bool, btn_phase, advance_phase_func: Callable,
                     player_can_act: Callable) -> Optional[str]:

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up
                if self.state.hovering_graveyard:
                    self.state.graveyard_scroll_index += 1
                    self._update_graveyard_display()

            elif event.button == 5:  # Scroll down
                if self.state.hovering_graveyard:
                    self.state.graveyard_scroll_index -= 1
                    self._update_graveyard_display()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4 or event.button == 5:  # Scroll arriba/abajo
                # Obtener el rectángulo del log desde el renderer (necesitamos una referencia)
                # Podemos almacenar una referencia al renderer en el event handler,
                # o calcular aquí el rectángulo igual que en el renderer.
                # Por simplicidad, calculamos el rectángulo del log aquí también.
                W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
                log_w = GameConfig.LOG_WIDTH
                log_x = W - log_w - 5
                log_y = 10
                log_h = H - 20
                log_rect = pygame.Rect(log_x, log_y, log_w, log_h)

                if log_rect.collidepoint(event.pos):
                    total_lines = len(self.game.log_messages)
                    line_height = 16
                    visible_lines = (log_h - 40) // line_height
                    max_offset = max(0, total_lines - visible_lines)
                    # Si el scroll está en el final, activar auto-scroll; si no, desactivar.
                    if self.state.log_scroll_offset >= max_offset - 1:
                        self.state.log_auto_scroll = True
                    else:
                        self.state.log_auto_scroll = False
                    if event.button == 4:
                        self.state.log_scroll_offset -= 3
                    else:
                        self.state.log_scroll_offset += 3
                    self.state.log_scroll_offset = max(0, min(self.state.log_scroll_offset, max_offset))

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "menu"
            # SPACE activo si es el turno del jugador O está bloqueando durante turno IA
            if event.key == pygame.K_SPACE and player_can_act():
                advance_phase_func()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            return self._handle_click(mx, my, is_player_turn, is_combat_phase,
                                      is_main_phase, btn_phase, advance_phase_func,
                                      player_can_act)

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
            self._update_graveyard_hover(event.pos)  # Añadir esta línea
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4 or event.button == 5:  # Scroll
                self._handle_graveyard_scroll(event.button)

        return None

    def _handle_click(self, mx, my, is_player_turn, is_combat_phase, is_main_phase,
                      btn_phase, advance_phase_func, player_can_act) -> Optional[str]:
        if btn_phase.collidepoint(mx, my) and player_can_act():
            advance_phase_func()
            return None
        for card, rect, zone in reversed(self.card_rects):
            if rect.collidepoint(mx, my):
                self._handle_card_click(card, zone, is_player_turn, is_main_phase, is_combat_phase)
                return None
        self.state.selected_card = None
        return None

    def _handle_card_click(self, card: Card, zone: str,
                           is_player_turn: bool, is_main_phase: bool, is_combat_phase: bool):
        if zone in ("opp_hand", "land_opp"):
            self.on_set_status("No puedes interactuar con las cartas del oponente")
            return

        # ── MODO BLOQUEO (válido en ambos turnos si hay atacantes) ────
        if is_combat_phase and self.state.combat_subphase == "bloquear" and self.game.attackers:
            self._handle_block_click(card, zone)
            return

        if not is_player_turn:
            return

        # ── MANO ─────────────────────────────────────────────────────
        if zone == "hand" and is_main_phase:
            self._play_from_hand(card)

        # ── TIERRA EN CAMPO ──────────────────────────────────────────
        elif zone == "land_player" and (is_main_phase or is_combat_phase):
            player = self.game.players[0]
            if not card.tapped:
                if player.tap_land_for_mana(card):
                    self.state.rotate_card(card, 90)
                    self.on_log(f"🌍 Giras {card.name} (+{land_mana_color(card.name)})")
            else:
                self.on_set_status(f"{card.name} ya está girada")

        # ── CRIATURA EN CAMPO: activar habilidad O declarar ataque ───
        elif zone == "creature_player":
            player = self.game.players[0]
            if is_combat_phase and self.state.combat_subphase == "declarar":
                self._toggle_attacker(card)
            elif is_main_phase and not card.tapped:
                # Intentar activar habilidad de maná (ej. Llanowar Elves)
                if player.activate_creature_ability(card):
                    self.state.rotate_card(card, 90)
                    self.on_log(f"🔧 {card.name}: +1 maná verde")

    def _handle_block_click(self, card: Card, zone: str):
        if zone == "creature_opp":
            attacker = next((a for a in self.game.attackers if a is card), None)
            if attacker is None:
                self.on_set_status(f"{card.name} no está atacando")
                return
            if attacker in self.state.temp_blockers:
                self.on_set_status(f"{card.name} ya está bloqueado")
            else:
                self.state.selecting_blocker_for = attacker
                self.on_set_status(f"Selecciona criatura para bloquear a {card.name}")
        elif zone == "creature_player":
            if self.state.selecting_blocker_for is None:
                self.on_set_status("Primero selecciona un atacante (criatura del oponente)")
                return
            if not card.can_block():
                reason = "está girada" if card.tapped else "tiene fiebre de ataque"
                self.on_set_status(f"{card.name} no puede bloquear ({reason})")
                return
            if card in self.state.temp_blockers.values():
                self.on_set_status(f"{card.name} ya está bloqueando")
                return
            self.state.temp_blockers[self.state.selecting_blocker_for] = card
            self.on_set_status(f"{card.name} bloquea a {self.state.selecting_blocker_for.name}")
            self.state.selecting_blocker_for = None
        else:
            # Clic fuera de criatura: cancelar selección
            if self.state.selecting_blocker_for is not None:
                self.state.selecting_blocker_for = None
                self.on_set_status("Selección cancelada")

    def _play_from_hand(self, card: Card):
        player = self.game.players[0]
        if card.card_type == CardType.LAND:
            if player.play_land(card):
                self.on_log(f"🌍 Juegas {card.name}")
            else:
                self.on_set_status("Ya jugaste una tierra este turno")
        elif card.card_type == CardType.CREATURE:
            if self.game.cast_spell(card, []):
                self.on_log(f"🃏 Juegas {card.name}")
            else:
                self.on_set_status(f"No puedes jugar {card.name} (¿maná insuficiente?)")
        elif card.card_type in (CardType.SORCERY, CardType.INSTANT):
            targets = self._pick_spell_targets(card)
            if self.game.cast_spell(card, targets):
                self.on_log(f"✨ Lanzas {card.name}")
            else:
                self.on_set_status(f"No puedes lanzar {card.name}")

    def _toggle_attacker(self, card: Card):
        if card.can_attack():
            if card in self.state.pending_attackers:
                self.state.pending_attackers.remove(card)
                self.on_set_status(f"{card.name} ya no atacará")
            else:
                self.state.pending_attackers.append(card)
                self.on_set_status(f"{card.name} atacará")
        else:
            reason = "tiene fiebre de ataque" if card.summoning_sickness else "está girada"
            self.on_set_status(f"{card.name} no puede atacar ({reason})")

    def _pick_spell_targets(self, card: Card) -> List:
        text = card.text.lower()
        if "daño" in text:
            return [self.game.opponent()]
        if "ganas" in text and "vida" in text:
            return [self.game.current_player()]
        return []

    def _update_hover(self, pos):
        self.state.hovered_card = None
        self.state.hovered_zone = None
        mouse_x, mouse_y = pos
        screen_h = GameConfig.SCREEN_HEIGHT
        
        # Detectar hover en cementerio (zona derecha del playmat)
        # Las coordenadas aproximadas del cementerio están en playmat.py
        # Asumimos que el cementerio está en la zona derecha, alrededor de x > ancho-120
        
        # Resetear estado de cementerio
        self.state.hovering_graveyard = False
        
        # Verificar si el ratón está sobre el área del cementerio del jugador
        # (esto es aproximado, puedes ajustar las coordenadas)
        if mouse_x > GameConfig.SCREEN_WIDTH - 130 and mouse_y > GameConfig.SCREEN_HEIGHT - 250:
            self.state.hovering_graveyard = True
            # Actualizar la carta mostrada según el índice
            player = self.game.players[0]
            if player.graveyard:
                idx = self.state.graveyard_scroll_index
                if idx < 0:
                    idx = 0
                if idx >= len(player.graveyard):
                    idx = len(player.graveyard) - 1
                self.state.selected_graveyard_card = player.graveyard[idx]
        
        # Verificar cartas normales
        for card, rect, zone in self.card_rects:
            if rect.collidepoint(pos) and zone != "opp_hand":
                self.state.hovered_card = card
                self.state.hovered_zone = zone
                break

    def _update_graveyard_display(self):
        """Actualiza la carta mostrada del cementerio según el índice"""
        player = self.game.players[0]
        if player.graveyard:
            # Limitar índice
            max_idx = len(player.graveyard) - 1
            self.state.graveyard_scroll_index = max(0, min(self.state.graveyard_scroll_index, max_idx))
            self.state.selected_graveyard_card = player.graveyard[self.state.graveyard_scroll_index]
    
    def _update_graveyard_hover(self, pos):
        """Detecta si el ratón está sobre el área del cementerio"""
        mouse_x, mouse_y = pos
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        
        # Área del cementerio del jugador (esquina inferior derecha)
        graveyard_rect = pygame.Rect(W - 120, H - 250, 100, 120)
        
        if graveyard_rect.collidepoint(mouse_x, mouse_y):
            self.state.hovering_graveyard = True
            player = self.game.players[0]
            if player.graveyard:
                max_idx = len(player.graveyard) - 1
                self.state.graveyard_scroll_index = max(0, min(self.state.graveyard_scroll_index, max_idx))
                self.state.graveyard_display_card = player.graveyard[self.state.graveyard_scroll_index]
            else:
                self.state.graveyard_display_card = None
        else:
            self.state.hovering_graveyard = False
            self.state.graveyard_display_card = None

    def _handle_graveyard_scroll(self, button):
        """Maneja el scroll en el cementerio"""
        if not self.state.hovering_graveyard:
            return
        
        player = self.game.players[0]
        if not player.graveyard:
            return
        
        if button == 4:  # Scroll up (anterior)
            self.state.graveyard_scroll_index += 1
        elif button == 5:  # Scroll down (siguiente)
            self.state.graveyard_scroll_index -= 1
        
        # Limitar índice
        max_idx = len(player.graveyard) - 1
        self.state.graveyard_scroll_index = max(0, min(self.state.graveyard_scroll_index, max_idx))
        self.state.graveyard_display_card = player.graveyard[self.state.graveyard_scroll_index]