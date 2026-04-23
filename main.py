# main.py
import pygame
import sys
from core.config import GameConfig
from ui.fonts import FontManager
from managers.deck_manager import DeckManager
from ui.screens.menu_screen import MenuScreen
from ui.screens.deck_list_screen import DeckListScreen
from ui.screens.deck_builder_screen import DeckBuilderScreen
from ui.screens.game_screen import GameScreen
from ui.screens.game_over_screen import GameOverScreen


class MTGSimulator:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT),
            pygame.FULLSCREEN if GameConfig.FULLSCREEN else 0,
        )
        pygame.display.set_caption("Magic: The Gathering — Simulador")
        self.clock = pygame.time.Clock()
        self.fonts = FontManager()
        self.running = True

        self.deck_manager = DeckManager()
        self.state = "menu"
        self.selected_player_deck_name = None
        self.selected_ai_deck_name = None

        self.menu_screen = MenuScreen(self.screen, self.fonts)
        self.deck_list_screen = None
        self.deck_builder_screen = None
        self.game_screen = None
        self.game_over_screen = None

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(GameConfig.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self._handle_event(event)

            self._update(dt)
            self._render()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def _handle_event(self, event):
        if self.state == "menu":
            result = self.menu_screen.handle_event(event)
            if result == "play":
                self.deck_list_screen = DeckListScreen(self.screen, self.fonts)
                self.state = "deck_list"
            elif result == "quit":
                self.running = False

        elif self.state == "deck_list" and self.deck_list_screen:
            result = self.deck_list_screen.handle_event(event)
            if result == "new":
                self.deck_builder_screen = DeckBuilderScreen(self.screen, self.fonts)
                self.state = "deck_builder"
            elif result == "play":
                self.selected_player_deck_name = self.deck_list_screen.selected_player_deck
                self.selected_ai_deck_name = self.deck_list_screen.selected_ai_deck
                self._start_game()
            elif result == "back":
                self.state = "menu"

        elif self.state == "deck_builder" and self.deck_builder_screen:
            result = self.deck_builder_screen.handle_event(event)
            if result == "saved":
                self.deck_list_screen = DeckListScreen(self.screen, self.fonts)
                self.state = "deck_list"
            elif result == "back":
                self.state = "deck_list"

        elif self.state == "game" and self.game_screen:
            result = self.game_screen.handle_event(event)
            if result == "menu":
                self.state = "menu"

        elif self.state == "game_over" and self.game_over_screen:
            result = self.game_over_screen.handle_event(event)
            if result == "restart":
                self._start_game()
            elif result == "menu":
                self.state = "menu"

    # ------------------------------------------------------------------
    # Iniciar partida
    # ------------------------------------------------------------------

    def _start_game(self):
        from core.game_core import Player, Game
        from copy import copy

        player_deck = self.deck_manager.load_deck(self.selected_player_deck_name)
        ai_deck = self.deck_manager.load_deck(self.selected_ai_deck_name)
        if not player_deck or not ai_deck:
            return

        player = Player("Jugador")
        opponent = Player("IA")
        player.library = [copy(c) for c in player_deck.cards]
        opponent.library = [copy(c) for c in ai_deck.cards]
        player.shuffle_library()
        opponent.shuffle_library()

        game = Game(player, opponent)
        player.draw_card(7)
        opponent.draw_card(7)

        self.game_screen = GameScreen(self.screen, self.fonts, game)
        self.state = "game"

    # ------------------------------------------------------------------
    # Update / Render
    # ------------------------------------------------------------------

    def _update(self, dt):
        if self.state == "game" and self.game_screen:
            winner, loser = self.game_screen.update(dt)
            if loser:
                self.game_over_screen = GameOverScreen(self.screen, self.fonts, winner, loser)
                self.state = "game_over"

    def _render(self):
        if self.state == "menu":
            self.menu_screen.render()
        elif self.state == "deck_list" and self.deck_list_screen:
            self.deck_list_screen.render()
        elif self.state == "deck_builder" and self.deck_builder_screen:
            self.deck_builder_screen.render()
        elif self.state == "game" and self.game_screen:
            self.game_screen.render()
        elif self.state == "game_over" and self.game_over_screen:
            if self.game_screen:
                self.game_screen.render()
            self.game_over_screen.render()


if __name__ == "__main__":
    MTGSimulator().run()
