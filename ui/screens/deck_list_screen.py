# ui/screens/deck_list_screen.py
import pygame
from typing import Optional
from managers.deck_manager import DeckManager
from ui.draw_utils import draw_button, draw_panel, draw_rounded_rect_gradient
from ui.colors import (
    DARK_GRAY, GOLD, LIGHT_GRAY, BRIGHT_BLUE, BRIGHT_RED,
    GRAY, WHITE, GREEN, BLUE, RED,
    MTG_GLOW_GOLD, MTG_GLOW_BLUE, MTG_TEXT_MAIN, MTG_TEXT_DIM,
    MTG_PANEL_BG, MTG_BORDER
)
from core.config import GameConfig


class DeckListScreen:
    """Pantalla para ver y seleccionar mazos para ambos jugadores"""
    
    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts = fonts
        self.deck_manager = DeckManager()
        
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        
        self.selected_player_deck = None
        self.selected_ai_deck = None
        
        self.btn_new = pygame.Rect(W // 2 - 100, H - 80, 200, 50)
        self.btn_back = pygame.Rect(W - 120, H - 50, 100, 35)
        self.btn_play = pygame.Rect(W // 2 - 50, H - 140, 100, 35)
        
        self.scroll_player_y = 0
        self.scroll_ai_y = 0
        self.scroll_speed = 40
    
    def handle_event(self, event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if self.btn_new.collidepoint(mx, my):
                return "new"
            if self.btn_back.collidepoint(mx, my):
                return "back"
            if self.btn_play.collidepoint(mx, my) and self.selected_player_deck and self.selected_ai_deck:
                return "play"
            
            self._handle_deck_click(mx, my, "player")
            self._handle_deck_click(mx, my, "ai")
            
            if event.button == 4:
                if mx < GameConfig.SCREEN_WIDTH // 2:
                    self.scroll_player_y = max(0, self.scroll_player_y - self.scroll_speed)
                else:
                    self.scroll_ai_y = max(0, self.scroll_ai_y - self.scroll_speed)
            elif event.button == 5:
                if mx < GameConfig.SCREEN_WIDTH // 2:
                    self.scroll_player_y += self.scroll_speed
                else:
                    self.scroll_ai_y += self.scroll_speed
        
        return None
    
    def _handle_deck_click(self, mx, my, player_type):
        decks = self.deck_manager.list_decks()
        W = GameConfig.SCREEN_WIDTH
        
        if player_type == "player":
            x_start = 50
            y_offset = 180 - self.scroll_player_y
        else:
            x_start = W // 2 + 50
            y_offset = 180 - self.scroll_ai_y
        
        for deck_name in decks:
            rect = pygame.Rect(x_start, y_offset, 400, 40)
            if rect.collidepoint(mx, my):
                if player_type == "player":
                    self.selected_player_deck = deck_name
                else:
                    self.selected_ai_deck = deck_name
                break
            y_offset += 50
    
    def render(self):
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        decks = self.deck_manager.list_decks()
        
        # Fondo con degradado
        for y in range(0, H, 3):
            t = y / H
            r = int(8 + 10 * t)
            g = int(8 + 5 * t)
            b = int(20 + 20 * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (W, y))
            pygame.draw.line(self.screen, (r, g, b), (0, y+1), (W, y+1))
            pygame.draw.line(self.screen, (r, g, b), (0, y+2), (W, y+2))
        
        title = self.fonts['large'].render("SELECCIÓN DE MAZOS", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(W // 2, 60)))
        
        pygame.draw.line(self.screen, GOLD, (W // 2, 100), (W // 2, H - 100), 2)
        
        player_title = self.fonts['medium'].render("JUGADOR", True, BRIGHT_BLUE)
        ai_title = self.fonts['medium'].render("IA (OPONENTE)", True, BRIGHT_RED)
        self.screen.blit(player_title, player_title.get_rect(center=(W // 4, 130)))
        self.screen.blit(ai_title, ai_title.get_rect(center=(3 * W // 4, 130)))
        
        # Lista jugador
        y_offset = 180 - self.scroll_player_y
        for deck_name in decks:
            rect = pygame.Rect(50, y_offset, 400, 40)
            bg_color = BRIGHT_BLUE if deck_name == self.selected_player_deck else GRAY
            border_color = GOLD if deck_name == self.selected_player_deck else WHITE
            
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)
            
            name_text = self.fonts['medium'].render(deck_name, True, WHITE)
            self.screen.blit(name_text, (rect.x + 10, rect.y + 8))
            y_offset += 50
        
        # Lista IA
        y_offset = 180 - self.scroll_ai_y
        for deck_name in decks:
            rect = pygame.Rect(W // 2 + 50, y_offset, 400, 40)
            bg_color = BRIGHT_RED if deck_name == self.selected_ai_deck else GRAY
            border_color = GOLD if deck_name == self.selected_ai_deck else WHITE
            
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)
            
            name_text = self.fonts['medium'].render(deck_name, True, WHITE)
            self.screen.blit(name_text, (rect.x + 10, rect.y + 8))
            y_offset += 50
        
        # Botones
        mx, my = pygame.mouse.get_pos()
        
        draw_button(self.screen, self.fonts, "+ Crear Nuevo Mazo", self.btn_new,
                    GREEN, (100, 200, 100),
                    self.btn_new.collidepoint(mx, my), 'medium')
        
        draw_button(self.screen, self.fonts, "Volver (ESC)", self.btn_back,
                    GRAY, LIGHT_GRAY,
                    self.btn_back.collidepoint(mx, my), 'small')
        
        play_enabled = self.selected_player_deck and self.selected_ai_deck
        draw_button(self.screen, self.fonts, "▶ JUGAR", self.btn_play,
                    BLUE if play_enabled else GRAY,
                    BRIGHT_BLUE if play_enabled else GRAY,
                    self.btn_play.collidepoint(mx, my) and play_enabled, 'medium')
        
        if not play_enabled and decks:
            tip = self.fonts['tiny'].render("Selecciona un mazo para JUGADOR y otro para IA", True, GOLD)
            self.screen.blit(tip, tip.get_rect(center=(W // 2, H - 130)))