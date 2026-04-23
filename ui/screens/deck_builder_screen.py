# ui/screens/deck_builder_screen.py
import pygame
import os
from typing import List, Optional, Tuple
from copy import copy
from core.card import Card, ALL_CARDS, CARDS_BY_NAME, CardType, Color
from managers.deck_manager import Deck, DeckManager
from managers.image_manager import ImageManager
from core.config import GameConfig
from ui.draw_utils import draw_card, draw_button, get_card_bg, draw_panel, draw_rounded_rect_gradient
from ui.colors import (
    DARK_GRAY, GOLD, WHITE, BLACK, BRIGHT_BLUE, GRAY, LIGHT_GRAY,
    GREEN, RED, ORANGE, BRIGHT_RED,
    MTG_GLOW_GOLD, MTG_GLOW_BLUE, MTG_TEXT_MAIN, MTG_TEXT_DIM,
    MTG_PANEL_BG, MTG_BORDER
)


def draw_card_with_image(screen, fonts, card: Card, x: int, y: int,
                         w=GameConfig.CARD_WIDTH, h=GameConfig.CARD_HEIGHT):
    """Dibuja una carta usando su imagen PNG"""
    image_manager = ImageManager()
    image = image_manager.load_card_image(card)
    
    if image:
        screen.blit(image, (x, y))
        pygame.draw.rect(screen, BLACK, (x, y, w, h), 2, border_radius=4)
    else:
        draw_card(screen, fonts, card, x, y, w=w, h=h)


def draw_mini_card(screen, fonts, card: Card, x: int, y: int, w=100, h=140):
    """Dibuja una versión mini de la carta"""
    image_manager = ImageManager()
    image = image_manager.load_card_image(card)
    
    if image:
        scaled = pygame.transform.scale(image, (w, h))
        screen.blit(scaled, (x, y))
        pygame.draw.rect(screen, GOLD, (x, y, w, h), 1, border_radius=3)
    else:
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        bg = get_card_bg(card)
        pygame.draw.rect(surface, bg, (0, 0, w, h), border_radius=4)
        pygame.draw.rect(surface, BLACK, (0, 0, w, h), 1, border_radius=4)
        name_small = fonts['tiny'].render(card.name[:12], True, BLACK)
        surface.blit(name_small, (2, 2))
        if card.card_type == CardType.CREATURE and card.power is not None:
            pt_text = fonts['tiny'].render(f"{card.power}/{card.toughness}", True, BLACK)
            surface.blit(pt_text, (w - 30, h - 16))
        screen.blit(surface, (x, y))


class DeckBuilderScreen:
    """Pantalla para crear y editar mazos"""
    
    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts = fonts
        self.deck_manager = DeckManager()
        
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        CW, CH = GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT
        
        self.deck_name = ""
        self.selected_cards: List[Card] = []
        self.available_cards = ALL_CARDS.copy()
        self.filtered_cards = self.available_cards.copy()
        self.search_text = ""
        self.scroll_y = 0
        self.scroll_speed = 30
        self.message = ""
        self.message_timer = 0
        
        self.name_input_rect = pygame.Rect(W // 2 - 150, 50, 300, 40)
        self.name_input_active = True
        
        self.btn_save = pygame.Rect(W - 160, 60, 140, 45)
        self.btn_cancel = pygame.Rect(W - 160, 115, 140, 40)
        self.btn_clear = pygame.Rect(W - 160, 170, 140, 40)
        self.btn_remove_last = pygame.Rect(W - 160, 225, 140, 40)
        
        self.available_area = pygame.Rect(20, 100, W - 200, H - 120)
        self.deck_area = pygame.Rect(W - 180, 100, 160, H - 120)
    
    def set_message(self, msg: str, duration=180):
        self.message = msg
        self.message_timer = duration
    
    def handle_event(self, event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
            if self.name_input_active:
                if event.key == pygame.K_RETURN:
                    self.name_input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.deck_name = self.deck_name[:-1]
                else:
                    if len(self.deck_name) < 30 and event.unicode.isprintable():
                        self.deck_name += event.unicode
                return None
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if self.name_input_rect.collidepoint(mx, my):
                self.name_input_active = True
                return None
            
            if self.btn_save.collidepoint(mx, my):
                if self._validate_deck():
                    deck = Deck(self.deck_name, self.selected_cards)
                    if self.deck_manager.save_deck(deck):
                        self.set_message(f"✅ ¡Mazo '{self.deck_name}' guardado!", 180)
                        return "saved"
                    else:
                        self.set_message("❌ Error al guardar el mazo", 180)
                else:
                    if not self.deck_name.strip():
                        self.set_message("❌ Escribe un nombre para el mazo", 120)
                    elif len(self.selected_cards) != 60:
                        self.set_message(f"❌ Necesitas exactamente 60 cartas (tienes {len(self.selected_cards)})", 120)
                return None
            
            if self.btn_cancel.collidepoint(mx, my):
                return "back"
            
            if self.btn_clear.collidepoint(mx, my):
                self.selected_cards.clear()
                self.set_message("🧹 Mazo limpiado", 90)
                return None
            
            if self.btn_remove_last.collidepoint(mx, my):
                if self.selected_cards:
                    removed = self.selected_cards.pop()
                    self.set_message(f"🗑️ Eliminada: {removed.name}", 90)
                return None
            
            if self.available_area.collidepoint(mx, my):
                self._handle_card_click(mx, my, self.filtered_cards, 
                                        self.available_area.x, self.available_area.y)
                return None
            
            if self.deck_area.collidepoint(mx, my):
                self._handle_deck_card_click(mx, my)
                return None
            
            if event.button == 4:
                self.scroll_y = max(0, self.scroll_y - self.scroll_speed)
            elif event.button == 5:
                max_scroll = self._get_max_scroll()
                self.scroll_y = min(max_scroll, self.scroll_y + self.scroll_speed)
        
        if event.type == pygame.KEYDOWN and not self.name_input_active:
            if event.key == pygame.K_BACKSPACE:
                self.search_text = self.search_text[:-1]
                self._filter_cards()
            elif event.key == pygame.K_RETURN:
                self.name_input_active = True
            elif event.unicode.isprintable():
                self.search_text += event.unicode
                self._filter_cards()
        
        if self.message_timer > 0:
            self.message_timer -= 1
        
        return None
    
    def _get_max_scroll(self) -> int:
        CW, CH = GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT
        margin = 8
        cards_per_row = max(1, (self.available_area.width) // (CW + margin))
        total_rows = (len(self.filtered_cards) + cards_per_row - 1) // cards_per_row
        total_height = total_rows * (CH + margin)
        return max(0, total_height - self.available_area.height)
    
    def _handle_card_click(self, mx, my, cards, start_x, start_y):
        CW, CH = GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT
        margin = 8
        cards_per_row = max(1, (self.available_area.width) // (CW + margin))
        
        for i, card in enumerate(cards):
            row = i // cards_per_row
            col = i % cards_per_row
            x = start_x + col * (CW + margin)
            y = start_y + row * (CH + margin) - self.scroll_y
            
            card_rect = pygame.Rect(x, y, CW, CH)
            if card_rect.collidepoint(mx, my):
                self.selected_cards.append(copy(card))
                self.set_message(f"➕ Añadida: {card.name} ({len(self.selected_cards)}/60)", 60)
                break
    
    def _handle_deck_card_click(self, mx, my):
        w, h = 140, GameConfig.CARD_HEIGHT
        margin = 4
        y_offset = self.deck_area.y + 10
        start_idx = max(0, len(self.selected_cards) - 10)
        
        for i, card in enumerate(self.selected_cards[start_idx:]):
            x = self.deck_area.x + 10
            y = y_offset + i * (h + margin)
            card_rect = pygame.Rect(x, y, w, h)
            if card_rect.collidepoint(mx, my):
                real_index = start_idx + i
                if 0 <= real_index < len(self.selected_cards):
                    removed = self.selected_cards.pop(real_index)
                    self.set_message(f"🗑️ Eliminada: {removed.name} ({len(self.selected_cards)}/60)", 90)
                break
    
    def _filter_cards(self):
        if not self.search_text:
            self.filtered_cards = self.available_cards.copy()
        else:
            search_lower = self.search_text.lower()
            self.filtered_cards = [
                c for c in self.available_cards 
                if search_lower in c.name.lower() or 
                   search_lower in c.card_type.value.lower() or
                   (c.mana_cost and search_lower in c.mana_cost.lower())
            ]
        self.scroll_y = 0
    
    def _validate_deck(self) -> bool:
        if not self.deck_name.strip():
            return False
        if len(self.selected_cards) != 60:
            return False
        return True
    
    def render(self):
        W, H = GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT
        CW, CH = GameConfig.CARD_WIDTH, GameConfig.CARD_HEIGHT
        margin = 8
        
        for yy in range(0, H, 3):
            t = yy / H
            r = int(8 + 8 * t); g = int(8 + 5 * t); b = int(20 + 18 * t)
            pygame.draw.line(self.screen, (r, g, b), (0, yy), (W, yy))
            pygame.draw.line(self.screen, (r, g, b), (0, yy+1), (W, yy+1))
            pygame.draw.line(self.screen, (r, g, b), (0, yy+2), (W, yy+2))
        
        title = self.fonts['large'].render("CONSTRUCTOR DE MAZOS", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(W // 2, 20)))
        
        name_label = self.fonts['small'].render("Nombre del mazo:", True, WHITE)
        self.screen.blit(name_label, (self.name_input_rect.x, self.name_input_rect.y - 25))
        
        input_color = BRIGHT_BLUE if self.name_input_active else GRAY
        pygame.draw.rect(self.screen, BLACK, self.name_input_rect, border_radius=5)
        pygame.draw.rect(self.screen, input_color, self.name_input_rect, 2, border_radius=5)
        
        name_display = self.deck_name if self.deck_name else "Escribe el nombre..."
        name_color = WHITE if self.deck_name else GRAY
        name_surf = self.fonts['medium'].render(name_display[:25], True, name_color)
        self.screen.blit(name_surf, (self.name_input_rect.x + 5, self.name_input_rect.y + 8))
        
        card_count = len(self.selected_cards)
        if card_count == 60:
            count_color = GREEN
            count_text = f"✓ {card_count}/60 - ¡Completo!"
        elif card_count > 60:
            count_color = RED
            count_text = f"⚠️ {card_count}/60 - ¡Sobran {card_count - 60}!"
        else:
            count_color = ORANGE
            count_text = f"📦 {card_count}/60 - Faltan {60 - card_count}"
        
        count_surf = self.fonts['medium'].render(count_text, True, count_color)
        self.screen.blit(count_surf, (self.name_input_rect.x + self.name_input_rect.width + 20, 
                                       self.name_input_rect.y + 8))
        
        mx, my = pygame.mouse.get_pos()
        
        save_hover = self.btn_save.collidepoint(mx, my)
        save_color = GREEN if card_count == 60 else GRAY
        save_hover_color = (100, 200, 100) if card_count == 60 else GRAY
        draw_button(self.screen, self.fonts, "💾 GUARDAR", self.btn_save,
                    save_color, save_hover_color, save_hover, 'small')
        
        draw_button(self.screen, self.fonts, "✖ CANCELAR (ESC)", self.btn_cancel,
                    RED, BRIGHT_RED,
                    self.btn_cancel.collidepoint(mx, my), 'small')
        
        draw_button(self.screen, self.fonts, "🗑 Limpiar Todo", self.btn_clear,
                    (150, 50, 50), (200, 80, 80),
                    self.btn_clear.collidepoint(mx, my), 'small')
        
        draw_button(self.screen, self.fonts, "↩ Quitar Última", self.btn_remove_last,
                    (150, 100, 50), (200, 130, 80),
                    self.btn_remove_last.collidepoint(mx, my), 'small')
        
        search_rect = pygame.Rect(self.available_area.x, self.available_area.y - 30, 200, 25)
        pygame.draw.rect(self.screen, BLACK, search_rect, border_radius=3)
        pygame.draw.rect(self.screen, WHITE, search_rect, 1, border_radius=3)
        search_display = self.search_text if self.search_text else "🔍 Buscar carta..."
        search_color = WHITE if self.search_text else GRAY
        search_surf = self.fonts['tiny'].render(search_display[:25], True, search_color)
        self.screen.blit(search_surf, (search_rect.x + 3, search_rect.y + 4))
        
        pygame.draw.rect(self.screen, BLACK, self.available_area, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, self.available_area, 2, border_radius=8)
        
        avail_title = self.fonts['small'].render(f"Cartas Disponibles ({len(self.filtered_cards)})", True, GOLD)
        self.screen.blit(avail_title, (self.available_area.x + 10, self.available_area.y - 20))
        
        cards_per_row = max(1, (self.available_area.width) // (CW + margin))
        clip_rect = self.screen.get_clip()
        self.screen.set_clip(self.available_area)
        
        for i, card in enumerate(self.filtered_cards):
            row = i // cards_per_row
            col = i % cards_per_row
            x = self.available_area.x + col * (CW + margin)
            y = self.available_area.y + row * (CH + margin) - self.scroll_y
            
            if y + CH > self.available_area.y and y < self.available_area.y + self.available_area.height:
                draw_card_with_image(self.screen, self.fonts, card, x, y, w=CW, h=CH)
        
        self.screen.set_clip(clip_rect)
        
        pygame.draw.rect(self.screen, BLACK, self.deck_area, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, self.deck_area, 2, border_radius=8)
        
        deck_title = self.fonts['small'].render(f"Tu Mazo ({card_count})", True, GOLD)
        self.screen.blit(deck_title, (self.deck_area.x + 10, self.deck_area.y - 20))
        
        y_offset = self.deck_area.y + 5
        start_idx = max(0, len(self.selected_cards) - 10)
        mini_w, mini_h = 140, GameConfig.CARD_HEIGHT
        
        for i, card in enumerate(self.selected_cards[start_idx:]):
            x = self.deck_area.x + 10
            y = y_offset + i * (mini_h + 4)
            if y + mini_h < self.deck_area.y + self.deck_area.height:
                draw_mini_card(self.screen, self.fonts, card, x, y, mini_w, mini_h)
        
        if not self.selected_cards:
            empty_text = self.fonts['small'].render("Haz clic en cartas para añadirlas", True, LIGHT_GRAY)
            self.screen.blit(empty_text, (self.deck_area.x + 15, self.deck_area.y + self.deck_area.height // 2))
        
        max_scroll = self._get_max_scroll()
        if max_scroll > 0:
            scroll_percent = self.scroll_y / max_scroll
            bar_height = max(30, self.available_area.height * 0.3)
            bar_y = self.available_area.y + scroll_percent * (self.available_area.height - bar_height)
            pygame.draw.rect(self.screen, GRAY, 
                            (self.available_area.x + self.available_area.width - 10, bar_y, 8, bar_height), 
                            border_radius=4)
        
        if self.message_timer > 0 and self.message:
            msg_surf = self.fonts['small'].render(self.message, True, GOLD)
            msg_rect = msg_surf.get_rect(center=(W // 2, H - 35))
            bg_rect = msg_rect.inflate(20, 8)
            pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect, border_radius=8)
            self.screen.blit(msg_surf, msg_rect)