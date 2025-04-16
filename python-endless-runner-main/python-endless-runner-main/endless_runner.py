import pygame
from pygame.locals import *
import random
import math
import sys
import os # Added for path joining

# --- Constants ---
# Screen Dimensions
GAME_WIDTH = 800
GAME_HEIGHT = 400
SIZE = (GAME_WIDTH, GAME_HEIGHT)
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
MAX_SPEED = 15
SPEED_INCREASE_INTERVAL = 3 # Increase speed every N points
SPEED_INCREASE_AMOUNT = 0.5
SCORE_POS_RIGHT_MARGIN = 15
SCORE_POS_TOP_MARGIN = 15
HEALTH_POS_LEFT_MARGIN = 10
HEALTH_POS_TOP_MARGIN = 10
HEALTH_HEART_SPACING = 5
HEART_ANIMATION_SPEED = 0.1

# Font Sizes
MENU_FONT_SIZE = 40
BUTTON_FONT_SIZE = 30
SCORE_FONT_SIZE = 24
# INFO_FONT_SIZE = 16 # Not currently used, can remove or keep for future

# File Paths (using os.path.join for compatibility)
IMAGE_DIR = 'images'
BG_DIR = os.path.join(IMAGE_DIR, 'bg')
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

# --- Font Loading ---
# It's good practice to check if font loading succeeds
try:
    menu_font = pygame.font.Font(pygame.font.get_default_font(), MENU_FONT_SIZE)
    button_font = pygame.font.Font(pygame.font.get_default_font(), BUTTON_FONT_SIZE)
    score_font = pygame.font.Font(pygame.font.get_default_font(), SCORE_FONT_SIZE)
except pygame.error as e:
    print(f"Error loading default font: {e}. Using system font.")
    # Fallback to system font if default fails
    menu_font = pygame.font.SysFont(None, MENU_FONT_SIZE)
    button_font = pygame.font.SysFont(None, BUTTON_FONT_SIZE)
    score_font = pygame.font.SysFont(None, SCORE_FONT_SIZE)


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

def draw_text(text, font, color, surface, x, y, center=True):
    """Draws text onto a surface."""
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    if center:
        textrect.center = (x, y)
    else:
        textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

# --- Asset Loading ---
# Moved asset loading here to ensure they are loaded before being used
# Backgrounds
try:
    sky_image = load_scaled_image(os.path.join(BG_DIR, 'sky.png'), use_alpha=False) # Sky usually doesn't need alpha
    # Scale sky to exact game width if tiling isn't perfect
    sky_image = pygame.transform.scale(sky_image, (GAME_WIDTH, GAME_HEIGHT))
    background_layers = [
        load_scaled_image(os.path.join(BG_DIR, 'mountains.png')),
        load_scaled_image(os.path.join(BG_DIR, 'trees.png')),
        load_scaled_image(os.path.join(BG_DIR, 'bushes.png'))
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
            self.running_sprites = load_animation_frames(RUNNING_DIR, 10, self.height)
            self.jumping_sprites = load_animation_frames(JUMPING_DIR, 10, self.height)
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
        self.x -= self.game_speed * dt * FPS # Frame-independent movement (approx)
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
            for j in range(num_tiles + 1): # Add +1 tile for smoother looping
                pos_x = j * layer.get_width() + offset
                surface.blit(layer, (pos_x, pos_y))


def update_parallax(offsets, layers, current_speed, dt):
    """Updates the scroll offset for parallax layers."""
    new_offsets = []
    for i in range(len(layers)):
         if i < len(offsets): # Check index validity
             # Scroll speed increases for closer layers (higher index)
             # Adjusted calculation for smoother, speed-dependent parallax
             scroll_amount = (i + 1) * current_speed * 0.5 * dt
             new_offset = offsets[i] - scroll_amount

             # Reset offset when layer scrolls completely off-screen
             if abs(new_offset) > layers[i].get_width():
                 new_offset = 0
             new_offsets.append(new_offset)
         else:
             new_offsets.append(0) # Append 0 if offset doesn't exist
    return new_offsets


# --- Menu Drawing Functions ---
def draw_menu_background(surface):
    """Helper function to draw the static layered background for menus."""
    draw_layered_background(surface, sky_image, background_layers, [0]*len(background_layers), num_bg_tiles)


def draw_main_menu(surface):
    """Draws the main menu and its buttons."""
    draw_menu_background(surface)
    draw_text('Endless Runner', menu_font, BLACK, surface, GAME_WIDTH / 2, GAME_HEIGHT / 4)

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
        draw_text(button_texts[name], button_font, BLACK, surface, rect.centerx, rect.centery)

    return button_rects


def draw_pause_menu(surface):
    """Draws the pause menu overlay and buttons."""
    overlay = pygame.Surface(SIZE, pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150)) # Black with alpha transparency
    surface.blit(overlay, (0, 0))

    draw_text('Paused', menu_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 4)

    button_rects = {
        "resume": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 - 30, 200, 50),
        "menu": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 + 30, 200, 50),
        "quit": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 + 90, 200, 50)
    }
    button_texts = {"resume": "Resume", "menu": "Main Menu", "quit": "Quit"}

    for name, rect in button_rects.items():
        pygame.draw.rect(surface, LIGHT_GRAY, rect)
        draw_text(button_texts[name], button_font, BLACK, surface, rect.centerx, rect.centery)

    return button_rects

def draw_instructions_screen(surface):
    """Draws the instructions screen."""
    draw_menu_background(surface)

    # Semi-transparent box for text
    text_box = pygame.Surface((GAME_WIDTH * 0.8, GAME_HEIGHT * 0.5), pygame.SRCALPHA)
    text_box.fill((0, 0, 0, 120)) # Slightly more opaque
    surface.blit(text_box, (GAME_WIDTH * 0.1, GAME_HEIGHT / 4 - 20))

    draw_text('Instructions', menu_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 4)
    draw_text('Press SPACE to jump over obstacles.', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2 - 40)
    draw_text('Avoid rocks and spikes!', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2 )
    draw_text('Press ESC to pause.', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2 + 40)

    # Back button
    button_back = pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT * 0.75, 200, 50)
    pygame.draw.rect(surface, LIGHT_GRAY, button_back)
    draw_text('Back', button_font, BLACK, surface, button_back.centerx, button_back.centery)
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
    draw_text('Back', button_font, BLACK, surface, button_back.centerx, button_back.centery)
    return {"back": button_back} # Return as dict

def draw_game_over_screen(surface, current_score):
    """Draws the game over screen."""
    overlay = pygame.Surface(SIZE, pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) # Darker overlay
    surface.blit(overlay, (0, 0))

    draw_text('Game Over!', menu_font, RED, surface, GAME_WIDTH / 2, GAME_HEIGHT / 4)
    draw_text(f'Final Score: {current_score}', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2 - 20)

    button_rects = {
        "retry": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 + 30, 200, 50),
        "menu": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 + 90, 200, 50)
    }
    button_texts = {"retry": "Retry", "menu": "Main Menu"}

    for name, rect in button_rects.items():
        pygame.draw.rect(surface, LIGHT_GRAY, rect)
        draw_text(button_texts[name], button_font, BLACK, surface, rect.centerx, rect.centery)

    return button_rects

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
            if event.key == K_ESCAPE:
                game_state = STATE_PAUSED

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
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if buttons["resume"].collidepoint(mouse_pos):
                game_state = STATE_PLAYING
            elif buttons["menu"].collidepoint(mouse_pos):
                game_state = STATE_MAIN_MENU
            elif buttons["quit"].collidepoint(mouse_pos):
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
            elif buttons["menu"].collidepoint(mouse_pos):
                game_state = STATE_MAIN_MENU


# --- Main Game Loop ---
quit_game = False
while not quit_game:

    # Get delta time for frame-independent calculations
    dt = clock.tick(FPS) / 1000.0

    # --- Universal Event Handling ---
    # Get all events since the last frame
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
pygame.quit()
sys.exit()
