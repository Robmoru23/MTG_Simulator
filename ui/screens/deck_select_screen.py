# deck_select_screen.py - Pantalla de selección de mazos con dos jugadores
import pygame
from typing import Optional
from deck_manager import DeckManager
from config import GameConfig


def draw_button(screen, fonts, text, rect, color, hover_color, hover=False, font_key='small'):
    col = hover_color if hover else color
    pygame.draw.rect(screen, col, rect, border_radius=6)
    pygame.draw.rect(screen, GameConfig.WHITE, rect, 2, border_radius=6)
    t = fonts[font_key].render(text, True, GameConfig.WHITE)
    tr = t.get_rect(center=rect.center)
    screen.blit(t, tr)


class DeckListScreen:
    """Pantalla para ver y seleccionar mazos para ambos jugadores"""
    
    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts = fonts
        self.deck_manager = DeckManager()
        
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        
        # Selección de mazos
        self.selected_player_deck = None
        self.selected_ai_deck = None
        
        # Botones
        self.btn_new = pygame.Rect(W // 2 - 100, H - 80, 200, 50)
        self.btn_back = pygame.Rect(W - 120, H - 50, 100, 35)
        self.btn_play = pygame.Rect(W // 2 - 50, H - 140, 100, 35)
        
        # Scroll para cada lista
        self.scroll_player_y = 0
        self.scroll_ai_y = 0
        self.scroll_speed = 40
        
    def handle_event(self, event) -> Optional[str]:
        """Maneja eventos. Retorna 'new', 'play', 'back' o None"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
                
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Botón nuevo mazo
            if self.btn_new.collidepoint(mx, my):
                return "new"
            
            # Botón volver
            if self.btn_back.collidepoint(mx, my):
                return "back"
            
            # Botón jugar
            if self.btn_play.collidepoint(mx, my) and self.selected_player_deck and self.selected_ai_deck:
                return "play"
            
            # Clic en lista de mazos del jugador
            self._handle_deck_click(mx, my, "player")
            
            # Clic en lista de mazos de la IA
            self._handle_deck_click(mx, my, "ai")
            
            # Scroll
            if event.button == 4:  # Scroll up
                if mx < W // 2:
                    self.scroll_player_y = max(0, self.scroll_player_y - self.scroll_speed)
                else:
                    self.scroll_ai_y = max(0, self.scroll_ai_y - self.scroll_speed)
            elif event.button == 5:  # Scroll down
                if mx < W // 2:
                    self.scroll_player_y += self.scroll_speed
                else:
                    self.scroll_ai_y += self.scroll_speed
        
        return None
    
    def _handle_deck_click(self, mx, my, player_type):
        """Maneja clic en un mazo de la lista"""
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
        """Renderiza la pantalla de selección de mazos"""
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        decks = self.deck_manager.list_decks()
        
        self.screen.fill(GameConfig.DARK_GRAY)
        
        # Título
        title = self.fonts['large'].render("SELECCIÓN DE MAZOS", True, GameConfig.GOLD)
        self.screen.blit(title, title.get_rect(center=(W // 2, 60)))
        
        # Línea divisoria
        pygame.draw.line(self.screen, GameConfig.GOLD, (W // 2, 100), (W // 2, H - 100), 2)
        
        # Títulos de columnas
        player_title = self.fonts['medium'].render("JUGADOR", True, GameConfig.BRIGHT_BLUE)
        ai_title = self.fonts['medium'].render("IA (OPONENTE)", True, GameConfig.BRIGHT_RED)
        self.screen.blit(player_title, player_title.get_rect(center=(W // 4, 130)))
        self.screen.blit(ai_title, ai_title.get_rect(center=(3 * W // 4, 130)))
        
        # Lista de mazos del jugador (izquierda)
        y_offset = 180 - self.scroll_player_y
        
        if not decks:
            empty_text = self.fonts['small'].render("No hay mazos. ¡Crea uno!", True, GameConfig.LIGHT_GRAY)
            self.screen.blit(empty_text, empty_text.get_rect(center=(W // 4, H // 2)))
        else:
            for deck_name in decks:
                rect = pygame.Rect(50, y_offset, 400, 40)
                
                # Color según selección
                if deck_name == self.selected_player_deck:
                    bg_color = GameConfig.BRIGHT_BLUE
                    border_color = GameConfig.GOLD
                else:
                    bg_color = GameConfig.GRAY
                    border_color = GameConfig.WHITE
                
                pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
                pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)
                
                # Nombre del mazo
                name_text = self.fonts['medium'].render(deck_name, True, GameConfig.WHITE)
                self.screen.blit(name_text, (rect.x + 10, rect.y + 8))
                
                y_offset += 50
        
        # Lista de mazos de la IA (derecha)
        y_offset = 180 - self.scroll_ai_y
        
        for deck_name in decks:
            rect = pygame.Rect(W // 2 + 50, y_offset, 400, 40)
            
            # Color según selección
            if deck_name == self.selected_ai_deck:
                bg_color = GameConfig.BRIGHT_RED
                border_color = GameConfig.GOLD
            else:
                bg_color = GameConfig.GRAY
                border_color = GameConfig.WHITE
            
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)
            
            # Nombre del mazo
            name_text = self.fonts['medium'].render(deck_name, True, GameConfig.WHITE)
            self.screen.blit(name_text, (rect.x + 10, rect.y + 8))
            
            y_offset += 50
        
        # Botones
        mx, my = pygame.mouse.get_pos()
        
        draw_button(self.screen, self.fonts, "+ Crear Nuevo Mazo", self.btn_new,
                    GameConfig.GREEN, (100, 200, 100),
                    self.btn_new.collidepoint(mx, my), 'medium')
        
        draw_button(self.screen, self.fonts, "Volver (ESC)", self.btn_back,
                    GameConfig.GRAY, GameConfig.LIGHT_GRAY,
                    self.btn_back.collidepoint(mx, my), 'small')
        
        # Botón jugar (solo activo si ambos mazos están seleccionados)
        play_enabled = self.selected_player_deck and self.selected_ai_deck
        draw_button(self.screen, self.fonts, "▶ JUGAR", self.btn_play,
                    GameConfig.BLUE if play_enabled else GameConfig.GRAY,
                    GameConfig.BRIGHT_BLUE if play_enabled else GameConfig.GRAY,
                    self.btn_play.collidepoint(mx, my) and play_enabled, 'medium')
        
        # Instrucciones
        if not play_enabled:
            tip = self.fonts['tiny'].render("Selecciona un mazo para JUGADOR y otro para IA", True, GameConfig.GOLD)
            self.screen.blit(tip, tip.get_rect(center=(W // 2, H - 130)))
        elif self.selected_player_deck and self.selected_ai_deck:
            tip = self.fonts['tiny'].render(f"Jugador: {self.selected_player_deck}  |  IA: {self.selected_ai_deck}", True, GameConfig.GREEN)
            self.screen.blit(tip, tip.get_rect(center=(W // 2, H - 130)))