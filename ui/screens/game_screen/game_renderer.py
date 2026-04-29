# ui/screens/game_screen/game_renderer.py
import pygame
from typing import List, Optional
from core.card import Card, CardType
from core.game_core import Game
from core.config import GameConfig
from ui.draw_utils import draw_card, draw_button, get_card_bg
from ui.widgets.playmat import PlayerPlaymat
from ui.widgets.phase_indicator import PhaseIndicator
from ui.colors import (GOLD, GREEN, WHITE, LIGHT_GRAY, BRIGHT_RED,
                       BRIGHT_BLUE, BLUE, BROWN, RED, ORANGE, BLACK,
                       MTG_GLOW_GOLD, MTG_GLOW_BLUE, MTG_GLOW_RED, MTG_TEXT_DIM,
                       MTG_TEXT_MAIN, MTG_PANEL_BG, MTG_BORDER, MANA_W, MANA_U,
                       MANA_B, MANA_R, MANA_G, MANA_C)
from ui.draw_utils import draw_glow, draw_rounded_rect_gradient, draw_panel
from utils.helpers import wrap_text
from managers.image_manager import ImageManager

# Mapa de color de maná -> RGB  (centralizado, evita recrearlo en cada frame)
_MANA_RGB = {
    "W": (255, 255, 200),
    "U": (100, 150, 255),
    "B": (100, 100, 100),
    "R": (255, 100, 100),
    "G": (100, 255, 100),
    "C": (200, 200, 200),
}


class GameRenderer:
    """Renderiza todos los elementos del juego."""

    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts = fonts
        self.card_rects: list = []
        self._image_manager = ImageManager()

    def get_card_rects(self):
        return self.card_rects

    # ------------------------------------------------------------------
    # Render principal
    # ------------------------------------------------------------------

    def render(self, game: Game, state, playmat_player: PlayerPlaymat,
            playmat_opponent: PlayerPlaymat, phase_indicator: PhaseIndicator,
            positions, buttons, is_player_turn, is_combat_phase,
            combat_subphase, pending_attackers, card_rotations):

        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        CW, CH = GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT
        player = game.players[0]
        opponent = game.players[1]

        self.card_rects.clear()
        # Fondo con degradado premium
        W2, H2 = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        for y in range(0, H2, 4):
            t = y / H2
            r = int(6 + 10 * t)
            g = int(8 + 6 * t)
            b = int(18 + 20 * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (W2, y))
            pygame.draw.line(self.screen, (r, g, b), (0, y+1), (W2, y+1))
            pygame.draw.line(self.screen, (r, g, b), (0, y+2), (W2, y+2))
            pygame.draw.line(self.screen, (r, g, b), (0, y+3), (W2, y+3))

        # Dibujar playmats
        playmat_opponent.draw(self.screen, self.fonts, opponent)
        playmat_player.draw(self.screen, self.fonts, player)
        phase_indicator.draw(self.screen, self.fonts)

        # Cartas del oponente
        self._render_cards(
            opponent, game, game.attackers,
            positions["opp_creatures"], positions["opp_lands"],
            state, card_rotations, is_opponent=True,
        )

        land_rects = self._render_cards(
            player, game, [],
            positions["player_creatures"], positions["player_lands"],
            state, card_rotations, is_opponent=False,
            pending_attackers=pending_attackers, return_land_rects=True,
        )

        self._render_floating_mana(player, land_rects)
        self._render_opponent_hand(opponent, playmat_opponent, state.opponent_hand_offset)
        self._render_player_hand(player, state.selected_card, state.hovered_card, state.player_hand_offset)
        self._render_hand_indicators(len(player.hand), len(opponent.hand), state)
        self._render_buttons(buttons, is_player_turn, is_combat_phase, combat_subphase)
        self._render_log(game.log_messages, state)   # pasar state
        self._render_mana(player, playmat_player)  # Pasar el playmat del jugador
        self._draw_blocking_lines(game, state, positions["player_creatures"], positions["opp_creatures"])

        # Dibujar biblioteca
        player_library_rect = playmat_player.library_rect
        self._render_library_mini(game.players[0], player_library_rect)

        opp_library_rect = playmat_opponent.library_rect
        self._render_library_mini(game.players[1], opp_library_rect)

        # Dibujar miniaturas de cementerio
        player_graveyard_rect = playmat_player.graveyard_rect
        self._render_graveyard_mini(game.players[0], player_graveyard_rect)
        
        opp_graveyard_rect = playmat_opponent.graveyard_rect
        self._render_graveyard_mini(game.players[1], opp_graveyard_rect)

        # Dibujar exilio
        player_exile_rect = playmat_player.exile_rect
        self._render_exile_mini(game.players[0], player_exile_rect)

        opp_exile_rect = playmat_opponent.exile_rect
        self._render_exile_mini(game.players[1], opp_exile_rect)

        # Tooltips
        if state.hovered_card and state.hovered_zone != "opp_hand":
            self._render_tooltip(state.hovered_card)

        if state.hovering_graveyard and state.graveyard_display_card:
            self._render_graveyard_tooltip(state.graveyard_display_card, len(game.players[0].graveyard), state.graveyard_scroll_index)
        
        if state.hovering_graveyard and state.graveyard_display_card:
            self._render_graveyard_tooltip(state.graveyard_display_card, len(game.players[0].graveyard), state.graveyard_scroll_index, "JUGADOR")

        if state.hovering_opponent_graveyard and state.graveyard_display_card:
            self._render_graveyard_tooltip(state.graveyard_display_card, len(game.players[1].graveyard), state.opponent_graveyard_scroll_index, "OPONENTE")

        # Animaciones
        for anim in state.animations:
            pos = anim.get_pos()
            draw_card(self.screen, self.fonts, anim.card, pos[0], pos[1], w=CW, h=CH)

        return self.card_rects

    # ------------------------------------------------------------------
    # Cartas en el campo de batalla
    # ------------------------------------------------------------------

    def _render_cards(self, player, game, attackers, creatures_pos, lands_pos,
                    state, card_rotations, is_opponent=False,
                    pending_attackers=None, return_land_rects=False):
        CW, CH = GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT
        land_rects = []
        
        # Obtener posiciones de todas las criaturas para las líneas de conexión
        creature_positions = {}
        
        # Criaturas
        creatures = [c for c in player.battlefield if c.card_type == CardType.CREATURE]
        for i, card in enumerate(creatures):
            x = creatures_pos[0] + i * (CW + 8)
            y = creatures_pos[1]
            
            is_selected_as_attacker = not is_opponent and pending_attackers and card in pending_attackers
            is_att = card in attackers
            angle = card_rotations.get(card, 0)
            
            rect = draw_card(self.screen, self.fonts, card, x, y,
                            selected=is_selected_as_attacker,
                            hovered=(card == state.hovered_card),
                            tapped=card.tapped, rotation_angle=angle,
                            w=CW, h=CH)
            
            # Guardar posición para líneas de conexión
            creature_positions[card.name] = (x + CW // 2, y + CH // 2)
            
            # Borde rojo para atacantes confirmados
            if is_att:
                pygame.draw.rect(self.screen, BRIGHT_RED, (x - 3, y - 3, CW + 6, CH + 6), 3, border_radius=8)
            
            # Resalte: atacante seleccionado para bloquear (naranja)
            if is_opponent and state.selecting_blocker_for is card:
                pygame.draw.rect(self.screen, ORANGE, (x - 3, y - 3, CW + 6, CH + 6), 3, border_radius=8)
            
            # Resalte: bloqueador asignado temporalmente (dorado)
            if not is_opponent and state.temp_blockers:
                for attacker, blocker in state.temp_blockers.items():
                    if blocker is card:
                        pygame.draw.rect(self.screen, GOLD, (x - 3, y - 3, CW + 6, CH + 6), 3, border_radius=8)
                        break
            
            # Resalte para habilidades con objetivo (Festering Goblin)
            if hasattr(game, 'pending_target_selection') and game.pending_target_selection:
                if card in game.pending_target_selection["targets"]:
                    pygame.draw.rect(self.screen, (255, 0, 255), (x-2, y-2, CW+4, CH+4), 2, border_radius=6)
            
            zone = "creature_opp" if is_opponent else "creature_player"
            self.card_rects.append((card, rect, zone))
        
        # Tierras
        lands = [c for c in player.battlefield if c.card_type == CardType.LAND]
        for i, land in enumerate(lands):
            x = lands_pos[0] + i * (CW + 8)
            y = lands_pos[1]
            angle = card_rotations.get(land, 0)
            rect = draw_card(self.screen, self.fonts, land, x, y,
                            tapped=land.tapped, rotation_angle=angle, w=CW, h=CH)
            zone = "land_opp" if is_opponent else "land_player"
            self.card_rects.append((land, rect, zone))
            land_rects.append(rect)
        
        # Dibujar líneas de conexión entre atacantes y bloqueadores (solo durante fase de bloqueo)
        if state.combat_subphase == "bloquear" and state.temp_blockers and not is_opponent:
            for attacker, blocker in state.temp_blockers.items():
                att_pos = None
                blk_pos = None
                
                # Buscar posición del atacante (en el campo del oponente)
                # Para obtener las posiciones de los atacantes, necesitamos las coordenadas que se pasaron
                # Usamos las posiciones guardadas en creature_positions del oponente
                # Esto se hace en la llamada a _render_cards para el oponente, pero aquí no tenemos acceso a eso.
                # Alternativa: dibujar las líneas en el método render después de ambas llamadas.
                pass
        
        if return_land_rects:
            return land_rects

    def _draw_blocking_lines(self, game, state, player_creatures_pos, opponent_creatures_pos):
        """Dibuja líneas doradas conectando atacantes con sus bloqueadores asignados"""
        CW, CH = GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT
        
        # Diccionario para guardar posiciones por objeto de carta (no por nombre)
        opponent_positions = {}
        player_positions = {}
        
        # Obtener posiciones de las criaturas del oponente (atacantes)
        opponent_creatures = [c for c in game.players[1].battlefield if c.card_type == CardType.CREATURE]
        for i, card in enumerate(opponent_creatures):
            x = opponent_creatures_pos[0] + i * (CW + 8)
            y = opponent_creatures_pos[1]
            opponent_positions[card] = (x + CW // 2, y + CH // 2)
        
        # Obtener posiciones de las criaturas del jugador (bloqueadores)
        player_creatures = [c for c in game.players[0].battlefield if c.card_type == CardType.CREATURE]
        for i, card in enumerate(player_creatures):
            x = player_creatures_pos[0] + i * (CW + 8)
            y = player_creatures_pos[1]
            player_positions[card] = (x + CW // 2, y + CH // 2)
        
        # Dibujar líneas para cada bloqueo temporal
        for attacker, blocker in state.temp_blockers.items():
            # Buscar la posición usando el objeto de carta directamente
            att_pos = opponent_positions.get(attacker)
            blk_pos = player_positions.get(blocker)
            
            if att_pos and blk_pos:
                # Línea con efecto de resplandor (múltiples capas)
                for offset in range(3, 0, -1):
                    alpha = 60 - offset * 15
                    color = (255, 215, 0, alpha)
                    line_width = 3 - offset + 1
                    pygame.draw.line(self.screen, color[:3], att_pos, blk_pos, line_width)
                
                # Línea principal dorada
                pygame.draw.line(self.screen, GOLD, att_pos, blk_pos, 3)
                
                # Círculos en los extremos para mejor visibilidad
                pygame.draw.circle(self.screen, GOLD, att_pos, 6)
                pygame.draw.circle(self.screen, GOLD, blk_pos, 6)

    # ------------------------------------------------------------------
    # Maná flotante
    # ------------------------------------------------------------------

    def _render_floating_mana(self, player, land_rects: list):
        for i, mana in enumerate(player.floating_mana):
            if i >= len(land_rects):
                break
            land_rect = land_rects[i]
            color_key = mana["color"]
            life_ratio = mana["life"] / 60
            y_offset = int((1 - life_ratio) * 40)
            cx = land_rect.centerx
            cy = land_rect.y - 20 - y_offset
            
            icon = self._image_manager.load_mana_icon(color_key)
            if icon:
                scaled = pygame.transform.smoothscale(icon, (24, 24))
                self.screen.blit(scaled, scaled.get_rect(center=(cx, cy)))
            else:
                # Fallback: círculo con color y letra
                color = _MANA_RGB.get(color_key, (200, 200, 200))
                pygame.draw.circle(self.screen, color, (cx, cy), 12)
                sym = self.fonts["small"].render(color_key, True, (255, 255, 255))
                self.screen.blit(sym, sym.get_rect(center=(cx, cy)))

    # ------------------------------------------------------------------
    # Manos
    # ------------------------------------------------------------------

    def _render_opponent_hand(self, opponent, playmat, hand_offset):
        W = GameConfig.SCREEN_WIDTH
        CW, CH = GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT
        hand_width = len(opponent.hand) * (CW + 4)
        hand_x = max(playmat.rect.x + 10,
                     min(W // 2 - hand_width // 2, playmat.rect.right - CW - 10))
        base_y = playmat.rect.y + hand_offset

        for i, card in enumerate(opponent.hand):
            rx = hand_x + i * (CW + 4)
            ry = base_y
            if ry + CH > playmat.rect.y:
                rect = draw_card(self.screen, self.fonts, card, rx, ry, w=CW, h=CH, facedown=True)
                self.card_rects.append((card, rect, "opp_hand"))

    def _render_player_hand(self, player, selected_card, hovered_card, hand_offset):
        W = GameConfig.SCREEN_WIDTH
        CW, CH = GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT
        margin = 8
        total_w = len(player.hand) * (CW + margin)
        hand_x = max(20, min(W // 2 - total_w // 2, W - CW - 20))
        base_y = GameConfig.SCREEN_HEIGHT - CH + hand_offset

        for i, card in enumerate(player.hand):
            rx = hand_x + i * (CW + margin)
            is_highlighted = card is hovered_card or card is selected_card
            extra = -10 if is_highlighted and hand_offset > -50 else 0
            ry = base_y + extra
            if 0 < ry + CH and ry < GameConfig.SCREEN_HEIGHT:
                rect = draw_card(self.screen, self.fonts, card, rx, ry,
                                 selected=(card is selected_card),
                                 hovered=(card is hovered_card), w=CW, h=CH)
                self.card_rects.append((card, rect, "hand"))

    def _render_hand_indicators(self, player_count, opponent_count, state):
        W = GameConfig.SCREEN_WIDTH

        if player_count > 0 and state.player_hand_offset < -20:
            ay = GameConfig.SCREEN_HEIGHT - 30
            pygame.draw.polygon(self.screen, GOLD,
                                [(W // 2 - 15, ay), (W // 2, ay - 12), (W // 2 + 15, ay)])
            self._blit_centered(str(player_count), "small", W // 2, ay - 20)
            self._blit_centered("MANO", "tiny", W // 2, ay - 35)

        if opponent_count > 0 and state.opponent_hand_offset < -20:
            ay = 30
            pygame.draw.polygon(self.screen, GOLD,
                                [(W // 2 - 15, ay), (W // 2, ay + 12), (W // 2 + 15, ay)])
            self._blit_centered(str(opponent_count), "small", W // 2, ay + 20)
            self._blit_centered("MANO", "tiny", W // 2, ay + 35)

    # ------------------------------------------------------------------
    # HUD: maná, botones, log, estado
    # ------------------------------------------------------------------

    def _render_mana(self, player, playmat):
        x = playmat.rect.x + 10
        y = playmat.rect.y + playmat.rect.height - 50

        available = [(color, amount) for color, amount in player.mana_pool.items() if amount > 0]
        if available:
            # Posiciones en pentágono (solo para visualización, pero si hay muchos se pueden alinear)
            # Para simplicidad, los mostramos en línea horizontal por ahora.
            # Si quieres pentágono estricto, habría que calcular posiciones.
            x_offset = 0
            for color, amount in available:
                icon = self._image_manager.load_mana_icon(color)
                if icon:
                    scaled = pygame.transform.smoothscale(icon, (24, 24))
                    self.screen.blit(scaled, (x + x_offset, y))
                    num_surf = self.fonts['small'].render(str(amount), True, WHITE)
                    self.screen.blit(num_surf, (x + x_offset + 18, y + 12))
                    x_offset += 35
                else:
                    # fallback a círculo
                    color_rgb = _MANA_RGB.get(color, (200,200,200))
                    pygame.draw.circle(self.screen, color_rgb, (x + 15 + x_offset, y + 15), 12)
                    num_surf = self.fonts['small'].render(str(amount), True, WHITE)
                    self.screen.blit(num_surf, (x + 10 + x_offset, y + 8))
                    x_offset += 35
        else:
            zero_surf = self.fonts['medium'].render("0", True, LIGHT_GRAY)
            self.screen.blit(zero_surf, (x + 10, y + 8))
        label = self.fonts['tiny'].render("MANÁ", True, MTG_GLOW_GOLD)
        self.screen.blit(label, (x, y - 5))

    def _render_buttons(self, buttons, is_player_turn, is_combat_phase, combat_subphase):
        mx, my = pygame.mouse.get_pos()
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT

        # Durante el turno de la IA en fase de bloqueo, el jugador puede actuar
        ai_blocking_phase = (not is_player_turn and is_combat_phase
                             and combat_subphase in ("bloquear", "damage"))

        if ai_blocking_phase:
            if combat_subphase == "bloquear":
                label = "Confirmar Bloqueos [SPACE]"
                col, hcol = (160, 80, 0), ORANGE
            else:
                label = "Resolver Daño [SPACE]"
                col, hcol = (80, 140, 80), GREEN
            draw_button(self.screen, self.fonts, label, buttons["phase"],
                        col, hcol, buttons["phase"].collidepoint(mx, my), 'small')
            # Indicador sutil de turno IA
            info = self.fonts['tiny'].render("Turno IA — tú bloqueas", True, GOLD)
            self.screen.blit(info, info.get_rect(midright=(buttons["phase"].left - 12, buttons["phase"].centery)))
            return

        # Turno del jugador
        if is_combat_phase:
            if combat_subphase == "declarar":
                label, col, hcol = "Atacar / Pasar [SPACE]", RED, BRIGHT_RED
            elif combat_subphase == "bloquear":
                label, col, hcol = "Confirmar Bloqueo IA [SPACE]", (80, 80, 180), BRIGHT_BLUE
            else:
                label, col, hcol = "Resolver Daño [SPACE]", (80, 140, 80), GREEN
            draw_button(self.screen, self.fonts, label, buttons["phase"],
                        col, hcol, buttons["phase"].collidepoint(mx, my), 'small')
        else:
            draw_button(self.screen, self.fonts, "Siguiente Fase [SPACE]", buttons["phase"],
                        BLUE, BRIGHT_BLUE, buttons["phase"].collidepoint(mx, my), 'small')

    def _render_log(self, messages, state):
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        log_w = GameConfig.LOG_WIDTH
        log_x = W - log_w - 5
        log_y = 10
        log_h = H - 60
        
        # Guardar el rectángulo del log para detección de scroll (se usará en eventos)
        self.log_rect = pygame.Rect(log_x, log_y, log_w, log_h)
        
        # Panel premium del log
        log_rect = pygame.Rect(log_x, log_y, log_w, log_h)
        draw_panel(self.screen, log_rect, alpha=210, border_color=MTG_BORDER, radius=10)
        
        # Encabezado con degradado
        header_rect = pygame.Rect(log_x, log_y, log_w, 32)
        draw_rounded_rect_gradient(self.screen, header_rect, (30, 25, 50), (18, 15, 35), radius=10)
        pygame.draw.line(self.screen, MTG_BORDER, (log_x + 6, log_y + 32), (log_x + log_w - 6, log_y + 32), 1)
        
        # Título con ícono
        title = self.fonts['small'].render("📜 COMBATE", True, MTG_GLOW_GOLD)
        self.screen.blit(title, (log_x + 10, log_y + 7))
        
        # Calcular número de líneas visibles
        line_height = 16
        visible_lines = (log_h - 40) // line_height   # 40 = espacio para título
        total_lines = len(messages)
        
        # Ajustar offset del scroll (desde state)
        max_offset = max(0, total_lines - visible_lines)
        offset = min(state.log_scroll_offset, max_offset)
        state.log_scroll_offset = max(0, offset)   # actualizar por si se pasó
        
        if state.log_auto_scroll:
            state.log_scroll_offset = max_offset
        else:
            # limitar offset
            state.log_scroll_offset = max(0, min(state.log_scroll_offset, max_offset))

        # Dibujar líneas visibles
        start_idx = offset
        end_idx = min(start_idx + visible_lines, total_lines)
        
        for i, msg in enumerate(messages[start_idx:end_idx]):
            display_msg = msg[:42] if len(msg) > 42 else msg
            # Colorear según contenido
            if any(x in msg for x in ["daño", "ataca", "muere", "⚔", "💀"]):
                txt_col = (220, 130, 120)
            elif any(x in msg for x in ["bloquea", "🛡", "defiende"]):
                txt_col = (120, 180, 220)
            elif any(x in msg for x in ["maná", "tierra", "🌿"]):
                txt_col = (120, 200, 140)
            elif any(x in msg for x in ["roba", "✦"]):
                txt_col = (180, 160, 220)
            else:
                txt_col = MTG_TEXT_MAIN
            t = self.fonts['tiny'].render(display_msg, True, txt_col)
            self.screen.blit(t, (log_x + 8, log_y + 40 + i * line_height))
        
        # Scrollbar estilizada
        if total_lines > visible_lines:
            bar_height = max(30, int(visible_lines / total_lines * (log_h - 40)))
            bar_ratio = offset / max_offset if max_offset > 0 else 0
            bar_y = log_y + 40 + bar_ratio * ((log_h - 40) - bar_height)
            # Track
            pygame.draw.rect(self.screen, (30, 28, 45), 
                             (log_x + log_w - 7, log_y + 40, 4, log_h - 40), border_radius=2)
            # Thumb
            pygame.draw.rect(self.screen, MTG_GLOW_GOLD,
                             (log_x + log_w - 7, int(bar_y), 4, int(bar_height)), border_radius=2)

    def _render_tooltip(self, card: Card):
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        big_w, big_h = 400, 580
        mx, my = pygame.mouse.get_pos()

        tx = mx + 30
        ty = my - big_h // 2
        if tx + big_w > W:
            tx = mx - big_w - 30
        ty = max(10, min(ty, H - big_h - 10))

        highres = self._image_manager.load_card_image_highres(card)
        if highres:
            scaled = pygame.transform.smoothscale(highres, (big_w, big_h))
            shadow = pygame.Surface((big_w, big_h), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 150))
            self.screen.blit(shadow, (tx + 8, ty + 8))
            self.screen.blit(scaled, (tx, ty))
            pygame.draw.rect(self.screen, GOLD, (tx, ty, big_w, big_h), 3, border_radius=8)
        else:
            self._render_tooltip_fallback(card, tx, ty, big_w, big_h)

    def _render_tooltip_fallback(self, card: Card, tx, ty, big_w, big_h):
        bg = pygame.Surface((big_w, big_h), pygame.SRCALPHA)
        bg.fill((20, 20, 30, 240))
        self.screen.blit(bg, (tx, ty))
        pygame.draw.rect(self.screen, GOLD, (tx, ty, big_w, big_h), 2, border_radius=8)

        y = ty + 10
        self.screen.blit(self.fonts["large"].render(card.name, True, GOLD), (tx + 10, y)); y += 30
        self.screen.blit(self.fonts["small"].render(f"Coste: {card.mana_cost or '(ninguno)'}", True, WHITE), (tx + 10, y)); y += 22
        self.screen.blit(self.fonts["small"].render(f"Tipo: {card.card_type.value}", True, LIGHT_GRAY), (tx + 10, y)); y += 22

        if card.card_type == CardType.CREATURE and card.power is not None:
            self.screen.blit(self.fonts["medium"].render(f"⚔️ {card.power} / {card.toughness} 🛡️", True, WHITE), (tx + 10, y)); y += 28

        for line in wrap_text(card.text, self.fonts["small"], big_w - 20)[:6]:
            self.screen.blit(self.fonts["small"].render(line, True, (220, 220, 220)), (tx + 10, y)); y += 20

    # ------------------------------------------------------------------
    # Utilidad
    # ------------------------------------------------------------------

    def _blit_centered(self, text: str, font_key: str, cx: int, cy: int):
        surf = self.fonts[font_key].render(text, True, GOLD)
        self.screen.blit(surf, surf.get_rect(center=(cx, cy)))

    def _render_graveyard_tooltip(self, card: Card, total_cards: int, current_index: int, owner: str = "CEMENTERIO"):
        """Renderiza la carta del cementerio con navegación"""
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        big_w, big_h = 400, 580
        
        # Posición cerca del cursor
        mx, my = pygame.mouse.get_pos()
        tx = mx + 30
        ty = my - big_h // 2
        if tx + big_w > W:
            tx = mx - big_w - 30
        ty = max(10, min(ty, H - big_h - 10))
        
        highres = self._image_manager.load_card_image_highres(card)
        if highres:
            scaled = pygame.transform.smoothscale(highres, (big_w, big_h))
            shadow = pygame.Surface((big_w, big_h), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 150))
            self.screen.blit(shadow, (tx + 8, ty + 8))
            self.screen.blit(scaled, (tx, ty))
            pygame.draw.rect(self.screen, GOLD, (tx, ty, big_w, big_h), 3, border_radius=8)
            
            # Información de navegación
            nav_text = f"{owner}: {current_index + 1} / {total_cards} (rueda del ratón)"
            nav_surf = self.fonts['small'].render(nav_text, True, GOLD)
            nav_rect = nav_surf.get_rect(center=(tx + big_w // 2, ty + big_h + 20))
            bg_rect = nav_rect.inflate(20, 8)
            pygame.draw.rect(self.screen, (0, 0, 0, 200), bg_rect, border_radius=5)
            self.screen.blit(nav_surf, nav_rect)
        else:
            self._render_tooltip_fallback(card, tx, ty, big_w, big_h)

    def _render_graveyard_mini(self, player, graveyard_rect):
        """Muestra la última carta del cementerio con su imagen en miniatura (vertical)"""
        if not player.graveyard:
            empty_surf = self.fonts['tiny'].render("Vacío", True, LIGHT_GRAY)
            empty_rect = empty_surf.get_rect(center=graveyard_rect.center)
            self.screen.blit(empty_surf, empty_rect)
            return
        
        # Obtener la última carta
        last_card = player.graveyard[-1]
        
        # Usar el tamaño completo del rectángulo (vertical)
        mini_w = graveyard_rect.width - 8
        mini_h = graveyard_rect.height - 8
        x = graveyard_rect.x + 4
        y = graveyard_rect.y + 4
        
        # Cargar la imagen de la carta
        image = self._image_manager.load_card_image(last_card)
        
        if image:
            # Escalar manteniendo la proporción para que quepa en vertical
            img_w, img_h = image.get_width(), image.get_height()
            scale = min(mini_w / img_w, mini_h / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            try:
                scaled = pygame.transform.smoothscale(image, (new_w, new_h))
            except:
                scaled = pygame.transform.scale(image, (new_w, new_h))
            
            # Centrar la imagen en el rectángulo
            draw_x = x + (mini_w - new_w) // 2
            draw_y = y + (mini_h - new_h) // 2
            
            self.screen.blit(scaled, (draw_x, draw_y))
            pygame.draw.rect(self.screen, GOLD, (x, y, mini_w, mini_h), 2, border_radius=4)
            
            # Si hay más cartas, mostrar un indicador
            if len(player.graveyard) > 1:
                more_surf = self.fonts['small'].render(f"+{len(player.graveyard)-1}", True, GOLD)
                more_rect = more_surf.get_rect(bottomright=(x + mini_w - 5, y + mini_h - 5))
                bg_rect = more_rect.inflate(8, 4)
                pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect, border_radius=4)
                self.screen.blit(more_surf, more_rect)
        else:
            # Fallback
            name_surf = self.fonts['tiny'].render(last_card.name[:10], True, WHITE)
            name_rect = name_surf.get_rect(center=(graveyard_rect.centerx, graveyard_rect.centery))
            self.screen.blit(name_surf, name_rect)

    def _render_exile_mini(self, player, exile_rect):
        """Muestra el exilio (boca abajo, como la biblioteca)"""
        # Verificar si el jugador tiene el atributo exile
        if not hasattr(player, 'exile') or not player.exile:
            # Si no hay cartas en exilio, mostrar solo el texto (ya dibujado por el playmat)
            return
        
        # Mostrar el dorso de la carta (exilio boca abajo)
        back_image = self._image_manager.get_back_card_image()
        mini_w = exile_rect.width - 8
        mini_h = exile_rect.height - 20
        x = exile_rect.x + 4
        y = exile_rect.y + 15
        
        if back_image:
            img_w, img_h = back_image.get_width(), back_image.get_height()
            scale = min(mini_w / img_w, mini_h / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            try:
                scaled = pygame.transform.smoothscale(back_image, (new_w, new_h))
            except:
                scaled = pygame.transform.scale(back_image, (new_w, new_h))
            
            draw_x = x + (mini_w - new_w) // 2
            draw_y = y + (mini_h - new_h) // 2
            
            self.screen.blit(scaled, (draw_x, draw_y))
            pygame.draw.rect(self.screen, GOLD, (x, y, mini_w, mini_h), 2, border_radius=4)
            
            # Mostrar número de cartas en exilio
            count_surf = self.fonts['small'].render(str(len(player.exile)), True, GOLD)
            count_rect = count_surf.get_rect(center=(exile_rect.centerx, exile_rect.bottom - 8))
            self.screen.blit(count_surf, count_rect)

    def _render_library_mini(self, player, library_rect):
        """Muestra la biblioteca (boca abajo) con el dorso de la carta"""
        if not player.library:
            empty_surf = self.fonts['tiny'].render("Vacío", True, LIGHT_GRAY)
            empty_rect = empty_surf.get_rect(center=library_rect.center)
            self.screen.blit(empty_surf, empty_rect)
            return
        
        # Mostrar el dorso de la carta (biblioteca boca abajo)
        back_image = self._image_manager.get_back_card_image()
        mini_w = library_rect.width - 8
        mini_h = library_rect.height - 30  # Dejar espacio para el contador
        x = library_rect.x + 4
        y = library_rect.y + 4
        
        if back_image:
            # Escalar manteniendo proporción
            img_w, img_h = back_image.get_width(), back_image.get_height()
            scale = min(mini_w / img_w, mini_h / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            try:
                scaled = pygame.transform.smoothscale(back_image, (new_w, new_h))
            except:
                scaled = pygame.transform.scale(back_image, (new_w, new_h))
            
            # Centrar la imagen
            draw_x = x + (mini_w - new_w) // 2
            draw_y = y + (mini_h - new_h) // 2
            
            self.screen.blit(scaled, (draw_x, draw_y))
            pygame.draw.rect(self.screen, GOLD, (x, y, mini_w, mini_h), 2, border_radius=4)
            
            # Mostrar número de cartas
            count_surf = self.fonts['large'].render(str(len(player.library)), True, GOLD)
            count_rect = count_surf.get_rect(center=(library_rect.centerx, library_rect.bottom - 15))
            # Fondo para el contador
            bg_rect = count_rect.inflate(12, 6)
            pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect, border_radius=4)
            self.screen.blit(count_surf, count_rect)
        else:
            # Fallback
            count_surf = self.fonts['large'].render(str(len(player.library)), True, GOLD)
            count_rect = count_surf.get_rect(center=library_rect.center)
            self.screen.blit(count_surf, count_rect)