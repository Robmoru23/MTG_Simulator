# ui/widgets/zone.py
import pygame
from core.config import GameConfig
from ui.colors import DARK_BLUE, GOLD, WHITE

def draw_zone(screen, fonts, title, count, x, y, w, h, color=DARK_BLUE):
    """Dibuja una zona de juego (biblioteca, cementerio)"""
    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=8)
    pygame.draw.rect(screen, GOLD, (x, y, w, h), 2, border_radius=8)
    
    title_surf = fonts['tiny'].render(title, True, GOLD)
    screen.blit(title_surf, (x + 5, y + 5))
    
    count_surf = fonts['large'].render(str(count), True, WHITE)
    count_rect = count_surf.get_rect(center=(x + w // 2, y + h // 2))
    screen.blit(count_surf, count_rect)