import pygame
from pygame.locals import *
import random
import math
import sys
import os # Added for path joining

# --- Constants ---
# Screen Dimensions
GAME_WIDTH = 800
GAME_HEIGHT = 432
SIZE = (GAME_WIDTH, GAME_HEIGHT)
screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
FPS = 60

# Colors (Consider using pygame.Color objects for more features)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)
SKY_BLUE = (135, 206, 235) # Fallback sky color

# Player Settings
PLAYER_START_X = 25
PLAYER_HEIGHT = 150
PLAYER_START_HEALTH = 3
PLAYER_JUMP_VELOCITY = -4 # Using negative for upward movement
PLAYER_GRAVITY = 0.2 # Simplified gravity/landing effect
PLAYER_LAND_Y = GAME_HEIGHT - PLAYER_HEIGHT
PLAYER_ANIMATION_SPEED = 0.2
PLAYER_INVINCIBILITY_DURATION = 60 # In frames

# Obstacle Settings
OBSTACLE_SCALE_WIDTH = 50 # Scale obstacles to this width
OBSTACLE_TYPES = ['rock1', 'rock2', 'rock3', 'spikes']
OBSTACLE_SPAWN_OFFSET_MIN = 0
OBSTACLE_SPAWN_OFFSET_MAX = 200

# Game Settings
STARTING_SPEED = 5
MAX_SPEED = 13
SPEED_INCREASE_INTERVAL = 4 # Increase speed every N points
SPEED_INCREASE_AMOUNT = 0.4
SCORE_POS_RIGHT_MARGIN = 15
SCORE_POS_TOP_MARGIN = 15
HEALTH_POS_LEFT_MARGIN = 10
HEALTH_POS_TOP_MARGIN = 10
HEALTH_HEART_SPACING = 5
HEART_ANIMATION_SPEED = 0.1


BOX_PADDING_X = 30 # Horizontal padding inside the box
BOX_PADDING_Y = 20 # Vertical padding inside the box
BUTTON_SPACING_Y = 10 # Vertical space between buttons

# Font Sizes
MENU_FONT_SIZE = 40
BUTTON_FONT_SIZE = 30
SCORE_FONT_SIZE = 24
# INFO_FONT_SIZE = 16 # Not currently used, can remove or keep for future

# File Paths (using os.path.join for compatibility)
IMAGE_DIR = 'images'
SOUND_DIR = 'sounds'
BG_DIR = os.path.join(IMAGE_DIR, 'background')
RUNNING_DIR = os.path.join(IMAGE_DIR, 'running')
JUMPING_DIR = os.path.join(IMAGE_DIR, 'jumping')
OBSTACLE_DIR = os.path.join(IMAGE_DIR, 'obstacles')
HEART_DIR = os.path.join(IMAGE_DIR, 'heart')

# Game States
STATE_MAIN_MENU = 'MAIN_MENU'
STATE_PLAYING = 'PLAYING'
STATE_PAUSED = 'PAUSED'
STATE_INSTRUCTIONS = 'INSTRUCTIONS'
STATE_SETTINGS = 'SETTINGS'
STATE_GAME_OVER = 'GAME_OVER'

# --- Pygame Initialization ---
pygame.init()
game = pygame.display.set_mode(SIZE)
pygame.display.set_caption('Endless Runner')
clock = pygame.time.Clock()

# --- ADD MIXER INITIALIZATION ---
try:
    pygame.mixer.init() # Initialize the mixer
    print("Mixer initialized successfully.")
except pygame.error as e:
    print(f"Error initializing mixer: {e}. Audio may not work.")
    # Optionally disable audio features if init fails
# --- END ADDITION ---

# --- Font Loading ---
# It's good practice to check if font loading succeeds
# Replace the existing font loading code with:
try:
    menu_font = pygame.font.Font('fonts/upheavtt.ttf', MENU_FONT_SIZE)
    button_font = pygame.font.Font('fonts/upheavtt.ttf', BUTTON_FONT_SIZE)
    score_font = pygame.font.Font('fonts/upheavtt.ttf', SCORE_FONT_SIZE)
except pygame.error as e:
    print(f"Error loading custom fonts: {e}. Using system fonts.")
    # Fallback to system fonts
    menu_font = pygame.font.SysFont(None, MENU_FONT_SIZE)
    button_font = pygame.font.SysFont(None, BUTTON_FONT_SIZE)
    score_font = pygame.font.SysFont(None, SCORE_FONT_SIZE)

# --- ADD MUSIC LOADING ---
try:
    music_path = os.path.join(SOUND_DIR, 'Soundtrack.mp3')
    pygame.mixer.music.load(music_path)
    print(f"Loaded music: {music_path}")
    # Set initial volume (optional, 0.0 to 1.0)
    pygame.mixer.music.set_volume(0.7)
except pygame.error as e:
    print(f"Error loading music '{music_path}': {e}")
    # Handle music loading failure (e.g., disable music playback)
# --- END ADDITION ---

# --- Helper Functions ---
def load_scaled_image(path, target_height=None, target_width=None, use_alpha=True):
    """Loads an image, scales it, and handles errors."""
    try:
        image = pygame.image.load(path)
        if use_alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()

        if target_height:
            scale = target_height / image.get_height()
            new_width = image.get_width() * scale
            new_height = image.get_height() * scale
            image = pygame.transform.scale(image, (new_width, new_height))
        elif target_width:
            scale = target_width / image.get_width()
            new_width = image.get_width() * scale
            new_height = image.get_height() * scale
            image = pygame.transform.scale(image, (new_width, new_height))
        # Can add scaling based on both width and height if needed

        return image
    except pygame.error as e:
        print(f"Error loading or scaling image: {path} - {e}")
        # Return a placeholder surface on error
        fallback_size = (50, 50) # Default placeholder size
        if target_height: fallback_size = (50, target_height)
        if target_width: fallback_size = (target_width, 50) # Prioritize width if both given
        placeholder = pygame.Surface(fallback_size)
        placeholder.fill(RED)
        return placeholder

def load_animation_frames(directory, num_frames, target_height):
    """Loads a sequence of animation frames."""
    frames = []
    for i in range(num_frames):
        filename = f'run{i}.png' if 'running' in directory else f'jump{i}.png' if 'jumping' in directory else f'heart{i}.png'
        path = os.path.join(directory, filename)
        frames.append(load_scaled_image(path, target_height=target_height))
    return frames

def draw_text(text, font, color, surface, x, y, center=True, border_color=None):
    """Draws text with optional border onto a surface."""
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    if center:
        textrect.center = (x, y)
    else:
        textrect.topleft = (x, y)

    if border_color:
        # Offsets for a 1-pixel outline
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            border_text = font.render(text, True, border_color)
            border_rect = border_text.get_rect(center=textrect.center)
            surface.blit(border_text, (border_rect.x + dx, border_rect.y + dy))

    surface.blit(textobj, textrect)


# --- Asset Loading ---
# Moved asset loading here to ensure they are loaded before being used
# Backgrounds
try:
    sky_image = load_scaled_image(os.path.join(BG_DIR, 'plx-1.png'), use_alpha=False) # Sky usually doesn't need alpha
    # Scale sky to exact game width if tiling isn't perfect
    sky_image = pygame.transform.scale(sky_image, (GAME_WIDTH, GAME_HEIGHT))

    ground_image = pygame.image.load(os.path.join(BG_DIR, "ground.png")).convert_alpha()
    ground_height = ground_image.get_height()

    background_layers = [
        load_scaled_image(os.path.join(BG_DIR, 'plx-2.png'), target_height=GAME_HEIGHT),
        load_scaled_image(os.path.join(BG_DIR, 'plx-3.png'), target_height=GAME_HEIGHT),
        load_scaled_image(os.path.join(BG_DIR, 'plx-4.png'), target_height=GAME_HEIGHT),
        load_scaled_image(os.path.join(BG_DIR, 'plx-5.png'), target_height=GAME_HEIGHT)
    ]

    # Calculate tiles needed (only if sky isn't scaled to full width)
    # num_bg_tiles = math.ceil(GAME_WIDTH / sky_image.get_width()) + 1 if sky_image.get_width() < GAME_WIDTH else 1
    num_bg_tiles = 1 # Since we scale sky to full width now

except Exception as e: # Catch broader exceptions during loading sequence
    print(f"Error during background asset loading: {e}")
    sky_image = pygame.Surface(SIZE)
    sky_image.fill(SKY_BLUE)
    background_layers = []
    num_bg_tiles = 1

# Hearts
try:
    heart_sprites = load_animation_frames(HEART_DIR, 8, target_height=30)
except Exception as e:
    print(f"Error during heart asset loading: {e}")
    heart_sprites = [] # Indicate failure

# Obstacle Images (Loaded within the Obstacle class __init__)


# --- Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.height = PLAYER_HEIGHT
        self.x = PLAYER_START_X
        self.y = PLAYER_LAND_Y
        self.action = 'running' # Initial action
        self.health = PLAYER_START_HEALTH
        self.invincibility_frame = 0
        self.vel_y = 0 # Vertical velocity for jumping/gravity

        # Load animations
        try:
            self.running_sprites = load_animation_frames(RUNNING_DIR, 8, self.height)
            self.jumping_sprites = load_animation_frames(JUMPING_DIR, 8, self.height)
        except Exception as e:
             print(f"FATAL: Could not load player sprites: {e}")
             # Potentially exit or handle more gracefully if player sprites missing
             self.running_sprites = []
             self.jumping_sprites = []
             # Create dummy sprites to avoid crashes later
             dummy_surf = pygame.Surface((50, self.height)); dummy_surf.fill(RED)
             self.running_sprites.append(dummy_surf)
             self.jumping_sprites.append(dummy_surf)


        self.running_sprite_index = 0
        self.jumping_sprite_index = 0

        # Initial sprite setup
        self.current_sprite_list = self.running_sprites
        self.current_sprite_index = self.running_sprite_index
        self.image = self.current_sprite_list[0]
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, surface):
        """Draws the player with invincibility effect."""
        if not self.current_sprite_list: return # Don't draw if no sprites

        index = int(self.current_sprite_index)
        # Ensure index is within bounds (shouldn't be needed with modulo, but safe)
        index = max(0, min(index, len(self.current_sprite_list) - 1))
        sprite_to_draw = self.current_sprite_list[index]

        if self.invincibility_frame > 0:
            if self.invincibility_frame % 10 < 5: # Flash effect
                surface.blit(sprite_to_draw, self.rect.topleft)
        else:
            surface.blit(sprite_to_draw, self.rect.topleft)

    def update(self, dt): # Pass delta time for frame-independent updates
        """Updates player animation and position (jump/gravity)."""
        if not self.running_sprites or not self.jumping_sprites: return # Skip update if sprites failed

        # --- Handle Jumping and Gravity ---
        if self.action == 'jumping':
            self.y += self.vel_y
            self.vel_y += PLAYER_GRAVITY # Apply gravity
            # Transition to landing (can be smoother)
            if self.vel_y >= 0: # If starting to fall
                 # Optional: Could change sprite set here if you had falling sprites
                 pass # Keep jump sprites for now
            # Check for landing
            if self.y >= PLAYER_LAND_Y:
                self.y = PLAYER_LAND_Y
                self.action = 'running'
                self.vel_y = 0
        elif self.action == 'running':
             # Ensure player stays on the ground if somehow slightly above
             if self.y < PLAYER_LAND_Y:
                  self.y = PLAYER_LAND_Y # Snap to ground


        # --- Handle Animation ---
        if self.action == 'running':
            self.current_sprite_list = self.running_sprites
            self.running_sprite_index = (self.running_sprite_index + PLAYER_ANIMATION_SPEED) % len(self.running_sprites)
            self.current_sprite_index = self.running_sprite_index
        elif self.action == 'jumping':
            self.current_sprite_list = self.jumping_sprites
            # Simple jump animation: cycle through, could freeze on peak/fall later
            self.jumping_sprite_index = (self.jumping_sprite_index + PLAYER_ANIMATION_SPEED) % len(self.jumping_sprites)
            self.current_sprite_index = self.jumping_sprite_index

        # Update image, rect, and mask
        index = int(self.current_sprite_index)
        index = max(0, min(index, len(self.current_sprite_list) - 1))
        self.image = self.current_sprite_list[index]
        # self.rect = self.image.get_rect(topleft=(self.x, self.y)) # Update rect position
        self.rect.topleft = (self.x, self.y) # More efficient rect update
        self.mask = pygame.mask.from_surface(self.image)

        # Update invincibility timer
        if self.invincibility_frame > 0:
            self.invincibility_frame -= 1


    def jump(self):
        """Initiates the player jump."""
        if self.action == 'running': # Only jump if on the ground
            self.action = 'jumping'
            self.vel_y = PLAYER_JUMP_VELOCITY # Apply upward velocity
            self.jumping_sprite_index = 0 # Reset jump animation

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, game_speed):
        pygame.sprite.Sprite.__init__(self)
        self.obstacle_images = self._load_obstacle_images()

        if not self.obstacle_images: # Handle case where no images loaded
             placeholder = pygame.Surface((OBSTACLE_SCALE_WIDTH, 50)); placeholder.fill(RED)
             self.obstacle_images.append(placeholder)

        self.image = random.choice(self.obstacle_images)
        self.game_speed = game_speed
        self.x = GAME_WIDTH # Start off-screen right
        self.y = GAME_HEIGHT - self.image.get_height() # Position on ground
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.image)


    def _load_obstacle_images(self):
        """Loads and scales obstacle images."""
        images = []
        for image_name in OBSTACLE_TYPES:
            path = os.path.join(OBSTACLE_DIR, f'{image_name}.png')
            # Scale based on width, keeping aspect ratio
            img = load_scaled_image(path, target_width=OBSTACLE_SCALE_WIDTH)
            if img: # Check if loading was successful
                images.append(img)
        return images

    def draw(self, surface):
        """Draws the obstacle."""
        surface.blit(self.image, self.rect.topleft)

    def update(self, dt): # Pass delta time
        """Moves the obstacle left based on game speed."""
        # self.x -= self.game_speed # Frame-dependent movement
        self.x -= (self.game_speed * 0.5) * dt * FPS # Frame-independent movement (approx) - 04/23
        self.rect.x = int(self.x) # Update rect position

    def reset(self, game_speed):
        """Resets the obstacle to the right with a new image and speed."""
        self.image = random.choice(self.obstacle_images)
        self.x = GAME_WIDTH + random.randint(OBSTACLE_SPAWN_OFFSET_MIN, OBSTACLE_SPAWN_OFFSET_MAX)
        self.y = GAME_HEIGHT - self.image.get_height()
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.image)
        self.game_speed = game_speed # Update speed


# --- Game State Variables ---
# These are managed globally or passed around; could be encapsulated in a Game class later
game_state = STATE_MAIN_MENU
score = 0
speed = 0
parallax_offsets = [0] * len(background_layers)
heart_sprite_index = 0

# Game Objects (initialized in reset_game)
player = None
obstacles_group = None
obstacle = None

# --- Game Logic Functions ---
def reset_game():
    """Resets all variables for a new game."""
    global player, obstacles_group, obstacle, score, speed, parallax_offsets, heart_sprite_index
    score = 0
    speed = STARTING_SPEED
    player = Player()
    obstacles_group = pygame.sprite.Group()
    obstacle = Obstacle(speed)
    obstacles_group.add(obstacle)
    parallax_offsets = [0] * len(background_layers) # Reset parallax scroll
    heart_sprite_index = 0
    # Ensure player's invincibility is reset if applicable
    player.invincibility_frame = 0


# Define game variables
scroll = 0
ground_image = pygame.image.load(os.path.join(BG_DIR, "ground.png")).convert_alpha()
ground_width = ground_image.get_width()
ground_height = ground_image.get_height()


def draw_ground(surface, ground_img):
    surface.blit(ground_img, (0, GAME_HEIGHT - ground_height))


def draw_layered_background(surface, sky, layers, offsets, num_tiles):
    """Draws the sky and parallax layers."""
    # Draw Sky (assuming it's scaled to screen width)
    surface.blit(sky, (0, 0))

    # Draw Parallax Layers
    for i in range(len(layers)):
        if i < len(offsets): # Check index validity
            layer = layers[i]
            offset = offsets[i]
            pos_y = GAME_HEIGHT - layer.get_height()
            # Tile layer horizontally
            layer_width = layer.get_width()
            start_x = int(offset % layer_width) - layer_width
            for j in range(num_tiles + 2):  # +2 to ensure full coverage
                pos_x = start_x + j * layer_width
                surface.blit(layer, (pos_x, pos_y))



def update_parallax(offsets, layers, current_speed, dt):
    new_offsets = []
    for i in range(len(layers)):
        if i < len(offsets):
            scroll_amount = (i + 10) * current_speed * 3 * dt
            layer_width = layers[i].get_width()
            new_offset = offsets[i] - scroll_amount

            # Ensure seamless wrap-around in negative direction
            if new_offset <= -layer_width:
                new_offset += layer_width

            new_offsets.append(new_offset)
        else:
            new_offsets.append(0)
    return new_offsets




# --- Menu Drawing Functions ---
def draw_menu_background(surface):
    """Helper function to draw the static layered background for menus."""
    draw_layered_background(surface, sky_image, background_layers, [0]*len(background_layers), num_bg_tiles)

def draw_main_menu(surface):
    """Draws the main menu and its buttons."""
    draw_menu_background(surface)
    draw_text('Endless Runner', menu_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 4)

    # Define buttons (consider a Button class later for more complex menus)
    button_rects = {
        "start": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 - 30, 200, 50),
        "instructions": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 + 30, 200, 50),
        "settings": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 + 90, 200, 50),
        "quit": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 + 150, 200, 50)
    }
    button_texts = {
        "start": "Start Game", "instructions": "Instructions",
        "settings": "Settings", "quit": "Quit"
    }

    # Draw buttons
    for name, rect in button_rects.items():
        pygame.draw.rect(surface, LIGHT_GRAY, rect)
        draw_text(button_texts[name], button_font, WHITE, surface, rect.centerx, rect.centery)

    return button_rects


def draw_pause_menu(surface):
    """Draws the pause menu with a dynamically sized background box."""
    draw_menu_background(surface) # Draw the main background first

    # --- Dynamic Box Calculation ---
    title_text = 'Paused'
    button_texts_list = ["Resume", "Main Menu", "Quit"]
    button_height = 50 # Assuming standard button height
    num_buttons = len(button_texts_list)

    # Calculate content height
    title_height = menu_font.get_height()
    buttons_total_height = num_buttons * button_height + (num_buttons - 1) * BUTTON_SPACING_Y
    content_height = title_height + buttons_total_height + BOX_PADDING_Y * 3 # Padding: top, between title/buttons, bottom

    # Calculate box dimensions (width can still be fixed or dynamic)
    box_width = GAME_WIDTH * 0.6 # Keep width fixed for now
    box_height = content_height
    box_x = (GAME_WIDTH - box_width) / 2
    box_y = (GAME_HEIGHT - box_height) / 2 # Center vertically

    # Create and draw the box
    menu_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    menu_box.fill((0, 0, 0, 130)) # Slightly adjusted alpha perhaps
    surface.blit(menu_box, (box_x, box_y))
    # --- End Dynamic Calculation ---

    # Position title and buttons relative to the box top/center
    title_y = box_y + BOX_PADDING_Y
    draw_text(title_text, menu_font, WHITE, surface, GAME_WIDTH / 2, title_y + title_height / 2) # Center text vertically

    # Define button rects based on calculated positions
    button_rects = {}
    current_button_y = title_y + title_height + BOX_PADDING_Y # Start buttons below title + padding
    button_x = GAME_WIDTH / 2 - 100 # Keep buttons centered horizontally

    # Create mapping for keys used in the main loop logic
    button_keys = ["resume", "menu", "quit"]

    for i, text in enumerate(button_texts_list):
        key = button_keys[i]
        rect = pygame.Rect(button_x, current_button_y, 200, button_height)
        button_rects[key] = rect
        pygame.draw.rect(surface, WHITE, rect)
        draw_text(text, button_font, WHITE, surface, rect.centerx, rect.centery)
        current_button_y += button_height + BUTTON_SPACING_Y # Move down for next button

    return button_rects # Return the dict expected by the main loop


def draw_instructions_screen(surface):
    """Draws the instructions screen."""
    draw_menu_background(surface)

    # Semi-transparent box for text
    text_box = pygame.Surface((GAME_WIDTH * 0.8, GAME_HEIGHT * 0.5), pygame.SRCALPHA)
    text_box.fill((0, 0, 0, 120))
    surface.blit(text_box, (GAME_WIDTH * 0.1, GAME_HEIGHT / 4 - 20))

    draw_text('Instructions', menu_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 4, border_color=BLACK)
    draw_text('Press SPACE to jump over obstacles.', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2 - 40, border_color=BLACK)
    draw_text('Avoid rocks and spikes!', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2, border_color=BLACK)
    draw_text('Press ESC to pause.', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2 + 40, border_color=BLACK)

    # Back button
    button_back = pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT * 0.75, 200, 50)
    pygame.draw.rect(surface, LIGHT_GRAY, button_back)
    draw_text('Back', button_font, WHITE, surface, button_back.centerx, button_back.centery)
    return {"back": button_back} # Return as dict for consistency

def draw_settings_screen(surface):
    """Draws the settings screen."""
    draw_menu_background(surface)

    # Semi-transparent box for text
    text_box = pygame.Surface((GAME_WIDTH * 0.8, GAME_HEIGHT * 0.4), pygame.SRCALPHA)
    text_box.fill((0, 0, 0, 120))
    surface.blit(text_box, (GAME_WIDTH * 0.1, GAME_HEIGHT / 4 - 20))

    draw_text('Settings', menu_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 4)
    draw_text('Audio settings (Not implemented yet)', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2)

    # Back button
    button_back = pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT * 0.75, 200, 50)
    pygame.draw.rect(surface, LIGHT_GRAY, button_back)
    draw_text('Back', button_font, WHITE, surface, button_back.centerx, button_back.centery)
    return {"back": button_back} # Return as dict

def draw_game_over_screen(surface, current_score):
    """Draws the game over screen with a dynamically sized background box."""
    draw_menu_background(surface) # Draw the main background first

    # --- Dynamic Box Calculation ---
    title_text = 'Game Over!'
    score_text = f'Final Score: {current_score}'
    button_texts_list = ["Retry", "Main Menu"]
    button_height = 50
    num_buttons = len(button_texts_list)

    # Calculate content height
    title_height = menu_font.get_height()
    score_text_height = button_font.get_height() # Use button font for score text height
    buttons_total_height = num_buttons * button_height + (num_buttons - 1) * BUTTON_SPACING_Y
    # Padding: top, between title/score, between score/buttons, bottom
    content_height = title_height + score_text_height + buttons_total_height + BOX_PADDING_Y * 4

    # Calculate box dimensions
    box_width = GAME_WIDTH * 0.6
    box_height = content_height
    box_x = (GAME_WIDTH - box_width) / 2
    box_y = (GAME_HEIGHT - box_height) / 2

    # Create and draw the box
    menu_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    menu_box.fill((0, 0, 0, 160)) # Make game over box slightly more opaque
    surface.blit(menu_box, (box_x, box_y))
    # --- End Dynamic Calculation ---

    # Position title, score, and buttons relative to the box top/center
    title_y = box_y + BOX_PADDING_Y
    draw_text(title_text, menu_font, RED, surface, GAME_WIDTH / 2, title_y + title_height / 2)

    score_text_y = title_y + title_height + BOX_PADDING_Y
    draw_text(score_text, button_font, WHITE, surface, GAME_WIDTH / 2, score_text_y + score_text_height / 2)

    # Define button rects
    button_rects = {}
    current_button_y = score_text_y + score_text_height + BOX_PADDING_Y # Start buttons below score text + padding
    button_x = GAME_WIDTH / 2 - 100

    button_keys = ["retry", "menu"]

    for i, text in enumerate(button_texts_list):
        key = button_keys[i]
        rect = pygame.Rect(button_x, current_button_y, 200, button_height)
        button_rects[key] = rect
        pygame.draw.rect(surface, LIGHT_GRAY, rect)
        draw_text(text, button_font, BLACK, surface, rect.centerx, rect.centery)
        current_button_y += button_height + BUTTON_SPACING_Y

    return button_rects # Return the dict

def draw_hud(surface, current_score, current_health):
    """Draws the Heads Up Display (Score and Health)."""
    global heart_sprite_index # Need to modify global index

    # Draw Hearts
    if heart_sprites: # Only draw if images loaded successfully
        heart_sprite_index = (heart_sprite_index + HEART_ANIMATION_SPEED) % len(heart_sprites)
        current_heart_sprite = heart_sprites[int(heart_sprite_index)]
        heart_width = current_heart_sprite.get_width()
        for life in range(current_health):
            x_pos = HEALTH_POS_LEFT_MARGIN + life * (heart_width + HEALTH_HEART_SPACING)
            surface.blit(current_heart_sprite, (x_pos, HEALTH_POS_TOP_MARGIN))
    else: # Fallback if heart images failed
         draw_text(f'Health: {current_health}', score_font, BLACK, surface, HEALTH_POS_LEFT_MARGIN, HEALTH_POS_TOP_MARGIN, center=False)

    # Draw Score (Anchored Top-Right)
    score_text = score_font.render(f'Score: {current_score}', True, BLACK)
    score_rect = score_text.get_rect(topright=(GAME_WIDTH - SCORE_POS_RIGHT_MARGIN, SCORE_POS_TOP_MARGIN))
    surface.blit(score_text, score_rect)


# --- State Handling Functions ---
def handle_main_menu(events):
    """Handles input and drawing for the main menu state."""
    global game_state, quit_game
    buttons = draw_main_menu(game)

    for event in events:
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if buttons["start"].collidepoint(mouse_pos):
                reset_game()
                game_state = STATE_PLAYING
                 # --- ADD MUSIC START ---
                try:
                    pygame.mixer.music.play(-1) # Play indefinitely (-1 loops)
                except pygame.error as e:
                    print(f"Error playing music: {e}")
                # --- END MUSIC START ---
            elif buttons["instructions"].collidepoint(mouse_pos):
                game_state = STATE_INSTRUCTIONS
            elif buttons["settings"].collidepoint(mouse_pos):
                game_state = STATE_SETTINGS
            elif buttons["quit"].collidepoint(mouse_pos):
                quit_game = True

def handle_instructions(events):
    """Handles input and drawing for the instructions state."""
    global game_state
    buttons = draw_instructions_screen(game)
    for event in events:
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
             if buttons["back"].collidepoint(event.pos):
                game_state = STATE_MAIN_MENU
        elif event.type == KEYDOWN and event.key == K_ESCAPE: # Allow ESC to go back
             game_state = STATE_MAIN_MENU

def handle_settings(events):
    """Handles input and drawing for the settings state."""
    global game_state
    buttons = draw_settings_screen(game)
    for event in events:
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
             if buttons["back"].collidepoint(event.pos):
                game_state = STATE_MAIN_MENU
        elif event.type == KEYDOWN and event.key == K_ESCAPE: # Allow ESC to go back
             game_state = STATE_MAIN_MENU


def handle_playing(events, dt):
    """Handles input, updates, and drawing for the playing state."""
    global game_state, score, speed, obstacle, parallax_offsets

    # --- Input ---
    for event in events:
        if event.type == KEYDOWN:
            if event.key == K_SPACE:
                player.jump()
                # ADD JUMP SOUND EFFECT LATER HERE?
            if event.key == K_ESCAPE:
                game_state = STATE_PAUSED
                # --- ADD MUSIC PAUSE ---
                try:
                    pygame.mixer.music.pause() # Pause music
                except pygame.error as e:
                    print(f"Error pausing music: {e}")
                # --- END MUSIC PAUSE ---

    # --- Updates ---
    player.update(dt)
    obstacle.update(dt)
    obstacles_group.update(dt) # Group update might be needed if using more sprites
    parallax_offsets = update_parallax(parallax_offsets, background_layers, speed, dt)

    # Obstacle Management
    if obstacle.rect.right < 0:
        score += 1
        # Increase speed gradually
        if score % SPEED_INCREASE_INTERVAL == 0 and speed < MAX_SPEED:
            speed = min(MAX_SPEED, speed + SPEED_INCREASE_AMOUNT) # Ensure max speed isn't exceeded

        # Replace obstacle - Pass the potentially updated speed
        obstacles_group.remove(obstacle)
        obstacle = Obstacle(speed)
        obstacles_group.add(obstacle)


    # Collision Detection
    if player.invincibility_frame <= 0:
         # Use the group for collision detection
         collided_obstacles = pygame.sprite.spritecollide(player, obstacles_group, False, pygame.sprite.collide_mask)
         if collided_obstacles:
             # Only handle collision with the first obstacle in the list if multiple somehow collide at once
             collided_obstacle = collided_obstacles[0]

             player.health -= 1
             player.invincibility_frame = PLAYER_INVINCIBILITY_DURATION

             # Remove the specific collided obstacle and add a new one
             obstacles_group.remove(collided_obstacle)
             # Update obstacle variable to the new one for tracking off-screen
             obstacle = Obstacle(speed)
             obstacles_group.add(obstacle)

             if player.health <= 0:
                game_state = STATE_GAME_OVER
                # --- ADD MUSIC STOP ---
                try:
                    # pygame.mixer.music.stop() # Stop immediately
                    pygame.mixer.music.fadeout(500) # Fade out over 500ms
                except pygame.error as e:
                    print(f"Error stopping/fading music: {e}")
                 # --- END MUSIC STOP ---
                 


    # --- Drawing ---
    draw_layered_background(game, sky_image, background_layers, parallax_offsets, num_bg_tiles)
    player.draw(game)
    obstacles_group.draw(game) # Draw all obstacles in the group
    draw_hud(game, score, player.health)


def handle_pause(events):
    """Handles input and drawing for the paused state."""
    global game_state, quit_game
    # Draw the last gameplay frame underneath? (Optional, can be slow)
    # For simplicity, draw menu directly:
    buttons = draw_pause_menu(game)

    for event in events:
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            game_state = STATE_PLAYING # Resume on ESC
            # --- ADD MUSIC UNPAUSE ---
            try:
                pygame.mixer.music.unpause() # Unpause music
            except pygame.error as e:
                print(f"Error unpausing music: {e}")
            # --- END MUSIC UNPAUSE ---
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if buttons["resume"].collidepoint(mouse_pos):
                game_state = STATE_PLAYING
                # --- ADD MUSIC UNPAUSE ---
                try:
                    pygame.mixer.music.unpause() # Unpause music
                except pygame.error as e:
                    print(f"Error unpausing music: {e}")
                # --- END MUSIC UNPAUSE ---
            elif buttons["menu"].collidepoint(mouse_pos):
                game_state = STATE_MAIN_MENU
                # --- ADD MUSIC STOP ---
                try:
                    pygame.mixer.music.stop() # Stop immediately when going to menu
                except pygame.error as e:
                    print(f"Error stopping music: {e}")
                 # --- END MUSIC STOP ---
            elif buttons["quit"].collidepoint(mouse_pos):
                # --- ADD MUSIC STOP ---
                try:
                    pygame.mixer.music.stop() # Stop music before quitting
                except pygame.error as e:
                    print(f"Error stopping music: {e}")
                 # --- END MUSIC STOP ---
                quit_game = True


def handle_game_over(events):
    """Handles input and drawing for the game over state."""
    global game_state
    # Draw the last gameplay frame underneath? (Optional)
    # Draw menu directly:
    buttons = draw_game_over_screen(game, score) # Pass final score

    for event in events:
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if buttons["retry"].collidepoint(mouse_pos):
                reset_game()
                game_state = STATE_PLAYING
                # --- ADD MUSIC START ---
                try:
                    pygame.mixer.music.play(-1) # Play indefinitely
                except pygame.error as e:
                    print(f"Error playing music: {e}")
                # --- END MUSIC START ---
            elif buttons["menu"].collidepoint(mouse_pos):
                game_state = STATE_MAIN_MENU
                # Music should already be stopped from handle_playing transition

# --- Main Game Loop ---
quit_game = False
while not quit_game:

    # Get delta time for frame-independent calculations
    dt = clock.tick(FPS) / 1000.0

    events = pygame.event.get()
    for event in events:
        if event.type == QUIT:
            quit_game = True
        # Other universal events (like window resizing) could go here

    # --- State-Based Logic ---
    if game_state == STATE_MAIN_MENU:
        handle_main_menu(events)
    elif game_state == STATE_INSTRUCTIONS:
        handle_instructions(events)
    elif game_state == STATE_SETTINGS:
        handle_settings(events)
    elif game_state == STATE_PLAYING:
        handle_playing(events, dt)
    elif game_state == STATE_PAUSED:
        handle_pause(events)
    elif game_state == STATE_GAME_OVER:
        handle_game_over(events)

    # --- Update Display ---
    pygame.display.update()


# --- Cleanup ---
try:
    pygame.mixer.music.stop()
except pygame.error: pass # Ignore if mixer wasn't initialized or other errors
pygame.quit()
sys.exit()
