import arcade
import os
import random
import math
import datetime

# =================== CONFIG ===================
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Stickman Fighter"

PLAYER_SCALE = 0.1
PLAYER_SPEED = 12
DASH_SPEED = 25
DASH_DURATION = 15
DASH_COOLDOWN = 300
JUMP_SPEED = 14
GRAVITY = 0.6
GROUND_Y = 120

LEVEL_LEFT = -250
LEVEL_RIGHT = 1500

ROUND_TIME = 99

# Knockback
PUNCH_KNOCKBACK_X = 16
PUNCH_KNOCKBACK_Y = 6
KICK_KNOCKBACK_X = 12
KICK_KNOCKBACK_Y = 10

# Fatality
FATALITY_KNOCKBACK_X = 18
FATALITY_KNOCKBACK_Y = 14
FATALITY_BOUNCE_HEIGHTS = [12, 7, 4, 2, 1]
FATALITY_SLOW_MO_DURATION = 60
FATALITY_BOUNCE_DELAY = 8

# Combo
COMBO_TIMER_MAX = 60

# Animation
IDLE_ANIMATION_SPEED = 50
HIT_FLASH_DURATION = 4

# Block
BLOCK_DURATION = 30
BLOCK_COOLDOWN = 20
PARRY_WINDOW = 12
STUN_DURATION = 120

# Slide
SLIDE_DURATION = 8

# Punch forward movement
PUNCH_FORWARD_MOVE = 8

# Обновленные пути
ASSET_PATH = r".\Game"
SOUNDS_PATH = os.path.join(ASSET_PATH, "sounds")
TEXTURES_PATH = os.path.join(ASSET_PATH, "textures")
SETTINGS_FILE = "game_settings.txt"
RECORDS_FILE = "game_stats.txt"
BATTLE_HISTORY_FILE = "battle_history.txt"


# =================== PARTICLE SYSTEM ===================
class Particle:
    def __init__(self, x, y, velocity_x=0, velocity_y=0, color=arcade.color.RED,
                 size=3, lifetime=30, gravity=0.1, fade_out=True, texture=None):
        self.x = x
        self.y = y
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.fade_out = fade_out
        self.texture = texture
        self.angle = random.uniform(0, 360)
        self.angular_velocity = random.uniform(-5, 5)

    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y -= self.gravity
        self.angle += self.angular_velocity
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self):
        alpha = 255
        if self.fade_out:
            alpha = int(255 * (self.lifetime / self.max_lifetime))

        if self.texture:
            arcade.draw_texture_rectangle(
                self.x, self.y,
                self.size, self.size,
                self.texture,
                self.angle,
                alpha
            )
        else:
            color_with_alpha = (self.color[0], self.color[1], self.color[2], alpha)
            rect = arcade.rect.XYWH(self.x, self.y, self.size, self.size)
            arcade.draw_rect_filled(rect, color_with_alpha, self.angle)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add_particle(self, particle):
        self.particles.append(particle)

    def create_blood_splash(self, x, y, count=15):
        colors = [
            arcade.color.RED,
            arcade.color.DARK_RED,
            arcade.color.MAROON,
            (139, 0, 0)
        ]

        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed

            particle = Particle(
                x, y,
                velocity_x, velocity_y,
                random.choice(colors),
                random.uniform(2, 6),
                random.randint(20, 40),
                gravity=0.2
            )
            self.particles.append(particle)

    def create_dust_cloud(self, x, y, direction=1, count=10):
        for _ in range(count):
            velocity_x = random.uniform(-1, 1) * direction
            velocity_y = random.uniform(-0.5, 0.5)

            particle = Particle(
                x, y,
                velocity_x, velocity_y,
                arcade.color.LIGHT_GRAY,
                random.uniform(2, 4),
                random.randint(10, 20),
                gravity=0.05,
                fade_out=True
            )
            self.particles.append(particle)

    def create_block_spark(self, x, y, direction=1):
        for _ in range(8):
            angle = random.uniform(-math.pi / 4, math.pi / 4) + (math.pi if direction < 0 else 0)
            speed = random.uniform(3, 6)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed

            colors = [
                arcade.color.YELLOW,
                arcade.color.GOLD,
                arcade.color.ORANGE
            ]

            particle = Particle(
                x, y,
                velocity_x, velocity_y,
                random.choice(colors),
                random.uniform(2, 4),
                random.randint(15, 25),
                gravity=0.1
            )
            self.particles.append(particle)

    def create_dash_trail(self, x, y, direction=1, count=5):
        for _ in range(count):
            offset_x = random.uniform(-10, 10)
            offset_y = random.uniform(-5, 5)

            particle = Particle(
                x + offset_x,
                y + offset_y,
                -direction * random.uniform(0.5, 1.5),
                0,
                arcade.color.CYAN,
                random.uniform(3, 6),
                random.randint(20, 30),
                gravity=0,
                fade_out=True
            )
            self.particles.append(particle)

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self):
        for particle in self.particles:
            particle.draw()


# =================== UI HELPERS ===================
class UIButton:
    def __init__(self, text, x, y, w, h):
        self.text = text
        self.left = x - w / 2
        self.right = x + w / 2
        self.bottom = y - h / 2
        self.top = y + h / 2
        self.hover = False

    def draw(self):
        color = arcade.color.DARK_SLATE_GRAY if not self.hover else arcade.color.SLATE_GRAY

        rect = arcade.rect.XYWH(
            x=(self.left + self.right) / 2,
            y=(self.bottom + self.top) / 2,
            width=self.right - self.left,
            height=self.top - self.bottom
        )

        arcade.draw_rect_filled(rect, color)
        arcade.draw_rect_outline(rect, arcade.color.DARK_SLATE_GRAY, 2)

        arcade.draw_text(
            self.text,
            (self.left + self.right) / 2,
            (self.bottom + self.top) / 2,
            arcade.color.WHITE,
            20,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

    def hit_test(self, x, y):
        return self.left <= x <= self.right and self.bottom <= y <= self.top


class KeyBindingButton:
    def __init__(self, action, x, y, w, h, key_name):
        self.action = action
        self.text = action
        self.key_name = key_name
        self.left = x - w / 2
        self.right = x + w / 2
        self.bottom = y - h / 2
        self.top = y + h / 2
        self.hover = False
        self.waiting_for_input = False

    def draw(self):
        if self.waiting_for_input:
            color = arcade.color.GOLD
            border_color = arcade.color.YELLOW
            text_color = arcade.color.ARSENIC
            status_text = "Нажмите клавишу..."
        else:
            color = arcade.color.DARK_SLATE_GRAY if not self.hover else arcade.color.SLATE_GRAY
            border_color = arcade.color.DARK_SLATE_GRAY
            text_color = arcade.color.WHITE
            status_text = ""

        rect = arcade.rect.XYWH(
            x=(self.left + self.right) / 2,
            y=(self.bottom + self.top) / 2,
            width=self.right - self.left,
            height=self.top - self.bottom
        )

        arcade.draw_rect_filled(rect, color)
        arcade.draw_rect_outline(rect, border_color, 2)

        arcade.draw_text(
            self.text,
            self.left + 10,
            (self.bottom + self.top) / 2,
            text_color,
            16,
            anchor_y="center",
            bold=True
        )

        arcade.draw_text(
            self.key_name,
            self.right - 10,
            (self.bottom + self.top) / 2,
            text_color,
            16,
            anchor_x="right",
            anchor_y="center",
            bold=True
        )

        if self.waiting_for_input:
            arcade.draw_text(
                status_text,
                (self.left + self.right) / 2,
                self.top + 25,
                arcade.color.YELLOW,
                12,
                anchor_x="center",
                anchor_y="bottom"
            )

    def hit_test(self, x, y):
        return self.left <= x <= self.right and self.bottom <= y <= self.top


# =================== MAP OBJECTS ===================
class Platform:
    def __init__(self, x, y, width, height, texture: arcade.Texture):
        self.rect = arcade.rect.XYWH(x, y, width, height)
        self.texture = texture

    def draw(self):
        arcade.draw_texture_rect(self.texture, self.rect)

    @property
    def top(self):
        return self.rect.top

    @property
    def left(self):
        return self.rect.left

    @property
    def right(self):
        return self.rect.right


# =================== PLAYER ===================
class Player(arcade.Sprite):
    def __init__(self, start_x, name="Player", name_color=arcade.color.BLUE, controls=None):
        super().__init__(scale=PLAYER_SCALE, hit_box_algorithm="None")

        self.name = name
        self.name_color = name_color
        self.controls = controls or {
            "left": arcade.key.A,
            "right": arcade.key.D,
            "jump": arcade.key.W,
            "punch": arcade.key.Q,
            "kick": arcade.key.E,
            "block": arcade.key.S,
            "dash": arcade.key.LSHIFT
        }

        self.center_x = start_x
        self.center_y = GROUND_Y

        self.change_x = 0
        self.change_y = 0
        self.facing_right = True
        self.on_ground = False

        self.walking_left = False
        self.walking_right = False
        self.sliding = False
        self.slide_timer = 0
        self.slide_direction = 0
        self.last_move_time = 0
        self.just_landed = False

        self.max_health = 100
        self.health = 100
        self.attacking = False
        self.attack_timer = 0
        self.attack_type = None
        self.attack_index = 0
        self.hit_stun_timer = 0
        self.hit_flash_timer = 0
        self.hit_flash_visible = True

        self.blocking = False
        self.block_timer = 0
        self.block_cooldown = 0
        self.parry_window = False
        self.stunned = False
        self.stun_timer = 0

        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_direction = 0
        self.dash_invulnerable = False

        self.stats_hits = 0
        self.stats_combos = 0
        self.total_wins = 0

        self.combo_counter = 0
        self.combo_timer = 0
        self.show_combo = False

        self.state = "idle"
        self.fatality_phase = 0
        self.fatality_timer = 0
        self.bounce_count = 0
        self.fatality_ground_bounce_timer = 0
        self.fatality_velocity_y = 0

        self.idle_frame = 0
        self.idle_frame_timer = 0
        self.walk_frame = 0
        self.walk_timer = 0

        self.load_textures()

        self.texture = self.idle_textures_right[0]
        self.center_y = GROUND_Y + self.height / 2

    def load_textures(self):
        self.idle_textures_right = []
        self.idle_textures_left = []
        for i in range(1, 5):
            texture_path = os.path.join(TEXTURES_PATH, f"Stand_R_{i}.png")
            if os.path.exists(texture_path):
                texture = arcade.load_texture(texture_path)
                self.idle_textures_right.append(texture)
                self.idle_textures_left.append(texture.flip_horizontally())

        self.run_r = []
        self.run_l = []
        for i in range(1, 8):
            texture_path = os.path.join(TEXTURES_PATH, f"Run_L_{i}.png")
            if os.path.exists(texture_path):
                t = arcade.load_texture(texture_path)
                self.run_l.append(t)
                self.run_r.append(t.flip_horizontally())

        self.jump_r = arcade.load_texture(os.path.join(TEXTURES_PATH, "Jump_R.png"))
        self.jump_l = self.jump_r.flip_horizontally()

        self.fall_r = arcade.load_texture(os.path.join(TEXTURES_PATH, "Fall_R.png"))
        self.fall_l = self.fall_r.flip_horizontally()

        self.punch_textures_r = [
            arcade.load_texture(os.path.join(TEXTURES_PATH, "Punch_1_R.png")),
            arcade.load_texture(os.path.join(TEXTURES_PATH, "Punch_2_R.png"))
        ]
        self.punch_textures_l = [tex.flip_horizontally() for tex in self.punch_textures_r]

        self.kick_textures_r = [
            arcade.load_texture(os.path.join(TEXTURES_PATH, "Kick_1_R.png")),
            arcade.load_texture(os.path.join(TEXTURES_PATH, "Kick_2_R.png"))
        ]
        self.kick_textures_l = [tex.flip_horizontally() for tex in self.kick_textures_r]

        self.slay_r = arcade.load_texture(os.path.join(TEXTURES_PATH, "Slay_R.png"))
        self.slay_l = self.slay_r.flip_horizontally()

        self.block_r = arcade.load_texture(os.path.join(TEXTURES_PATH, "Block_R.png"))
        self.block_l = self.block_r.flip_horizontally()

        self.dash_r = arcade.load_texture(os.path.join(TEXTURES_PATH, "Dash_R.png"))
        self.dash_l = self.dash_r.flip_horizontally()

        self.hit_r = arcade.load_texture(os.path.join(TEXTURES_PATH, "Fatality_R_1.png"))
        self.hit_l = self.hit_r.flip_horizontally()

        self.fatality_2_r = arcade.load_texture(os.path.join(TEXTURES_PATH, "Fatality_R_2.png"))
        self.fatality_3_r = arcade.load_texture(os.path.join(TEXTURES_PATH, "Fatality_R_3.png"))
        self.fatality_2_l = self.fatality_2_r.flip_horizontally()
        self.fatality_3_l = self.fatality_3_r.flip_horizontally()

        self.fatality_1_r = self.hit_r
        self.fatality_1_l = self.hit_l

    def reset_for_round(self, start_x):
        self.center_x = start_x
        self.center_y = GROUND_Y + self.height / 2
        self.change_x = 0
        self.change_y = 0
        self.health = self.max_health
        self.state = "idle"
        self.on_ground = False
        self.attacking = False
        self.attack_timer = 0
        self.blocking = False
        self.block_timer = 0
        self.block_cooldown = 0
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_invulnerable = False
        self.sliding = False
        self.slide_timer = 0
        self.stunned = False
        self.stun_timer = 0
        self.combo_counter = 0
        self.combo_timer = 0
        self.show_combo = False
        self.hit_stun_timer = 0
        self.hit_flash_timer = 0
        self.hit_flash_visible = True
        self.attack_index = 0
        self.just_landed = False

        self.stats_hits = 0
        self.stats_combos = 0

    def start_slide(self, direction):
        if self.state not in ["hit", "fatality", "dead", "dash"]:
            self.sliding = True
            self.slide_timer = SLIDE_DURATION
            self.slide_direction = direction
            self.state = "slide"
            self.change_x = direction * PLAYER_SPEED * 0.8

    def update_slide(self):
        if self.sliding:
            self.slide_timer -= 1
            self.change_x = self.slide_direction * PLAYER_SPEED * (self.slide_timer / SLIDE_DURATION) * 0.8

            if self.slide_timer <= 0:
                self.sliding = False
                self.change_x = 0
                if self.state == "slide":
                    self.state = "idle"

    def start_block(self):
        if (self.state not in ["hit", "fatality", "dead", "dash", "attack"] and
                self.block_cooldown <= 0 and not self.stunned):
            self.blocking = True
            self.block_timer = BLOCK_DURATION
            self.state = "block"
            self.parry_window = True

    def update_block(self):
        if self.blocking:
            self.block_timer -= 1

            if self.block_timer < BLOCK_DURATION - PARRY_WINDOW:
                self.parry_window = False

            if self.block_timer <= 0:
                self.blocking = False
                self.block_cooldown = BLOCK_COOLDOWN
                if self.state == "block":
                    self.state = "idle"

        if self.block_cooldown > 0:
            self.block_cooldown -= 1

        if self.stunned:
            self.stun_timer -= 1
            if self.stun_timer <= 0:
                self.stunned = False
                if self.state == "block":
                    self.state = "idle"

    def start_dash(self):
        if (self.state not in ["hit", "fatality", "dead"] and
                self.dash_cooldown <= 0 and self.on_ground):
            self.dashing = True
            self.dash_timer = DASH_DURATION
            self.dash_cooldown = DASH_COOLDOWN
            self.dash_invulnerable = True
            self.dash_direction = 1 if self.facing_right else -1
            self.state = "dash"
            self.change_x = self.dash_direction * DASH_SPEED

    def update_dash(self):
        if self.dashing:
            self.dash_timer -= 1

            if self.dash_timer <= 0:
                self.dashing = False
                self.dash_invulnerable = False
                self.change_x = 0
                if self.state == "dash":
                    self.state = "idle"

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

    def attack(self, attack_type):
        if self.state not in ["hit", "fatality", "dead", "dash", "block", "slide"]:
            self.attacking = True
            self.attack_timer = 10
            self.attack_type = attack_type
            self.state = "attack"

            if attack_type == "punch":
                self.attack_index = (self.attack_index + 1) % len(self.punch_textures_r)
            else:
                self.attack_index = (self.attack_index + 1) % len(self.kick_textures_r)

    def take_hit(self, damage, attacker_facing_right, attack_type):
        if self.state in ["fatality", "dead"] or self.dash_invulnerable:
            return False

        damage_multiplier = 1.0
        stun_attacker = False

        if self.blocking:
            if self.parry_window:
                damage_multiplier = 0.0
                stun_attacker = True
                self.block_timer = 0
                self.block_cooldown = BLOCK_COOLDOWN
                self.state = "block"
                self.hit_stun_timer = 10
                return "parry"
            else:
                damage_multiplier = 0.5
                self.state = "block"
                self.hit_stun_timer = 5

        actual_damage = int(damage * damage_multiplier)
        self.health -= actual_damage

        if not self.blocking or not self.parry_window:
            hit_from_right = not attacker_facing_right
            self.facing_right = hit_from_right

            direction = 1 if attacker_facing_right else -1

            if attack_type == "punch":
                self.change_x = direction * PUNCH_KNOCKBACK_X
                self.change_y = PUNCH_KNOCKBACK_Y
            else:
                self.change_x = direction * KICK_KNOCKBACK_X
                self.change_y = KICK_KNOCKBACK_Y

            self.hit_flash_timer = HIT_FLASH_DURATION * 3
            self.hit_flash_visible = True

        if self.health <= 0:
            self.start_fatality(from_right=not attacker_facing_right)
            return "fall"
        else:
            if not self.blocking:
                self.state = "hit"
                self.hit_stun_timer = 12

            return "parry" if (self.blocking and self.parry_window) else False

    def update_combo(self):
        if self.combo_counter > 0:
            self.combo_timer -= 1
            self.show_combo = True
            if self.combo_timer <= 0:
                self.combo_counter = 0
                self.show_combo = False
                self.attack_index = 0
        else:
            self.show_combo = False

    def add_combo_hit(self):
        self.combo_counter += 1
        self.combo_timer = COMBO_TIMER_MAX
        self.show_combo = True
        if self.combo_counter == 2:
            self.stats_combos += 1

    def get_combo_damage(self, base_damage):
        if self.combo_counter <= 1:
            return base_damage
        multiplier = 1.0 + (self.combo_counter - 1) * 0.15
        return int(base_damage * multiplier)

    def start_fatality(self, from_right=True):
        self.state = "fatality"
        self.fatality_phase = 1
        self.fatality_timer = 12

        self.facing_right = from_right
        direction = 1 if from_right else -1

        self.change_x = -direction * FATALITY_KNOCKBACK_X
        self.fatality_velocity_y = FATALITY_KNOCKBACK_Y
        self.bounce_count = 0
        self.fatality_ground_bounce_timer = 0
        self.on_ground = False
        self.health = 0

    def update_fatality(self):
        if self.state != "fatality":
            return

        if self.fatality_phase == 1:
            self.texture = self.fatality_1_r if self.facing_right else self.fatality_1_l

            self.fatality_velocity_y -= GRAVITY * 0.7
            self.center_x += self.change_x * 0.8
            self.center_y += self.fatality_velocity_y

            self.fatality_timer -= 1
            if self.fatality_timer <= 0:
                self.fatality_phase = 2
                self.fatality_timer = 25
                self.change_x *= 0.4
                self.fatality_velocity_y = 8

        elif self.fatality_phase == 2:
            self.texture = self.fatality_2_r if self.facing_right else self.fatality_2_l

            self.fatality_velocity_y -= GRAVITY * 1.3
            self.center_x += self.change_x * 0.6
            self.center_y += self.fatality_velocity_y

            if self.center_y <= GROUND_Y + self.height / 2:
                self.center_y = GROUND_Y + self.height / 2
                self.fatality_phase = 3
                self.bounce_count = 0
                self.fatality_ground_bounce_timer = 8
                self.change_x = abs(self.change_x) * 0.4
                self.fatality_velocity_y = 0
                self.on_ground = True
                self.just_landed = True

        elif self.fatality_phase == 3:
            self.texture = self.fatality_3_r if self.facing_right else self.fatality_3_l

            if self.on_ground:
                if self.fatality_ground_bounce_timer > 0:
                    self.fatality_ground_bounce_timer -= 1
                    return

                if self.bounce_count < len(FATALITY_BOUNCE_HEIGHTS):
                    bounce_height = FATALITY_BOUNCE_HEIGHTS[self.bounce_count]
                    self.fatality_velocity_y = bounce_height
                    self.on_ground = False
                    self.bounce_count += 1
                else:
                    self.change_x = 0
                    self.state = "dead"
                    return

            if not self.on_ground:
                self.fatality_velocity_y -= GRAVITY * 1.5
                self.center_y += self.fatality_velocity_y
                self.center_x += self.change_x * (1.0 - self.bounce_count * 0.4)

                if self.center_y <= GROUND_Y + self.height / 2:
                    self.center_y = GROUND_Y + self.height / 2
                    self.fatality_velocity_y = 0
                    self.on_ground = True
                    self.fatality_ground_bounce_timer = FATALITY_BOUNCE_DELAY
                    if self.bounce_count > 0:
                        self.just_landed = True

    def update_attack(self):
        if self.attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.attacking = False
                self.attack_type = None

        if self.hit_stun_timer > 0:
            self.hit_stun_timer -= 1
            if self.hit_stun_timer == 0 and self.state == "hit":
                self.state = "idle"

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
            if self.hit_flash_timer % HIT_FLASH_DURATION == 0:
                self.hit_flash_visible = not self.hit_flash_visible

    def update_animation(self):
        if self.state == "fatality":
            self.update_fatality()
            return
        if self.state == "dead":
            return

        if self.stunned:
            self.texture = self.hit_r if self.facing_right else self.hit_l
            return

        if self.state == "hit":
            if self.hit_flash_visible:
                self.texture = self.hit_r if self.facing_right else self.hit_l
            return

        if self.state == "block":
            self.texture = self.block_r if self.facing_right else self.block_l
            return

        if self.state == "dash":
            self.texture = self.dash_r if self.facing_right else self.dash_l
            return

        if self.state == "slide":
            self.texture = self.slay_r if self.facing_right else self.slay_l
            return

        if self.attacking:
            if self.attack_type == "punch":
                tex = self.punch_textures_r[self.attack_index]
            else:
                tex = self.kick_textures_r[self.attack_index]

            self.texture = tex if self.facing_right else tex.flip_horizontally()

        elif not self.on_ground:
            self.texture = self.jump_r if self.change_y > 0 else self.fall_r
            if not self.facing_right:
                self.texture = self.texture.flip_horizontally()

        elif self.change_x != 0 and not self.sliding:
            self.walk_timer += 1
            if self.walk_timer >= 5:
                self.walk_frame = (self.walk_frame + 1) % len(self.run_r)
                self.walk_timer = 0
            self.texture = self.run_r[self.walk_frame] if self.facing_right else self.run_l[self.walk_frame]

        else:
            self.idle_frame_timer += 1
            if self.idle_frame_timer >= IDLE_ANIMATION_SPEED:
                self.idle_frame = (self.idle_frame + 1) % len(self.idle_textures_right)
                self.idle_frame_timer = 0

            self.texture = self.idle_textures_right[self.idle_frame] if self.facing_right else self.idle_textures_left[
                self.idle_frame]


# =================== GAME WINDOW ===================
class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.ARSENIC)

        try:
            from pyglet.image import load as pyglet_load
            icon_path = os.path.join(TEXTURES_PATH, "Stand_R_1.png")
            if os.path.exists(icon_path):
                # Этот метод наследуется от pyglet и устанавливает иконку[citation:2]
                self.set_icon(pyglet_load(icon_path))
                print(f"Иконка установлена: {icon_path}")
            else:
                print(f"Файл иконки не найден: {icon_path}")
        except Exception as e:
            print(f"Не удалось загрузить иконку: {e}")
            # ====================================================

        self.camera = arcade.Camera2D()
        self.ui_camera = arcade.Camera2D()

        self.camera = arcade.Camera2D()
        self.ui_camera = arcade.Camera2D()

        self.state = "MENU"

        # ===== UI Buttons с новой позицией кнопки Назад =====
        self.btn_play = UIButton("Играть", SCREEN_WIDTH / 2, 420, 260, 60)
        self.btn_stats = UIButton("Статистика", SCREEN_WIDTH / 2, 345, 260, 60)
        self.btn_levels = UIButton("Выбор уровня", SCREEN_WIDTH / 2, 270, 260, 60)
        self.btn_controls = UIButton("Управление", SCREEN_WIDTH / 2, 195, 260, 60)
        self.btn_settings = UIButton("Настройки", SCREEN_WIDTH / 2, 120, 260, 60)
        self.btn_exit = UIButton("Выход", SCREEN_WIDTH / 2, 45, 260, 60)

        self.btn_level_main = UIButton("Основной уровень", SCREEN_WIDTH / 2, 320, 320, 60)
        self.btn_level_flat = UIButton("Плоский уровень", SCREEN_WIDTH / 2, 240, 320, 60)
        self.btn_back = UIButton("Назад", SCREEN_WIDTH / 2, 100, 260, 60)  # Изменена позиция

        # ===== Settings =====
        self.settings_shake = True
        self.settings_slowmo = True
        self.settings_music = True
        self.settings_sound = True

        # ===== Control Settings =====
        self.control_settings_buttons = []
        self.current_control_button = None
        self.default_controls_p1 = {
            "left": arcade.key.A,
            "right": arcade.key.D,
            "jump": arcade.key.W,
            "punch": arcade.key.Q,
            "kick": arcade.key.E,
            "block": arcade.key.S,
            "dash": arcade.key.LSHIFT
        }
        self.default_controls_p2 = {
            "left": arcade.key.LEFT,
            "right": arcade.key.RIGHT,
            "jump": arcade.key.UP,
            "punch": arcade.key.K,
            "kick": arcade.key.L,
            "block": arcade.key.DOWN,
            "dash": arcade.key.RSHIFT
        }

        self.controls_p1 = self.load_controls("p1", self.default_controls_p1)
        self.controls_p2 = self.load_controls("p2", self.default_controls_p2)

        # ===== Level choice =====
        self.selected_level = "main"

        # ===== Input names =====
        self.input_stage = 1
        self.p1_name = ""
        self.p2_name = ""

        # ===== countdown =====
        self.countdown_timer = 0

        # ===== fight timer =====
        self.round_time_left = ROUND_TIME
        self.round_frame_timer = 0

        # ===== records =====
        self.records = self.load_records()
        self.record_name = ""
        self.record_wins = 0
        self.update_record_display()

        # ===== textures =====
        self.bg_far = arcade.load_texture(os.path.join(TEXTURES_PATH, "bg_far.png"))
        self.bg_mid = arcade.load_texture(os.path.join(TEXTURES_PATH, "bg_mid.png"))
        self.bg_near = arcade.load_texture(os.path.join(TEXTURES_PATH, "bg_near.png"))

        self.bg_scale = 0.83
        self.bg_far_factor = 0.10
        self.bg_mid_factor = 0.20
        self.bg_near_factor = 0.35

        self.ground_tile = arcade.load_texture(os.path.join(TEXTURES_PATH, "ground_tile.png"))
        self.platform_texture = arcade.load_texture(os.path.join(TEXTURES_PATH, "Wood.png"))
        self.border_texture = self.platform_texture

        # ===== sound system =====
        self.sounds = {}
        self.music_sound = None
        self.music_player = None
        self.load_sounds()

        self.verify_folder_structure()

        # ===== particle system =====
        self.particle_system = ParticleSystem()

        # ===== map =====
        self.platforms = arcade.SpriteList(use_spatial_hash=True)
        self.border_sprites = arcade.SpriteList(use_spatial_hash=True)

        self.create_map()

        # ===== players =====
        self.p1 = Player(200, "P1", arcade.color.BLUE, self.controls_p1)
        self.p2 = Player(400, "P2", arcade.color.RED, self.controls_p2)
        self.players = arcade.SpriteList()
        self.players.extend([self.p1, self.p2])

        self.keys = set()
        self.hit_stop = 0
        self.screen_shake = 0
        self.slow_motion = 0
        self.fatality_effects = []

        self.winner = None
        self.last_fight_duration = 0

        # ===== start background music =====
        if self.settings_music:
            self.play_background_music()

    # =================== SOUND SYSTEM ===================
    def load_sounds(self):
        sound_files = {
            "die": "Die.wav",
            "punch1": "Punch_1.wav",
            "punch2": "Punch_2.wav",
            "punch3": "Punch_3.wav",
            "punch_block": "Punch_block.wav",
            "punch_miss": "Punch_miss.wav",
            "fall": "Fall.mp3",
            "top": "Top.mp3",
            "run": "Run.mp3",
        }

        for sound_name, filename in sound_files.items():
            file_path = os.path.join(SOUNDS_PATH, filename)
            if os.path.exists(file_path):
                streaming = filename.endswith('.mp3') and sound_name != 'run'
                self.sounds[sound_name] = arcade.load_sound(file_path, streaming=streaming)
                print(f"Загружен звук: {sound_name} из {filename}")
            else:
                print(f"Предупреждение: файл {file_path} не найден")
                self.sounds[sound_name] = None

        print(f"Всего загружено {len([s for s in self.sounds.values() if s])} звуков")

    def verify_folder_structure(self):
        print("\n=== Проверка структуры папок ===")

        folders = [ASSET_PATH, SOUNDS_PATH, TEXTURES_PATH]
        for folder in folders:
            if os.path.exists(folder):
                print(f"✓ Папка найдена: {folder}")
                files = os.listdir(folder)
                print(f"  Файлов: {len(files)}")
            else:
                print(f"✗ Папка отсутствует: {folder}")

        print("\n=== Проверка звуковых файлов ===")
        sound_files = ["Fall.mp3", "Top.mp3", "Run.mp3", "Die.wav", "Punch_1.wav"]
        for sf in sound_files:
            path = os.path.join(SOUNDS_PATH, sf)
            print(f"{'✓' if os.path.exists(path) else '✗'} {sf}")

        print("\n=== Проверка текстур ===")
        texture_files = ["bg_far.png", "bg_mid.png", "bg_near.png", "Wood.png", "ground_tile.png"]
        for tf in texture_files:
            path = os.path.join(TEXTURES_PATH, tf)
            print(f"{'✓' if os.path.exists(path) else '✗'} {tf}")

    def play_background_music(self):
        if not self.settings_music:
            return

        # Останавливаем предыдущую музыку, если она играет
        self.stop_background_music()

        music_path = os.path.join(SOUNDS_PATH, "Music.mp3")

        if not os.path.exists(music_path):
            alt_names = ["music.mp3", "background.mp3", "background_music.mp3"]
            for alt_name in alt_names:
                alt_path = os.path.join(SOUNDS_PATH, alt_name)
                if os.path.exists(alt_path):
                    music_path = alt_path
                    print(f"Найден альтернативный файл: {alt_name}")
                    break
            else:
                print("Музыкальный файл не найден")
                return

        self.music_sound = arcade.Sound(music_path, streaming=True)
        self.music_player = self.music_sound.play(volume=0.3, loop=True)

        if self.music_player:
            print(f"Фоновая музыка запущена: {os.path.basename(music_path)}")


    def stop_background_music(self):
        if self.music_player:
            self.music_player.stop()
            self.music_player = None
        if hasattr(self, 'music_sound'):
            self.music_sound = None

    def play_sound(self, sound_name, volume=1.0):
        if not self.settings_sound:
            return None

        if sound_name not in self.sounds or self.sounds[sound_name] is None:
            return None

        playback = self.sounds[sound_name].play(volume=volume)
        return playback

    def play_fall_sound(self):
        self.play_sound("fall", volume=0.7)

    def play_top_sound(self):
        self.play_sound("top", volume=0.5)

    def play_run_sound(self):
        self.play_sound("run", volume=0.3)

    # =================== RECORDS SYSTEM ===================
    def load_records(self):
        records = {}
        if os.path.exists(RECORDS_FILE):
            with open(RECORDS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            player_name = parts[0]
                            stats = parts[1].split(',')
                            if len(stats) >= 4:
                                records[player_name] = {
                                    "wins": int(stats[0]),
                                    "total_hits": int(stats[1]),
                                    "total_combos": int(stats[2]),
                                    "total_fights": int(stats[3]),
                                    "last_fight": stats[4] if len(stats) > 4 else ""
                                }
        return records

    def save_records(self):
        with open(RECORDS_FILE, 'w', encoding='utf-8') as f:
            for player_name, stats in self.records.items():
                line = f"{player_name}:{stats.get('wins', 0)},{stats.get('total_hits', 0)},{stats.get('total_combos', 0)},{stats.get('total_fights', 0)},{stats.get('last_fight', '')}\n"
                f.write(line)

    def update_record_display(self):
        if self.records:
            max_wins = 0
            best_player = ""

            for player_name, stats in self.records.items():
                if stats.get("wins", 0) > max_wins:
                    max_wins = stats["wins"]
                    best_player = player_name

            if best_player:
                self.record_name = best_player
                self.record_wins = max_wins
        else:
            self.record_name = ""
            self.record_wins = 0

    def update_player_record(self, player_name, stats):
        if player_name not in self.records:
            self.records[player_name] = {
                "wins": 0,
                "total_hits": 0,
                "total_combos": 0,
                "total_fights": 0,
                "last_fight": ""
            }

        self.records[player_name]["wins"] += 1
        self.records[player_name]["total_hits"] += stats.get("hits", 0)
        self.records[player_name]["total_combos"] += stats.get("combos", 0)
        self.records[player_name]["total_fights"] += 1
        self.records[player_name]["last_fight"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        self.save_records()
        self.update_record_display()

    # =================== CONTROLS MANAGEMENT ===================
    def load_controls(self, player, default_controls):
        controls = default_controls.copy()
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{player}_"):
                        parts = line.split('=')
                        if len(parts) == 2:
                            key_name = parts[0].replace(f"{player}_", "")
                            key_value = int(parts[1])
                            if key_name in controls:
                                controls[key_name] = key_value
                    elif line.startswith("shake="):
                        self.settings_shake = line.split('=')[1].strip() == "True"
                    elif line.startswith("slowmo="):
                        self.settings_slowmo = line.split('=')[1].strip() == "True"
                    elif line.startswith("music="):
                        self.settings_music = line.split('=')[1].strip() == "True"
                    elif line.startswith("sound="):
                        self.settings_sound = line.split('=')[1].strip() == "True"
        return controls

    def save_controls(self):
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            for key_name, key_value in self.controls_p1.items():
                f.write(f"p1_{key_name}={key_value}\n")

            for key_name, key_value in self.controls_p2.items():
                f.write(f"p2_{key_name}={key_value}\n")

            f.write(f"shake={self.settings_shake}\n")
            f.write(f"slowmo={self.settings_slowmo}\n")
            f.write(f"music={self.settings_music}\n")
            f.write(f"sound={self.settings_sound}\n")

    def create_control_settings_ui(self):
        self.control_settings_buttons = []

        left_column_x = SCREEN_WIDTH / 2 - 220
        right_column_x = SCREEN_WIDTH / 2 + 220

        headers_y = 500

        actions_p1 = [
            ("Движение влево", "left"),
            ("Движение вправо", "right"),
            ("Прыжок", "jump"),
            ("Удар рукой", "punch"),
            ("Удар ногой", "kick"),
        ]

        for i, (action_text, action_key) in enumerate(actions_p1):
            btn = KeyBindingButton(
                f"P1: {action_text}",
                left_column_x,
                headers_y - i * 60,
                320,
                40,
                ""
            )
            btn.action_key = action_key
            btn.player = "p1"
            self.control_settings_buttons.append(btn)

        actions_p1_extra = [
            ("Блок", "block"),
            ("Дэш", "dash"),
        ]

        for i, (action_text, action_key) in enumerate(actions_p1_extra):
            btn = KeyBindingButton(
                f"P1: {action_text}",
                left_column_x,
                headers_y - (len(actions_p1) + i) * 60,
                320,
                40,
                ""
            )
            btn.action_key = action_key
            btn.player = "p1"
            self.control_settings_buttons.append(btn)

        for i, (action_text, action_key) in enumerate(actions_p1):
            btn = KeyBindingButton(
                f"P2: {action_text}",
                right_column_x,
                headers_y - i * 60,
                320,
                40,
                ""
            )
            btn.action_key = action_key
            btn.player = "p2"
            self.control_settings_buttons.append(btn)

        for i, (action_text, action_key) in enumerate(actions_p1_extra):
            btn = KeyBindingButton(
                f"P2: {action_text}",
                right_column_x,
                headers_y - (len(actions_p1) + i) * 60,
                320,
                40,
                ""
            )
            btn.action_key = action_key
            btn.player = "p2"
            self.control_settings_buttons.append(btn)

        self.update_control_display_names()

    def update_control_display_names(self):
        key_names = {
            arcade.key.A: "A", arcade.key.B: "B", arcade.key.C: "C", arcade.key.D: "D",
            arcade.key.E: "E", arcade.key.F: "F", arcade.key.G: "G", arcade.key.H: "H",
            arcade.key.I: "I", arcade.key.J: "J", arcade.key.K: "K", arcade.key.L: "L",
            arcade.key.M: "M", arcade.key.N: "N", arcade.key.O: "O", arcade.key.P: "P",
            arcade.key.Q: "Q", arcade.key.R: "R", arcade.key.S: "S", arcade.key.T: "T",
            arcade.key.U: "U", arcade.key.V: "V", arcade.key.W: "W", arcade.key.X: "X",
            arcade.key.Y: "Y", arcade.key.Z: "Z",
            arcade.key.LEFT: "←", arcade.key.RIGHT: "→", arcade.key.UP: "↑", arcade.key.DOWN: "↓",
            arcade.key.SPACE: "Space", arcade.key.ENTER: "Enter", arcade.key.ESCAPE: "Esc",
            arcade.key.LSHIFT: "LShift", arcade.key.RSHIFT: "RShift",
            arcade.key.LCTRL: "LCtrl", arcade.key.RCTRL: "RCtrl",
            arcade.key.LALT: "LAlt", arcade.key.RALT: "RAlt",
            arcade.key.TAB: "Tab", arcade.key.BACKSPACE: "Backspace",
            arcade.key.INSERT: "Ins", arcade.key.DELETE: "Del",
            arcade.key.HOME: "Home", arcade.key.END: "End",
            arcade.key.PAGEUP: "PgUp", arcade.key.PAGEDOWN: "PgDown",
            arcade.key.NUM_0: "Num0", arcade.key.NUM_1: "Num1", arcade.key.NUM_2: "Num2",
            arcade.key.NUM_3: "Num3", arcade.key.NUM_4: "Num4", arcade.key.NUM_5: "Num5",
            arcade.key.NUM_6: "Num6", arcade.key.NUM_7: "Num7", arcade.key.NUM_8: "Num8",
            arcade.key.NUM_9: "Num9"
        }

        for btn in self.control_settings_buttons:
            if btn.player == "p1":
                key_value = self.controls_p1[btn.action_key]
            else:
                key_value = self.controls_p2[btn.action_key]

            btn.key_name = key_names.get(key_value, f"Key{key_value}")

    # =================== MAP ===================
    def create_map(self):
        self.platforms = arcade.SpriteList(use_spatial_hash=True)
        self.border_sprites = arcade.SpriteList(use_spatial_hash=True)

        wall_w = 60
        wall_h = 700

        left_wall = arcade.Sprite(self.border_texture)
        left_wall.width = wall_w
        left_wall.height = wall_h
        left_wall.center_x = LEVEL_LEFT + wall_w / 2
        left_wall.center_y = GROUND_Y + wall_h / 2 - 40

        right_wall = arcade.Sprite(self.border_texture)
        right_wall.width = wall_w
        right_wall.height = wall_h
        right_wall.center_x = LEVEL_RIGHT - wall_w / 2
        right_wall.center_y = GROUND_Y + wall_h / 2 - 40

        self.border_sprites.append(left_wall)
        self.border_sprites.append(right_wall)

        if self.selected_level == "main":
            for x, y, w, h in [
                (200, 260, 280, 40),
                (650, 300, 320, 40),
                (1100, 260, 280, 40),
                (720, 420, 260, 40),
            ]:
                s = arcade.Sprite(self.platform_texture)
                s.width = w
                s.height = h
                s.center_x = x
                s.center_y = y
                self.platforms.append(s)

        elif self.selected_level == "flat":
            pass

    # =================== DRAW HELPERS ===================
    def draw_parallax_layer(self, texture, cam_x, cam_y, factor):
        w = texture.width * self.bg_scale
        h = texture.height * self.bg_scale

        x = cam_x * factor
        y = cam_y * factor

        arcade.draw_texture_rect(
            texture,
            arcade.LRBT(
                x - w / 2,
                x + w / 2,
                y - h / 2,
                y + h / 2
            )
        )

    def draw_ground(self):
        tile_w = self.ground_tile.width
        tile_h = self.ground_tile.height
        ground_scale = 0.15
        draw_w = tile_w * ground_scale
        draw_h = tile_h * ground_scale

        start_x = LEVEL_LEFT - 600
        end_x = LEVEL_RIGHT + 600

        x = start_x
        while x < end_x:
            rect = arcade.rect.XYWH(x + draw_w / 2, GROUND_Y - 140, draw_w, draw_h)
            arcade.draw_texture_rect(self.ground_tile, rect)
            x += draw_w * 0.95

    # =================== UI DRAW ===================
    def draw_health_bar(self, player, x, y, align="left"):
        bar_width = 300
        bar_height = 18
        health_ratio = max(0, min(1, player.health / player.max_health))
        fill_width = bar_width * health_ratio

        bg_rect = arcade.rect.XYWH(x + bar_width / 2, y, bar_width, bar_height)
        fill_rect = arcade.rect.XYWH(x + fill_width / 2, y, fill_width, bar_height)

        arcade.draw_rect_filled(bg_rect, arcade.color.DARK_GRAY)
        arcade.draw_rect_filled(fill_rect, arcade.color.RED if player.health > 20 else arcade.color.DARK_RED)
        arcade.draw_rect_outline(bg_rect, arcade.color.ARSENIC, 2)

        # Исправлено: для игрока 1 текст справа, для игрока 2 - слева
        if align == "left":
            text_x = x + bar_width + 10
            anchor_x = "left"
        else:
            text_x = x - 10
            anchor_x = "right"

        arcade.draw_text(
            player.name,
            text_x,
            y,
            player.name_color,
            16,
            anchor_x=anchor_x,
            anchor_y="center",
            bold=True
        )

    def draw_combo_counter(self, player, x, y):
        if player.show_combo and player.combo_counter > 1:
            combo_text = f"COMBO x{player.combo_counter}"
            alpha = min(255, player.combo_timer * 4)

            size = 24 + min(10, (COMBO_TIMER_MAX - player.combo_timer) // 5)

            arcade.draw_text(
                combo_text,
                x,
                y,
                (255, 215, 0, alpha),
                size,
                anchor_x="center",
                bold=True
            )

    def draw_dash_cooldown(self, player, x, y):
        size = 40
        padding = 5

        bg_rect = arcade.rect.XYWH(x, y, size + padding * 2, size + padding * 2)
        arcade.draw_rect_filled(bg_rect, arcade.color.DARK_SLATE_GRAY)

        icon_color = arcade.color.LIGHT_GRAY if player.dash_cooldown <= 0 else arcade.color.DARK_GRAY
        arcade.draw_text(
            ">>",
            x,
            y,
            icon_color,
            size // 2,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        if player.dash_cooldown > 0:
            seconds = player.dash_cooldown // 60 + 1
            arcade.draw_text(
                str(seconds),
                x,
                y,
                arcade.color.WHITE,
                size // 3,
                anchor_x="center",
                anchor_y="center",
                bold=True
            )

            progress = 1.0 - (player.dash_cooldown / DASH_COOLDOWN)
            arcade.draw_arc_filled(
                x, y, size // 2, size // 2,
                arcade.color.CYAN,
                0, 360 * progress
            )

    # =================== STATISTICS SCREEN ===================
    def load_battle_history(self):
        history = []
        if os.path.exists(BATTLE_HISTORY_FILE):
            with open(BATTLE_HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                battles = content.split("===")
                for battle in battles:
                    if battle.strip():
                        history.append("===" + battle.strip())
        return history

    def draw_stats_screen(self):
        arcade.draw_text("Статистика боев", SCREEN_WIDTH / 2, 520, arcade.color.WHITE, 36,
                         anchor_x="center", bold=True)

        history = self.load_battle_history()

        start_y = 450
        line_height = 24

        if not history:
            arcade.draw_text("История боев пуста", SCREEN_WIDTH / 2, 400,
                             arcade.color.LIGHT_GRAY, 20, anchor_x="center")
        else:
            recent_battles = history[-5:]
            recent_battles.reverse()

            for i, battle in enumerate(recent_battles):
                lines = battle.split("\n")
                if len(lines) > 2:
                    date_line = lines[0] if lines[0].startswith("===") else ""
                    winner_line = ""
                    for line in lines:
                        if "Победитель:" in line:
                            winner_line = line
                            break

                    if date_line:
                        arcade.draw_text(date_line[4:], 50, start_y - i * line_height * 3,
                                         arcade.color.LIGHT_BLUE, 16)
                    if winner_line:
                        arcade.draw_text(winner_line, 50, start_y - i * line_height * 3 - 25,
                                         arcade.color.GOLD, 16)

        arcade.draw_text(f"Всего боев: {len(history)}", SCREEN_WIDTH / 2, 150,
                         arcade.color.LIGHT_GREEN, 20, anchor_x="center")

        if self.record_name:
            arcade.draw_text(f"Лучший боец: {self.record_name} ({self.record_wins} побед)",
                             SCREEN_WIDTH / 2, 170, arcade.color.GOLD, 18, anchor_x="center")

        self.btn_back.draw()

        arcade.draw_text("Нажмите ESC для возврата в меню", SCREEN_WIDTH / 2, 50,
                         arcade.color.LIGHT_GRAY, 14, anchor_x="center")

    # =================== GAME LOOP ===================
    def on_draw(self):
        self.clear()

        if self.state in ["MENU", "SETTINGS", "LEVELS", "NAME_INPUT", "RESULTS", "CONTROL_SETTINGS", "STATS"]:
            self.ui_camera.use()
            self.draw_menu_screens()
            return

        self.camera.use()
        cam_x, cam_y = self.camera.position

        if self.selected_level == "flat":
            arcade.draw_lrbt_rectangle_filled(0, LEVEL_RIGHT, 0, SCREEN_HEIGHT * 2, arcade.color.DARK_SLATE_BLUE)
        else:
            self.draw_parallax_layer(self.bg_far, cam_x + 5650, cam_y + 4700, self.bg_far_factor)
            self.draw_parallax_layer(self.bg_mid, cam_x + 2000, cam_y + 1500, self.bg_mid_factor)
            self.draw_parallax_layer(self.bg_near, cam_x + 1200, cam_y + 600, self.bg_near_factor)

        self.draw_ground()

        self.platforms.draw()
        self.border_sprites.draw()

        self.particle_system.draw()

        self.players.draw()

        for p in self.players:
            arcade.draw_text(
                p.name,
                p.center_x - 20,
                p.center_y + p.height / 2 + 10,
                p.name_color,
                14,
                bold=True
            )

        self.ui_camera.use()
        self.draw_health_bar(self.p1, 30, SCREEN_HEIGHT - 50)
        self.draw_health_bar(self.p2, SCREEN_WIDTH - 330, SCREEN_HEIGHT - 50)

        arcade.draw_text(
            f"{self.round_time_left:02d}",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 55,
            arcade.color.WHITE,
            28,
            anchor_x="center",
            bold=True
        )

        self.draw_combo_counter(self.p1, SCREEN_WIDTH / 4, SCREEN_HEIGHT - 110)
        self.draw_combo_counter(self.p2, SCREEN_WIDTH * 3 / 4, SCREEN_HEIGHT - 110)

        self.draw_dash_cooldown(self.p1, 60, SCREEN_HEIGHT - 130)
        self.draw_dash_cooldown(self.p2, SCREEN_WIDTH - 60, SCREEN_HEIGHT - 130)

        if self.record_name:
            arcade.draw_text(
                f"РЕКОРД: {self.record_name} ({self.record_wins} побед)",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT - 90,
                arcade.color.GOLD,
                16,
                anchor_x="center",
                bold=True
            )

        if self.state == "COUNTDOWN":
            t = self.countdown_timer
            text = "FIGHT!"
            if t > 120:
                text = "3"
            elif t > 60:
                text = "2"
            elif t > 0:
                text = "1"
            arcade.draw_text(
                text,
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                80,
                anchor_x="center",
                anchor_y="center",
                bold=True
            )

    def draw_menu_screens(self):
        arcade.draw_text("Stickman Fighter", SCREEN_WIDTH / 2, 560, arcade.color.WHITE, 44,
                         anchor_x="center", bold=True)

        if self.state == "MENU":
            for b in [self.btn_play, self.btn_stats, self.btn_levels,
                      self.btn_controls, self.btn_settings, self.btn_exit]:
                b.draw()

            if self.record_name:
                arcade.draw_text(
                    f"Лучший боец: {self.record_name}",
                    SCREEN_WIDTH / 2,
                    500,
                    arcade.color.GOLD,
                    24,
                    anchor_x="center",
                    bold=True
                )
                arcade.draw_text(
                    f"Побед: {self.record_wins}",
                    SCREEN_WIDTH / 2,
                    470,
                    arcade.color.LIGHT_GOLDENROD_YELLOW,
                    20,
                    anchor_x="center"
                )

        elif self.state == "STATS":
            self.draw_stats_screen()

        elif self.state == "LEVELS":
            arcade.draw_text("Выбор уровня", SCREEN_WIDTH / 2, 440, arcade.color.WHITE, 28,
                             anchor_x="center", bold=True)
            self.btn_level_main.draw()
            self.btn_level_flat.draw()
            self.btn_back.draw()

            arcade.draw_text(f"Текущий: {self.selected_level}", SCREEN_WIDTH / 2, 130,
                             arcade.color.LIGHT_GRAY, 16, anchor_x="center")

        elif self.state == "SETTINGS":
            arcade.draw_text("Настройки", SCREEN_WIDTH / 2, 440, arcade.color.WHITE, 28,
                             anchor_x="center", bold=True)

            arcade.draw_text(f"Тряска: {'ВКЛ' if self.settings_shake else 'ВЫКЛ'} (S)", SCREEN_WIDTH / 2, 340,
                             arcade.color.LIGHT_GRAY, 18, anchor_x="center")
            arcade.draw_text(f"Замедление: {'ВКЛ' if self.settings_slowmo else 'ВЫКЛ'} (M)", SCREEN_WIDTH / 2, 300,
                             arcade.color.LIGHT_GRAY, 18, anchor_x="center")
            arcade.draw_text(f"Музыка: {'ВКЛ' if self.settings_music else 'ВЫКЛ'} (B)", SCREEN_WIDTH / 2, 260,
                             arcade.color.LIGHT_GRAY, 18, anchor_x="center")
            arcade.draw_text(f"Звуки: {'ВКЛ' if self.settings_sound else 'ВЫКЛ'} (V)", SCREEN_WIDTH / 2, 220,
                             arcade.color.LIGHT_GRAY, 18, anchor_x="center")

            self.btn_back.draw()

        elif self.state == "CONTROL_SETTINGS":
            arcade.draw_text("Настройки управления", SCREEN_WIDTH / 2, 540, arcade.color.WHITE, 28,
                             anchor_x="center", bold=True)

            arcade.draw_text("Игрок 1", SCREEN_WIDTH / 2 - 220, 500, arcade.color.CYAN, 20,
                             anchor_x="center", bold=True)
            arcade.draw_text("Игрок 2", SCREEN_WIDTH / 2 + 220, 500, arcade.color.PINK, 20,
                             anchor_x="center", bold=True)

            arcade.draw_text("Нажмите на кнопку, затем нажмите новую клавишу", SCREEN_WIDTH / 2, 120,
                             arcade.color.LIGHT_GRAY, 14, anchor_x="center")

            for btn in self.control_settings_buttons:
                btn.draw()

            self.btn_back.draw()

        elif self.state == "NAME_INPUT":
            arcade.draw_text("Введите имена игроков", SCREEN_WIDTH / 2, 440, arcade.color.WHITE, 28,
                             anchor_x="center", bold=True)

            p1_line = f"P1: {self.p1_name}" + ("_" if self.input_stage == 1 else "")
            p2_line = f"P2: {self.p2_name}" + ("_" if self.input_stage == 2 else "")

            arcade.draw_text(p1_line, SCREEN_WIDTH / 2, 340, arcade.color.CYAN, 22, anchor_x="center", bold=True)
            arcade.draw_text(p2_line, SCREEN_WIDTH / 2, 290, arcade.color.PINK, 22, anchor_x="center", bold=True)

            arcade.draw_text("ENTER - далее | BACKSPACE - стереть", SCREEN_WIDTH / 2, 220,
                             arcade.color.LIGHT_GRAY, 14, anchor_x="center")

        elif self.state == "RESULTS":
            arcade.draw_text("Результат боя", SCREEN_WIDTH / 2, 440, arcade.color.WHITE, 28,
                             anchor_x="center", bold=True)
            arcade.draw_text(f"Победитель: {self.winner}", SCREEN_WIDTH / 2, 360,
                             arcade.color.GOLD, 26, anchor_x="center", bold=True)

            arcade.draw_text(f"Ударов P1: {self.p1.stats_hits} | Комбо: {self.p1.stats_combos}",
                             SCREEN_WIDTH / 2, 300, arcade.color.CYAN, 16, anchor_x="center")
            arcade.draw_text(f"Ударов P2: {self.p2.stats_hits} | Комбо: {self.p2.stats_combos}",
                             SCREEN_WIDTH / 2, 270, arcade.color.PINK, 16, anchor_x="center")

            arcade.draw_text("R - Рестарт | ESC - меню", SCREEN_WIDTH / 2, 200,
                             arcade.color.LIGHT_GRAY, 16, anchor_x="center")

    # =================== UPDATE ===================
    def on_update(self, delta_time):
        if self.state in ["MENU", "SETTINGS", "LEVELS", "NAME_INPUT", "RESULTS", "CONTROL_SETTINGS", "STATS"]:
            return

        if self.state == "COUNTDOWN":
            self.countdown_timer -= 1
            if self.countdown_timer <= 0:
                self.state = "FIGHT"
            self.update_camera()
            return

        if self.slow_motion > 0:
            self.slow_motion -= 1
        if self.hit_stop > 0:
            self.hit_stop -= 1
            return

        self.round_frame_timer += 1
        if self.round_frame_timer >= 60:
            self.round_frame_timer = 0
            self.round_time_left -= 1
            if self.round_time_left <= 0:
                if self.p1.health > self.p2.health:
                    self.end_fight(self.p1)
                elif self.p2.health > self.p1.health:
                    self.end_fight(self.p2)
                else:
                    self.end_fight(None)

        slow_factor = 0.5 if (self.slow_motion > 0 and self.settings_slowmo) else 1.0

        self.particle_system.update()

        for p in self.players:
            if p.state in ["fatality", "dead"]:
                p.update_animation()
                p.update_combo()
                self.clamp_player_in_level(p)
                if p.just_landed:
                    self.play_top_sound()
                    p.just_landed = False
                continue

            p.update_block()
            p.update_dash()
            p.update_slide()

            if p.state == "run" and p.on_ground:
                p.last_move_time += 1
                if p.last_move_time > 15:
                    self.play_run_sound()
                    p.last_move_time = 0

                if p.last_move_time % 5 == 0:
                    self.particle_system.create_dust_cloud(
                        p.center_x - (10 if p.facing_right else -10),
                        p.center_y - p.height / 2,
                        1 if p.facing_right else -1,
                        3
                    )

            old_y = p.center_y

            p.change_y -= GRAVITY * slow_factor
            p.center_x += p.change_x * slow_factor
            p.center_y += p.change_y * slow_factor

            p.on_ground = False

            self.resolve_platform_collisions(p, old_y)

            if p.center_y <= GROUND_Y + p.height / 2:
                p.center_y = GROUND_Y + p.height / 2
                p.change_y = 0
                p.on_ground = True

            self.resolve_border_collisions(p)

            self.clamp_player_in_level(p)

            p.update_attack()
            p.update_animation()
            p.update_combo()

        self.handle_attacks()
        self.update_controls()
        self.update_camera()

    # =================== COLLISIONS ===================
    def clamp_player_in_level(self, p: Player):
        half = p.width / 2
        if p.center_x < LEVEL_LEFT + half + 30:
            p.center_x = LEVEL_LEFT + half + 30
            p.change_x = 0
        if p.center_x > LEVEL_RIGHT - half - 30:
            p.center_x = LEVEL_RIGHT - half - 30
            p.change_x = 0

    def resolve_border_collisions(self, p: Player):
        hits = arcade.check_for_collision_with_list(p, self.border_sprites)
        if not hits:
            return
        for wall in hits:
            if p.center_x < wall.center_x:
                p.right = wall.left
            else:
                p.left = wall.right
            p.change_x = 0

    def resolve_platform_collisions(self, p: Player, old_y: float):
        if p.change_y > 0:
            return
        hits = arcade.check_for_collision_with_list(p, self.platforms)
        if not hits:
            return

        for plat in hits:
            plat_top = plat.top
            player_bottom = p.bottom
            old_bottom = old_y - p.height / 2

            if old_bottom >= plat_top - 5 and player_bottom <= plat_top + 5:
                p.bottom = plat_top
                p.change_y = 0
                p.on_ground = True
                return

    # =================== COMBAT ===================
    def handle_attacks(self):
        self.check_attack(self.p1, self.p2)
        self.check_attack(self.p2, self.p1)

    def check_attack(self, attacker: Player, target: Player):
        if attacker.attacking:
            if attacker.attack_timer == 8:
                direction = 1 if attacker.facing_right else -1
                hitbox = arcade.SpriteSolidColor(40, 30, arcade.color.RED)
                hitbox.center_x = attacker.center_x + direction * 45
                hitbox.center_y = attacker.center_y

                if not arcade.check_for_collision(hitbox, target):
                    self.play_sound("punch_miss", 0.3)

                    move_direction = 1 if attacker.facing_right else -1
                    new_x = attacker.center_x + move_direction * PUNCH_FORWARD_MOVE

                    if LEVEL_LEFT + attacker.width / 2 + 30 <= new_x <= LEVEL_RIGHT - attacker.width / 2 - 30:
                        attacker.center_x = new_x

            if attacker.attack_timer == 5 and target.state not in ["fatality", "dead"]:
                direction = 1 if attacker.facing_right else -1
                hitbox = arcade.SpriteSolidColor(40, 30, arcade.color.RED)
                hitbox.center_x = attacker.center_x + direction * 45
                hitbox.center_y = attacker.center_y

                if arcade.check_for_collision(hitbox, target):
                    base_damage = 7
                    actual_damage = attacker.get_combo_damage(base_damage)
                    result = target.take_hit(actual_damage, attacker.facing_right, attacker.attack_type)

                    attacker.stats_hits += 1

                    if result == "fall":
                        self.play_sound("die", 0.8)
                        self.play_fall_sound()
                        self.hit_stop = 20
                        if self.settings_shake:
                            self.screen_shake = 25
                        if self.settings_slowmo:
                            self.slow_motion = FATALITY_SLOW_MO_DURATION

                        self.particle_system.create_blood_splash(
                            target.center_x, target.center_y, 25
                        )
                    elif result == "parry":
                        attacker.stunned = True
                        attacker.stun_timer = STUN_DURATION
                        attacker.state = "block"
                        self.hit_stop = 15
                        if self.settings_shake:
                            self.screen_shake = 15

                        self.play_sound("punch_block", 0.7)

                        self.particle_system.create_block_spark(
                            target.center_x + (20 if target.facing_right else -20),
                            target.center_y,
                            1 if target.facing_right else -1
                        )
                    else:
                        punch_sounds = ["punch1", "punch2", "punch3"]
                        self.play_sound(random.choice(punch_sounds), 0.6)

                        self.hit_stop = 6
                        if self.settings_shake:
                            self.screen_shake = 10
                        attacker.add_combo_hit()

                        if actual_damage > 0 and not target.blocking:
                            self.particle_system.create_blood_splash(
                                target.center_x, target.center_y, 10
                            )
                        elif target.blocking:
                            self.particle_system.create_block_spark(
                                target.center_x + (20 if target.facing_right else -20),
                                target.center_y,
                                1 if target.facing_right else -1
                            )

                    attacker.attacking = False
                    attacker.attack_timer = 0

        if target.state == "dead":
            self.end_fight(attacker)

    # =================== CAMERA ===================
    def update_camera(self):
        mid_x = (self.p1.center_x + self.p2.center_x) / 2
        mid_y = (self.p1.center_y + self.p2.center_y) / 2

        dist = abs(self.p1.center_x - self.p2.center_x)
        zoom = max(0.65, min(1.2, 850 / (dist + 1)))

        shake_x = shake_y = 0
        if self.screen_shake > 0:
            self.screen_shake -= 1
            intensity = 6
            shake_x = random.randint(-intensity, intensity)
            shake_y = random.randint(-intensity, intensity)

        self.camera.position = (mid_x + shake_x, mid_y + shake_y + 130)
        self.camera.zoom = zoom

    # =================== CONTROLS ===================
    def update_controls(self):
        if self.state != "FIGHT":
            return

        if self.p1.state not in ["hit", "fatality", "dead", "dash", "slide", "stunned"]:
            self.p1.walking_left = False
            self.p1.walking_right = False

            left_pressed = any(key in self.keys for key in [self.p1.controls["left"]])
            right_pressed = any(key in self.keys for key in [self.p1.controls["right"]])

            if left_pressed and not right_pressed:
                self.p1.change_x = -PLAYER_SPEED
                self.p1.facing_right = False
                self.p1.walking_left = True
                if self.p1.state != "run":
                    self.p1.state = "run"
            elif right_pressed and not left_pressed:
                self.p1.change_x = PLAYER_SPEED
                self.p1.facing_right = True
                self.p1.walking_right = True
                if self.p1.state != "run":
                    self.p1.state = "run"
            else:
                if self.p1.change_x != 0 and self.p1.on_ground and not self.p1.sliding:
                    self.p1.start_slide(self.p1.change_x / abs(self.p1.change_x) if self.p1.change_x != 0 else 0)
                elif not self.p1.sliding:
                    self.p1.change_x = 0
                    if self.p1.state == "run":
                        self.p1.state = "idle"

        if self.p2.state not in ["hit", "fatality", "dead", "dash", "slide", "stunned"]:
            self.p2.walking_left = False
            self.p2.walking_right = False

            left_pressed = any(key in self.keys for key in [self.p2.controls["left"]])
            right_pressed = any(key in self.keys for key in [self.p2.controls["right"]])

            if left_pressed and not right_pressed:
                self.p2.change_x = -PLAYER_SPEED
                self.p2.facing_right = False
                self.p2.walking_left = True
                if self.p2.state != "run":
                    self.p2.state = "run"
            elif right_pressed and not left_pressed:
                self.p2.change_x = PLAYER_SPEED
                self.p2.facing_right = True
                self.p2.walking_right = True
                if self.p2.state != "run":
                    self.p2.state = "run"
            else:
                if self.p2.change_x != 0 and self.p2.on_ground and not self.p2.sliding:
                    self.p2.start_slide(self.p2.change_x / abs(self.p2.change_x) if self.p2.change_x != 0 else 0)
                elif not self.p2.sliding:
                    self.p2.change_x = 0
                    if self.p2.state == "run":
                        self.p2.state = "idle"

    # =================== GAME FLOW ===================
    def start_game(self):
        # Убрали вызов play_background_music, чтобы музыка не накладывалась
        self.p1 = Player(200, self.p1_name or "P1", arcade.color.BLUE, self.controls_p1)
        self.p2 = Player(400, self.p2_name or "P2", arcade.color.RED, self.controls_p2)
        self.players = arcade.SpriteList()
        self.players.extend([self.p1, self.p2])

        self.round_time_left = ROUND_TIME
        self.round_frame_timer = 0

        self.create_map()

        self.countdown_timer = 180
        self.state = "COUNTDOWN"

    def end_fight(self, winner_player):
        self.state = "RESULTS"

        duration = ROUND_TIME - self.round_time_left
        self.last_fight_duration = duration

        if winner_player is None:
            self.winner = "Ничья"
        else:
            self.winner = winner_player.name

            stats = {
                "hits": winner_player.stats_hits,
                "combos": winner_player.stats_combos
            }
            self.update_player_record(winner_player.name, stats)

        self.save_stats_file(winner_player)

    def save_stats_file(self, winner_player):
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        winner_name = "Ничья" if winner_player is None else winner_player.name
        duration = ROUND_TIME - self.round_time_left

        battle_record = [
            f"=== Бой {dt} ===",
            f"Уровень: {self.selected_level}",
            f"Длительность: {duration} сек",
            f"Игрок 1: {self.p1.name} | Здоровье: {self.p1.health}/{self.p1.max_health} | Ударов: {self.p1.stats_hits} | Комбо: {self.p1.stats_combos}",
            f"Игрок 2: {self.p2.name} | Здоровье: {self.p2.health}/{self.p2.max_health} | Ударов: {self.p2.stats_hits} | Комбо: {self.p2.stats_combos}",
            f"Победитель: {winner_name}",
            ""
        ]

        with open(BATTLE_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write("\n".join(battle_record))
            f.write("\n\n")
        print(f"Статистика боя сохранена в {BATTLE_HISTORY_FILE}")

        if winner_player is not None:
            stats = {
                "hits": winner_player.stats_hits,
                "combos": winner_player.stats_combos
            }
            self.update_player_record(winner_player.name, stats)

    # =================== INPUT EVENTS ===================
    def on_mouse_motion(self, x, y, dx, dy):
        if self.state == "MENU":
            for b in [self.btn_play, self.btn_stats, self.btn_levels,
                      self.btn_controls, self.btn_settings, self.btn_exit]:
                b.hover = b.hit_test(x, y)

        elif self.state == "LEVELS":
            for b in [self.btn_level_main, self.btn_level_flat, self.btn_back]:
                b.hover = b.hit_test(x, y)

        elif self.state == "SETTINGS":
            self.btn_back.hover = self.btn_back.hit_test(x, y)

        elif self.state == "CONTROL_SETTINGS":
            self.btn_back.hover = self.btn_back.hit_test(x, y)
            for btn in self.control_settings_buttons:
                btn.hover = btn.hit_test(x, y)

        elif self.state == "STATS":
            self.btn_back.hover = self.btn_back.hit_test(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == "MENU":
            if self.btn_play.hit_test(x, y):
                self.state = "NAME_INPUT"
                self.input_stage = 1
                self.p1_name = ""
                self.p2_name = ""
            elif self.btn_stats.hit_test(x, y):
                self.state = "STATS"
            elif self.btn_levels.hit_test(x, y):
                self.state = "LEVELS"
            elif self.btn_controls.hit_test(x, y):
                self.create_control_settings_ui()
                self.update_control_display_names()
                self.state = "CONTROL_SETTINGS"
            elif self.btn_settings.hit_test(x, y):
                self.state = "SETTINGS"
            elif self.btn_exit.hit_test(x, y):
                arcade.close_window()

        elif self.state == "LEVELS":
            if self.btn_level_main.hit_test(x, y):
                self.selected_level = "main"
                self.create_map()
            elif self.btn_level_flat.hit_test(x, y):
                self.selected_level = "flat"
                self.create_map()
            elif self.btn_back.hit_test(x, y):
                self.state = "MENU"

        elif self.state == "SETTINGS":
            if self.btn_back.hit_test(x, y):
                self.state = "MENU"

        elif self.state == "STATS":
            if self.btn_back.hit_test(x, y):
                self.state = "MENU"

        elif self.state == "CONTROL_SETTINGS":
            if self.btn_back.hit_test(x, y):
                self.state = "MENU"
                self.save_controls()
            else:
                for btn in self.control_settings_buttons:
                    if btn.hit_test(x, y):
                        for b in self.control_settings_buttons:
                            b.waiting_for_input = False
                        btn.waiting_for_input = True
                        self.current_control_button = btn
                        break

    def on_key_press(self, key, modifiers):
        self.keys.add(key)

        if self.state == "CONTROL_SETTINGS" and self.current_control_button:
            if key != arcade.key.ESCAPE:
                if self.current_control_button.player == "p1":
                    self.controls_p1[self.current_control_button.action_key] = key
                else:
                    self.controls_p2[self.current_control_button.action_key] = key

                self.update_control_display_names()

            self.current_control_button.waiting_for_input = False
            self.current_control_button = None
            return

        if key == arcade.key.ESCAPE:
            if self.state == "CONTROL_SETTINGS":
                if self.current_control_button:
                    self.current_control_button.waiting_for_input = False
                    self.current_control_button = None
                else:
                    self.state = "MENU"
                    self.save_controls()
            elif self.state == "STATS":
                self.state = "MENU"
            elif self.state == "FIGHT":
                pass
            else:
                self.state = "MENU"
            return

        if self.state == "SETTINGS":
            if key == arcade.key.S:
                self.settings_shake = not self.settings_shake
                self.save_controls()
            if key == arcade.key.M:
                self.settings_slowmo = not self.settings_slowmo
                self.save_controls()
            if key == arcade.key.B:
                self.settings_music = not self.settings_music
                self.save_controls()
                if self.settings_music:
                    self.play_background_music()
                else:
                    self.stop_background_music()
            if key == arcade.key.V:
                self.settings_sound = not self.settings_sound
                self.save_controls()

        if self.state == "NAME_INPUT":
            if key == arcade.key.ENTER:
                if self.input_stage == 1:
                    self.input_stage = 2
                else:
                    self.start_game()
            elif key == arcade.key.BACKSPACE:
                if self.input_stage == 1:
                    self.p1_name = self.p1_name[:-1]
                else:
                    self.p2_name = self.p2_name[:-1]
            else:
                ch = None
                if 32 <= key <= 126:
                    ch = chr(key)
                if ch:
                    if self.input_stage == 1 and len(self.p1_name) < 12:
                        self.p1_name += ch
                    elif self.input_stage == 2 and len(self.p2_name) < 12:
                        self.p2_name += ch

        if self.state == "RESULTS":
            if key == arcade.key.R:
                self.state = "NAME_INPUT"
                self.input_stage = 1
                self.p1_name = ""
                self.p2_name = ""

        if self.state != "FIGHT":
            return

        if key == self.p1.controls["jump"] and self.p1.on_ground and self.p1.state not in ["fatality", "dead", "slide"]:
            self.p1.change_y = JUMP_SPEED
            self.p1.state = "jump"

        if key == self.p1.controls["punch"] and self.p1.state not in ["fatality", "dead", "dash", "slide", "stunned"]:
            self.p1.attack("punch")

        if key == self.p1.controls["kick"] and self.p1.state not in ["fatality", "dead", "dash", "slide", "stunned"]:
            self.p1.attack("kick")

        if key == self.p1.controls["block"] and self.p1.state not in ["fatality", "dead", "dash", "slide", "attack"]:
            self.p1.start_block()

        if key == self.p1.controls["dash"] and self.p1.state not in ["fatality", "dead", "slide"]:
            self.p1.start_dash()
            self.particle_system.create_dash_trail(
                self.p1.center_x,
                self.p1.center_y,
                1 if self.p1.facing_right else -1,
                8
            )

        if key == self.p2.controls["jump"] and self.p2.on_ground and self.p2.state not in ["fatality", "dead", "slide"]:
            self.p2.change_y = JUMP_SPEED
            self.p2.state = "jump"

        if key == self.p2.controls["punch"] and self.p2.state not in ["fatality", "dead", "dash", "slide", "stunned"]:
            self.p2.attack("punch")

        if key == self.p2.controls["kick"] and self.p2.state not in ["fatality", "dead", "dash", "slide", "stunned"]:
            self.p2.attack("kick")

        if key == self.p2.controls["block"] and self.p2.state not in ["fatality", "dead", "dash", "slide", "attack"]:
            self.p2.start_block()

        if key == self.p2.controls["dash"] and self.p2.state not in ["fatality", "dead", "slide"]:
            self.p2.start_dash()
            self.particle_system.create_dash_trail(
                self.p2.center_x,
                self.p2.center_y,
                1 if self.p2.facing_right else -1,
                8
            )

    def on_key_release(self, key, modifiers):
        self.keys.discard(key)

        if self.state == "FIGHT":
            if key == self.p1.controls["block"] and self.p1.blocking:
                self.p1.block_timer = 0
            if key == self.p2.controls["block"] and self.p2.blocking:
                self.p2.block_timer = 0


def main():
    GameWindow()
    arcade.run()


if __name__ == "__main__":
    main()