# ui/screens/game_over_screen.py — Pantalla de fin de juego mejorada
import pygame
import math
import random
from typing import Optional
from core.config import GameConfig
from core.game_core import Player
from ui.draw_utils import draw_button, draw_rounded_rect_gradient, draw_panel
from ui.colors import (MTG_GLOW_GOLD, MTG_GLOW_RED, MTG_TEXT_MAIN, MTG_TEXT_DIM,
                       MANA_W, MANA_U, MANA_B, MANA_R, MANA_G,
                       BLUE, BRIGHT_BLUE, GRAY, LIGHT_GRAY, GOLD, WHITE)


class ConfettiParticle:
    COLORS = [(255, 215, 0), (255, 100, 100), (100, 200, 255),
              (150, 255, 150), (255, 180, 50), (200, 100, 255)]

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.x = random.uniform(0, W)
        self.y = random.uniform(-50, 0)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(1.5, 4.0)
        self.size = random.randint(4, 10)
        self.color = random.choice(self.COLORS)
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-3, 3)
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.angle += self.rot_speed
        if self.y > self.H + 20:
            self.alive = False

    def draw(self, screen):
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.rect(surf, self.color, (0, 0, self.size, self.size))
        rotated = pygame.transform.rotate(surf, self.angle)
        screen.blit(rotated, (int(self.x), int(self.y)))


class GameOverScreen:
    """Pantalla de fin de juego espectacular."""

    def __init__(self, screen, fonts, winner: Player, loser: Player):
        self.screen = screen
        self.fonts = fonts
        self.winner = winner
        self.loser = loser
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        cx = W // 2

        btn_w, btn_h = 140, 50
        self.btn_restart = pygame.Rect(cx - btn_w - 10, H // 2 + 110, btn_w, btn_h)
        self.btn_menu = pygame.Rect(cx + 10, H // 2 + 110, btn_w, btn_h)

        self.confetti: list[ConfettiParticle] = []
        self.spawn_timer = 0
        self.time = 0
        self.is_player_winner = (winner.name == "Jugador")

    def handle_event(self, event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_restart.collidepoint(event.pos):
                return "restart"
            if self.btn_menu.collidepoint(event.pos):
                return "menu"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                return "restart"
            if event.key == pygame.K_ESCAPE:
                return "menu"
        return None

    def render(self):
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        cx, cy = W // 2, H // 2
        self.time += 16

        # Fondo oscuro
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 15, 210))
        self.screen.blit(overlay, (0, 0))

        # Confetti solo si ganó el jugador
        if self.is_player_winner:
            self.spawn_timer += 1
            if self.spawn_timer % 3 == 0 and len(self.confetti) < 200:
                self.confetti.append(ConfettiParticle(W, H))
            self.confetti = [p for p in self.confetti if p.alive]
            for p in self.confetti:
                p.update()
                p.draw(self.screen)

        # Halo de victoria/derrota
        halo_color = (200, 160, 0) if self.is_player_winner else (180, 40, 40)
        pulse = 0.7 + 0.3 * math.sin(self.time / 500)
        for rr in range(250, 170, -20):
            a = int(25 * pulse * (rr - 170) / 80)
            hs = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(hs, (*halo_color, a), (rr, rr), rr)
            self.screen.blit(hs, (cx - rr, cy - 40 - rr))

        # Panel principal
        panel_w, panel_h = 600, 300
        panel_rect = pygame.Rect(cx - panel_w // 2, cy - panel_h // 2 - 20, panel_w, panel_h)
        draw_panel(self.screen, panel_rect, alpha=230,
                   border_color=halo_color, radius=14)

        # Título principal
        if self.is_player_winner:
            title_text = "¡VICTORIA!"
            title_color = MTG_GLOW_GOLD
        else:
            title_text = "DERROTA"
            title_color = MTG_GLOW_RED

        # Sombra del título
        for dx, dy in [(4, 4), (2, 2)]:
            shadow = self.fonts['huge'].render(title_text, True, (0, 0, 0))
            self.screen.blit(shadow, shadow.get_rect(center=(cx + dx, cy - 80 + dy)))

        title_pulse = tuple(int(c * pulse) for c in title_color[:3])
        title = self.fonts['huge'].render(title_text, True, title_pulse)
        self.screen.blit(title, title.get_rect(center=(cx, cy - 80)))

        # Nombre del ganador
        winner_text = f"{self.winner.name} triunfa en combate"
        wt = self.fonts['medium'].render(winner_text, True, MTG_TEXT_MAIN)
        self.screen.blit(wt, wt.get_rect(center=(cx, cy - 20)))

        # Detalles del perdedor
        loser_text = f"{self.loser.name} cayó a 0 puntos de vida"
        lt = self.fonts['small'].render(loser_text, True, MTG_TEXT_DIM)
        self.screen.blit(lt, lt.get_rect(center=(cx, cy + 20)))

        # Línea decorativa
        pygame.draw.line(self.screen, (80, 70, 110),
                         (cx - 200, cy + 45), (cx + 200, cy + 45), 1)

        # Atajos de teclado
        hint = self.fonts['tiny'].render("R = Reiniciar   •   ESC = Menú", True, MTG_TEXT_DIM)
        self.screen.blit(hint, hint.get_rect(center=(cx, cy + 65)))

        # Botones
        mx, my = pygame.mouse.get_pos()
        draw_button(self.screen, self.fonts, "⟳  Reiniciar", self.btn_restart,
                    (50, 90, 170), (80, 130, 255),
                    self.btn_restart.collidepoint(mx, my), 'small')
        draw_button(self.screen, self.fonts, "⌂  Menú", self.btn_menu,
                    (70, 60, 90), (110, 100, 140),
                    self.btn_menu.collidepoint(mx, my), 'small')
