# -*- coding: utf-8 -*-
import pygame
import sys
import math
import random
import colorsys
import asyncio

# --- 定数 ---
WIDTH, HEIGHT = 1000, 640
FPS = 60
GRID_SIZE = 40
STAGE_WIDTH, STAGE_HEIGHT = 2000, 2000

WHITE, BLACK = (255, 255, 255), (10, 10, 10)
BLUE, GRAY = (50, 150, 255), (200, 200, 200)
GOLD = (255, 215, 0)
BACK_COLOR = (200, 200, 200)
COLOR_RED = (232, 74, 148)
COLOR_BLUE = (0, 150, 238)
COLOR_YELLOW = (253, 209, 41) 
COLOR_DEFAULT = (50, 50, 50)
COLOR_MM = (130, 130, 130)

FONT_DIR = "font"
FONT_NAME = "KiwiMaru-Regular.ttf"

# --- マップ設計図 ---
STAGE_DATA = {
    1: [
        "#..................................................#",
        "#..................................................#",
        "#..................................................#",
        "#.P...1..S.......2I.....###...r....................#",
        "####################....####..b..+Y-...............#",
        "####################....#####.y4.+Y-...............#",
        "#####################################............rr#",
        "#####################################............bb#",
        "######################################...........yy#",
        "######################################..........6..#",
        "#######################################VV#EE#OO#####",
        "#####################################..............#",
        "#####################################..............#",
        "#####################################..............#",
        "######################################.............#",
        "#################################....##3A.........A#",
        "#################################....######XXX######",
        "#################################.B...#####...######",
        "####################################...####...######",
        "#####################################..............#",
        "#####################################..............#",
        "#####################################..............#",
        "#####################################J.8....G.....#",
        "####################################################"
    ],
    2: [
        "##########################",
        "#........................#",
        "#........................#",
        "#......A.......X.........#",
        "#.....###.....###........#",
        "#......S.................#",
        "#...####....M............#",
        "##..#....................#",
        "#...#....................#",
        "#...#....................#",
        "#..##....................#",
        "#...#....................#",
        "#...#############........#",
        "##..-...R................#",
        "#...-...R................#",
        "#...-...R................#",
        "#..#######################",
        "#...#...#................#",
        "#...#...#................#",
        "##......####.............#",
        "#..........#.............#",
        "#..........#.............#",
        "#..#########.............#",
        "#...#......#.............#",
        "#...#......#.............#",
        "##..###....#.............#",
        "#.....+....#.............#",
        "#.G.P.+.B..#SSSSSSSSSSSSS#",
        "##########################"
    ]
}

# --- クラス定義 ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.color_id = "BLUE"
        self.current_color = COLOR_BLUE
        self.vel_x, self.vel_y = 0, 0
        self.speed, self.jump_power, self.gravity = 4, -15, 0.8
        self.on_ground = False
        self.is_alive = True
        self.base_radius = 20
        self.squish = 0.0; self.squish_vel = 0.0; self.spring_k = 0.1; self.friction = 0.7; self.target_squish = 0.0

    def update(self, platforms, particles_group, can_move=True):
        if not self.is_alive: return None
        if can_move:
            keys = pygame.key.get_pressed()
            self.vel_x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
        else:
            self.vel_x = 0
            
        self.vel_y += self.gravity
    

        self.rect.x += self.vel_x; self.check_collision(platforms, 'x')
        self.rect.y += self.vel_y; self.check_collision(platforms, 'y')

        if self.on_ground and self.vel_x != 0 and pygame.time.get_ticks() % 5 == 0:
            particles_group.add(Particle(self.rect.centerx, self.rect.bottom - 2, self.current_color, "FOOT"))

        if self.rect.top > STAGE_HEIGHT:
            self.is_alive = False
            return "FELL"
        return None

    def check_collision(self, platforms, direction):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for hit in hits:
            if hasattr(hit, 'color_type') and hit.color_type is not None:
                if hit.color_type == self.color_id:
                    continue

            if direction == 'x':
                if self.vel_x > 0: self.rect.right = hit.rect.left
                elif self.vel_x < 0: self.rect.left = hit.rect.right
            elif direction == 'y':
                if self.vel_y > 0:
                    if not self.on_ground: self.squish_vel = self.vel_y * 0.05
                    self.rect.bottom = hit.rect.top
                    self.vel_y, self.on_ground = 0, True
                elif self.vel_y < 0: self.rect.top = hit.rect.bottom; self.vel_y = 0
        if direction == 'y' and not hits: self.on_ground = False

    def jump(self, particles_group):
        if self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
            self.squish_vel = -0.3 
            for _ in range(10): particles_group.add(Particle(self.rect.centerx, self.rect.bottom, self.current_color, "SPLASH"))

    def change_color(self, new_color_name, color_value):
        self.color_id = new_color_name; self.current_color = color_value 

    def draw(self, surface, camera_x, camera_y):
        if not self.is_alive: return 
        w = self.base_radius * (1 + self.squish) * 2.5
        h = self.base_radius * (1 / (1 + self.squish)) * 3
        base_x, base_y = self.rect.centerx - camera_x, self.rect.bottom - camera_y
        fixed_scale = self.base_radius * 2.5
        face_tilt = self.vel_x * 1.5
        # 直接 surface に polygon を描く（Surface作成を省く）
        res = 24
        points = []
        for j in range(res):
            angle = (j / res) * math.pi * 2
            px, py = math.cos(angle) * (w / 2), math.sin(angle) * (h / 2)
            if py > 0: py *= 0.2
            points.append((base_x + px, base_y + py - (h * 0.1)))
        
        pygame.draw.polygon(surface, self.current_color, points)
        
        # 目と頬
        pink_color = (255, 180, 190, 200)
        for side in [-1, 1]:
            cx = base_x + (side * w * 0.3) + face_tilt
            pygame.draw.circle(surface, pink_color, (int(cx), int(base_y - h * 0.2)), int(fixed_scale/10))
            ex = base_x + (side * w * 0.2) + face_tilt
            pygame.draw.circle(surface, COLOR_DEFAULT, (int(ex), int(base_y - h * 0.3)), int(fixed_scale / 10))
            pygame.draw.circle(surface, WHITE, (int(ex), int(base_y - h * 0.3)), int(fixed_scale / 25))

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, p_type="SPLASH"):
        super().__init__()
        self.p_type, self.color = p_type, color
        if self.p_type == "SPLASH":
            self.size = random.randint(4, 8)
            self.vel_x, self.vel_y = random.uniform(-4, 4), random.uniform(-8, -2)
            self.gravity, self.lifetime = 0.5, 30
        elif self.p_type == "RISE":  # ← 追加：上昇する光
            self.size = random.randint(3, 6)
            self.vel_x, self.vel_y = random.uniform(-0.5, 0.5), random.uniform(-1, -3)
            self.gravity, self.lifetime = 0, 40 # 重力なしで上に昇る
        else:
            self.size = random.randint(8, 18)
            self.vel_x, self.vel_y, self.gravity, self.lifetime = 0, 0, 0, 60
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, platforms):
        self.vel_y += self.gravity; self.rect.x += self.vel_x; self.rect.y += self.vel_y
        self.lifetime -= 1
        if self.lifetime <= 0: self.kill()
        else:
            alpha = int((self.lifetime / 60) * 200) if self.p_type == "FOOT" else 255
            s = max(1, int(self.size * (self.lifetime / (30 if self.p_type=="SPLASH" else 60))))
            self.image = pygame.Surface((s, s), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (*self.color, alpha), (s//2, s//2), s//2)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color_type=None, color_val=None, image_path=None):
        super().__init__()
        self.color_type = color_type
        
        if image_path:
            try:
                # 指定された画像を読み込んでリサイズ
                original_img = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(original_img, (width, height))
            except:
                # 画像読み込み失敗時のバックアップ
                self.image = pygame.Surface((width, height))
                self.image.fill(color_val if color_val else (100, 100, 100))
        else:
            # 画像パスがない場合は色指定で作成
            self.image = pygame.Surface((width, height))
            self.image.fill(color_val if color_val else (100, 100, 100))
            
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_breakable = False # 基本は壊れない

class BreakableBlock(Platform):
    def __init__(self, x, y):
        super().__init__(x, y, GRID_SIZE, GRID_SIZE, image_path="img/block_x.png")
        if not hasattr(self, 'image') or self.image.get_at((0,0)) == (100,100,100): # 画像がない場合
            self.image.fill((139, 69, 19)) # 茶色
            pygame.draw.line(self.image, WHITE, (0,0), (40,40), 2)
        self.is_breakable = True
class InfoSign(pygame.sprite.Sprite):
    def __init__(self, x, y, message, player_ref):
        super().__init__()
        try:
            self.image = pygame.image.load("img/infosign.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (GRID_SIZE, GRID_SIZE))
        except:
            self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
            self.image.fill((100, 70, 0)) 
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.full_message = message
        self.player = player_ref
        # システムフォント(SysFont)ではなく、ファイルから読み込む(Font)
        try:
            # フォルダを分けているなら "fonts/ZenMaruGothic-Regular.ttf" のように指定
            self.font = pygame.font.Font(FONT_PATH, 18)
        except:
            # 万が一ファイルが見つからない時のためのバックアップ
            self.font = pygame.font.SysFont("msgothic", 16)
        self.is_showing_message = False
        
        # --- 修正: 看板用の画像をあらかじめ生成しておく ---
        lines = [message[i:i + 6] for i in range(0, len(message), 6)]
        line_surfs = [self.font.render(l, True, WHITE) for l in lines]
        max_w = max(s.get_width() for s in line_surfs)
        total_h = sum(s.get_height() for s in line_surfs) + (len(lines)-1)*4
        
        self.text_bg_surf = pygame.Surface((max_w + 16, total_h + 12), pygame.SRCALPHA)
        pygame.draw.rect(self.text_bg_surf, (30, 30, 30, 220), self.text_bg_surf.get_rect(), border_radius=5)
        pygame.draw.rect(self.text_bg_surf, WHITE, self.text_bg_surf.get_rect(), 1, border_radius=5)
        
        curr_y = 6
        for s in line_surfs:
            self.text_bg_surf.blit(s, ( (max_w+16)//2 - s.get_width()//2, curr_y))
            curr_y += s.get_height() + 4

    def update(self, *args):
        # 距離判定のみ
        dist = math.hypot(self.rect.centerx - self.player.rect.centerx, 
                          self.rect.centery - self.player.rect.centery)
        self.is_showing_message = (dist < 100)

    def draw(self, screen, cam_x, cam_y):
        if self.is_showing_message:
            # 作成済みの画像を1回blitするだけなので超高速！
            pos = self.text_bg_surf.get_rect(midbottom=(self.rect.centerx - cam_x, self.rect.top - cam_y - 10))
            screen.blit(self.text_bg_surf, pos)
            
# --- アイテムシステム（インベントリ用） ---
class Collectible(pygame.sprite.Sprite):
    def __init__(self, x, y, item_type):
        super().__init__()
        self.item_type = item_type # "BLOCK" or "AXE"
        self.base_y = y
        self.angle = 0
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x + GRID_SIZE//2, y + GRID_SIZE//2))

    def update(self, platforms):
        self.angle += 0.1
        self.rect.y = self.base_y + math.sin(self.angle) * 5
        # 光る演出：アルファ値をサイン波で変化させる
        alpha = int(200 + math.sin(self.angle * 2) * 10)
        # --- ここから画像対応のロジック ---
        if hasattr(self, 'image_src') and self.image_src:
            # 画像がある場合：読み込んだ画像を使って、透明度だけ更新する
            self.image = self.image_src.copy()
            self.image.set_alpha(alpha)
        else:
            # 画像がない場合のバックアップ（以前の図形描画）
            self.image.fill((0, 0, 0, 0)) # 透明化
            if self.item_type == "BLOCK":
                pygame.draw.rect(self.image, (*GOLD, alpha), (5, 5, 20, 20))
                pygame.draw.rect(self.image, WHITE, (5, 5, 20, 20), 2)
            elif self.item_type == "AXE":
                pygame.draw.rect(self.image, (180, 180, 180, alpha), (10, 5, 10, 20))
                pygame.draw.rect(self.image, (139, 69, 19, alpha), (13, 15, 4, 15))
            elif self.item_type == "INK":
                # インク用のデフォルト描画（画像がない時用）
                pygame.draw.rect(self.image, (*self.color_val, alpha), (5, 8, 20, 20))
                pygame.draw.rect(self.image, WHITE, (5, 8, 20, 20), 2)

class Axe(Collectible):
    def __init__(self, x, y):
        super().__init__(x, y, "AXE")
        try: self.image_src = pygame.transform.scale(pygame.image.load('img/axe.png').convert_alpha(), (30, 30))
        except: self.image_src = None

class Item(Collectible):
    def __init__(self, x, y):
        super().__init__(x, y, "BLOCK")
        try: self.image_src = pygame.transform.scale(pygame.image.load('img/plus_item.png').convert_alpha(), (30, 30))
        except: self.image_src = None

class Ink(Collectible):
    def __init__(self, x, y, color_name, color_val):
        super().__init__(x, y, "INK")
        self.color_name = color_name
        self.color_val = color_val
        
        # 色名から画像パスを自動生成（例: "RED" -> "img/item_red.png"）
        image_path = f"img/ink_{color_name.lower()}.png"
        
        try:
            # 画像を読み込んでリサイズ
            self.image_src = pygame.image.load(image_path).convert_alpha()
            self.image_src = pygame.transform.scale(self.image_src, (30, 30))
        except:
            # 画像がない場合のバックアップ表示
            self.image_src = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.rect(self.image_src, self.color_val, (5, 8, 20, 20))
            pygame.draw.rect(self.image_src, WHITE, (5, 8, 20, 20), 2)

        self.image = self.image_src.copy()
        self.rect = self.image.get_rect(center=(x + GRID_SIZE//2, y + GRID_SIZE//2))
    def update(self, platforms):
        # 親クラスの浮遊アニメーション（上下に動く）を呼び出す
        super().update(platforms)
        
        # もし画像が正常に読み込まれていれば、何もしなくてOK（画像は維持される）
        # 画像がない場合のみ、元の図形を描画するようにする
        if not hasattr(self, 'image_src') or self.image_src is None:
            self.image.fill((0, 0, 0, 0))
            pygame.draw.rect(self.image, self.color_val, (5, 8, 20, 20))
            pygame.draw.rect(self.image, WHITE, (5, 8, 20, 20), 2)

    def mix_with(self, other):
        """他のインクと混ぜた結果を返す"""
        if not isinstance(other, Ink):
            return None
        
        pair = frozenset([self.color_name, other.color_name])
        # 合成レシピ
        recipes = {
            frozenset(["RED", "BLUE"]): ("PURPLE", (160, 32, 240)),
            frozenset(["BLUE", "YELLOW"]): ("GREEN", (0, 200, 0)),
            frozenset(["RED", "YELLOW"]): ("ORANGE", (255, 165, 0)),
        }
        return recipes.get(pair)
# --- ギミック ---
class Spike(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try: self.image = pygame.transform.scale(pygame.image.load('img/needleink.png').convert_alpha(), (40, 40))
        except:
            self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (150, 0, 0), [(20, 0), (0, 40), (40, 40)])
        self.rect = self.image.get_rect(topleft=(x, y))
    def update(self, platforms): pass

class MovingPlatform(Platform):
    def __init__(self, x, y, width, height, move_range=200, speed=2):
        super().__init__(x, y, width, height)
        self.start_x = x; self.move_range = move_range; self.speed = speed; self.direction = 1
    def update(self, platforms):
        self.rect.x += self.speed * self.direction
        if abs(self.rect.x - self.start_x) > self.move_range: self.direction *= -1

class Spring(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.image = pygame.transform.scale(pygame.image.load('img/spring.png').convert_alpha(), (40, 40))
        except:
            self.image = pygame.Surface((GRID_SIZE, 20)); self.image.fill(GOLD)
        self.rect = self.image.get_rect(x=x, bottom=y+GRID_SIZE)
        self.jump_force = -20
    def update(self, platforms): pass

class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 扉のサイズを指定 (横: GRID_SIZE, 縦: GRID_SIZEの1.5倍くらいが扉らしいです)
        self.width = int(GRID_SIZE * 2)
        self.height = int(GRID_SIZE * 3)

        try:
            # 読み込みと同時にリサイズ
            self.img_close = pygame.image.load("img/door_close.png").convert_alpha()
            self.img_close = pygame.transform.scale(self.img_close, (self.width, self.height))
            
            self.img_open = pygame.image.load("img/door_open.png").convert_alpha()
            self.img_open = pygame.transform.scale(self.img_open, (self.width, self.height))
        except:
            self.img_close = pygame.Surface((self.width, self.height)); self.img_close.fill((50, 50, 50))
            self.img_open = pygame.Surface((self.width, self.height)); self.img_open.fill((255, 255, 255))
            
        self.image = self.img_close
        # 足元を基準に配置を調整
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_open = False

    def check_open(self, buttons_group, particles_group):
        is_triggered = any(b.is_pressed for b in buttons_group if b.target_goal == self)
        
        if is_triggered:
            self.is_open = True
            self.image = self.img_open
            
            if random.random() < 0.2:
                px = self.rect.x + random.randint(5, self.rect.width - 5)
                py = self.rect.bottom - 5
                p = Particle(px, py, (200, 255, 255), "RISE")
                particles_group.add(p)
        else:
            self.is_open = False
            self.image = self.img_close

    def update(self, *args):
        pass

class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, target_goal):
        super().__init__()
        self.target_goal = target_goal; self.is_pressed = False; self.base_y = y
        try:
            self.img_off = pygame.transform.scale(pygame.image.load('img/button_off.png').convert_alpha(), (40, 40))
            self.img_on = pygame.transform.scale(pygame.image.load('img/button_on.png').convert_alpha(), (40, 20))
        except:
            self.img_off = pygame.Surface((40, 40)); self.img_off.fill((200, 0, 0))
            self.img_on = pygame.Surface((40, 20)); self.img_on.fill((255, 100, 100))
        self.image = self.img_off; self.rect = self.image.get_rect(topleft=(x, y))

    def check_press(self, player):
        if self.rect.colliderect(player.rect) and not self.is_pressed:
            self.is_pressed = True; self.image = self.img_on; self.rect.y = self.base_y + 20
            if self.target_goal: self.target_goal.is_open = True

class ColorChanger(pygame.sprite.Sprite):
    def __init__(self, x, y, target_color):
        super().__init__()
        self.target_color = target_color
        try:
            filename = f'img/changer_{target_color.lower()}.png'
            self.image = pygame.transform.scale(pygame.image.load(filename).convert_alpha(), (30, 30))
        except:
            self.image = pygame.Surface((30, 30))
            cols = {"RED": COLOR_RED, "BLUE": COLOR_BLUE, "YELLOW": COLOR_YELLOW}
            self.image.fill(cols.get(target_color, WHITE))
        self.rect = self.image.get_rect(center=(x + GRID_SIZE//2, y + GRID_SIZE//2))

    def check_interaction(self, player):
        if self.rect.colliderect(player.rect):
            cols = {"RED": COLOR_RED, "BLUE": COLOR_BLUE, "YELLOW": COLOR_YELLOW}
            player.change_color(self.target_color, cols[self.target_color])

    def mix_with(self, other):
        """他のインクと混ぜた結果（色名, 色の値）を返す"""
        if not isinstance(other, Ink):
            return None
        
        # 順番に関係なく判定するためにセット（frozenset）を使う
        pair = frozenset([self.color_name, other.color_name])
        
        # 合成レシピの定義
        recipes = {
            frozenset(["RED", "BLUE"]):   ("PURPLE", (160, 32, 240)),
            frozenset(["BLUE", "YELLOW"]): ("GREEN", (0, 200, 0)),
            frozenset(["RED", "YELLOW"]): ("ORANGE", (255, 165, 0)),
            # 必要に応じて「紫＋黄色」などの3色合成もここに追加できます
        }
        
        return recipes.get(pair) # レシピにない場合はNoneを返す

class ClearParticle(pygame.sprite.Sprite):
    def __init__(self, cx, cy, angle, speed, life, hue):
        super().__init__()
        self.hue, self.speed, self.life, self.max_life = hue, speed, life, life
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA); self.rect = self.image.get_rect(center=(cx, cy))
    def update(self):
        self.rect.x += self.vx; self.rect.y += self.vy; self.life -= 1
        if self.life <= 0: self.kill()
        else:
            s = max(2, int(30 * (self.life/self.max_life)))
            r, g, b = [int(x*255) for x in colorsys.hsv_to_rgb(self.hue, 1, 1)]
            self.image = pygame.Surface((s, s), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (r,g,b, int(255*(self.life/self.max_life))), (s//2, s//2), s//2)

# --- システム関数 ---
def setup_stage(stage_num, all_sprites, platforms, items_group, buttons_group, changers_group, spikes_group, player, inventory, moving_platforms, springs_group, goal_group, info_signs_group):
    all_sprites.empty(); platforms.empty(); items_group.empty(); buttons_group.empty(); moving_platforms.empty()
    changers_group.empty(); spikes_group.empty(); springs_group.empty(); goal_group.empty(); inventory.clear(); info_signs_group.empty()
    player.is_alive = True; player.vel_x = 0; player.vel_y = 0
    if stage_num not in STAGE_DATA: return None
    
    stage_map = STAGE_DATA[stage_num]
    player.change_color("RED" if stage_num == 2 else "BLUE", COLOR_RED if stage_num == 2 else COLOR_BLUE)
    
    temp_goal = None
    for y, row in enumerate(stage_map):
        for x, char in enumerate(row):
            if char == 'G':
                temp_goal = Goal(x*GRID_SIZE, y*GRID_SIZE - 60); all_sprites.add(temp_goal)
                goal_group.add(temp_goal)

    for y, row in enumerate(stage_map):
        for x, char in enumerate(row):
            px, py = x * GRID_SIZE, y * GRID_SIZE
            if char == '#':
                p = Platform(px, py, GRID_SIZE, GRID_SIZE, image_path="img/block.png")
                platforms.add(p); all_sprites.add(p)
            elif char == 'P': player.rect.topleft = (px, py)
            elif char == 'M': m = MovingPlatform(px, py, GRID_SIZE*2, GRID_SIZE//2, 80, 1); platforms.add(m); moving_platforms.add(m); all_sprites.add(m)
            elif char == 'J': j = Spring(px, py); springs_group.add(j); all_sprites.add(j)
            elif char == 'A': a = Axe(px, py); items_group.add(a); all_sprites.add(a)
            elif char == 'X': b = BreakableBlock(px, py); platforms.add(b); all_sprites.add(b)
            elif char == 'S': s = Spike(px, py); spikes_group.add(s); all_sprites.add(s)
            elif char == 'B': b = Button(px, py, temp_goal); buttons_group.add(b); all_sprites.add(b)
            elif char == 'I': i = Item(px, py); items_group.add(i); all_sprites.add(i)
            elif char == '-': # 青の壁
                p = Platform(px, py, GRID_SIZE, GRID_SIZE, "BLUE", COLOR_BLUE, "img/block_blue.png")
                platforms.add(p); all_sprites.add(p)
            elif char == '+': # 赤の壁
                p = Platform(px, py, GRID_SIZE, GRID_SIZE, "RED", COLOR_RED, "img/block_red.png")
                platforms.add(p); all_sprites.add(p)
            elif char == 'Y': # 黄の壁
                p = Platform(px, py, GRID_SIZE, GRID_SIZE, "YELLOW", COLOR_YELLOW, "img/block_yellow.png")
                platforms.add(p); all_sprites.add(p)
            elif char == 'V': # 紫の壁
                p = Platform(px, py, GRID_SIZE, GRID_SIZE, "PURPLE", (160, 32, 240), "img/block_purple.png")
                platforms.add(p); all_sprites.add(p)
            elif char == 'E': # 緑の壁
                p = Platform(px, py, GRID_SIZE, GRID_SIZE, "GREEN", (0, 200, 0), "img/block_green.png")
                platforms.add(p); all_sprites.add(p)
            elif char == 'O': # 橙の壁
                p = Platform(px, py, GRID_SIZE, GRID_SIZE, "ORANGE", (255, 165, 0), "img/block_orange.png")
                platforms.add(p); all_sprites.add(p)
            elif char == 'r':
                ink = Ink(px, py, "RED", COLOR_RED)
                items_group.add(ink); all_sprites.add(ink)
            elif char == 'b':
                ink = Ink(px, py, "BLUE", COLOR_BLUE)
                items_group.add(ink); all_sprites.add(ink)
            elif char == 'y':
                ink = Ink(px, py, "YELLOW", COLOR_YELLOW)
                items_group.add(ink); all_sprites.add(ink)
            elif char in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']:
                # 看板を作る時に player を渡す
                if char == '1': msg = "はりはあたるとやりなおし"
                if char == '2': msg = "このあいてむはゆかになる、まうすでおいてみて"
                if char == '3': msg = "これはこわれかけのかべをこわせるよ"
                if char == '4': msg = "いんくはすらいむのいろをかえれる"
                if char == '5': msg = "おなじいろのかべはとおれるよ"
                if char == '6': msg = "いんくはふたつまぜれる、まぜてみて"
                if char == '7': msg = "これはのるとたかくとべる、とびすぎちゅうい"
                if char == '8': msg = "ぼたんをおしたらごーるがひらく"
                if char == '9': msg = "ぜんぶくりあがんばってね"
                if char == '0': msg = "ぜんぶくりあがんばってね"
                sign = InfoSign(px, py, msg, player) 
                info_signs_group.add(sign)
                all_sprites.add(sign)
    return temp_goal

def draw_text(screen, text, size, x, y, color):
    font = pygame.font.SysFont(None, size)
    img = font.render(text, True, color)
    screen.blit(img, img.get_rect(center=(x, y)))

async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    game_state, cleared_stages, current_stage = "TITLE", [False]*5, 1
    death_timer, current_goal = 0, None
    selected_item_index, clear_timer = -1, 0
    inventory = {}
    ui_font = pygame.font.SysFont("arial", 20)
    
    all_sprites = pygame.sprite.Group()
    platforms, items_group, goal_group, particles_group = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
    moving_platforms, springs_group = pygame.sprite.Group(), pygame.sprite.Group()
    buttons_group, changers_group, particles_group, spikes_group = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
    clear_particles_group = pygame.sprite.Group()
    info_signs_group = pygame.sprite.Group()
    player = Player()

    def load_img(path, size=None):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size: img = pygame.transform.scale(img, size)
            return img
        except:
            surf = pygame.Surface(size if size else (100, 100))
            surf.fill((255, 0, 255))
            return surf
        
    title_logo = load_img("img/title_rogo.png", (661, 326))
    title_bg = load_img("img/title_back.png", (WIDTH, HEIGHT))
    select_bg = load_img("img/select_back.png", (WIDTH, HEIGHT))
    icon_normal = load_img("img/stage_icon.png", (100, 100))
    icon_clear = load_img("img/stage_icon_clear.png", (100, 100))
    stage_bg = load_img("img/stage_back.png", (WIDTH, HEIGHT))
    inve = load_img("img/inve.png", (WIDTH, HEIGHT))
    

    
    while True:
        m_pos = pygame.mouse.get_pos()
        cam_x = max(0, min(player.rect.centerx - WIDTH // 2, STAGE_WIDTH - WIDTH))
        cam_y = max(0, min(player.rect.centery - HEIGHT // 2, STAGE_HEIGHT - HEIGHT))

        events = pygame.event.get()

        # --- main関数内のイベントループ内 ---
        for e in events:
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if game_state == "PLAYING" and player.is_alive and clear_timer == 0:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    
                    # 現在のインベントリのキー（中身）をリストとして取得
                    # これにより slot 番号から特定のアイテムデータにアクセスできます
                    inv_keys = list(inventory.keys())

                    # --- A. インベントリのスロット選択 ---
                    if m_pos[1] > HEIGHT - 100:
                        slot = (m_pos[0] - 15) // 70
                        if 0 <= slot < len(inv_keys):
                            # 1. クリックしたスロットがすでに選択中なら、選択解除
                            if selected_item_index == slot:
                                selected_item_index = -1
                            
                            # 2. 別のスロットを選択中で、かつ両方がインクなら「合成」
                            elif selected_item_index != -1:
                                key_a = inv_keys[selected_item_index]
                                key_b = inv_keys[slot]
                                item_a = inventory[key_a]['item']
                                item_b = inventory[key_b]['item']

                                if isinstance(item_a, Ink) and isinstance(item_b, Ink):
                                    result = item_a.mix_with(item_b)
                                    if result:
                                        new_name, new_val = result
                                        # 合成：両方の個数を1減らし、新しいインクを追加
                                        # (スタックから1つずつ消費する処理)
                                        inventory[key_a]['count'] -= 1
                                        if inventory[key_a]['count'] <= 0: del inventory[key_a]
                                        
                                        inventory[key_b]['count'] -= 1
                                        if inventory[key_b]['count'] <= 0: del inventory[key_b]

                                        # 新しいインクをスタック形式で追加
                                        new_key = f"INK_{new_name}"
                                        new_ink = Ink(0, 0, new_name, new_val)
                                        if new_key in inventory:
                                            inventory[new_key]['count'] += 1
                                        else:
                                            inventory[new_key] = {'item': new_ink, 'count': 1}
                                        
                                        selected_item_index = -1
                                        print(f"Mixed New Color:{new_name}")
                                    else:
                                        selected_item_index = slot
                                else:
                                    selected_item_index = slot
                            else:
                                selected_item_index = slot
                        continue

                    # --- B. アイテムの使用 ---
                    elif selected_item_index != -1 and m_pos[1] <= HEIGHT - 100:
                        # 選択中のアイテムデータを取得
                        if selected_item_index < len(inv_keys):
                            target_key = inv_keys[selected_item_index]
                            item_data = inventory[target_key]
                            item = item_data['item']
                            
                            used = False # 使用成功フラグ
                            world_mouse_x, world_mouse_y = m_pos[0] + cam_x, m_pos[1] + cam_y

                            # インク使用
                            if isinstance(item, Ink):
                                if player.rect.collidepoint(world_mouse_x, world_mouse_y):
                                    player.change_color(item.color_name, item.color_val)
                                    for _ in range(15):
                                        particles_group.add(Particle(player.rect.centerx, player.rect.centery, player.current_color, "SPLASH"))
                                    used = True

                            # ブロック設置
                            elif item.item_type == "BLOCK":
                                gx = (int(world_mouse_x) // GRID_SIZE) * GRID_SIZE
                                gy = (int(world_mouse_y) // GRID_SIZE) * GRID_SIZE
                                temp_rect = pygame.Rect(gx, gy, GRID_SIZE, GRID_SIZE)
                                if not any(p.rect.colliderect(temp_rect) for p in platforms) and not player.rect.colliderect(temp_rect):
                                    new_block = Platform(gx, gy, GRID_SIZE, GRID_SIZE, image_path="img/block.png")
                                    platforms.add(new_block); all_sprites.add(new_block)
                                    used = True

                            # アックス破壊
                            elif item.item_type == "AXE":
                                target_block = None
                                for p in platforms:
                                    if p.rect.collidepoint(world_mouse_x, world_mouse_y):
                                        if hasattr(p, 'is_breakable') and p.is_breakable:
                                            target_block = p; break
                                if target_block:
                                    target_block.kill()
                                    for _ in range(15):
                                        particles_group.add(Particle(target_block.rect.centerx, target_block.rect.centery, (120, 100, 80)))
                                    used = True

                            # 使用した場合の個数減少処理
                            if used:
                                item_data['count'] -= 1
                                if item_data['count'] <= 0:
                                    del inventory[target_key]
                                    selected_item_index = -1

                # 2. キーボード操作
                if e.type == pygame.KEYDOWN:
                    # Rキーでリセット
                    if e.key == pygame.K_r:
                        current_goal = setup_stage(current_stage, all_sprites, platforms, items_group, buttons_group, changers_group, spikes_group, player, inventory, moving_platforms, springs_group, goal_group, info_signs_group)
                    # SPACEキーでジャンプ
                    if e.key == pygame.K_SPACE:
                        player.jump(particles_group)
                    # ESCキーでセレクト画面に戻る
                    if e.key == pygame.K_ESCAPE:
                        game_state = "SELECT"

        if game_state == "TITLE":
            screen.blit(title_bg, (0, 0))
            logo_x = (WIDTH - title_logo.get_width()) // 2
            logo_y = (HEIGHT - title_logo.get_height()) // 2 - 80 # ロゴを少し上に持ち上げる

            screen.blit(title_logo, (logo_x, logo_y))
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                draw_text(screen, "Press SPACE to START", 40, WIDTH//2, HEIGHT//2+150, BLACK)
            if any(e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE for e in events):
                game_state = "SELECT"
        
        elif game_state == "SELECT":
            screen.blit(select_bg, (0, 0))
            draw_text(screen, "STAGE SELECT", 48, WIDTH//2, 50, WHITE)

            for i in range(2):
                rect = pygame.Rect(100 + i*180, 250, 100, 100)
                img = icon_clear if cleared_stages[i] else icon_normal
                screen.blit(img, rect.topleft)
                color = BLACK if not cleared_stages[i] else (50, 50, 0)
                draw_text(screen, f"{i+1}", 40, rect.centerx, rect.centery - 5, color)
                if rect.collidepoint(m_pos):
                    pygame.draw.rect(screen, WHITE, rect, 3, border_radius=10)

                
                if any(e.type == pygame.MOUSEBUTTONDOWN and rect.collidepoint(e.pos) for e in events):
                    current_stage = i + 1
                    clear_timer = 0
                    current_goal = setup_stage(current_stage, all_sprites, platforms, items_group, buttons_group, changers_group, spikes_group, player, inventory, moving_platforms, springs_group, goal_group, info_signs_group)
                    game_state = "PLAYING"

        elif game_state == "PLAYING":
            if not player.is_alive:
                if death_timer == 0: death_timer = pygame.time.get_ticks()
                if pygame.time.get_ticks() - death_timer > 1000:
                    current_goal = setup_stage(current_stage, all_sprites, platforms, items_group, buttons_group, changers_group, spikes_group, player, inventory, moving_platforms, springs_group, goal_group, info_signs_group)
                    death_timer = 0
            elif clear_timer == 0:
                player.update(platforms, particles_group)
                
                # アイテム拾得
                picked = pygame.sprite.spritecollide(player, items_group, True)

                for p_item in picked:
                    if isinstance(p_item, Ink):
                        item_key = f"INK_{p_item.color_name}"
                    else:
                        item_key = p_item.item_type

                    if item_key in inventory:
                        inventory[item_key]['count'] += 1
                    elif len(inventory) < 10:
                        inventory[item_key] = {'item': p_item, 'count': 1}

                for sign in info_signs_group:
                    sign.update(player)

                # ギミック連動
                for spring in pygame.sprite.spritecollide(player, springs_group, False):
                    if player.vel_y > 0: player.vel_y = spring.jump_force; player.rect.bottom = spring.rect.top
                
                check_rect = pygame.Rect(player.rect.x, player.rect.bottom - 2, player.rect.width, 7)
                for m_plate in moving_platforms:
                    if check_rect.colliderect(m_plate.rect) and player.vel_y >= 0:
                        player.rect.x += m_plate.speed * m_plate.direction; break

                for p in platforms:
                    if hasattr(p, 'color_type') and p.color_type:
                        if p.color_type == player.color_id:
                            p.image.set_alpha(100)
                        else:
                            p.image.set_alpha(255)

                if current_goal and current_goal.is_open and player.rect.colliderect(current_goal.rect): clear_timer = pygame.time.get_ticks()
                if pygame.sprite.spritecollide(player, spikes_group, False):
                    player.is_alive = False
                    for _ in range(30): particles_group.add(Particle(player.rect.centerx, player.rect.centery, player.current_color))

            # 更新
            all_sprites.update(platforms) 

            for b in buttons_group:
                b.check_press(player)

            for g in goal_group:
                g.check_open(buttons_group, particles_group)

            for c in changers_group:
                c.check_interaction(player)

            # パーティクルの更新
            particles_group.update(platforms)
            clear_particles_group.update()

            if clear_timer > 0:
                elapsed = pygame.time.get_ticks() - clear_timer
                if elapsed < 100 and not clear_particles_group:
                    for i in range(40): clear_particles_group.add(ClearParticle(WIDTH//2, HEIGHT//2, (i/40)*math.pi*2, random.uniform(5,12), 60, random.random()))
                if elapsed > 1500: cleared_stages[current_stage-1] = True; game_state = "SELECT"; clear_particles_group.empty()

            # 描画
            # --- 描画開始 ---
            screen.fill(BACK_COLOR)
            screen.blit(stage_bg, (0, 0))
            
            # グリッド
            for x in range(0, STAGE_WIDTH, GRID_SIZE): pygame.draw.line(screen, WHITE, (x-cam_x, 0), (x-cam_x, HEIGHT))
            for y in range(0, STAGE_HEIGHT, GRID_SIZE): pygame.draw.line(screen, WHITE, (0, y-cam_y), (WIDTH, y-cam_y))
            
            # 全スプライト
            for s in all_sprites: screen.blit(s.image, (s.rect.x - cam_x, s.rect.y - cam_y))
            for p in particles_group: screen.blit(p.image, (p.rect.x - cam_x, p.rect.y - cam_y))
            
            # 看板の文字（インベントリより先に描く！）
            for sign in info_signs_group: 
                sign.draw(screen, cam_x, cam_y)

            # プレイヤー
            player.draw(screen, cam_x, cam_y)

            # クリア演出
            if clear_timer > 0:
                for p in clear_particles_group: screen.blit(p.image, p.rect)
                draw_text(screen, "STAGE CLEAR!", 80, WIDTH//2, HEIGHT//2, BLACK)

            # --- インベントリUI (ここで描画を完結させる) ---
            #pygame.draw.rect(screen, BLACK, (0, HEIGHT-100, WIDTH, 100))
            screen.blit(inve, (0, 0))

            # インベントリUI描画セクション
            # inventory.items() で辞書の中身をループ
            for i, (key, data) in enumerate(inventory.items()):
                slot_rect = pygame.Rect(15+i*70, HEIGHT-80, 60, 60)
                color = GOLD if i == selected_item_index else GRAY
                pygame.draw.rect(screen, color, slot_rect, 2)
                
                item = data['item']
                count = data['count']
                
                # アイテム画像を表示
                screen.blit(item.image_src, (slot_rect.x + 15, slot_rect.y + 15))
                
                # ★ 個数が2個以上の時に「×数字」を表示
                if count >= 2:
                    # 小さめのフォントで描画（UI用のフォントをあらかじめ作っておくと良いです）
                    count_text = ui_font.render(f"x{count}", True, WHITE)
                    # スロットの右下に配置
                    text_rect = count_text.get_rect(bottomright=(slot_rect.right - 5, slot_rect.bottom - 5))
                    # 文字を見やすくするために小さな影や背景をつける
                    screen.blit(count_text, text_rect)

            # プレビュー表示
            if selected_item_index != -1 and m_pos[1] <= HEIGHT - 100:
                inv_keys = list(inventory.keys())
                if selected_item_index != -1 and selected_item_index < len(inv_keys):
                    item_key = inv_keys[selected_item_index]
                    item = inventory[item_key]['item']

                if item.item_type == "BLOCK":
                    gx, gy = ((m_pos[0]+cam_x)//GRID_SIZE)*GRID_SIZE - cam_x, ((m_pos[1]+cam_y)//GRID_SIZE)*GRID_SIZE - cam_y
                    pygame.draw.rect(screen, (255, 255, 0), (gx, gy, GRID_SIZE, GRID_SIZE), 3)
                elif item.item_type == "AXE":
                    pygame.draw.circle(screen, (255, 255, 0), (m_pos[0], m_pos[1]), 20, 2)

        pygame.display.flip()
        await asyncio.sleep(0) 
        clock.tick(FPS)

if __name__ == "__main__":
    asyncio.run(main())

