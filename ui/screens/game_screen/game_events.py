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

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if hasattr(self.game, 'pending_target_selection'):
                    del self.game.pending_target_selection
                    self.on_set_status("Selección de objetivo cancelada")
                    return "menu"
                return "menu"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            return self._handle_click(mx, my, is_player_turn, is_combat_phase,
                                      is_main_phase, btn_phase, advance_phase_func,
                                      player_can_act)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Clic derecho
            if self.state.selecting_blocker_for is not None:
                self.state.selecting_blocker_for = None
                self.on_set_status("Selección de bloqueador cancelada")
            return

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
        
        print(f"📌 CLICK en {card.name} | Zona: {zone} | Subfase: {self.state.combat_subphase}")
        if zone in ("opp_hand", "land_opp"):
            self.on_set_status("No puedes interactuar con las cartas del oponente")
            return

         # ── SELECCIÓN DE OBJETIVO PARA HABILIDAD ───────────────────────
        if hasattr(self.game, 'pending_target_selection') and self.game.pending_target_selection:
            if zone in ("creature_player", "creature_opp"):
                if card in self.game.pending_target_selection["targets"]:
                    callback = self.game.pending_target_selection["callback"]
                    callback(card)
                    self.on_log(f"🎯 Objetivo seleccionado: {card.name}")
                    return
                else:
                    self.on_set_status("❌ Esa criatura no es un objetivo válido")
                    return
            else:
                self.on_set_status("⚠️ Debes seleccionar una criatura como objetivo")
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
        print(f"🔍 _handle_block_click: zone={zone}, card={card.name}, selecting_for={self.state.selecting_blocker_for}")
        
        if zone == "creature_opp":
            # Buscar el PRIMER atacante con este nombre que NO tenga bloqueador
            attacker = None
            for a in self.game.attackers:
                if a.name == card.name and a not in self.state.temp_blockers:
                    attacker = a
                    break
            
            if attacker is None:
                # Verificar si todos los atacantes con este nombre ya están bloqueados
                all_blocked = all(a in self.state.temp_blockers for a in self.game.attackers if a.name == card.name)
                if all_blocked:
                    self.on_set_status(f"Todos los {card.name} ya están bloqueados")
                else:
                    self.on_set_status(f"{card.name} no está atacando")
                return
            
            self.state.selecting_blocker_for = attacker
            self.on_set_status(f"Selecciona una criatura para bloquear a {card.name}")
            print(f"✅ Atacante seleccionado: {attacker.name} (id={id(attacker)})")
        
        elif zone == "creature_player":
            if self.state.selecting_blocker_for is None:
                self.on_set_status("Primero selecciona un atacante (criatura del oponente)")
                return
            
            if not card.can_block():
                reason = "está girada" if card.tapped else "tiene mareo de invocación"
                self.on_set_status(f"{card.name} no puede bloquear ({reason})")
                return
            
            # Verificar si esta criatura ya está bloqueando a otro atacante
            if card in self.state.temp_blockers.values():
                self.on_set_status(f"{card.name} ya está bloqueando a otra criatura")
                return
            
            # Verificar que el atacante no tenga ya un bloqueador
            attacker = self.state.selecting_blocker_for
            if attacker in self.state.temp_blockers:
                self.on_set_status(f"{attacker.name} ya tiene bloqueador")
                self.state.selecting_blocker_for = None
                return
            
            # ASIGNAR BLOQUEO
            self.state.temp_blockers[attacker] = card
            print(f"✅ BLOQUEO ASIGNADO: {card.name} bloquea a {attacker.name} (id={id(attacker)})")
            print(f"📦 temp_blockers ahora: {[(a.name, b.name) for a, b in self.state.temp_blockers.items()]}")
            self.on_set_status(f"{card.name} bloquea a {attacker.name}")
            
            # Limpiar selección para poder elegir otro atacante
            self.state.selecting_blocker_for = None
            self.on_set_status(f"Selecciona otro atacante o presiona ESPACIO para continuar")

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
            reason = "tiene mareo de invocación" if card.summoning_sickness else "está girada"
            self.on_set_status(f"{card.name} no puede atacar ({reason})")

    def _pick_spell_targets(self, card: Card) -> List:
        text = card.text.lower()
        
        # Bandage (prevenir daño) - NO es daño
        if "bandage" in card.name.lower():
            # Elegir una criatura del jugador o al propio jugador
            player = self.game.current_player()
            creatures = [c for c in player.battlefield if c.card_type == CardType.CREATURE]
            if creatures:
                return [creatures[0]]
            return [player]
        
        # Peek (robar carta) - no requiere objetivo
        if "peek" in card.name.lower():
            return []
        
        # Terror (destruir criatura enemiga)
        if "terror" in card.name.lower():
            opponent = self.game.opponent()
            creatures = [c for c in opponent.battlefield if c.card_type == CardType.CREATURE]
            if creatures:
                return [creatures[0]]
            return []
        
        # Giant Growth y Fists of the Anvil (buff a criatura)
        if "giant growth" in card.name.lower() or "fists of the anvil" in card.name.lower():
            player = self.game.current_player()
            creatures = [c for c in player.battlefield if c.card_type == CardType.CREATURE]
            if creatures:
                return [creatures[0]]
            return []
        
        # Hechizos de daño
        if "daño" in text and "prevén" not in text:
            return [self.game.opponent()]
        
        # Ganar vida
        if "ganas" in text and "vida" in text:
            return [self.game.current_player()]
        
        return []

    def _update_hover(self, pos):
        # Guardar la carta anterior antes de actualizar
        previous_hovered = self.state.hovered_card
        
        self.state.hovered_card = None
        self.state.hovered_zone = None
        mouse_x, mouse_y = pos
        screen_h = GameConfig.SCREEN_HEIGHT
        
        # Resetear estado de cementerio
        self.state.hovering_graveyard = False
        
        # Verificar si el ratón está sobre el área del cementerio del jugador
        if mouse_x > GameConfig.SCREEN_WIDTH - 130 and mouse_y > GameConfig.SCREEN_HEIGHT - 250:
            self.state.hovering_graveyard = True
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
        
        # Solo imprimir si la carta ha cambiado
        if self.state.hovered_card != previous_hovered:
            if self.state.hovered_card:
                print(f"🖱️ HOVER sobre {self.state.hovered_card.name} (zona {self.state.hovered_zone})")
            else:
                # Opcional: cuando deja de hacer hover
                # print(f"🖱️ HOVER terminado")
                pass

    def _update_graveyard_display(self):
        """Actualiza la carta mostrada del cementerio según el índice"""
        player = self.game.players[0]
        if player.graveyard:
            # Limitar índice
            max_idx = len(player.graveyard) - 1
            self.state.graveyard_scroll_index = max(0, min(self.state.graveyard_scroll_index, max_idx))
            self.state.selected_graveyard_card = player.graveyard[self.state.graveyard_scroll_index]
    
    def _update_graveyard_hover(self, pos):
        """Detecta si el ratón está sobre el área del cementerio (jugador u oponente)"""
        mouse_x, mouse_y = pos
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        
        # Área del cementerio del jugador (esquina inferior derecha del playmat del jugador)
        # Ajusta estas coordenadas según la posición real de tu playmat
        player_graveyard_rect = pygame.Rect(W - 130, H - 250, 100, 120)
        
        # Área del cementerio del oponente (esquina superior derecha del playmat del oponente)
        opponent_graveyard_rect = pygame.Rect(W - 130, 130, 100, 120)
        
        # Resetear estado
        self.state.hovering_graveyard = False
        self.state.hovering_opponent_graveyard = False
        self.state.graveyard_display_card = None
        
        # Verificar cementerio del jugador
        if player_graveyard_rect.collidepoint(mouse_x, mouse_y):
            self.state.hovering_graveyard = True
            player = self.game.players[0]
            if player.graveyard:
                max_idx = len(player.graveyard) - 1
                self.state.graveyard_scroll_index = max(0, min(self.state.graveyard_scroll_index, max_idx))
                self.state.graveyard_display_card = player.graveyard[self.state.graveyard_scroll_index]
            return
        
        # Verificar cementerio del oponente
        if opponent_graveyard_rect.collidepoint(mouse_x, mouse_y):
            self.state.hovering_opponent_graveyard = True
            opponent = self.game.players[1]
            if opponent.graveyard:
                # Usar un índice separado para el oponente (opcional)
                max_idx = len(opponent.graveyard) - 1
                idx = min(self.state.opponent_graveyard_scroll_index, max_idx)
                self.state.graveyard_display_card = opponent.graveyard[idx]
            return

    def _handle_graveyard_scroll(self, button):
        """Maneja el scroll en el cementerio (jugador u oponente)"""
        if self.state.hovering_graveyard:
            player = self.game.players[0]
            if not player.graveyard:
                return
            
            if button == 4:  # Scroll up
                self.state.graveyard_scroll_index += 1
            elif button == 5:  # Scroll down
                self.state.graveyard_scroll_index -= 1
            
            max_idx = len(player.graveyard) - 1
            self.state.graveyard_scroll_index = max(0, min(self.state.graveyard_scroll_index, max_idx))
            self.state.graveyard_display_card = player.graveyard[self.state.graveyard_scroll_index]
        
        elif self.state.hovering_opponent_graveyard:
            opponent = self.game.players[1]
            if not opponent.graveyard:
                return
            
            if button == 4:  # Scroll up
                self.state.opponent_graveyard_scroll_index += 1
            elif button == 5:  # Scroll down
                self.state.opponent_graveyard_scroll_index -= 1
            
            max_idx = len(opponent.graveyard) - 1
            self.state.opponent_graveyard_scroll_index = max(0, min(self.state.opponent_graveyard_scroll_index, max_idx))
            self.state.graveyard_display_card = opponent.graveyard[self.state.opponent_graveyard_scroll_index]

    def set_graveyard_rects(self, player_rect, opponent_rect):
        self.player_graveyard_rect = player_rect
        self.opponent_graveyard_rect = opponent_rect