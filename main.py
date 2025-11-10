import pygame
import random
import time
from enum import Enum
from typing import Dict, Tuple, List, Optional


# --- Enums ---
class GameMode(Enum):
    MAIN_MENU = "main_menu"
    IN_GAME = "in_game"


class Difficulty(Enum):
    EASY = "Easy"
    NORMAL = "Normal"
    HARD = "Hard"


# --- Constants ---
class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (192, 192, 192)
    LIGHT_GRAY = (211, 211, 211)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)


class UIConstants:
    TILE_SIZE = 30
    PANEL_TOP_HEIGHT = 60
    PANEL_SIDES_WIDTH = 40
    PANEL_BOTTOM_HEIGHT = 60

    # Main menu constants
    MAIN_MENU_WIDTH = 500
    MAIN_MENU_HEIGHT = 500
    BUTTON_WIDTH = 150
    BUTTON_HEIGHT = 50
    BUTTON_SPACING = 60

    # Button dimensions
    GAME_BUTTON_WIDTH = 100
    GAME_BUTTON_HEIGHT = 40
    GAME_BUTTON_SPACING = 10


# --- Configuration ---
class GameConfig:
    DIFFICULTY_SETTINGS = {
        Difficulty.EASY: {"size": (12, 9), "mines": 10},
        Difficulty.NORMAL: {"size": (18, 14), "mines": 40},
        Difficulty.HARD: {"size": (32, 18), "mines": 99}
    }

    def __init__(self, difficulty: Difficulty):
        self.difficulty = difficulty
        self.update_settings()

    def update_settings(self):
        settings = self.DIFFICULTY_SETTINGS[self.difficulty]
        self.grid_width, self.grid_height = settings["size"]
        self.num_mines = settings["mines"]

        self.screen_width = (self.grid_width * UIConstants.TILE_SIZE +
                            2 * UIConstants.PANEL_SIDES_WIDTH)
        self.screen_height = (self.grid_height * UIConstants.TILE_SIZE +
                             UIConstants.PANEL_TOP_HEIGHT +
                             UIConstants.PANEL_BOTTOM_HEIGHT)

    def set_difficulty(self, difficulty: Difficulty):
        self.difficulty = difficulty
        self.update_settings()


# --- Board ---
class Board:
    def __init__(self, config: GameConfig):
        self.config = config
        self.grid: List[List[Dict]] = []
        self.create_board()

    def create_board(self):
        """Creates the game board."""
        self.grid = [[{
            'is_mine': False,
            'is_revealed': False,
            'is_flagged': False,
            'neighbor_mines': 0
        } for _ in range(self.config.grid_width)]
        for _ in range(self.config.grid_height)]

    def place_mines(self, first_click_pos: Tuple[int, int]):
        """Places mines randomly on the board, avoiding the first click area."""
        mines_placed = 0
        while mines_placed < self.config.num_mines:
            x = random.randint(0, self.config.grid_width - 1)
            y = random.randint(0, self.config.grid_height - 1)
            if (x, y) != first_click_pos and not self.grid[y][x]['is_mine']:
                self.grid[y][x]['is_mine'] = True
                mines_placed += 1

    def calculate_neighbor_mines(self):
        """Calculates the number of neighboring mines for each tile."""
        for y in range(self.config.grid_height):
            for x in range(self.config.grid_width):
                if not self.grid[y][x]['is_mine']:
                    count = 0
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            ny, nx = y + i, x + j
                            if (0 <= ny < self.config.grid_height and
                                0 <= nx < self.config.grid_width):
                                if self.grid[ny][nx]['is_mine']:
                                    count += 1
                    self.grid[y][x]['neighbor_mines'] = count

    def reveal_tile(self, x: int, y: int):
        """Reveals a tile and iteratively reveals neighbors if it's empty."""
        if not (0 <= x < self.config.grid_width and
                0 <= y < self.config.grid_height):
            return

        stack = [(x, y)]

        while stack:
            x, y = stack.pop()
            tile = self.grid[y][x]

            if tile['is_revealed'] or tile['is_flagged']:
                continue

            tile['is_revealed'] = True

            if tile['is_mine']:
                continue

            if tile['neighbor_mines'] == 0:
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if i == 0 and j == 0:
                            continue
                        nx, ny = x + j, y + i
                        if (0 <= nx < self.config.grid_width and
                            0 <= ny < self.config.grid_height):
                            if not self.grid[ny][nx]['is_revealed']:
                                stack.append((nx, ny))

    def reveal_all_mines(self):
        """Reveals all mines on the board."""
        for row in self.grid:
            for tile in row:
                if tile['is_mine']:
                    tile['is_revealed'] = True

    def toggle_flag(self, x: int, y: int) -> bool:
        """Toggles flag on a tile. Returns True if successful."""
        if (0 <= x < self.config.grid_width and
            0 <= y < self.config.grid_height):
            if not self.grid[y][x]['is_revealed']:
                self.grid[y][x]['is_flagged'] = not self.grid[y][x]['is_flagged']
                return True
        return False

    def check_victory(self) -> bool:
        """Checks if all non-mine tiles have been revealed."""
        for y in range(self.config.grid_height):
            for x in range(self.config.grid_width):
                tile = self.grid[y][x]
                if not tile['is_mine'] and not tile['is_revealed']:
                    return False
        return True

    def count_flags(self) -> int:
        """Counts the number of flags placed on the board."""
        return sum(tile['is_flagged'] for row in self.grid for tile in row)


# --- UI Renderer ---
class UIRenderer:
    def __init__(self, config: GameConfig):
        self.config = config
        self.font = pygame.font.Font(None, 36)
        self.tile_font = pygame.font.Font(None, UIConstants.TILE_SIZE)
        self.title_font = pygame.font.Font(None, 72)

        self.main_menu_button_rect: Optional[pygame.Rect] = None
        self.restart_button_rect: Optional[pygame.Rect] = None
        self.update_button_positions()

    def update_button_positions(self):
        """Calculates the positions of the game buttons."""
        total_button_width = (UIConstants.GAME_BUTTON_WIDTH * 2 +
                            UIConstants.GAME_BUTTON_SPACING)
        start_x = self.config.screen_width // 2 - total_button_width // 2
        button_y = (UIConstants.PANEL_TOP_HEIGHT +
                   self.config.grid_height * UIConstants.TILE_SIZE +
                   (UIConstants.PANEL_BOTTOM_HEIGHT - UIConstants.GAME_BUTTON_HEIGHT) // 2)

        self.main_menu_button_rect = pygame.Rect(
            start_x, button_y,
            UIConstants.GAME_BUTTON_WIDTH,
            UIConstants.GAME_BUTTON_HEIGHT
        )
        self.restart_button_rect = pygame.Rect(
            start_x + UIConstants.GAME_BUTTON_WIDTH + UIConstants.GAME_BUTTON_SPACING,
            button_y,
            UIConstants.GAME_BUTTON_WIDTH,
            UIConstants.GAME_BUTTON_HEIGHT
        )

    def get_difficulty_buttons(self, screen_width: int, screen_height: int) -> Dict[Difficulty, pygame.Rect]:
        """Creates difficulty button rectangles for main menu."""
        center_x = screen_width // 2
        center_y = screen_height // 2

        return {
            Difficulty.EASY: pygame.Rect(
                center_x - UIConstants.BUTTON_WIDTH // 2,
                center_y,
                UIConstants.BUTTON_WIDTH,
                UIConstants.BUTTON_HEIGHT
            ),
            Difficulty.NORMAL: pygame.Rect(
                center_x - UIConstants.BUTTON_WIDTH // 2,
                center_y + UIConstants.BUTTON_SPACING,
                UIConstants.BUTTON_WIDTH,
                UIConstants.BUTTON_HEIGHT
            ),
            Difficulty.HARD: pygame.Rect(
                center_x - UIConstants.BUTTON_WIDTH // 2,
                center_y + UIConstants.BUTTON_SPACING * 2,
                UIConstants.BUTTON_WIDTH,
                UIConstants.BUTTON_HEIGHT
            )
        }

    def draw_main_menu(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Draws the main menu."""
        screen.fill(Colors.WHITE)

        # Title
        title_text = self.title_font.render("Minesweeper", True, Colors.BLACK)
        screen.blit(title_text, (
            screen_width // 2 - title_text.get_width() // 2,
            screen_height // 4
        ))

        # Difficulty buttons
        buttons = self.get_difficulty_buttons(screen_width, screen_height)

        for difficulty, button_rect in buttons.items():
            pygame.draw.rect(screen, Colors.LIGHT_GRAY, button_rect)
            text = self.font.render(difficulty.value, True, Colors.BLACK)
            text_rect = text.get_rect(center=button_rect.center)
            screen.blit(text, text_rect)

    def draw_board(self, screen: pygame.Surface, board: Board):
        """Draws the game board."""
        board_start_x = UIConstants.PANEL_SIDES_WIDTH
        board_start_y = UIConstants.PANEL_TOP_HEIGHT

        for y in range(self.config.grid_height):
            for x in range(self.config.grid_width):
                rect = pygame.Rect(
                    board_start_x + x * UIConstants.TILE_SIZE,
                    board_start_y + y * UIConstants.TILE_SIZE,
                    UIConstants.TILE_SIZE,
                    UIConstants.TILE_SIZE
                )

                tile = board.grid[y][x]

                if tile['is_revealed']:
                    pygame.draw.rect(screen, Colors.LIGHT_GRAY, rect)
                    if tile['is_mine']:
                        pygame.draw.ellipse(screen, Colors.RED, rect)
                    elif tile['neighbor_mines'] > 0:
                        text = self.tile_font.render(
                            str(tile['neighbor_mines']),
                            True,
                            Colors.BLACK
                        )
                        screen.blit(text, (
                            rect.x + (UIConstants.TILE_SIZE - text.get_width()) // 2,
                            rect.y + (UIConstants.TILE_SIZE - text.get_height()) // 2
                        ))
                else:
                    # Draw 3D-like button for unrevealed tiles
                    pygame.draw.rect(screen, Colors.GRAY, rect)
                    pygame.draw.line(screen, Colors.WHITE,
                                   (rect.left, rect.top),
                                   (rect.right - 1, rect.top), 2)
                    pygame.draw.line(screen, Colors.WHITE,
                                   (rect.left, rect.top),
                                   (rect.left, rect.bottom - 1), 2)
                    pygame.draw.line(screen, Colors.BLACK,
                                   (rect.left, rect.bottom - 1),
                                   (rect.right - 1, rect.bottom - 1), 2)
                    pygame.draw.line(screen, Colors.BLACK,
                                   (rect.right - 1, rect.top),
                                   (rect.right - 1, rect.bottom - 1), 2)

                    if tile['is_flagged']:
                        flag_text = self.tile_font.render('F', True, Colors.BLUE)
                        screen.blit(flag_text, (
                            rect.x + (UIConstants.TILE_SIZE - flag_text.get_width()) // 2,
                            rect.y + (UIConstants.TILE_SIZE - flag_text.get_height()) // 2
                        ))

        # Draw grid lines
        for i in range(self.config.grid_width + 1):
            pygame.draw.line(
                screen, Colors.BLACK,
                (board_start_x + i * UIConstants.TILE_SIZE, board_start_y),
                (board_start_x + i * UIConstants.TILE_SIZE,
                 board_start_y + self.config.grid_height * UIConstants.TILE_SIZE)
            )
        for i in range(self.config.grid_height + 1):
            pygame.draw.line(
                screen, Colors.BLACK,
                (board_start_x, board_start_y + i * UIConstants.TILE_SIZE),
                (board_start_x + self.config.grid_width * UIConstants.TILE_SIZE,
                 board_start_y + i * UIConstants.TILE_SIZE)
            )

    def draw_ui_frame(self, screen: pygame.Surface, elapsed_time: float, mines_left: int):
        """Draws the UI frame around the game board."""
        # Draw panels
        pygame.draw.rect(screen, Colors.GRAY,
                        (0, 0, self.config.screen_width, UIConstants.PANEL_TOP_HEIGHT))
        pygame.draw.rect(screen, Colors.GRAY,
                        (0, UIConstants.PANEL_TOP_HEIGHT + self.config.grid_height * UIConstants.TILE_SIZE,
                         self.config.screen_width, UIConstants.PANEL_BOTTOM_HEIGHT))
        pygame.draw.rect(screen, Colors.GRAY,
                        (0, UIConstants.PANEL_TOP_HEIGHT,
                         UIConstants.PANEL_SIDES_WIDTH,
                         self.config.grid_height * UIConstants.TILE_SIZE))
        pygame.draw.rect(screen, Colors.GRAY,
                        (UIConstants.PANEL_SIDES_WIDTH + self.config.grid_width * UIConstants.TILE_SIZE,
                         UIConstants.PANEL_TOP_HEIGHT,
                         UIConstants.PANEL_SIDES_WIDTH,
                         self.config.grid_height * UIConstants.TILE_SIZE))

        # Draw timer
        timer_text = self.font.render(f"Time: {int(elapsed_time)}", True, Colors.BLACK)
        screen.blit(timer_text, (10, 10))

        # Draw mines left
        mines_text = self.font.render(f"Mines: {mines_left}", True, Colors.BLACK)
        screen.blit(mines_text, (self.config.screen_width - mines_text.get_width() - 10, 10))

        # Draw buttons
        pygame.draw.rect(screen, Colors.LIGHT_GRAY, self.main_menu_button_rect)
        main_menu_text = self.font.render("Menu", True, Colors.BLACK)
        text_rect = main_menu_text.get_rect(center=self.main_menu_button_rect.center)
        screen.blit(main_menu_text, text_rect)

        pygame.draw.rect(screen, Colors.LIGHT_GRAY, self.restart_button_rect)
        restart_text = self.font.render("Restart", True, Colors.BLACK)
        text_rect = restart_text.get_rect(center=self.restart_button_rect.center)
        screen.blit(restart_text, text_rect)

    def draw_game_over(self, screen: pygame.Surface):
        """Draws game over message."""
        text = self.font.render("Game Over", True, Colors.RED)
        text_rect = text.get_rect(center=(
            self.config.screen_width // 2,
            UIConstants.PANEL_TOP_HEIGHT + (self.config.grid_height * UIConstants.TILE_SIZE) // 2
        ))
        screen.blit(text, text_rect)

    def draw_victory(self, screen: pygame.Surface):
        """Draws victory message."""
        text = self.font.render("You Win!", True, Colors.BLUE)
        text_rect = text.get_rect(center=(
            self.config.screen_width // 2,
            UIConstants.PANEL_TOP_HEIGHT + (self.config.grid_height * UIConstants.TILE_SIZE) // 2
        ))
        screen.blit(text, text_rect)


# --- Sound Manager ---
class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.main_menu_sound: Optional[pygame.mixer.Sound] = None
        self.play_sound: Optional[pygame.mixer.Sound] = None
        self.current_playing: Optional[pygame.mixer.Sound] = None
        self.load_sounds()

    def load_sounds(self):
        """Loads sound files with error handling."""
        try:
            self.main_menu_sound = pygame.mixer.Sound('sound/VC-Minesweeper_MainMenu.mp3')
        except (pygame.error, FileNotFoundError) as e:
            print(f"Warning: Could not load main menu sound: {e}")
            self.main_menu_sound = None

        try:
            self.play_sound = pygame.mixer.Sound('sound/VC-Minesweeper_Play.mp3')
        except (pygame.error, FileNotFoundError) as e:
            print(f"Warning: Could not load play sound: {e}")
            self.play_sound = None

    def play_main_menu_music(self):
        """Plays main menu music."""
        if self.main_menu_sound:
            self.stop_all()
            self.main_menu_sound.play(-1)
            self.current_playing = self.main_menu_sound

    def play_game_music(self):
        """Plays game music."""
        if self.play_sound:
            self.stop_all()
            self.play_sound.play(-1)
            self.current_playing = self.play_sound

    def stop_all(self):
        """Stops all sounds."""
        if self.main_menu_sound:
            self.main_menu_sound.stop()
        if self.play_sound:
            self.play_sound.stop()
        self.current_playing = None


# --- Game State ---
class GameState:
    def __init__(self, config: GameConfig):
        self.config = config
        self.board = Board(config)
        self.first_click = True
        self.game_over = False
        self.game_won = False
        self.start_time = 0

    def reset(self):
        """Resets the game state."""
        self.board = Board(self.config)
        self.first_click = True
        self.game_over = False
        self.game_won = False
        self.start_time = 0

    def handle_first_click(self, x: int, y: int):
        """Handles the first click by placing mines and calculating neighbors."""
        if self.first_click:
            self.start_time = time.time()
            self.board.place_mines((x, y))
            self.board.calculate_neighbor_mines()
            self.first_click = False

    def get_elapsed_time(self) -> float:
        """Returns elapsed time since game start."""
        if self.start_time > 0 and not self.game_over and not self.game_won:
            return time.time() - self.start_time
        return 0

    def get_mines_left(self) -> int:
        """Returns number of mines left (total mines - flags placed)."""
        return self.config.num_mines - self.board.count_flags()


# --- Main Game ---
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Minesweeper")

        self.config = GameConfig(Difficulty.EASY)
        self.game_mode = GameMode.MAIN_MENU
        self.game_state: Optional[GameState] = None
        self.ui_renderer = UIRenderer(self.config)
        self.sound_manager = SoundManager()

        # Set initial screen for main menu
        self.screen = pygame.display.set_mode(
            (UIConstants.MAIN_MENU_WIDTH, UIConstants.MAIN_MENU_HEIGHT),
            pygame.RESIZABLE
        )

        self.clock = pygame.time.Clock()
        self.running = False

    def start_game(self, difficulty: Difficulty):
        """Starts a new game with the specified difficulty."""
        self.config.set_difficulty(difficulty)
        self.ui_renderer = UIRenderer(self.config)
        self.game_state = GameState(self.config)
        self.game_mode = GameMode.IN_GAME

        self.screen = pygame.display.set_mode(
            (self.config.screen_width, self.config.screen_height),
            pygame.RESIZABLE
        )

        self.sound_manager.play_game_music()

    def return_to_menu(self):
        """Returns to the main menu."""
        self.game_mode = GameMode.MAIN_MENU
        self.game_state = None

        self.screen = pygame.display.set_mode(
            (UIConstants.MAIN_MENU_WIDTH, UIConstants.MAIN_MENU_HEIGHT),
            pygame.RESIZABLE
        )

        self.sound_manager.play_main_menu_music()

    def restart_game(self):
        """Restarts the current game."""
        if self.game_state:
            self.game_state.reset()

    def handle_main_menu_events(self, event: pygame.event.Event):
        """Handles events in the main menu."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            buttons = self.ui_renderer.get_difficulty_buttons(
                self.screen.get_width(),
                self.screen.get_height()
            )

            for difficulty, button_rect in buttons.items():
                if button_rect.collidepoint(pos):
                    self.start_game(difficulty)
                    return

    def handle_game_events(self, event: pygame.event.Event):
        """Handles events during gameplay."""
        if not self.game_state:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()

            # Check UI buttons
            if event.button == 1:
                if self.ui_renderer.main_menu_button_rect.collidepoint(pos):
                    self.return_to_menu()
                    return

                if self.ui_renderer.restart_button_rect.collidepoint(pos):
                    self.restart_game()
                    return

            # Handle game board clicks
            if not self.game_state.game_over and not self.game_state.game_won:
                x = (pos[0] - UIConstants.PANEL_SIDES_WIDTH) // UIConstants.TILE_SIZE
                y = (pos[1] - UIConstants.PANEL_TOP_HEIGHT) // UIConstants.TILE_SIZE

                if (0 <= x < self.config.grid_width and
                    0 <= y < self.config.grid_height):

                    if event.button == 1:  # Left click
                        self.game_state.handle_first_click(x, y)
                        self.game_state.board.reveal_tile(x, y)

                        tile = self.game_state.board.grid[y][x]
                        if tile['is_mine'] and not tile['is_flagged']:
                            self.game_state.game_over = True
                            self.game_state.board.reveal_all_mines()

                    elif event.button == 3:  # Right click
                        self.game_state.board.toggle_flag(x, y)

    def handle_events(self):
        """Handles all game events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (event.w, event.h),
                    pygame.RESIZABLE
                )
                if self.game_mode == GameMode.IN_GAME:
                    self.ui_renderer.update_button_positions()

            elif self.game_mode == GameMode.MAIN_MENU:
                self.handle_main_menu_events(event)

            elif self.game_mode == GameMode.IN_GAME:
                self.handle_game_events(event)

    def update(self):
        """Updates game logic."""
        if self.game_mode == GameMode.IN_GAME and self.game_state:
            if (not self.game_state.game_over and
                not self.game_state.first_click and
                not self.game_state.game_won):
                if self.game_state.board.check_victory():
                    self.game_state.game_won = True

    def render(self):
        """Renders the game."""
        self.screen.fill(Colors.WHITE)

        if self.game_mode == GameMode.MAIN_MENU:
            self.ui_renderer.draw_main_menu(
                self.screen,
                self.screen.get_width(),
                self.screen.get_height()
            )

        elif self.game_mode == GameMode.IN_GAME and self.game_state:
            elapsed_time = self.game_state.get_elapsed_time()
            mines_left = self.game_state.get_mines_left()

            self.ui_renderer.draw_ui_frame(self.screen, elapsed_time, mines_left)
            self.ui_renderer.draw_board(self.screen, self.game_state.board)

            if self.game_state.game_over:
                self.ui_renderer.draw_game_over(self.screen)
            elif self.game_state.game_won:
                self.ui_renderer.draw_victory(self.screen)

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        self.running = True
        self.sound_manager.play_main_menu_music()

        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)

        self.sound_manager.stop_all()
        pygame.quit()


# --- Entry Point ---
def main():
    """Entry point for the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
