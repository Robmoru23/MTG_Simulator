# ui/widgets/status_bar.py — Barra de estado con mensajes animados
import pygame
import math
from core.config import GameConfig
from ui.draw_utils import draw_rounded_rect_gradient
from ui.colors import MTG_GLOW_GOLD, MTG_GLOW_BLUE, MTG_GLOW_RED, WHITE, MTG_TEXT_DIM


class StatusBar:
    """Barra de estado animada con mensajes tipados."""

    TYPE_COLORS = {
        "info":    MTG_GLOW_BLUE,
        "warning": (220, 160, 50),
        "combat":  MTG_GLOW_RED,
        "success": (80, 220, 100),
        "gold":    MTG_GLOW_GOLD,
    }

    def __init__(self):
        self.message = ""
        self.msg_type = "info"
        self.timer = 0
        self.max_timer = 200
        self._fade_alpha = 255

    def set(self, msg: str, msg_type="info", duration=180):
        self.message = msg
        self.msg_type = msg_type
        self.timer = duration
        self.max_timer = duration
        self._fade_alpha = 255

    def update(self, dt_ms):
        if self.timer > 0:
            self.timer -= 1
            fade_ticks = self.max_timer // 4
            if self.timer < fade_ticks:
                self._fade_alpha = int(255 * self.timer / fade_ticks)

    def draw(self, screen, fonts):
        if not self.message or self.timer <= 0:
            return
        W = GameConfig.SCREEN_WIDTH
        col = self.TYPE_COLORS.get(self.msg_type, MTK_GLOW_BLUE if False else MTG_GLOW_BLUE)

        # Centro de la pantalla, zona inferior
        t_surf = fonts['small'].render(self.message, True, col)
        tw, th = t_surf.get_size()
        pad_x, pad_y = 24, 10
        bar_w = tw + pad_x * 2
        bar_h = th + pad_y * 2
        bx = W // 2 - bar_w // 2
        by = GameConfig.SCREEN_HEIGHT - bar_h - 55

        # Fondo con alpha
        bar_surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        a = self._fade_alpha
        dark = (12, 10, 22, min(220, a))
        pygame.draw.rect(bar_surf, dark, (0, 0, bar_w, bar_h), border_radius=8)
        pygame.draw.rect(bar_surf, (*col[:3], a), (0, 0, bar_w, bar_h), 1, border_radius=8)

        # Pulso suave en el borde
        pulse = 0.6 + 0.4 * math.sin(pygame.time.get_ticks() / 350)
        glow = pygame.Surface((bar_w + 6, bar_h + 6), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*col[:3], int(40 * pulse * a / 255)),
                         (0, 0, bar_w + 6, bar_h + 6), 2, border_radius=10)
        screen.blit(glow, (bx - 3, by - 3))

        screen.blit(bar_surf, (bx, by))

        # Texto con alpha
        txt_surf = pygame.Surface(t_surf.get_size(), pygame.SRCALPHA)
        txt_surf.blit(t_surf, (0, 0))
        txt_surf.set_alpha(self._fade_alpha)
        screen.blit(txt_surf, (bx + pad_x, by + pad_y))
