# ui/fonts.py — Gestor de fuentes mejorado
import pygame
import os


class FontManager:
    def __init__(self):
        self.fonts = {}

        # Prioridad de fuentes: buscamos algo que tenga buen aspecto en MTG
        preferred_fonts = [
            "Palatino Linotype",   # Elegante, serif
            "Palatino",
            "Book Antiqua",        # Buena alternativa
            "Georgia",             # Serif legible
            "Segoe UI",            # Moderno, Windows
            "Helvetica Neue",      # macOS
            "DejaVu Serif",        # Linux
            "Liberation Serif",    # Linux alternativo
            "Times New Roman",     # Fallback universal
            "Arial",
        ]

        # También probamos fuentes del sistema
        available = [f.lower() for f in pygame.font.get_fonts()]

        def best_font():
            for name in preferred_fonts:
                try:
                    f = pygame.font.SysFont(name, 20)
                    if f:
                        return name
                except Exception:
                    pass
            return None

        chosen = best_font()

        # Tamaños ajustados para mayor legibilidad
        sizes = {
            'tiny':   15,
            'small':  20,
            'medium': 27,
            'large':  36,
            'huge':   54,
            'title':  72,
        }

        for name, size in sizes.items():
            if chosen:
                try:
                    self.fonts[name] = pygame.font.SysFont(chosen, size)
                    continue
                except Exception:
                    pass
            self.fonts[name] = pygame.font.Font(None, size + 4)

    def __getitem__(self, key):
        return self.fonts.get(key, self.fonts.get('small'))
