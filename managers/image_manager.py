# managers/image_manager.py
import pygame
import os
import logging
from typing import Optional, Dict
from core.card import Card
from core.config import GameConfig

logger = logging.getLogger(__name__)

# Rutas candidatas relativas al directorio base (en orden de prioridad)
_SEARCH_SUBDIRS = [
    os.path.join("assets", "cards_imgs"),
    "cards_imgs",
]


class ImageManager:
    """Singleton para gestionar la carga y caché de imágenes."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._card_images: Dict[str, Optional[pygame.Surface]] = {}
        self._card_images_highres: Dict[str, Optional[pygame.Surface]] = {}
        self._back_card_image: Optional[pygame.Surface] = None
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._mana_icons: Dict[str, Optional[pygame.Surface]] = {}

    # ------------------------------------------------------------------
    # Búsqueda de rutas
    # ------------------------------------------------------------------

    def _candidate_paths(self, card: Card) -> list:
        """Genera la lista de rutas donde buscar la imagen de una carta."""
        paths = []
        if card.image_path:
            paths.append(card.image_path)
            paths.append(os.path.join(self.base_dir, card.image_path))
            filename = os.path.basename(card.image_path)
            for subdir in _SEARCH_SUBDIRS:
                paths.append(os.path.join(self.base_dir, subdir, filename))
                paths.append(os.path.join(subdir, filename))

        safe_name = card.name.lower().replace(" ", "_").replace("'", "")
        for ext in (".png", ".jpg", ".jpeg"):
            for subdir in _SEARCH_SUBDIRS:
                paths.append(os.path.join(self.base_dir, subdir, safe_name + ext))
                paths.append(os.path.join(subdir, safe_name + ext))
        return paths

    def _first_existing(self, paths: list) -> Optional[str]:
        return next((p for p in paths if p and os.path.exists(p)), None)

    # ------------------------------------------------------------------
    # Carga pública
    # ------------------------------------------------------------------

    def load_card_image(self, card: Card) -> Optional[pygame.Surface]:
        """Carga la imagen de una carta escalada al tamaño de juego con alta calidad"""
        if card.name in self._card_images:
            return self._card_images[card.name]

        path = self._first_existing(self._candidate_paths(card))
        if path:
            try:
                # Cargar imagen original
                original = pygame.image.load(path)
                
                # Escalar con smoothscale para mejor calidad (usar si está disponible)
                try:
                    img = pygame.transform.smoothscale(original, (GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT))
                except:
                    # Fallback a scale si smoothscale no está disponible
                    img = pygame.transform.scale(original, (GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT))
                
                self._card_images[card.name] = img
                logger.debug("Imagen cargada: %s desde %s", card.name, path)
                return img
            except pygame.error as e:
                logger.warning("No se pudo cargar %s: %s", path, e)

        logger.debug("Imagen no encontrada: %s", card.name)
        self._card_images[card.name] = None
        return None

    def load_card_image_highres(self, card: Card) -> Optional[pygame.Surface]:
        """Carga la imagen original sin escalar (para tooltips)."""
        if card.name in self._card_images_highres:
            return self._card_images_highres[card.name]

        path = self._first_existing(self._candidate_paths(card))
        if path:
            try:
                img = pygame.image.load(path)
                self._card_images_highres[card.name] = img
                logger.debug("Alta resolución cargada: %s (%dx%d)", card.name, img.get_width(), img.get_height())
                return img
            except pygame.error as e:
                logger.warning("No se pudo cargar highres %s: %s", path, e)

        logger.debug("Alta resolución no encontrada: %s", card.name)
        self._card_images_highres[card.name] = None
        return None

    def get_back_card_image(self) -> pygame.Surface:
        """Devuelve la imagen del reverso de las cartas."""
        if self._back_card_image is not None:
            return self._back_card_image

        back_candidates = [
            os.path.join("assets", "cards_imgs", "0_Back_card.png"),
            os.path.join(self.base_dir, "assets", "cards_imgs", "0_Back_card.png"),
            os.path.join("cards_imgs", "0_Back_card.png"),
            os.path.join(self.base_dir, "cards_imgs", "0_Back_card.png"),
            os.path.join("assets", "cards_imgs", "back.png"),
        ]
        path = self._first_existing(back_candidates)
        if path:
            try:
                img = pygame.image.load(path)
                img = pygame.transform.scale(img, (GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT))
                img = pygame.transform.rotate(img, 180)
                self._back_card_image = img
                logger.debug("Reverso cargado desde: %s", path)
                return img
            except pygame.error as e:
                logger.warning("No se pudo cargar el reverso desde %s: %s", path, e)

        logger.warning("Usando reverso genérico")
        self._back_card_image = self._create_back_card_fallback()
        return self._back_card_image

    def _create_back_card_fallback(self) -> pygame.Surface:
        surface = pygame.Surface((GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT))
        surface.fill((60, 40, 100))
        pygame.draw.rect(surface, GameConfig.GOLD, surface.get_rect(), 2)
        return surface

    def clear_cache(self):
        self._card_images.clear()
        self._card_images_highres.clear()
        self._back_card_image = None
    
    def load_mana_icon(self, color: str) -> Optional[pygame.Surface]:
        """Carga el icono de maná para el color especificado."""
        if not hasattr(self, '_mana_icons'):
            self._mana_icons = {}
        
        if color in self._mana_icons:
            return self._mana_icons[color]
        
        color_lower = color.lower()
        filename = f"{color_lower}_mana.png"
        
        # Posibles rutas donde buscar
        possible_paths = [
            os.path.join(self.base_dir, "assets", "icons", filename),
            os.path.join("assets", "icons", filename),
            os.path.join(self.base_dir, "assets", "icons", f"{color_lower}_mana.png"),
            os.path.join("assets", "icons", f"{color_lower}_mana.png"),
            # También buscar directamente en la carpeta icons
            filename,
        ]
        
        print(f"🔍 Buscando icono para {color} en: {possible_paths}")
        
        for path in possible_paths:
            if path and os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self._mana_icons[color] = img
                    print(f"✅ Icono de maná cargado: {color} desde {path}")
                    return img
                except pygame.error as e:
                    print(f"❌ Error cargando {path}: {e}")
        
        print(f"⚠️ No se encontró icono para {color}, usando fallback")
        self._mana_icons[color] = None
        return None