# ui/widgets/playmat.py — Tapete de juego premium
import pygame
import math
from core.config import GameConfig
from ui.colors import (MTG_GLOW_GOLD, MTG_TEXT_MAIN, MTG_TEXT_DIM, MANA_G, MANA_R,
                       PLAYER_ZONE_BG, OPPONENT_ZONE_BG, ZONE_BORDER, WHITE, BLACK)
from ui.draw_utils import draw_rounded_rect_gradient, draw_panel


class PlayerPlaymat:
    """Tapete de juego individual mejorado con diseño premium."""

    def __init__(self, x, y, width, height, is_player=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_player = is_player
        self.width = width
        self.height = height
        self.flipped = not is_player

        self.center_width = int(width * 0.775)
        self.side_width = int(width * 0.10)

        self.left_x = x + 15
        self.center_x = x + self.side_width + 25
        self.right_x = x + width - self.side_width

        self.play_area_y = y + 48
        self.play_area_height = height - 68

        top_zone_pct = 0.50
        bottom_zone_pct = 0.50
        top_height = int(self.play_area_height * top_zone_pct)
        bottom_height = int(self.play_area_height * bottom_zone_pct)

        self.creatures_rect = pygame.Rect(self.center_x, self.play_area_y,
                                          self.center_width, top_height)
        self.lands_rect = pygame.Rect(self.center_x, self.play_area_y + top_height + 8,
                                      self.center_width, bottom_height)

        card_ratio = 1.4
        card_width = self.side_width - 8
        card_height = int(card_width * card_ratio)
        available_height = self.play_area_height - 40
        if card_height > available_height // 2:
            card_height = available_height // 2
            card_width = int(card_height / card_ratio)

        total_zones_height = card_height * 2 + 20
        start_y = self.play_area_y + (self.play_area_height - total_zones_height) // 2

        self.plus_size = 1.1
        self.life_center = (int(self.left_x + card_width // 2),
                            int(start_y + card_height // 2))
        self.life_radius = int(min(card_width // 2, card_height // 3) * self.plus_size)
        self.exile_rect = pygame.Rect(int(self.left_x),
                                      int(start_y + card_height + 20),
                                      int(card_width * self.plus_size),
                                      int(card_height * self.plus_size))
        self.library_rect = pygame.Rect(int(self.right_x), int(start_y),
                                        int(card_width * self.plus_size),
                                        int(card_height * self.plus_size))
        self.graveyard_rect = pygame.Rect(int(self.right_x),
                                          int(start_y + card_height + 20),
                                          int(card_width * self.plus_size),
                                          int(card_height * self.plus_size))

        if self.flipped:
            self.creatures_rect, self.lands_rect = self.lands_rect, self.creatures_rect
            old_lr = self.life_radius
            new_exile_y = start_y
            self.exile_rect = pygame.Rect(self.left_x, int(new_exile_y),
                                          card_width, card_height)
            new_life_y = start_y + card_height + 20 + card_height // 2
            self.life_center = (int(self.left_x + card_width // 2), int(new_life_y))
            self.life_radius = old_lr
            self.library_rect, self.graveyard_rect = self.graveyard_rect, self.library_rect

        self.gradient_surface = self._create_gradient()

    def _create_gradient(self):
        """Degradado de fondo temático."""
        surface = pygame.Surface((self.width, self.height))
        if self.is_player:
            top = (10, 22, 14)
            bot = (6, 10, 22)
        else:
            top = (6, 10, 22)
            bot = (22, 10, 12)
        h = self.height
        for y in range(h):
            t = y / max(h - 1, 1)
            c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(surface, c, (0, y), (self.width, y))
        return surface

    def draw_hexagon(self, screen, center, radius, color, border_color, border_width=2):
        points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y))
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, border_color, points, border_width)
        return points

    def draw(self, screen, fonts, player):
        screen.blit(self.gradient_surface, self.rect)

        # Borde exterior del playmat (activo = dorado, inactivo = tenue)
        is_active = getattr(player, 'is_active', False)
        border_col = MTG_GLOW_GOLD if is_active else (40, 38, 60)
        border_width = 2 if is_active else 1
        pygame.draw.rect(screen, border_col, self.rect, border_width, border_radius=10)

        # Brillo en el borde si es activo
        if is_active:
            glow_surf = pygame.Surface((self.width + 6, self.height + 6), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*MTG_GLOW_GOLD[:3], 40),
                             (0, 0, self.width + 6, self.height + 6), 3, border_radius=12)
            screen.blit(glow_surf, (self.rect.x - 3, self.rect.y - 3))

        # Nombre del jugador
        accent = MANA_G if self.is_player else MANA_R
        name_surf = fonts['small'].render(player.name.upper(), True, accent)
        screen.blit(name_surf, (self.rect.x + 12, self.rect.y + 10))

        # Zona de criaturas
        zone_color = PLAYER_ZONE_BG if self.is_player else OPPONENT_ZONE_BG
        draw_rounded_rect_gradient(screen, self.creatures_rect,
                                    tuple(min(255, c + 8) for c in zone_color),
                                    tuple(max(0, c - 4) for c in zone_color), radius=8)
        pygame.draw.rect(screen, ZONE_BORDER, self.creatures_rect, 1, border_radius=8)
        ct = fonts['tiny'].render("CRIATURAS", True, (100, 110, 140))
        screen.blit(ct, (self.creatures_rect.x + 12, self.creatures_rect.y + 8))

        # Separador decorativo en zona de criaturas
        sep_y = self.creatures_rect.y + 28
        pygame.draw.line(screen, (55, 65, 95),
                         (self.creatures_rect.x + 8, sep_y),
                         (self.creatures_rect.right - 8, sep_y), 1)

        # Zona de tierras
        land_color = (14, 35, 22) if self.is_player else (35, 14, 14)
        draw_rounded_rect_gradient(screen, self.lands_rect,
                                    tuple(min(255, c + 8) for c in land_color),
                                    tuple(max(0, c - 4) for c in land_color), radius=8)
        pygame.draw.rect(screen, ZONE_BORDER, self.lands_rect, 1, border_radius=8)
        lt = fonts['tiny'].render("TIERRAS", True, (100, 110, 140))
        screen.blit(lt, (self.lands_rect.x + 12, self.lands_rect.y + 8))

        # ── Hexágono de vida ───────────────────────────────────────
        lc = self.life_center
        lr = self.life_radius
        # Fondo del hexágono
        life_pct = max(0, min(1, player.life / 20))
        if life_pct > 0.5:
            hex_bg = (15, int(40 * life_pct), 15)
            hex_border = (80, int(200 * life_pct), 80)
        elif life_pct > 0.25:
            hex_bg = (40, 30, 10)
            hex_border = (200, 150, 50)
        else:
            hex_bg = (45, 10, 10)
            hex_border = (220, 50, 50)

        # Glow alrededor del hexágono si vida baja
        if life_pct <= 0.25:
            pulse = 0.6 + 0.4 * math.sin(pygame.time.get_ticks() / 400)
            for rr in range(int(lr) + 12, int(lr) + 4, -3):
                a = int(50 * pulse * (rr - lr) / 12)
                gs = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
                pygame.draw.circle(gs, (220, 50, 50, a), (rr, rr), rr)
                screen.blit(gs, (lc[0] - rr, lc[1] - rr))

        self.draw_hexagon(screen, lc, lr, hex_bg, hex_border, 2)

        # Etiqueta VIDA
        label_y = lc[1] - lr - 8
        vl = fonts['tiny'].render("VIDA", True, hex_border)
        screen.blit(vl, vl.get_rect(center=(lc[0], label_y)))

        life_surf = fonts['large'].render(str(player.life), True, WHITE)
        screen.blit(life_surf, life_surf.get_rect(center=lc))

        # ── Zona de exilio ─────────────────────────────────────────
        draw_panel(screen, self.exile_rect, alpha=160, border_color=(70, 65, 90), radius=6)
        et = fonts['tiny'].render("EXILIO", True, (100, 95, 120))
        screen.blit(et, et.get_rect(center=(self.exile_rect.centerx, self.exile_rect.y + 12)))
        ec = fonts['small'].render(str(len(player.exile) if hasattr(player, 'exile') else 0),
                                    True, (150, 140, 170))
        screen.blit(ec, ec.get_rect(center=self.exile_rect.center))

        # ── Biblioteca ─────────────────────────────────────────────
        lib_count = len(player.library)
        lib_urgency = lib_count < 10
        lib_color = (40, 15, 15) if lib_urgency else (15, 20, 40)
        lib_border = (200, 70, 70) if lib_urgency else (70, 80, 120)
        draw_panel(screen, self.library_rect, alpha=180, border_color=lib_border, radius=6)
        lb = fonts['tiny'].render("BIBLIO", True, lib_border)
        screen.blit(lb, lb.get_rect(center=(self.library_rect.centerx, self.library_rect.y + 12)))
        lc2 = fonts['small'].render(str(lib_count), True,
                                     (200, 70, 70) if lib_urgency else (120, 130, 180))
        screen.blit(lc2, lc2.get_rect(center=self.library_rect.center))

        # ── Cementerio ─────────────────────────────────────────────
        grave_count = len(player.graveyard)
        draw_panel(screen, self.graveyard_rect, alpha=160, border_color=(80, 70, 90), radius=6)
        gt = fonts['tiny'].render("CEMEN.", True, (110, 100, 130))
        screen.blit(gt, gt.get_rect(center=(self.graveyard_rect.centerx, self.graveyard_rect.y + 12)))
        gc = fonts['small'].render(str(grave_count), True, (150, 130, 160))
        screen.blit(gc, gc.get_rect(center=self.graveyard_rect.center))

    def get_creatures_area(self):
        return self.creatures_rect

    def get_lands_area(self):
        return self.lands_rect
