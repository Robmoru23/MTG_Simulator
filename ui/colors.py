# ui/colors.py — Paleta visual mejorada (MTG-themed)
from core.config import GameConfig

# Re-exportar colores de GameConfig
WHITE       = GameConfig.WHITE
BLACK       = GameConfig.BLACK
GRAY        = GameConfig.GRAY
DARK_GRAY   = GameConfig.DARK_GRAY
LIGHT_GRAY  = GameConfig.LIGHT_GRAY
GREEN       = GameConfig.GREEN
BRIGHT_GREEN = GameConfig.BRIGHT_GREEN
RED         = GameConfig.RED
BRIGHT_RED  = GameConfig.BRIGHT_RED
BLUE        = GameConfig.BLUE
BRIGHT_BLUE = GameConfig.BRIGHT_BLUE
GOLD        = GameConfig.GOLD
BROWN       = GameConfig.BROWN
DARK_GREEN  = GameConfig.DARK_GREEN
ORANGE      = GameConfig.ORANGE

DARK_BLUE   = (12, 18, 55)
PURPLE      = (110, 55, 165)
DEEP_PURPLE = (60, 20, 100)
CREAM       = (245, 240, 220)
WOOD        = (139, 90, 43)

MTG_DARK_BG     = (8, 10, 22)
MTG_PANEL_BG    = (14, 18, 36)
MTG_BORDER      = (60, 50, 90)
MTG_ACCENT      = (180, 140, 60)
MTG_GLOW_GOLD   = (255, 220, 80)
MTG_GLOW_BLUE   = (80, 160, 255)
MTG_GLOW_RED    = (255, 80, 60)
MTG_TEXT_DIM    = (140, 130, 160)
MTG_TEXT_MAIN   = (220, 215, 240)

ZONE_BG         = (18, 22, 38)
ZONE_BORDER     = (55, 65, 95)
PLAYER_ZONE_BG  = (16, 45, 28)
OPPONENT_ZONE_BG = (45, 18, 18)

MANA_W = (255, 253, 200)
MANA_U = (90, 155, 255)
MANA_B = (140, 100, 160)
MANA_R = (255, 90, 70)
MANA_G = (80, 220, 90)
MANA_C = (200, 195, 210)

CARD_BG = GameConfig.CARD_BG

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def alpha_color(color, alpha):
    return (*color[:3], alpha)
