# ui/widgets/phase_indicator.py — Indicador de fase renovado
import pygame
import math
from core.config import GameConfig
from ui.colors import (MTG_GLOW_GOLD, MTG_DARK_BG, MTG_TEXT_DIM, MTG_TEXT_MAIN,
                       MTG_PANEL_BG, MTG_BORDER, WHITE, BLACK, MANA_G, MANA_R)
from ui.draw_utils import draw_rounded_rect_gradient


class PhaseIndicator:
    """Indicador de fase del juego con diseño premium."""

    PHASES = [
        {"key": "mantenimiento", "short": "MANT", "icon": "↺"},
        {"key": "robo",          "short": "ROBO", "icon": "✦"},
        {"key": "principal1",    "short": "MAIN", "icon": "①"},
        {"key": "combate",       "short": "ATQ",  "icon": "⚔"},
        {"key": "bloqueo",       "short": "BLQ",  "icon": "🛡"},
        {"key": "daño",          "short": "DÑO",  "icon": "💥"},
        {"key": "principal2",    "short": "MAIN2","icon": "②"},
        {"key": "final",         "short": "FIN",  "icon": "⏹"},
    ]

    # Colores por fase
    PHASE_COLORS = {
        "mantenimiento": (80, 80, 140),
        "robo":          (60, 110, 180),
        "principal1":    (60, 150, 80),
        "combate":       (180, 60, 60),
        "bloqueo":       (160, 90, 30),
        "daño":          (200, 50, 50),
        "principal2":    (60, 150, 80),
        "final":         (100, 80, 140),
    }

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.current_phase = "mantenimiento"
        self.active_player = 0
        self.phase_width = (width - 20) // len(self.PHASES)
        self._anim_time = 0

    def update(self, phase: str, active_player: int):
        self.current_phase = phase
        self.active_player = active_player
        self._anim_time = pygame.time.get_ticks()

    def draw(self, screen, fonts):
        W = self.rect.width
        t_now = pygame.time.get_ticks()
        pulse = 0.7 + 0.3 * math.sin((t_now - self._anim_time) / 400)

        # Fondo del panel
        bg = pygame.Surface((W + 8, self.rect.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 12, 28, 200), (0, 0, W + 8, self.rect.height + 8),
                         border_radius=10)
        screen.blit(bg, (self.rect.x - 4, self.rect.y - 4))

        # Segmentos de fase
        seg_w = self.phase_width
        seg_h = self.rect.height
        start_x = self.rect.x + 5

        for i, phase_info in enumerate(self.PHASES):
            px = start_x + i * (seg_w + 2)
            prect = pygame.Rect(px, self.rect.y, seg_w, seg_h)
            is_active = phase_info["key"] == self.current_phase
            pc = self.PHASE_COLORS.get(phase_info["key"], (80, 80, 120))

            if is_active:
                # Fondo activo con degradado
                bright = tuple(min(255, int(c * 1.4 * pulse)) for c in pc)
                draw_rounded_rect_gradient(screen, prect, bright, pc, radius=6)
                # Borde dorado
                pygame.draw.rect(screen, MTG_GLOW_GOLD, prect, 2, border_radius=6)
                # Glow exterior
                for rr in range(6, 0, -2):
                    gs = pygame.Surface((seg_w + rr * 2, seg_h + rr * 2), pygame.SRCALPHA)
                    a = int(40 * pulse * (7 - rr) / 6)
                    pygame.draw.rect(gs, (*MTG_GLOW_GOLD[:3], a),
                                     (0, 0, seg_w + rr * 2, seg_h + rr * 2),
                                     border_radius=6 + rr)
                    screen.blit(gs, (px - rr, self.rect.y - rr))
                tc = (20, 15, 10)
            else:
                # Fondo inactivo
                dim = tuple(int(c * 0.35) for c in pc)
                draw_rounded_rect_gradient(screen, prect,
                                            tuple(min(255, c + 15) for c in dim), dim,
                                            radius=5)
                pygame.draw.rect(screen, (50, 48, 65), prect, 1, border_radius=5)
                tc = (140, 130, 155)

            text = fonts["tiny"].render(phase_info["short"], True, tc)
            screen.blit(text, text.get_rect(center=prect.center))

        # Indicador de turno (a la derecha de las fases)
        turn_x = start_x + len(self.PHASES) * (seg_w + 2) + 10
        turn_w = W - (turn_x - self.rect.x) - 10
        if turn_w > 30:
            turn_rect = pygame.Rect(turn_x, self.rect.y, turn_w, seg_h)
            if self.active_player == 0:
                tc_bg = (20, 55, 25)
                tc_border = MANA_G
                turn_text = "TU TURNO"
            else:
                tc_bg = (55, 18, 18)
                tc_border = MANA_R
                turn_text = "IA JUEGA"

            draw_rounded_rect_gradient(screen, turn_rect,
                                        tuple(min(255, c + 20) for c in tc_bg), tc_bg,
                                        radius=6)
            pygame.draw.rect(screen, tc_border, turn_rect, 2, border_radius=6)
            t = fonts["tiny"].render(turn_text, True, tc_border)
            screen.blit(t, t.get_rect(center=turn_rect.center))
