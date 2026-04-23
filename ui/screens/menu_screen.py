# ui/screens/menu_screen.py — Menú principal renovado
import pygame
import math
import random
from typing import Optional
from core.config import GameConfig
from ui.draw_utils import draw_button, draw_rounded_rect_gradient, draw_panel
from ui.colors import (MTG_DARK_BG, MTG_GLOW_GOLD, MTG_GLOW_BLUE, MTG_GLOW_RED,
                       MTG_TEXT_MAIN, MTG_TEXT_DIM, MTG_ACCENT, MANA_W, MANA_U,
                       MANA_B, MANA_R, MANA_G, WHITE, GOLD, GRAY, LIGHT_GRAY,
                       BLUE, BRIGHT_BLUE, RED, BRIGHT_RED)


class Particle:
    """Partícula de mana flotante para el fondo."""
    MANA_COLORS = [MANA_W, MANA_U, MANA_B, MANA_R, MANA_G, (255, 215, 80)]

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.reset()

    def reset(self):
        self.x = random.uniform(0, self.W)
        self.y = random.uniform(0, self.H)
        self.vx = random.uniform(-0.4, 0.4)
        self.vy = random.uniform(-0.8, -0.2)
        self.radius = random.uniform(2, 6)
        self.color = random.choice(self.MANA_COLORS)
        self.alpha = random.randint(40, 140)
        self.life = random.uniform(0.3, 1.0)
        self.max_life = self.life
        self.symbol = random.choice(["W", "U", "B", "R", "G", "✦"])

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.life -= dt / 6000
        if self.life <= 0 or self.y < -20:
            self.reset()
            self.y = self.H + 10

    def draw(self, screen, fonts):
        ratio = max(0, self.life / self.max_life)
        a = int(self.alpha * ratio)
        r = int(self.radius * ratio)
        if r <= 0:
            return
        surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color[:3], a), (r + 2, r + 2), r)
        screen.blit(surf, (int(self.x) - r - 2, int(self.y) - r - 2))


class MenuScreen:
    """Pantalla de menú principal espectacular."""

    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts = fonts
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        cx = W // 2

        # Posiciones de botones (más centrados y grandes)
        btn_w, btn_h = 260, 60
        self.btn_play = pygame.Rect(cx - btn_w // 2, H // 2 - 20, btn_w, btn_h)
        self.btn_quit = pygame.Rect(cx - btn_w // 2, H // 2 + 60, btn_w, btn_h)

        # Partículas de fondo
        self.particles = [Particle(W, H) for _ in range(80)]
        self.time = 0

        # Estrellas de fondo
        self.stars = [(random.randint(0, W), random.randint(0, H),
                       random.uniform(0.5, 2.5)) for _ in range(180)]

        # Pre-renderizar fondo
        self._bg = pygame.Surface((W, H))
        self._render_static_bg(W, H)

    def _render_static_bg(self, W, H):
        """Fondo estático: degradado oscuro + viñeta."""
        for y in range(H):
            t = y / H
            r = int(8 + 12 * t)
            g = int(10 + 5 * t)
            b = int(22 + 25 * t)
            pygame.draw.line(self._bg, (r, g, b), (0, y), (W, y))

    def handle_event(self, event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_play.collidepoint(event.pos):
                return "play"
            if self.btn_quit.collidepoint(event.pos):
                return "quit"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return "play"
            if event.key == pygame.K_ESCAPE:
                return "quit"
        return None

    def render(self):
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        cx, cy = W // 2, H // 2
        dt = 16
        self.time += dt

        self.screen.blit(self._bg, (0, 0))

        # Estrellas
        for sx, sy, sr in self.stars:
            flicker = 0.6 + 0.4 * math.sin(self.time / 1000 + sx * 0.01)
            a = int(180 * flicker)
            star_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(star_surf, (200, 200, 255, a), (2, 2), int(sr))
            self.screen.blit(star_surf, (sx - 2, sy - 2))

        # Partículas
        for p in self.particles:
            p.update(dt)
            p.draw(self.screen, self.fonts)

        # Halo central de fondo
        halo_y = H // 3
        halo_r = int(280 + 20 * math.sin(self.time / 1800))
        for rr in range(halo_r, halo_r - 80, -12):
            a = int(18 * (rr - halo_r + 80) / 80)
            hs = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(hs, (80, 60, 140, a), (rr, rr), rr)
            self.screen.blit(hs, (cx - rr, halo_y - rr))

        # ─── Logo / Título ───────────────────────────────────────────
        # Sombra del título
        title_text = "MAGIC: THE GATHERING"
        for dx, dy in [(3, 3), (2, 2), (1, 1)]:
            shadow = self.fonts['huge'].render(title_text, True, (0, 0, 0))
            self.screen.blit(shadow, shadow.get_rect(center=(cx + dx, 130 + dy)))

        # Título con color dorado vibrante
        pulse = 0.85 + 0.15 * math.sin(self.time / 900)
        gold_c = (int(255 * pulse), int(210 * pulse), int(40 * pulse))
        title = self.fonts['huge'].render(title_text, True, gold_c)
        self.screen.blit(title, title.get_rect(center=(cx, 130)))

        # Líneas decorativas a los lados del título
        line_w = 120
        line_y = 155
        for side, mul in [(-1, -1), (1, 1)]:
            base_x = cx + mul * (title.get_width() // 2 + 20)
            for i, thick in enumerate([3, 1]):
                lx1 = base_x + mul * (i * 20)
                lx2 = base_x + mul * (i * 20 + line_w)
                pygame.draw.line(self.screen, (*gold_c, 150 - i * 60),
                                 (lx1, line_y), (lx2, line_y), thick)

        # Subtítulo
        sub = self.fonts['medium'].render("— Simulador de Duelo —", True, MTG_TEXT_DIM)
        self.screen.blit(sub, sub.get_rect(center=(cx, 175)))

        # ─── Panel central con botones ───────────────────────────────
        panel_rect = pygame.Rect(cx - 180, cy - 50, 360, 160)
        draw_panel(self.screen, panel_rect, alpha=160,
                   border_color=MTG_GLOW_GOLD, radius=12)

        mx, my = pygame.mouse.get_pos()
        draw_button(self.screen, self.fonts, "⚔  NUEVA PARTIDA", self.btn_play,
                    (50, 90, 180), (80, 130, 255),
                    self.btn_play.collidepoint(mx, my), 'large')
        draw_button(self.screen, self.fonts, "✕  SALIR", self.btn_quit,
                    (130, 40, 40), (200, 70, 70),
                    self.btn_quit.collidepoint(mx, my), 'large')

        # ─── Iconos de mana decorativos ──────────────────────────────
        mana_colors = [MANA_W, MANA_U, MANA_B, MANA_R, MANA_G]
        mana_syms   = ["W", "U", "B", "R", "G"]
        n = len(mana_colors)
        for i, (mc, ms) in enumerate(zip(mana_colors, mana_syms)):
            angle = math.pi + (i / n) * math.pi  # arco inferior
            orbit_r = 220
            bob = 6 * math.sin(self.time / 1200 + i * 1.2)
            mx2 = int(cx + orbit_r * math.cos(angle))
            my2 = int(H // 3 + orbit_r * math.sin(angle) * 0.4 + bob)

            # Círculo de mana
            for rr in range(22, 14, -3):
                a = int(80 * (rr - 14) / 8)
                gs = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
                pygame.draw.circle(gs, (*mc[:3], a), (rr, rr), rr)
                self.screen.blit(gs, (mx2 - rr, my2 - rr))
            pygame.draw.circle(self.screen, mc, (mx2, my2), 16)
            pygame.draw.circle(self.screen, (30, 20, 50), (mx2, my2), 16, 2)
            sym = self.fonts['small'].render(ms, True, (20, 15, 35))
            self.screen.blit(sym, sym.get_rect(center=(mx2, my2)))

        # ─── Controles ───────────────────────────────────────────────
        ctrl_panel = pygame.Rect(cx - 310, H - 195, 620, 180)
        draw_panel(self.screen, ctrl_panel, alpha=120,
                   border_color=(60, 55, 90), radius=10)

        controls_title = self.fonts['small'].render("CONTROLES", True, MTG_GLOW_GOLD)
        self.screen.blit(controls_title, controls_title.get_rect(
            center=(cx, ctrl_panel.y + 16)))
        pygame.draw.line(self.screen, (80, 70, 110),
                         (cx - 100, ctrl_panel.y + 28), (cx + 100, ctrl_panel.y + 28), 1)

        controls = [
            ("ESPACIO / Botón 'Siguiente Fase'", "Avanzar fase"),
            ("Clic en tierra", "Girar para maná"),
            ("Clic en carta de mano", "Seleccionar / lanzar"),
            ("Clic en criatura (combate)", "Marcar como atacante"),
            ("ESC", "Volver al menú"),
            ("F11", "Pantalla completa"),
        ]
        col1_x = cx - 290
        col2_x = cx - 50
        for i, (key, desc) in enumerate(controls):
            row = i % 3
            col = i // 3
            base_x = col1_x if col == 0 else col2_x
            y = ctrl_panel.y + 40 + row * 42
            k_surf = self.fonts['tiny'].render(key, True, MTG_GLOW_BLUE)
            d_surf = self.fonts['tiny'].render(f"→  {desc}", True, MTG_TEXT_DIM)
            self.screen.blit(k_surf, (base_x, y))
            self.screen.blit(d_surf, (base_x, y + 16))

        # Versión
        ver = self.fonts['tiny'].render("v2.0 — Edición Mejorada", True, (60, 55, 80))
        self.screen.blit(ver, (W - ver.get_width() - 10, H - 20))
