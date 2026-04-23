# ui/widgets/board_zone.py
import pygame
from core.config import GameConfig
from ui.colors import GOLD, WHITE, DARK_GRAY, BLACK


class BoardZone:
    """Representa una zona del tablero (biblioteca, cementerio, etc.)"""
    
    def __init__(self, x, y, width, height, title, icon=None, bg_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.icon = icon
        self.count = 0
        self.items = []
        self.bg_color = bg_color or (30, 35, 45)
        
    def update(self, items):
        self.items = items
        self.count = len(items)
    
    def draw(self, screen, fonts):
        # Fondo de la zona
        pygame.draw.rect(screen, self.bg_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, GOLD, self.rect, 2, border_radius=8)
        
        # Título
        title_surf = fonts['tiny'].render(self.title, True, GOLD)
        screen.blit(title_surf, (self.rect.x + 5, self.rect.y + 5))
        
        # Contador
        if self.count > 0:
            count_surf = fonts['large'].render(str(self.count), True, WHITE)
            count_rect = count_surf.get_rect(center=(self.rect.centerx, self.rect.centery))
            screen.blit(count_surf, count_rect)
        
        # Si hay carta visible (para cementerio, mostrar la última)
        if self.items and self.title in ["CEMENTERIO", "GRAVEYARD"]:
            last_card = self.items[-1]
            mini_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 25, 
                                   self.rect.width - 10, self.rect.height - 30)
            pygame.draw.rect(screen, DARK_GRAY, mini_rect, border_radius=4)
            name_surf = fonts['tiny'].render(last_card.name[:12], True, WHITE)
            screen.blit(name_surf, (mini_rect.x + 5, mini_rect.y + 5))


class PlayerBoard:
    """Tablero completo de un jugador"""
    
    def __init__(self, x, y, width, height, is_player=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_player = is_player
        self.life = 20
        self.name = "JUGADOR" if is_player else "OPONENTE"
        self.is_active = False
        
        # Layout del tablero (en porcentaje del ancho)
        self.layout = {
            "life_total": (10, 10, 80, 60),
            "library": (width - 100, 10, 90, 120),
            "graveyard": (width - 100, 140, 90, 120),
            "exile": (width - 100, 270, 90, 80),
            "lands_area": (90, height - 160, width - 200, 150),
            "creatures_area": (90, 150, width - 200, height - 320),
        }
        
        # Crear zonas
        self.zones = {}
        self._create_zones()
        
    def _create_zones(self):
        """Crear las zonas del tablero"""
        # Biblioteca
        lib_x = self.rect.x + self.rect.width - 95
        lib_y = self.rect.y + 10
        self.zones["library"] = BoardZone(lib_x, lib_y, 90, 120, "BIBLIOTECA")
        
        # Cementerio
        grave_x = self.rect.x + self.rect.width - 95
        grave_y = self.rect.y + 140
        self.zones["graveyard"] = BoardZone(grave_x, grave_y, 90, 120, "CEMENTERIO")
        
        # Exilio
        exile_x = self.rect.x + self.rect.width - 95
        exile_y = self.rect.y + 270
        self.zones["exile"] = BoardZone(exile_x, exile_y, 90, 80, "EXILIO")
        
        # Áreas de cartas (se actualizarán en cada render)
        self.lands_rect = pygame.Rect(
            self.rect.x + 90,
            self.rect.y + self.rect.height - 160,
            self.rect.width - 200,
            150
        )
        self.creatures_rect = pygame.Rect(
            self.rect.x + 90,
            self.rect.y + 150,
            self.rect.width - 200,
            self.rect.height - 320
        )
    
    def update(self, player, is_active=False):
        """Actualizar las zonas con los datos del jugador"""
        self.life = player.life
        self.name = player.name.upper()
        self.is_active = is_active
        self.zones["library"].update(player.library)
        self.zones["graveyard"].update(player.graveyard)
        self.zones["exile"].update([])
    
    def draw(self, screen, fonts):
        # Fondo del tablero (con borde iluminado si es el turno activo)
        if self.is_player:
            bg_color = (25, 55, 35)  # Verde oscuro
            border_color = GameConfig.BRIGHT_GREEN if self.is_active else GameConfig.GOLD
        else:
            bg_color = (55, 35, 35)  # Rojo oscuro
            border_color = GameConfig.BRIGHT_RED if self.is_active else GameConfig.GOLD
        
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=12)
        pygame.draw.rect(screen, border_color, self.rect, 3, border_radius=12)
        
        # Nombre del jugador
        name_surf = fonts['medium'].render(self.name, True, GameConfig.WHITE)
        screen.blit(name_surf, (self.rect.x + 15, self.rect.y + 10))
        
        # Total de vida (estilo MTG Arena)
        life_bg = pygame.Rect(self.rect.x + 15, self.rect.y + 45, 70, 60)
        pygame.draw.rect(screen, GameConfig.RED, life_bg, border_radius=10)
        pygame.draw.rect(screen, GameConfig.GOLD, life_bg, 2, border_radius=10)
        
        life_surf = fonts['huge'].render(str(self.life), True, GameConfig.WHITE)
        life_rect = life_surf.get_rect(center=life_bg.center)
        screen.blit(life_surf, life_rect)
        
        life_label = fonts['tiny'].render("VIDA", True, GameConfig.GOLD)
        screen.blit(life_label, (life_bg.x + 5, life_bg.y - 15))
        
        # Dibujar zonas
        for zone in self.zones.values():
            zone.draw(screen, fonts)
        
        # Dibujar áreas de cartas
        self._draw_area(screen, fonts, self.lands_rect, "TIERRAS", (101, 67, 33))
        self._draw_area(screen, fonts, self.creatures_rect, "CRIATURAS", (20, 60, 20))
    
    def _draw_area(self, screen, fonts, rect, title, color):
        """Dibuja un área del tablero"""
        # Fondo semitransparente
        bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        bg.fill((color[0], color[1], color[2], 80))
        screen.blit(bg, rect)
        
        pygame.draw.rect(screen, GameConfig.GOLD, rect, 1, border_radius=8)
        
        title_surf = fonts['tiny'].render(title, True, GameConfig.GOLD)
        screen.blit(title_surf, (rect.x + 8, rect.y + 5))