# ui/widgets/button.py
import pygame
from core.config import GameConfig

class Button:
    def __init__(self, rect, text, color, hover_color, font_key='small'):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font_key = font_key
        self.hovered = False
        self.enabled = True
    
    def update(self, mouse_pos):
        self.hovered = self.enabled and self.rect.collidepoint(mouse_pos)
        return self.hovered
    
    def draw(self, screen, fonts):
        if not self.enabled:
            col = GameConfig.GRAY
        else:
            col = self.hover_color if self.hovered else self.color
        
        pygame.draw.rect(screen, col, self.rect, border_radius=6)
        pygame.draw.rect(screen, GameConfig.WHITE, self.rect, 2, border_radius=6)
        
        t = fonts[self.font_key].render(self.text, True, GameConfig.WHITE)
        tr = t.get_rect(center=self.rect.center)
        screen.blit(t, tr)
    
    def is_clicked(self, mouse_pos, mouse_click):
        return self.enabled and self.hovered and mouse_click