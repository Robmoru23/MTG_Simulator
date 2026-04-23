# core/config.py - Configuración del juego
import pygame


class GameConfig:
    # Obtener resolución de pantalla
    try:
        pygame.display.init()
        info = pygame.display.Info()
        SCREEN_WIDTH = info.current_w
        SCREEN_HEIGHT = info.current_h
        pygame.display.quit()
    except:
        SCREEN_WIDTH = 1920
        SCREEN_HEIGHT = 1080
    
    FULLSCREEN = True
    FPS = 60
    CARD_WIDTH = 100
    CARD_HEIGHT = 145
    
    # Colores del tapete (azul marino profundo con degradado)
    MATTE_BASE = (10, 15, 35)  # Azul marino muy oscuro
    MATTE_GLOW = (40, 20, 55)  # Púrpura/rosado para el resplandor
    LINE_COLOR = (255, 255, 255)  # Líneas blancas
    TEXT_COLOR = (255, 255, 255)
    
    # Proporciones del tapete (en porcentajes)
    CENTER_WIDTH_PERCENT = 0.70  # 70% del ancho
    LEFT_WIDTH_PERCENT = 0.15    # 15% del ancho
    RIGHT_WIDTH_PERCENT = 0.15   # 15% del ancho
    
    # Altura de la barra de fases
    PHASE_BAR_HEIGHT_PERCENT = 0.08
    
    # Área central dividida
    CREATURES_HEIGHT_PERCENT = 0.55  # 55% del área central
    LANDS_HEIGHT_PERCENT = 0.45      # 45% del área central
    
    # Colores de las áreas
    CREATURES_BG = (15, 20, 45, 80)  # Azul oscuro semitransparente
    LANDS_BG = (15, 20, 45, 80)
    LIBRARY_BG = (20, 25, 55, 100)
    GRAVEYARD_BG = (20, 25, 55, 100)
    EXILE_BG = (20, 25, 55, 100)
    LIFE_BG = (20, 25, 55, 100)
    
    # Colores básicos
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (128, 128, 128)
    DARK_GRAY = (40, 40, 40)
    LIGHT_GRAY = (200, 200, 200)
    GREEN = (34, 100, 34)
    BRIGHT_GREEN = (0, 200, 0)
    RED = (200, 50, 50)
    BRIGHT_RED = (255, 80, 80)
    BLUE = (60, 100, 200)
    BRIGHT_BLUE = (100, 160, 255)
    GOLD = (255, 215, 0)
    BROWN = (101, 67, 33)
    DARK_GREEN = (20, 60, 20)
    ORANGE = (220, 120, 0)

    # Colores de fondo por color de carta
    CARD_BG = {
        "W": (240, 238, 210),
        "U": (180, 210, 250),
        "B": (170, 160, 185),
        "R": (250, 190, 180),
        "G": (185, 235, 185),
        "C": (220, 220, 215),
        "multi": (235, 210, 140),
        "land": (195, 170, 130),
    }

    TOOLTIP_WIDTH = 400
    TOOLTIP_HEIGHT = 580
    
    # Layout del juego
    LOG_WIDTH = 280  # Ancho del registro de combate
    LEFT_PANEL_WIDTH = 180  # Ancho del panel izquierdo (biblioteca, cementerio, exilio)
    CENTER_WIDTH = SCREEN_WIDTH - LOG_WIDTH - LEFT_PANEL_WIDTH - 40  # Área central de juego