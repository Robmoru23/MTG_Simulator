# ui/screens/game_screen/game_state.py
from typing import List, Dict, Optional
from core.card import Card
from ui.animations import AnimatingCard


class GameState:
    def __init__(self):
        self.selected_card: Optional[Card] = None
        self.hovered_card: Optional[Card] = None
        self.hovered_zone: Optional[str] = None
        self.status_msg = ""
        self.status_timer = 0
        self.log_scroll_offset = 0
        self.log_auto_scroll = True  
        
        # Subfases de combate
        self.combat_subphase = "declarar"       # declarar | bloquear | damage
        self.pending_attackers: List[Card] = [] # Atacantes seleccionados por el jugador
        self.temp_blockers: Dict[Card, List[Card]] = {}
        self.selecting_blocker_for: Optional[Card] = None

        # Manos
        self.player_hand_hover = False
        self.opponent_hand_hover = False
        self.player_hand_offset = 0
        self.opponent_hand_offset = 0
        self.hand_animation_speed = 6

        # Animaciones
        self.animations: List[AnimatingCard] = []
        self.card_rotations: Dict[Card, float] = {}
        self.rotation_targets: Dict[Card, float] = {}
        
        # Estado del cementerio
        self.hovering_graveyard = False
        self.graveyard_scroll_index = 0
        self.graveyard_display_card = None
        
        self.hovering_opponent_graveyard = False
        self.opponent_graveyard_scroll_index = 0
        self.opponent_graveyard_display_card = None

        self.selecting_target_for_ability = False   # True cuando estamos esperando un objetivo
        self.pending_ability = None                 # Almacena la función a ejecutar al seleccionar objetivo
        self.valid_targets = []                    # Lista de cartas válidas como objetivo

    def update_hand_positions(self, mouse_y: int, screen_height: int):
        if mouse_y > screen_height - 100:
            self.player_hand_hover = True
            self.player_hand_offset = max(0, self.player_hand_offset - self.hand_animation_speed)
        else:
            self.player_hand_hover = False
            self.player_hand_offset = min(80, self.player_hand_offset + self.hand_animation_speed)
        if mouse_y < 100:
            self.opponent_hand_hover = True
            self.opponent_hand_offset = min(0, self.opponent_hand_offset + self.hand_animation_speed)
        else:
            self.opponent_hand_hover = False
            self.opponent_hand_offset = max(-80, self.opponent_hand_offset - self.hand_animation_speed)

    def set_status(self, msg: str, ticks: int = 180):
        self.status_msg = msg
        self.status_timer = ticks

    def update_status(self, dt_ms: int):
        if self.status_timer > 0:
            self.status_timer -= dt_ms

    def add_animation(self, card: Card, start_pos, end_pos, on_complete=None):
        self.animations.append(AnimatingCard(card, start_pos, end_pos, on_complete))

    def update_animations(self):
        self.animations = [a for a in self.animations if a.update()]

    def rotate_card(self, card: Card, target_angle: float):
        self.rotation_targets[card] = target_angle

    def update_rotations(self):
        for card in list(self.rotation_targets):
            target = self.rotation_targets[card]
            current = self.card_rotations.get(card, 0.0)
            new_val = current + (target - current) * 0.2
            if abs(new_val - target) < 0.5:
                self.card_rotations[card] = target
                del self.rotation_targets[card]
            else:
                self.card_rotations[card] = new_val

    def sync_rotations_with_tapped(self):
        for card in list(self.card_rotations):
            expected = 90.0 if card.tapped else 0.0
            if self.card_rotations[card] != expected and card not in self.rotation_targets:
                self.card_rotations[card] = expected
