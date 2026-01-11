import arcade
import os

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Stickman Fighter"

PLAYER_SCALE = 0.1
PLAYER_SPEED = 15
JUMP_SPEED = 14
GRAVITY = 0.6
GROUND_Y = 120

ASSET_PATH = r"C:\Users\Александр\Documents\PycharmProject\Game"


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__(scale=PLAYER_SCALE, hit_box_algorithm="None")

        self.center_x = SCREEN_WIDTH // 2
        self.center_y = GROUND_Y

        self.change_x = 0
        self.change_y = 0

        self.facing_right = True
        self.on_ground = False
        self.is_sitting = False
        self.wants_to_sit = False

        self.walk_frame = 0
        self.walk_frame_timer = 0

        self.idle_frame = 0
        self.idle_frame_timer = 0
        self.idle_animation_speed = 50

        self.foot_offset_y = 0

        self.idle_r_textures = [
            arcade.load_texture(os.path.join(ASSET_PATH, "Stand_R_1.png")),
            arcade.load_texture(os.path.join(ASSET_PATH, "Stand_R_2.png"))
        ]

        self.idle_l_textures = [
            self.idle_r_textures[0].flip_horizontally(),
            self.idle_r_textures[1].flip_horizontally()
        ]

        self.jump_l_texture = arcade.load_texture(os.path.join(ASSET_PATH, "Jump_L.png"))
        self.jump_r_texture = self.jump_l_texture.flip_horizontally()

        self.fall_l_texture = arcade.load_texture(os.path.join(ASSET_PATH, "Fall_L.png"))
        self.fall_r_texture = self.fall_l_texture.flip_horizontally()

        self.sit_r_texture = arcade.load_texture(os.path.join(ASSET_PATH, "Sit_R.png"))
        self.sit_l_texture = self.sit_r_texture.flip_horizontally()

        self.run_l_textures = []
        self.run_r_textures = []

        for i in range(1, 8):
            run_texture = arcade.load_texture(os.path.join(ASSET_PATH, f"Run_L_{i}.png"))
            self.run_l_textures.append(run_texture)
            self.run_r_textures.append(run_texture.flip_horizontally())

        self.texture = self.idle_r_textures[0]

        sprite_height = self.height
        self.center_y = GROUND_Y + sprite_height / 2
        self.foot_offset_y = -sprite_height / 2

    def update_animation(self, delta_time=1 / 60):
        if self.is_sitting:
            self.texture = self.sit_r_texture if self.facing_right else self.sit_l_texture
            return

        if not self.on_ground:
            if self.change_y >= 0:
                self.texture = self.jump_r_texture if self.facing_right else self.jump_l_texture
            else:
                self.texture = self.fall_r_texture if self.facing_right else self.fall_l_texture
            return

        if self.change_x != 0:
            self.walk_frame_timer += 1
            if self.walk_frame_timer >= 6:
                self.walk_frame = (self.walk_frame + 1) % len(self.run_l_textures)
                self.walk_frame_timer = 0
            self.texture = self.run_r_textures[self.walk_frame] if self.facing_right else self.run_l_textures[self.walk_frame]
            return

        self.idle_frame_timer += 1
        if self.idle_frame_timer >= self.idle_animation_speed:
            self.idle_frame = (self.idle_frame + 1) % len(self.idle_l_textures)
            self.idle_frame_timer = 0

        self.texture = self.idle_r_textures[self.idle_frame] if self.facing_right else self.idle_l_textures[self.idle_frame]

    def update_sitting_state(self):
        self.is_sitting = self.wants_to_sit and self.on_ground

    def set_wants_to_sit(self, wants):
        self.wants_to_sit = wants
        self.update_sitting_state()


class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # 📷 Камера (как в официальном туториале)
        self.camera = arcade.Camera2D()

        self.player_list = arcade.SpriteList()
        self.player = Player()
        self.player_list.append(self.player)

        self.keys_pressed = {
            arcade.key.A: False,
            arcade.key.LEFT: False,
            arcade.key.D: False,
            arcade.key.RIGHT: False,
            arcade.key.S: False,
            arcade.key.DOWN: False
        }

        self.ground_level = GROUND_Y

    def on_draw(self):
        self.clear()

        # 🎥 Используем камеру
        self.camera.use()

        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                SCREEN_WIDTH // 2,
                self.ground_level - 20,
                SCREEN_WIDTH * 10,  # земля длиннее экрана
                40
            ),
            arcade.color.DIM_GRAY
        )

        self.player_list.draw()

    def on_update(self, delta_time):
        self.player.change_y -= GRAVITY
        self.player.center_x += self.player.change_x
        self.player.center_y += self.player.change_y

        foot_y = self.player.center_y + self.player.foot_offset_y
        if foot_y <= self.ground_level:
            self.player.center_y = self.ground_level - self.player.foot_offset_y
            self.player.change_y = 0
            self.player.on_ground = True
        else:
            self.player.on_ground = False

        self.player.update_sitting_state()
        self.update_movement()
        self.player.update_animation(delta_time)

        # 📍 Камера следует за игроком (1 в 1 как в документации)
        self.camera.position = self.player.position

    def update_movement(self):
        speed = 0 if self.player.is_sitting else PLAYER_SPEED

        move_left = self.keys_pressed[arcade.key.A] or self.keys_pressed[arcade.key.LEFT]
        move_right = self.keys_pressed[arcade.key.D] or self.keys_pressed[arcade.key.RIGHT]

        if move_left and not move_right:
            self.player.change_x = -speed
            self.player.facing_right = False
        elif move_right and not move_left:
            self.player.change_x = speed
            self.player.facing_right = True
        elif not self.player.is_sitting:
            self.player.change_x = 0

    def on_key_press(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed[key] = True

        if key in (arcade.key.S, arcade.key.DOWN):
            self.player.set_wants_to_sit(True)

        if key in (arcade.key.W, arcade.key.UP, arcade.key.SPACE):
            if self.player.on_ground and not self.player.is_sitting:
                self.player.change_y = JUMP_SPEED
                self.player.on_ground = False

        self.update_movement()

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed[key] = False

        if key in (arcade.key.S, arcade.key.DOWN):
            self.player.set_wants_to_sit(False)

        self.update_movement()


def main():
    window = GameWindow()
    arcade.run()


if __name__ == "__main__":
    main()
