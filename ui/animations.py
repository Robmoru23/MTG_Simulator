# ui/animations.py
import pygame
from typing import Optional

class Tween:
    """Interpolación de valores para animaciones"""
    def __init__(self, duration=200):
        self.active = False
        self.start_value = 0
        self.end_value = 0
        self.start_time = 0
        self.duration = duration
    
    def start(self, start_val, end_val):
        self.active = True
        self.start_value = start_val
        self.end_value = end_val
        self.start_time = pygame.time.get_ticks()
    
    def update(self):
        if not self.active:
            return self.end_value
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            self.active = False
            return self.end_value
        t = elapsed / self.duration
        t = 1 - (1 - t) ** 3  # ease-out-cubic
        return self.start_value + (self.end_value - self.start_value) * t


class AnimatingCard:
    """Animación de movimiento de cartas"""
    def __init__(self, card, start_pos, end_pos, on_complete=None):
        self.card = card
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.progress = 0
        self.duration = 300
        self.start_time = pygame.time.get_ticks()
        self.on_complete = on_complete
    
    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            self.progress = 1
            if self.on_complete:
                self.on_complete()
            return False
        self.progress = elapsed / self.duration
        self.progress = 1 - (1 - self.progress) ** 3  # ease-out-cubic
        return True
    
    def get_pos(self):
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * self.progress
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * self.progress
        return (int(x), int(y))