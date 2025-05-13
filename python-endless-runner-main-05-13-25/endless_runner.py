import pygame
from pygame.locals import *
import random
import math
import sys
import os

# --- Constants ---
# Screen Dimensions
GAME_WIDTH = 800
GAME_HEIGHT = 432
SIZE = (GAME_WIDTH, GAME_HEIGHT)
screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
FPS = 60

# Box dimensions for menu
MENU_BOX_WIDTH = GAME_WIDTH * 0.6
MENU_BOX_HEIGHT = 300

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (150, 150, 150)
TEXT_HOVER = (255, 215, 0)
TEXT_SHADOW = (20, 20, 20)
SKY_BLUE = (135, 206, 235)

# Player Settings
PLAYER_START_X = 25
PLAYER_HEIGHT = 150
PLAYER_START_HEALTH = 3
PLAYER_JUMP_VELOCITY = -4
PLAYER_GRAVITY = 0.2
PLAYER_LAND_Y = GAME_HEIGHT - PLAYER_HEIGHT
PLAYER_ANIMATION_SPEED = 0.2
PLAYER_INVINCIBILITY_DURATION = 60

# Obstacle Settings
OBSTACLE_SCALE_WIDTH = 50
OBSTACLE_TYPES = ['rock1', 'rock2', 'rock3', 'spikes']
OBSTACLE_SPAWN_OFFSET_MIN = 0
OBSTACLE_SPAWN_OFFSET_MAX = 200

# Game Settings
STARTING_SPEED = 5
MAX_SPEED = 13
SPEED_INCREASE_INTERVAL = 4
SPEED_INCREASE_AMOUNT = 0.4
SCORE_POS_RIGHT_MARGIN = 15
SCORE_POS_TOP_MARGIN = 15
HEALTH_POS_LEFT_MARGIN = 10
HEALTH_POS_TOP_MARGIN = 10
HEALTH_HEART_SPACING = 5
HEART_ANIMATION_SPEED = 0.1

PAUSE_MENU_TITLE_PADDING = 20
BOX_PADDING_X = 30
BOX_PADDING_Y = 20
BUTTON_SPACING_Y = 10

# Font Sizes
FONT_PATH = 'fonts/upheavtt.ttf'
BASE_FONT_SIZE = 36
HOVER_FONT_SIZE = 44
MENU_FONT_SIZE = 40
BUTTON_FONT_SIZE = 30
SCORE_FONT_SIZE = 24

# Audio Settings
VOLUME_STEP = 0.1
MUSIC_TRACKS = ['Soundtrack.mp3', 'Soundtrack11.mp3']
MUSIC_TRACK_NAMES = ['Track 1', 'Track 2']

# File Paths
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
pygame.display.set_caption('Pixel Surge')
clock = pygame.time.Clock()

# Mixer Initialization
try:
    pygame.mixer.init()
    print("Mixer initialized successfully.")
except pygame.error as e:
    print(f"Error initializing mixer: {e}. Audio may not work.")

# Font Loading
try:
    menu_font = pygame.font.Font('fonts/upheavtt.ttf', MENU_FONT_SIZE)
    button_font = pygame.font.Font('fonts/upheavtt.ttf', BUTTON_FONT_SIZE)
    score_font = pygame.font.Font('fonts/upheavtt.ttf', SCORE_FONT_SIZE)
except pygame.error as e:
    print(f"Error loading custom fonts: {e}. Using system fonts.")
    menu_font = pygame.font.SysFont(None, MENU_FONT_SIZE)
    button_font = pygame.font.SysFont(None, BUTTON_FONT_SIZE)
    score_font = pygame.font.SysFont(None, SCORE_FONT_SIZE)

# Music Loading
try:
    music_paths = [os.path.join(SOUND_DIR, track) for track in MUSIC_TRACKS]
    pygame.mixer.music.load(music_paths[0])
    print(f"Loaded music: {music_paths[0]}")
except pygame.error as e:
    print(f"Error loading music: {e}")
    music_paths = []

# --- Game State Variables ---
game_state = STATE_MAIN_MENU
score = 0
speed = 0
parallax_offsets = []
heart_sprite_index = 0
current_track_index = 0
music_volume = 0.7
player = None
obstacles_group = None
obstacle = None
quit_game = False

# --- Helper Functions ---
def load_scaled_image(path, target_height=None, target_width=None, use_alpha=True):
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
        return image
    except pygame.error as e:
        print(f"Error loading or scaling image: {path} - {e}")
        fallback_size = (50, 50)
        if target_height:
            fallback_size = (50, target_height)
        if target_width:
            fallback_size = (target_width, 50)
        placeholder = pygame.Surface(fallback_size)
        placeholder.fill(RED)
        return placeholder

def load_animation_frames(directory, num_frames, target_height):
    frames = []
    for i in range(num_frames):
        filename = f'run{i}.png' if 'running' in directory else f'jump{i}.png' if 'jumping' in directory else f'heart{i}.png'
        path = os.path.join(directory, filename)
        frames.append(load_scaled_image(path, target_height=target_height))
    return frames

def draw_text(text, font, color, surface, x, y, center=True, border_color=None):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    if center:
        textrect.center = (x, y)
    else:
        textrect.topleft = (x, y)
    if border_color:
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            border_text = font.render(text, True, border_color)
            border_rect = border_text.get_rect(center=textrect.center)
            surface.blit(border_text, (border_rect.x + dx, border_rect.y + dy))
    surface.blit(textobj, textrect)

def switch_music_track(track_index):
    global current_track_index
    if track_index != current_track_index and music_paths:
        current_track_index = track_index
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(music_paths[current_track_index])
            pygame.mixer.music.set_volume(music_volume)
            if game_state == STATE_PLAYING:
                pygame.mixer.music.play(-1)
            print(f"Switched to music: {music_paths[current_track_index]}")
        except pygame.error as e:
            print(f"Error switching music to track {track_index}: {e}")

# --- Asset Loading ---
try:
    sky_image = load_scaled_image(os.path.join(BG_DIR, 'plx-1.png'), use_alpha=False)
    sky_image = pygame.transform.scale(sky_image, (GAME_WIDTH, GAME_HEIGHT))
    ground_image = pygame.image.load(os.path.join(BG_DIR, "ground.png")).convert_alpha()
    ground_height = ground_image.get_height()
    background_layers = [
        load_scaled_image(os.path.join(BG_DIR, 'plx-2.png'), target_height=GAME_HEIGHT),
        load_scaled_image(os.path.join(BG_DIR, 'plx-3.png'), target_height=GAME_HEIGHT),
        load_scaled_image(os.path.join(BG_DIR, 'plx-4.png'), target_height=GAME_HEIGHT),
        load_scaled_image(os.path.join(BG_DIR, 'plx-5.png'), target_height=GAME_HEIGHT)
    ]
    num_bg_tiles = 1
except Exception as e:
    print(f"Error during background asset loading: {e}")
    sky_image = pygame.Surface(SIZE)
    sky_image.fill(SKY_BLUE)
    background_layers = []
    num_bg_tiles = 1

try:
    heart_sprites = load_animation_frames(HEART_DIR, 8, target_height=30)
except Exception as e:
    print(f"Error during heart asset loading: {e}")
    heart_sprites = []

# --- Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.height = PLAYER_HEIGHT
        self.x = PLAYER_START_X
        self.y = PLAYER_LAND_Y
        self.action = 'running'
        self.health = PLAYER_START_HEALTH
        self.invincibility_frame = 0
        self.vel_y = 0
        try:
            self.running_sprites = load_animation_frames(RUNNING_DIR, 8, self.height)
            self.jumping_sprites = load_animation_frames(JUMPING_DIR, 8, self.height)
        except Exception as e:
            print(f"FATAL: Could not load player sprites: {e}")
            self.running_sprites = []
            self.jumping_sprites = []
            dummy_surf = pygame.Surface((50, self.height))
            dummy_surf.fill(RED)
            self.running_sprites.append(dummy_surf)
            self.jumping_sprites.append(dummy_surf)
        self.running_sprite_index = 0
        self.jumping_sprite_index = 0
        self.current_sprite_list = self.running_sprites
        self.current_sprite_index = self.running_sprite_index
        self.image = self.current_sprite_list[0]
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, surface):
        if not self.current_sprite_list:
            return
        index = int(self.current_sprite_index)
        index = max(0, min(index, len(self.current_sprite_list) - 1))
        sprite_to_draw = self.current_sprite_list[index]
        if self.invincibility_frame > 0:
            if self.invincibility_frame % 10 < 5:
                surface.blit(sprite_to_draw, self.rect.topleft)
        else:
            surface.blit(sprite_to_draw, self.rect.topleft)

    def update(self, dt):
        if not self.running_sprites or not self.jumping_sprites:
            return
        if self.action == 'jumping':
            self.y += self.vel_y
            self.vel_y += PLAYER_GRAVITY
            if self.y >= PLAYER_LAND_Y:
                self.y = PLAYER_LAND_Y
                self.action = 'running'
                self.vel_y = 0
        elif self.action == 'running':
            if self.y < PLAYER_LAND_Y:
                self.y = PLAYER_LAND_Y
        if self.action == 'running':
            self.current_sprite_list = self.running_sprites
            self.running_sprite_index = (self.running_sprite_index + PLAYER_ANIMATION_SPEED) % len(self.running_sprites)
            self.current_sprite_index = self.running_sprite_index
        elif self.action == 'jumping':
            self.current_sprite_list = self.jumping_sprites
            self.jumping_sprite_index = (self.jumping_sprite_index + PLAYER_ANIMATION_SPEED) % len(self.jumping_sprites)
            self.current_sprite_index = self.jumping_sprite_index
        index = int(self.current_sprite_index)
        index = max(0, min(index, len(self.current_sprite_list) - 1))
        self.image = self.current_sprite_list[index]
        self.rect.topleft = (self.x, self.y)
        self.mask = pygame.mask.from_surface(self.image)
        if self.invincibility_frame > 0:
            self.invincibility_frame -= 1

    def jump(self):
        if self.action == 'running':
            self.action = 'jumping'
            self.vel_y = PLAYER_JUMP_VELOCITY
            self.jumping_sprite_index = 0

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, game_speed):
        pygame.sprite.Sprite.__init__(self)
        self.obstacle_images = self._load_obstacle_images()
        if not self.obstacle_images:
            placeholder = pygame.Surface((OBSTACLE_SCALE_WIDTH, 50))
            placeholder.fill(RED)
            self.obstacle_images.append(placeholder)
        self.image = random.choice(self.obstacle_images)
        self.game_speed = game_speed
        self.x = GAME_WIDTH
        self.y = GAME_HEIGHT - self.image.get_height()
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.image)

    def _load_obstacle_images(self):
        images = []
        for image_name in OBSTACLE_TYPES:
            path = os.path.join(OBSTACLE_DIR, f'{image_name}.png')
            img = load_scaled_image(path, target_width=OBSTACLE_SCALE_WIDTH)
            if img:
                images.append(img)
        return images

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)

    def update(self, dt):
        self.x -= (self.game_speed) * dt * FPS
        self.rect.x = int(self.x)

    def reset(self, game_speed):
        self.image = random.choice(self.obstacle_images)
        self.x = GAME_WIDTH + random.randint(OBSTACLE_SPAWN_OFFSET_MIN, OBSTACLE_SPAWN_OFFSET_MAX)
        self.y = GAME_HEIGHT - self.image.get_height()
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.image)
        self.game_speed = game_speed

# --- Game Logic Functions ---
def reset_game():
    global player, obstacles_group, obstacle, score, speed, parallax_offsets, heart_sprite_index
    score = 0
    speed = STARTING_SPEED
    player = Player()
    obstacles_group = pygame.sprite.Group()
    obstacle = Obstacle(speed)
    obstacles_group.add(obstacle)
    parallax_offsets = [0] * len(background_layers)
    heart_sprite_index = 0
    player.invincibility_frame = 0

def draw_ground(surface, ground_img):
    surface.blit(ground_img, (0, GAME_HEIGHT - ground_height))

def draw_layered_background(surface, sky, layers, offsets, num_tiles):
    surface.blit(sky, (0, 0))
    for i in range(len(layers)):
        if i < len(offsets):
            layer = layers[i]
            offset = offsets[i]
            pos_y = GAME_HEIGHT - layer.get_height()
            layer_width = layer.get_width()
            start_x = int(offset % layer_width) - layer_width
            for j in range(num_tiles + 2):
                pos_x = start_x + j * layer_width
                surface.blit(layer, (pos_x, pos_y))

def update_parallax(offsets, layers, current_speed, dt):
    new_offsets = []
    for i in range(len(layers)):
        if i < len(offsets):
            scroll_amount = (i + 10) * current_speed * 3 * dt
            layer_width = layers[i].get_width()
            new_offset = offsets[i] - scroll_amount
            if new_offset <= -layer_width:
                new_offset += layer_width
            new_offsets.append(new_offset)
        else:
            new_offsets.append(0)
    return new_offsets

# --- Menu Drawing Functions ---
def draw_menu_background(surface):
    draw_layered_background(surface, sky_image, background_layers, [0]*len(background_layers), num_bg_tiles)

def draw_main_menu(surface):
    draw_menu_background(surface)
    title_font = pygame.font.Font(FONT_PATH, 72)
    draw_text('Pixel Surge', title_font, TEXT_SHADOW, surface, GAME_WIDTH / 2 + 2, GAME_HEIGHT / 4 + 2)
    draw_text('Pixel Surge', title_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 4)
    button_rects = {
        "start": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 - 30, 200, 50),
        "how to play": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 + 30, 200, 50),
        "settings": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 + 90, 200, 50),
        "quit": pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT / 2 + 150, 200, 50)
    }
    mouse_pos = pygame.mouse.get_pos()
    for name, rect in button_rects.items():
        text = name.replace('_', ' ').title()
        is_hovered = rect.collidepoint(mouse_pos)
        size = BASE_FONT_SIZE + 8 if is_hovered else BASE_FONT_SIZE
        font = pygame.font.Font(FONT_PATH, size)
        draw_text(text, font, TEXT_SHADOW, surface, rect.centerx + 2, rect.centery + 2)
        draw_text(text, font, TEXT_HOVER if is_hovered else WHITE, surface, rect.centerx, rect.centery)
    return button_rects

def draw_pause_menu(surface):
    draw_menu_background(surface)
    PAUSE_MENU_BOX_WIDTH = 300
    PAUSE_MENU_BOX_HEIGHT = 300
    title_text = 'Paused'
    button_texts_list = ["Resume", "Main Menu", "Quit"]
    button_height = 50
    num_buttons = len(button_texts_list)
    title_font_size = 60
    button_font_size = BASE_FONT_SIZE
    title_font = pygame.font.Font(FONT_PATH, title_font_size)
    button_font = pygame.font.Font(FONT_PATH, button_font_size)
    title_height = title_font.get_height()
    buttons_total_height = num_buttons * button_height + (num_buttons - 1) * BUTTON_SPACING_Y
    content_height = title_height + buttons_total_height + BOX_PADDING_Y * 3
    box_width = PAUSE_MENU_BOX_WIDTH
    box_height = PAUSE_MENU_BOX_HEIGHT
    box_x = (GAME_WIDTH - box_width) / 2
    box_y = (GAME_HEIGHT - box_height) / 2
    mouse_pos = pygame.mouse.get_pos()
    draw_text(title_text, title_font, TEXT_SHADOW, surface, GAME_WIDTH / 2 + 2, box_y + BOX_PADDING_Y + 2)
    draw_text(title_text, title_font, (255, 153, 51), surface, GAME_WIDTH / 2, box_y + BOX_PADDING_Y)
    button_rects = {}
    current_button_y = box_y + title_height + PAUSE_MENU_TITLE_PADDING + BOX_PADDING_Y
    button_x = GAME_WIDTH / 2 - 100
    for text in button_texts_list:
        rect = pygame.Rect(button_x, current_button_y, 200, button_height)
        button_rects[text.lower()] = rect
        is_hovered = rect.collidepoint(mouse_pos)
        size = HOVER_FONT_SIZE if is_hovered else button_font_size
        font = pygame.font.Font(FONT_PATH, size)
        draw_text(text, font, TEXT_SHADOW, surface, rect.centerx + 2, rect.centery + 2)
        draw_text(text, font, TEXT_HOVER if is_hovered else WHITE, surface, rect.centerx, rect.centery)
        current_button_y += button_height + BUTTON_SPACING_Y
    return button_rects

def draw_instructions_screen(surface):
    draw_menu_background(surface)
    PAUSE_MENU_BOX_WIDTH = 200
    PAUSE_MENU_BOX_HEIGHT = 300
    draw_text('How to play', menu_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 3.5, border_color=BLACK)
    draw_text('Press SPACE to jump over obstacles.', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2 - 40, border_color=BLACK)
    draw_text('Avoid rocks and spikes!', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2, border_color=BLACK)
    draw_text('Press ESC to pause.', button_font, WHITE, surface, GAME_WIDTH / 2, GAME_HEIGHT / 2 + 40, border_color=BLACK)
    button_back = pygame.Rect(GAME_WIDTH / 2 - 100, GAME_HEIGHT * 0.75, 200, 50)
    pygame.draw.rect(surface, TEXT_HOVER, button_back)
    draw_text('Back', button_font, WHITE, surface, button_back.centerx, button_back.centery)
    return {"back": button_back}

def draw_settings_screen(surface):
    draw_menu_background(surface)
    box_width = GAME_WIDTH * 0.6
    box_height = GAME_HEIGHT * 0.6
    text_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    text_box.fill((0, 0, 0, 160))
    box_x = (GAME_WIDTH - box_width) / 2
    box_y = (GAME_HEIGHT - box_height) / 2
    surface.blit(text_box, (box_x, box_y))
    draw_text('Settings', menu_font, WHITE, surface, GAME_WIDTH / 2, box_y + BOX_PADDING_Y)
    volume_y = box_y + BOX_PADDING_Y + menu_font.get_height() + BOX_PADDING_Y
    draw_text(f'Volume: {int(music_volume * 100)}%', button_font, WHITE, surface, GAME_WIDTH / 2, volume_y)
    volume_minus_rect = pygame.Rect(GAME_WIDTH / 2 - 120, volume_y + 20, 50, 40)
    volume_plus_rect = pygame.Rect(GAME_WIDTH / 2 + 70, volume_y + 20, 50, 40)
    mouse_pos = pygame.mouse.get_pos()
    for rect, text in [(volume_minus_rect, '-'), (volume_plus_rect, '+')]:
        is_hovered = rect.collidepoint(mouse_pos)
        font_size = HOVER_FONT_SIZE if is_hovered else BUTTON_FONT_SIZE
        font = pygame.font.Font(FONT_PATH, font_size)
        draw_text(text, font, TEXT_HOVER if is_hovered else WHITE, surface, rect.centerx, rect.centery)
    track_y = volume_y + 80
    draw_text('Music Track', button_font, WHITE, surface, GAME_WIDTH / 2, track_y)
    track_rects = {}
    for i, track_name in enumerate(MUSIC_TRACK_NAMES):
        x_offset = -100 if i == 0 else 50
        rect = pygame.Rect(GAME_WIDTH / 2 + x_offset, track_y + 20, 100, 40)
        track_rects[i] = rect
        is_hovered = rect.collidepoint(mouse_pos)
        font_size = HOVER_FONT_SIZE if is_hovered else BUTTON_FONT_SIZE
        font = pygame.font.Font(FONT_PATH, font_size)
        color = TEXT_HOVER if is_hovered or i == current_track_index else WHITE
        draw_text(track_name, font, color, surface, rect.centerx, rect.centery)
    back_rect = pygame.Rect(GAME_WIDTH / 2 - 100, box_y + box_height - 60, 200, 50)
    is_hovered = back_rect.collidepoint(mouse_pos)
    font_size = HOVER_FONT_SIZE if is_hovered else BUTTON_FONT_SIZE
    font = pygame.font.Font(FONT_PATH, font_size)
    draw_text('Back', font, TEXT_HOVER if is_hovered else WHITE, surface, back_rect.centerx, back_rect.centery)
    return {
        "volume_minus": volume_minus_rect,
        "volume_plus": volume_plus_rect,
        "back": back_rect,
        **{f"track_{i}": rect for i, rect in track_rects.items()}
    }

def draw_game_over_screen(surface, current_score):
    draw_menu_background(surface)
    title_text = 'Game Over!'
    score_text = f'Final Score: {current_score}'
    button_texts_list = ["Retry", "Main Menu"]
    button_height = 50
    num_buttons = len(button_texts_list)
    title_height = menu_font.get_height()
    score_text_height = button_font.get_height()
    buttons_total_height = num_buttons * button_height + (num_buttons - 1) * BUTTON_SPACING_Y
    content_height = title_height + score_text_height + buttons_total_height + BOX_PADDING_Y * 4
    box_width = GAME_WIDTH * 0.6
    box_height = content_height
    box_x = (GAME_WIDTH - box_width) / 2
    box_y = (GAME_HEIGHT - box_height) / 2
    menu_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    menu_box.fill((0, 0, 0, 160))
    surface.blit(menu_box, (box_x, box_y))
    title_y = box_y + BOX_PADDING_Y
    draw_text(title_text, menu_font, RED, surface, GAME_WIDTH / 2, title_y + title_height / 2)
    score_text_y = title_y + title_height + BOX_PADDING_Y
    draw_text(score_text, button_font, WHITE, surface, GAME_WIDTH / 2, score_text_y + score_text_height / 2)
    button_rects = {}
    current_button_y = score_text_y + score_text_height + BOX_PADDING_Y
    button_x = GAME_WIDTH / 2 - 100
    button_keys = ["retry", "menu"]
    for i, text in enumerate(button_texts_list):
        key = button_keys[i]
        rect = pygame.Rect(button_x, current_button_y, 200, button_height)
        button_rects[key] = rect
        pygame.draw.rect(surface, WHITE, rect)
        draw_text(text, button_font, BLACK, surface, rect.centerx, rect.centery)
        current_button_y += button_height + BUTTON_SPACING_Y
    return button_rects

def draw_hud(surface, current_score, current_health):
    global heart_sprite_index
    if heart_sprites:
        heart_sprite_index = (heart_sprite_index + HEART_ANIMATION_SPEED) % len(heart_sprites)
        current_heart_sprite = heart_sprites[int(heart_sprite_index)]
        heart_width = current_heart_sprite.get_width()
        for life in range(current_health):
            x_pos = HEALTH_POS_LEFT_MARGIN + life * (heart_width + HEALTH_HEART_SPACING)
            surface.blit(current_heart_sprite, (x_pos, HEALTH_POS_TOP_MARGIN))
    else:
        draw_text(f'Health: {current_health}', score_font, BLACK, surface, HEALTH_POS_LEFT_MARGIN, HEALTH_POS_TOP_MARGIN, center=False)
    score_text = score_font.render(f'Score: {current_score}', True, BLACK)
    score_rect = score_text.get_rect(topright=(GAME_WIDTH - SCORE_POS_RIGHT_MARGIN, SCORE_POS_TOP_MARGIN))
    surface.blit(score_text, score_rect)

# --- State Handling Functions ---
def handle_main_menu(events):
    global game_state, quit_game
    buttons = draw_main_menu(game)
    for event in events:
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if buttons["start"].collidepoint(mouse_pos):
                reset_game()
                game_state = STATE_PLAYING
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(music_paths[current_track_index])
                    pygame.mixer.music.set_volume(music_volume)
                    pygame.mixer.music.play(-1)
                except pygame.error as e:
                    print(f"Error playing music: {e}")
            elif buttons["how to play"].collidepoint(mouse_pos):
                game_state = STATE_INSTRUCTIONS
            elif buttons["settings"].collidepoint(mouse_pos):
                game_state = STATE_SETTINGS
            elif buttons["quit"].collidepoint(mouse_pos):
                quit_game = True

def handle_instructions(events):
    global game_state
    buttons = draw_instructions_screen(game)
    for event in events:
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if buttons["back"].collidepoint(event.pos):
                game_state = STATE_MAIN_MENU
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            game_state = STATE_MAIN_MENU

def handle_settings(events):
    global game_state, music_volume, current_track_index
    buttons = draw_settings_screen(game)
    for event in events:
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if buttons["back"].collidepoint(mouse_pos):
                game_state = STATE_MAIN_MENU
            elif buttons["volume_minus"].collidepoint(mouse_pos):
                music_volume = max(0.0, music_volume - VOLUME_STEP)
                pygame.mixer.music.set_volume(music_volume)
            elif buttons["volume_plus"].collidepoint(mouse_pos):
                music_volume = min(1.0, music_volume + VOLUME_STEP)
                pygame.mixer.music.set_volume(music_volume)
            elif buttons.get("track_0") and buttons["track_0"].collidepoint(mouse_pos):
                switch_music_track(0)
            elif buttons.get("track_1") and buttons["track_1"].collidepoint(mouse_pos):
                switch_music_track(1)
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            game_state = STATE_MAIN_MENU

def handle_playing(events, dt):
    global game_state, score, speed, obstacle, parallax_offsets
    for event in events:
        if event.type == KEYDOWN:
            if event.key == K_SPACE:
                player.jump()
            if event.key == K_ESCAPE:
                game_state = STATE_PAUSED
                try:
                    pygame.mixer.music.pause()
                except pygame.error as e:
                    print(f"Error pausing music: {e}")
    player.update(dt)
    obstacle.update(dt)
    obstacles_group.update(dt)
    parallax_offsets = update_parallax(parallax_offsets, background_layers, speed, dt)
    if obstacle.rect.right < 0:
        score += 1
        if score % SPEED_INCREASE_INTERVAL == 0 and speed < MAX_SPEED:
            speed = min(MAX_SPEED, speed + SPEED_INCREASE_AMOUNT)
        obstacles_group.remove(obstacle)
        obstacle = Obstacle(speed)
        obstacles_group.add(obstacle)
    if player.invincibility_frame <= 0:
        collided_obstacles = pygame.sprite.spritecollide(player, obstacles_group, False, pygame.sprite.collide_mask)
        if collided_obstacles:
            collided_obstacle = collided_obstacles[0]
            player.health -= 1
            player.invincibility_frame = PLAYER_INVINCIBILITY_DURATION
            obstacles_group.remove(collided_obstacle)
            obstacle = Obstacle(speed)
            obstacles_group.add(obstacle)
            if player.health <= 0:
                game_state = STATE_GAME_OVER
                try:
                    pygame.mixer.music.fadeout(500)
                except pygame.error as e:
                    print(f"Error stopping/fading music: {e}")
    draw_layered_background(game, sky_image, background_layers, parallax_offsets, num_bg_tiles)
    player.draw(game)
    obstacles_group.draw(game)
    draw_hud(game, score, player.health)

def handle_pause(events):
    global game_state, quit_game
    buttons = draw_pause_menu(game)
    for event in events:
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            game_state = STATE_PLAYING
            try:
                pygame.mixer.music.unpause()
            except pygame.error as e:
                print(f"Error unpausing music: {e}")
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for key, rect in buttons.items():
                if rect.collidepoint(mouse_pos):
                    if key == "resume":
                        game_state = STATE_PLAYING
                        try:
                            pygame.mixer.music.unpause()
                        except pygame.error as e:
                            print(f"Error unpausing music: {e}")
                    elif key == "main menu":
                        game_state = STATE_MAIN_MENU
                        try:
                            pygame.mixer.music.stop()
                        except pygame.error as e:
                            print(f"Error stopping music: {e}")
                    elif key == "quit":
                        try:
                            pygame.mixer.music.stop()
                        except pygame.error as e:
                            print(f"Error stopping music: {e}")
                        quit_game = True
                    break

def handle_game_over(events):
    global game_state
    buttons = draw_game_over_screen(game, score)
    for event in events:
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if buttons["retry"].collidepoint(mouse_pos):
                reset_game()
                game_state = STATE_PLAYING
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(music_paths[current_track_index])
                    pygame.mixer.music.set_volume(music_volume)
                    pygame.mixer.music.play(-1)
                except pygame.error as e:
                    print(f"Error playing music: {e}")
            elif buttons["menu"].collidepoint(mouse_pos):
                game_state = STATE_MAIN_MENU

# --- Main Game Loop ---
while not quit_game:
    dt = clock.tick(FPS) / 1000.0
    events = pygame.event.get()
    for event in events:
        if event.type == QUIT:
            quit_game = True
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
    pygame.display.update()

# --- Cleanup ---
try:
    pygame.mixer.music.stop()
except pygame.error:
    pass
pygame.quit()
sys.exit()