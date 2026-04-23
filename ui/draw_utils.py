# ui/draw_utils.py — Utilidades de dibujo mejoradas
import pygame
import math
from typing import Tuple
from core.card import Card, CardType, Color
from core.config import GameConfig
from managers.image_manager import ImageManager
from ui.colors import (CARD_BG, BLACK, GOLD, BRIGHT_BLUE, MTG_DARK_BG,
                       MTG_BORDER, MTG_GLOW_GOLD, MTG_GLOW_BLUE, MTG_TEXT_MAIN,
                       WHITE, MTG_ACCENT)
from utils.helpers import wrap_text

_image_manager = ImageManager()

# ─── Colores de frame por color de carta ───────────────────────
_FRAME_COLORS = {
    "W": (230, 225, 190),
    "U": (120, 170, 230),
    "B": (100, 80, 130),
    "R": (210, 100, 70),
    "G": (80, 160, 90),
    "C": (180, 175, 190),
    "multi": (210, 175, 80),
    "land": (160, 130, 90),
}

_FRAME_GLOW = {
    "W": (255, 255, 230),
    "U": (80, 160, 255),
    "B": (160, 100, 200),
    "R": (255, 100, 60),
    "G": (80, 220, 80),
    "C": (200, 200, 220),
    "multi": (255, 210, 80),
    "land": (180, 150, 100),
}


def get_card_bg(card: Card) -> Tuple[int, int, int]:
    if card.card_type == CardType.LAND:
        return CARD_BG["land"]
    if not card.colors or card.colors[0] == Color.COLORLESS:
        return CARD_BG["C"]
    if len(card.colors) > 1:
        return CARD_BG["multi"]
    return CARD_BG.get(card.colors[0].value, CARD_BG["C"])


def _get_card_key(card: Card) -> str:
    if card.card_type == CardType.LAND:
        return "land"
    if not card.colors or card.colors[0] == Color.COLORLESS:
        return "C"
    if len(card.colors) > 1:
        return "multi"
    return card.colors[0].value


def draw_glow(surface, center, radius, color, alpha=80, steps=4):
    """Dibuja un halo de luz difuso."""
    cx, cy = center
    for i in range(steps):
        r = int(radius * (1 + i * 0.5))
        a = max(0, alpha - i * (alpha // steps))
        glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color[:3], a), (r, r), r)
        surface.blit(glow_surf, (cx - r, cy - r), special_flags=pygame.BLEND_RGBA_ADD)


def draw_rounded_rect_gradient(surface, rect, color_top, color_bottom, radius=8):
    """Dibuja un rectángulo con degradado vertical."""
    w, h = rect.width, rect.height
    grad = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / max(h - 1, 1)
        c = tuple(int(color_top[i] + (color_bottom[i] - color_top[i]) * t) for i in range(3))
        pygame.draw.line(grad, c, (0, y), (w, y))
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
    grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(grad, rect.topleft)


def draw_card(screen, fonts, card: Card, x: int, y: int,
              selected=False, hovered=False, tapped=False,
              w=GameConfig.CARD_WIDTH, h=GameConfig.CARD_HEIGHT,
              facedown=False, rotation_angle=0):
    """Dibuja una carta con alta calidad visual."""

    # CASO 1: CARTA BOCA ABAJO
    if facedown:
        image = _image_manager.get_back_card_image()
        if image:
            try:
                scaled = pygame.transform.smoothscale(image, (w, h))
            except Exception:
                scaled = pygame.transform.scale(image, (w, h))
            if rotation_angle != 0:
                scaled = pygame.transform.rotate(scaled, rotation_angle)
            screen.blit(scaled, (x, y))
        else:
            surface = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(surface, (45, 30, 75), (0, 0, w, h), border_radius=7)
            pygame.draw.rect(surface, MTG_GLOW_GOLD, (0, 0, w, h), 2, border_radius=7)
            # Patrón en el dorso
            for i in range(3, min(w, h) // 2, 8):
                pygame.draw.rect(surface, (65, 45, 105), (i, i, w - i*2, h - i*2), 1, border_radius=max(1, 7 - i // 4))
            if rotation_angle != 0:
                surface = pygame.transform.rotate(surface, rotation_angle)
            screen.blit(surface, (x, y))
        return pygame.Rect(x, y, w, h)

    # CASO 2: CON IMAGEN
    image = _image_manager.load_card_image(card)
    if image:
        if rotation_angle != 0:
            rotated = pygame.transform.rotate(image, rotation_angle)
            screen.blit(rotated, (x, y))
        else:
            screen.blit(image, (x, y))

        if tapped:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((60, 60, 80, 90))
            screen.blit(overlay, (x, y))

        # Borde con glow
        ckey = _get_card_key(card)
        if selected:
            bc = MTG_GLOW_GOLD
            bw = 3
            draw_glow(screen, (x + w//2, y + h//2), max(w, h)//2 + 4, MTG_GLOW_GOLD, alpha=60)
        elif hovered:
            bc = MTG_GLOW_BLUE
            bw = 2
        else:
            bc = _FRAME_COLORS.get(ckey, (80, 80, 80))
            bw = 1
        pygame.draw.rect(screen, bc, (x, y, w, h), bw, border_radius=5)
        return pygame.Rect(x, y, w, h)

    # CASO 3: SIN IMAGEN — carta genérica de alta calidad
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    ckey = _get_card_key(card)
    bg = get_card_bg(card)
    frame_col = _FRAME_COLORS.get(ckey, (100, 100, 100))
    glow_col = _FRAME_GLOW.get(ckey, (200, 200, 200))

    if tapped:
        bg = tuple(max(0, c - 50) for c in bg)
        frame_col = tuple(max(0, c - 30) for c in frame_col)

    # Fondo con degradado sutil
    draw_rounded_rect_gradient(surface, pygame.Rect(0, 0, w, h),
                                tuple(min(255, c + 20) for c in bg), bg, radius=7)

    # Marco exterior
    border_col = MTG_GLOW_GOLD if selected else (MTG_GLOW_BLUE if hovered else frame_col)
    bw = 3 if (selected or hovered) else 2
    pygame.draw.rect(surface, border_col, (0, 0, w, h), bw, border_radius=7)

    # Barra de nombre
    name_bar_h = 18
    name_bar = pygame.Surface((w - 4, name_bar_h), pygame.SRCALPHA)
    pygame.draw.rect(name_bar, (*frame_col, 200), (0, 0, w - 4, name_bar_h), border_radius=4)
    surface.blit(name_bar, (2, 2))

    name_surf = fonts['tiny'].render(card.name[:16], True, (20, 20, 20))
    surface.blit(name_surf, (4, 3))

    if card.mana_cost:
        cost_surf = fonts['tiny'].render(card.mana_cost, True, (60, 30, 0))
        surface.blit(cost_surf, (w - cost_surf.get_width() - 4, 3))

    # Área de arte (bloque de color con textura)
    art_y = name_bar_h + 4
    art_h = h // 3
    art_surf = pygame.Surface((w - 8, art_h), pygame.SRCALPHA)
    draw_rounded_rect_gradient(art_surf, pygame.Rect(0, 0, w - 8, art_h),
                                tuple(min(255, c + 40) for c in bg),
                                tuple(max(0, c - 20) for c in bg), radius=4)
    surface.blit(art_surf, (4, art_y))

    # Línea tipo
    type_y = art_y + art_h + 2
    pygame.draw.line(surface, frame_col, (3, type_y), (w - 3, type_y), 1)
    type_surf = fonts['tiny'].render(card.card_type.value, True, (50, 40, 60))
    surface.blit(type_surf, (4, type_y + 1))

    # Texto de habilidad
    text_y = type_y + 14
    if card.text:
        lines = wrap_text(card.text[:120], fonts['tiny'], w - 10)
        for i, line in enumerate(lines[:3]):
            t = fonts['tiny'].render(line, True, (40, 35, 55))
            surface.blit(t, (5, text_y + i * 13))

    # P/T para criaturas
    if card.card_type == CardType.CREATURE and card.power is not None:
        pt_bg = pygame.Surface((30, 18), pygame.SRCALPHA)
        pygame.draw.rect(pt_bg, (*frame_col, 220), (0, 0, 30, 18), border_radius=4)
        surface.blit(pt_bg, (w - 32, h - 20))
        pt = fonts['tiny'].render(f"{card.power}/{card.toughness}", True, (20, 20, 20))
        surface.blit(pt, (w - 30, h - 19))

    # Daño recibido
    if card.damage > 0 and card.card_type == CardType.CREATURE:
        dmg_surf = fonts['tiny'].render(f"-{card.damage}", True, (220, 50, 50))
        surface.blit(dmg_surf, (4, h - 20))

    # Fiebre de ataque
    if card.summoning_sickness and card.card_type == CardType.CREATURE:
        sick = pygame.Surface((w, h), pygame.SRCALPHA)
        sick.fill((180, 0, 0, 45))
        pygame.draw.rect(sick, (180, 0, 0, 100), (0, 0, w, h), 2, border_radius=7)
        surface.blit(sick, (0, 0))

    if rotation_angle != 0:
        surface = pygame.transform.rotate(surface, rotation_angle)

    screen.blit(surface, (x, y))
    return pygame.Rect(x, y, w, h)


def draw_button(screen, fonts, text, rect, color, hover_color, hover=False,
                font_key='small', icon=None):
    """Botón con degradado y sombra."""
    col = hover_color if hover else color
    col_dark = tuple(max(0, c - 40) for c in col)

    # Sombra
    shadow = pygame.Surface((rect.width + 4, rect.height + 4), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80), (0, 0, rect.width + 4, rect.height + 4),
                     border_radius=8)
    screen.blit(shadow, (rect.x - 1, rect.y + 2))

    # Cuerpo con degradado
    draw_rounded_rect_gradient(screen, rect,
                                tuple(min(255, c + 30) for c in col), col_dark, radius=7)

    # Borde brillante superior
    border_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(border_surf, (255, 255, 255, 50 if hover else 25),
                     (0, 0, rect.width, 2), border_radius=7)
    screen.blit(border_surf, rect.topleft)

    # Borde exterior
    pygame.draw.rect(screen, tuple(min(255, c + 60) for c in col),
                     rect, 1, border_radius=7)

    # Texto con sombra
    shadow_t = fonts[font_key].render(text, True, (0, 0, 0))
    screen.blit(shadow_t, shadow_t.get_rect(center=(rect.centerx + 1, rect.centery + 1)))
    t = fonts[font_key].render(text, True, (255, 255, 255))
    screen.blit(t, t.get_rect(center=rect.center))

    return rect.collidepoint(pygame.mouse.get_pos())


def draw_panel(screen, rect, alpha=200, border_color=None, radius=10):
    """Panel semi-transparente con borde."""
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (14, 18, 36, alpha), (0, 0, rect.width, rect.height),
                     border_radius=radius)
    if border_color:
        pygame.draw.rect(panel, (*border_color[:3], 180),
                         (0, 0, rect.width, rect.height), 1, border_radius=radius)
    screen.blit(panel, rect.topleft)
