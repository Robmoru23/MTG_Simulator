# ui/widgets/stats_hud.py — HUD de estadísticas en partida
import pygame
import math
from core.config import GameConfig
from ui.draw_utils import draw_panel, draw_rounded_rect_gradient
from ui.colors import (MTG_GLOW_GOLD, MTG_TEXT_MAIN, MTG_TEXT_DIM, MTG_BORDER,
                       MANA_R, MANA_G, WHITE)


class StatsHUD:
    """Panel de estadísticas de partida en tiempo real."""

    def __init__(self):
        self.turn_count = 0
        self.player_creatures_destroyed = 0
        self.ai_creatures_destroyed = 0
        self.damage_dealt_to_ai = 0
        self.damage_dealt_to_player = 0
        self.start_time = pygame.time.get_ticks()
        self._visible = True

    def toggle(self):
        self._visible = not self._visible

    def record_damage(self, target_is_player: bool, amount: int):
        if target_is_player:
            self.damage_dealt_to_player += amount
        else:
            self.damage_dealt_to_ai += amount

    def record_creature_death(self, is_player_creature: bool):
        if is_player_creature:
            self.player_creatures_destroyed += 1
        else:
            self.ai_creatures_destroyed += 1

    def draw(self, screen, fonts, game):
        if not self._visible:
            return
        W = GameConfig.SCREEN_WIDTH
        elapsed_ms = pygame.time.get_ticks() - self.start_time
        elapsed_s = elapsed_ms // 1000
        mins, secs = divmod(elapsed_s, 60)

        panel_w = 200
        panel_h = 130
        px = W - GameConfig.LOG_WIDTH - panel_w - 30
        py = GameConfig.SCREEN_HEIGHT - panel_h - 10

        panel_rect = pygame.Rect(px, py, panel_w, panel_h)
        draw_panel(screen, panel_rect, alpha=200, border_color=(50, 45, 70), radius=8)

        # Título
        header = pygame.Surface((panel_w, 22), pygame.SRCALPHA)
        draw_rounded_rect_gradient(header, pygame.Rect(0, 0, panel_w, 22),
                                    (30, 25, 50), (18, 15, 35), radius=8)
        screen.blit(header, (px, py))
        title = fonts['tiny'].render("📊 ESTADÍSTICAS", True, MTG_GLOW_GOLD)
        screen.blit(title, (px + 8, py + 4))

        lines = [
            (f"⏱  {mins:02d}:{secs:02d}", MTG_TEXT_DIM),
            (f"🔄  Turno {game.turn_count if hasattr(game, 'turn_count') else '—'}", MTG_TEXT_MAIN),
            (f"❤  Daño al jugador: {self.damage_dealt_to_player}", MANA_R),
            (f"⚔  Daño a IA: {self.damage_dealt_to_ai}", MANA_G),
            (f"💀  Criaturas caídas: {self.player_creatures_destroyed + self.ai_creatures_destroyed}", MTG_TEXT_DIM),
        ]
        for i, (text, col) in enumerate(lines):
            t = fonts['tiny'].render(text, True, col)
            screen.blit(t, (px + 8, py + 28 + i * 18))
