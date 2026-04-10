import pygame
import sys
import random
import math
from pygame import mixer

pygame.init()

class GameObject(pygame.sprite.Sprite):
    """Class dasar untuk semua objek dalam game"""
    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.width = width
        self.height = height
        self.x = x
        self.y = y
    
    def update(self):
        pass
    
    def draw(self, screen, camera_x, camera_y):
        pass

class Character(GameObject):
    """Class untuk karakter yang bisa bergerak (player & musuh)"""
    def __init__(self, x, y, width, height, health=3):
        super().__init__(x, y, width, height)
        self.health = health
        self.max_health = health
        self.velocity_x = 0
        self.velocity_y = 0
        self.is_alive = True
    
    def take_damage(self, damage=1):
        self.health -= damage
        if self.health <= 0:
            self.is_alive = False
        return self.is_alive
    
class Coin(GameObject):
    def __init__(self, x, y):
        super().__init__(x,y,16, 16)
        self.animation_frames =[]
        self.current_frame = 0
        self.animation_speed = 0.1
        self.value = 10
        self.collected = False
        self.float_offset = 0
        self.float_speed = 0.03
        self.original_y = y

        try:
            sheet = pygame.image.load('kenney-pixel-platformer/Tiles/tile_0151.png').convert_alpha()
            for i in range(sheet.get_width()// 32):
                frame = sheet.subsurface((i*32,0,32,32))
                frame = pygame.transform.scale(frame, (16,16))

                self.animation_frames.append(frame)

        except:
            surf = pygame.Surface((16,16))
            surf.fill((255, 215, 0))
            pygame.draw.circle(surf,(255, 200, 0), (8, 8), 6)
            self.animation_frames=[surf]

    def update(self):
        if self.animation_frames:
            self.current_frame += self.animation_speed
            if self.current_frame >= len(self.animation_frames):
                self.current_frame = 0

        self.float_offset += self.float_speed
        self.y = self.original_y + (math.sin(self.float_offset) * 8)
        self.rect.y = self.y

    def draw(self, screen, camera_x, camera_y):
         if self.animation_frames:
            frame = self.animation_frames[int(self.current_frame)]
            screen_x = self.x - camera_x
            screen_y = self.y - camera_y
            screen.blit(frame, (screen_x, screen_y))
            
class Player(Character):
    """Class Player yang mewarisi Character"""
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32, health=5)
        self.speed = 5
        self.gravity = 0.8
        self.jump_power = -12
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 2
        self.direction = "right"
        self.last_direction = "right"
        self.action = "idle"
        self.frame = 0
        self.animations = {}
        self.score = 0
        self.kills = 0
        self.invicible_timer = 0
        self.invicible_duration = 60
    
    def jump(self):
        if self.jump_count < self.max_jumps:
            self.velocity_y = self.jump_power
            self.jump_count += 1
            self.on_ground = False
            return True
        return False
    
    def take_damage(self, damage = 1):
        if self.invicible_timer <= 0:
           self.health -= damage 
           self.invicible_timer = self.invicible_duration
           if self.health <= 0:
             self.is_alive = False
        return self.is_alive
    
    def update(self, tilemap, map_width, map_height):

        self.x += self.velocity_x

        if self.velocity_x != 0:
            self.last_direction = "right" if self.velocity_x > 0 else "left"

        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        for (tile_x, tile_y), tile_type in tilemap.items():
            tile_rect = pygame.Rect(tile_x * 32, tile_y * 32, 32, 32)
            if player_rect.colliderect(tile_rect):
                if self.velocity_x > 0:
                    self.x = tile_rect.left - self.width
                elif self.velocity_x < 0:
                    self.x = tile_rect.right
                player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        self.velocity_y += self.gravity
        self.y += self.velocity_y
        self.on_ground = False
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        for (tile_x, tile_y), tile_type in tilemap.items():
            tile_rect = pygame.Rect(tile_x * 32, tile_y * 32, 32, 32)
            if player_rect.colliderect(tile_rect):
                if self.velocity_y > 0:
                    self.y = tile_rect.top - self.height
                    self.velocity_y = 0
                    self.on_ground = True
                    self.jump_count = 0
                elif self.velocity_y < 0:
                    self.y = tile_rect.bottom
                    self.velocity_y = 0
        
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.x = max(0, min(self.x, map_width - self.width))
        self.y = max(0, min(self.y, map_height - self.height))

        if self.invicible_timer > 0:
            self.invicible_timer -= 1

class Enemy(Character):
    """Class dasar untuk semua musuh"""
    def __init__(self, x, y, width, height, health=3, damage=1):
        super().__init__(x, y, width, height, health)
        self.damage = damage
        self.direction = 1
        self.speed = 1.5
        self.move_range = [x - 100, x + 100]
        self.animation_frames = []
        self.current_frame = 0
        self.animation_speed = 0.15
        self.flip_sprite = False
    
    def update(self, tilemap, map_width, map_height):

        self.x += self.direction * self.speed
        
        if self.x <= self.move_range[0] or self.x >= self.move_range[1]:
            self.direction *= -1
        
        self.velocity_y += 0.3
        self.y += self.velocity_y
        
        enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for (tile_x, tile_y), tile_type in tilemap.items():
            tile_rect = pygame.Rect(tile_x * 32, tile_y * 32, 32, 32)
            if enemy_rect.colliderect(tile_rect):
                if self.velocity_y > 0:
                    enemy_rect.bottom = tile_rect.top
                    self.y = enemy_rect.y
                    self.velocity_y = 0
        
        self.rect = enemy_rect
        self.x = self.rect.x
        self.y = self.rect.y
        self.x = max(0, min(self.x, map_width - self.width))
        
        if self.animation_frames:
            self.current_frame += self.animation_speed
            if self.current_frame >= len(self.animation_frames):
                self.current_frame = 0
    
    def draw(self, screen, camera_x, camera_y):
        if self.animation_frames:
            frame = self.animation_frames[int(self.current_frame)]
            if self.flip_sprite and self.direction == -1:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (self.x - camera_x, self.y - camera_y))

class Bat(Enemy):
    def __init__(self, x, y, min_x, max_x):
        super().__init__(x, y, 32, 32, health=2, damage=1)
        self.move_range = [min_x, max_x]
        self.speed = 2
        self.flip_sprite = False
        
        self.animation_frames = []
        for i in range(24, 27):
            try:
                img = pygame.image.load(f'kenney_pixel-platformer/Tiles/Characters/tile_00{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (32, 32))
                self.animation_frames.append(img)
            except:
                surf = pygame.Surface((32, 32))
                surf.fill((100, 100, 150))
                self.animation_frames.append(surf)

class Snail(Enemy):
    def __init__(self, x, y, min_x, max_x):
        super().__init__(x, y, 32, 32, health=3, damage=1)
        self.move_range = [min_x, max_x]
        self.speed = 1
        self.flip_sprite = True
        
        self.animation_frames = []
        for i in range(18, 20):
            try:
                img = pygame.image.load(f'kenney_pixel-platformer/Tiles/Characters/tile_00{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (32, 32))
                self.animation_frames.append(img)
            except:
                surf = pygame.Surface((32, 32))
                surf.fill((150, 100, 50))
                self.animation_frames.append(surf)

class AngryBlock(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32, health=999, damage=1)
        self.speed = 0
        self.flip_sprite = False
        
        self.animation_frames = []
        for i in range(11, 13):
            try:
                img = pygame.image.load(f'kenney_pixel-platformer/Tiles/Characters/tile_00{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (32, 32))
                self.animation_frames.append(img)
            except:
                surf = pygame.Surface((32, 32))
                surf.fill((100, 50, 50))
                self.animation_frames.append(surf)
    
    def update(self, tilemap, map_width, map_height):
        if self.animation_frames:
            self.current_frame += 0.05
            if self.current_frame >= len(self.animation_frames):
                self.current_frame = 0

class Game:
    def __init__(self):
        pygame.display.set_caption('Platformer Game - PBO Project')
        mixer.init()
        
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
        self.game_state = "playing"
        self.editor_mode = True
        self.camera_x = 0
        self.camera_y = 0
        self.tile_size = 32
        
        self.map_width = 2000
        self.map_height = 1000
        
        self.enemies_to_win = 5
        
        self.enemies = []
        self.tilemap = {}
        self.decorations = []
        
        self.player = Player(100, 300)
        
        self.selected_tile = 'grass_top'
        self.tile_options = ['grass_top', 'grass_dirt', 'dirt', 'stone']
        self.deco_mode = False
        self.selected_deco = 'mushroom_red'
        
        self.editor_scroll_speed = 10
        self.scroll_left = False
        self.scroll_right = False
        self.scroll_up = False
        self.scroll_down = False
        
        self.tile_images = {}
        self.deco_images = {}
        
        self.load_tile_images()
        self.load_decoration_images()
        self.load_player_animations()
        self.load_music()
        
        self.load_map()
        self.jump_sound = None
        self.load_sounds()

        self.collected_coins = 0
        self.total_coins = 0

    def load_sounds(self):
        try:
            self.jump_sound = mixer.Sound('musik/lompat.mp3')
            self.jump_sound.set_volume(0.5)
        except:
            print("Gagal load suara lompat")
            self.jump_sound = None
    
    def play_jump_sound(self):
        if self.jump_sound:
            self.jump_sound.play()
    
    def load_tile_images(self):
        tile_files = {
            'grass_top': 'kenney_pixel-platformer/Tiles/tile_0022.png',
            'grass_dirt': 'kenney_pixel-platformer/Tiles/tile_0025.png',
            'dirt': 'kenney_pixel-platformer/Tiles/tile_0000.png',
            'stone': 'kenney_pixel-platformer/Tiles/tile_0001.png',
        }
        for name, path in tile_files.items():
            try:
                img = pygame.image.load(path).convert_alpha()
                self.tile_images[name] = pygame.transform.scale(img, (32, 32))
            except:
                surf = pygame.Surface((32, 32))
                if name == 'grass_top':
                    surf.fill((34, 139, 34))
                elif name == 'grass_dirt':
                    surf.fill((34, 139, 34))
                    pygame.draw.rect(surf, (101, 67, 33), (0, 16, 32, 16))
                elif name == 'dirt':
                    surf.fill((101, 67, 33))
                elif name == 'stone':
                    surf.fill((128, 128, 128))
                self.tile_images[name] = surf
    
    def load_decoration_images(self):
        deco_files = {
            'mushroom_red': 'kenney_pixel-platformer/Tiles/tile_0128.png',
            'pine_tree': 'kenney_pixel-platformer/Tiles/tile_0126.png',
            'long_grass': 'kenney_pixel-platformer/Tiles/tile_0125.png',
        }
        for name, path in deco_files.items():
            try:
                img = pygame.image.load(path).convert_alpha()
                self.deco_images[name] = pygame.transform.scale(img, (32, 32))
            except:
                surf = pygame.Surface((32, 32))
                if name == 'mushroom_red':
                    surf.fill((255, 0, 0))
                elif name == 'pine_tree':
                    surf.fill((0, 100, 0))
                elif name == 'long_grass':
                    surf.fill((0, 255, 0))
                self.deco_images[name] = surf
    
    def load_player_animations(self):
        animations = {}
        anim_types = ['idle', 'run', 'jump', 'fall']
        for anim in anim_types:
            try:
                sheet = pygame.image.load(f'assets/MainCharacters/PinkMan/{anim}.png').convert_alpha()
                frames = []
                for i in range(sheet.get_width() // 32):
                    frame = sheet.subsurface((i * 32, 0, 32, 32))
                    frames.append(frame)
                animations[anim] = frames
            except:
                surf = pygame.Surface((32, 32))
                surf.fill((255, 100, 200))
                animations[anim] = [surf]
        self.player.animations = animations
        return animations
    
    def load_music(self):
        try:
            mixer.music.load('musik/bgmmusicgame.mp3')
            mixer.music.set_volume(0.3)
            mixer.music.play(-1)
        except:
            print("Gagal load musik background")
    
    def change_music(self, music_file):
        try:
            mixer.music.load(f'musik/{music_file}')
            mixer.music.play(-1)
        except:
            print(f"Gagal load musik {music_file}")
    
    def check_win_lose(self):
        if len(self.coins) == 0:
           if self.game_state != "win":  # Hindari trigger berulang
               self.game_state = "win"
               self.change_music("kalaumenang.mp3")
               try:
                  win_sound = mixer.Sound('musik/suara_menang.mp3')
                  win_sound.play()
               except:
                  print("Gagal mainkan suara menang")
    
        if not self.player.is_alive:
           self.game_state = "lose"
           self.change_music("kalaukalah.mp3")
           try:
               lose_sound = mixer.Sound('musik/suara_kalah.mp3')
               lose_sound.play()
           except:
               print("Gagal mainkan suara kalah")
    
        if self.player.y > self.map_height:
            self.player.take_damage(999)
            self.game_state = "lose"
    
    def reset_game(self):
        self.player = Player(100, 300)
        self.player.kills = 0
        self.player.health = 5
        self.player.is_alive = True
        self.player.score = 0
        self.collected_coins = 0
        self.enemies = []
        self.coins=[]
        self.total_coins = 0
        self.game_state = "playing"
        self.load_map()
        self.change_music("bgmmusicgame.mp3")
    
    def spawn_bat(self, x, y, min_x, max_x):
        bat = Bat(x, y, min_x, max_x)
        self.enemies.append(bat)
        print(f"Kelelawar spawn di ({x}, {y})")
    
    def spawn_snail(self, x, y, min_x, max_x):
        snail = Snail(x, y, min_x, max_x)
        self.enemies.append(snail)
        print(f"Siput spawn di ({x}, {y})")
    
    def spawn_angry_block(self, x, y):
        block = AngryBlock(x, y)
        self.enemies.append(block)
        print(f"Batu marah spawn di ({x}, {y})")
    
    def update_enemies(self):
        for enemy in self.enemies[:]:
            enemy.update(self.tilemap, self.map_width, self.map_height)
            
            if self.player.rect.colliderect(enemy.rect):
                if self.player.velocity_y > 0 and self.player.rect.bottom - enemy.rect.top <= 15:
                    if enemy.take_damage(1):
                        self.player.velocity_y = -8
                        self.player.kills += 1
                    if not enemy.is_alive:
                        self.enemies.remove(enemy)
                else:
                    self.player.take_damage(enemy.damage)
                    self.player.velocity_y = -5

    def spawn_coin(self, x, y):
        coin = Coin(x, y - 25)
        self.coins.append(coin)
        self.total_coins += 1 
        print(f"Koin spawn di world position: ({x}, {y - 25})")
        print(f"Camera position: ({self.camera_x}, {self.camera_y})")
        print(f"Posisi di layar seharusnya: ({x - self.camera_x}, {y - 25 - self.camera_y})")

    def update_coins(self):
        for coin in self.coins[:]:
            coin.update()

            if self.player.rect.colliderect(coin.rect):
               print(f"Koin terkena player! Player rect: {self.player.rect}, Coin rect: {coin.rect}")
               if not coin.collected:
                  coin.collected = True
                  self.player.score += coin.value
                  self.collected_coins += 1
                  self.coins.remove(coin)
                  print(f"Koin diambil! Score: {self.player.score}, Total koin: {len(self.coins)}")
    
    def draw(self):
        self.screen.fill((100, 150, 200))
        
        for (tile_x, tile_y), tile_type in self.tilemap.items():
            world_x = tile_x * self.tile_size - self.camera_x
            world_y = tile_y * self.tile_size - self.camera_y
            if self.tile_images.get(tile_type):
                self.screen.blit(self.tile_images[tile_type], (world_x, world_y))
        
        for deco in self.decorations:
            screen_x = deco['rect'].x - self.camera_x
            screen_y = deco['rect'].y - self.camera_y
            if self.deco_images.get(deco['type']):
                self.screen.blit(self.deco_images[deco['type']], (screen_x, screen_y))
        
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_x, self.camera_y)
        
        self.draw_player()
        
        for coin in self.coins:
            coin.draw(self.screen, self.camera_x, self.camera_y)

        self.draw_ui()
        
        if self.game_state == "win":
            self.draw_win_screen()
        elif self.game_state == "lose":
            self.draw_lose_screen()


    
    def draw_player(self):
        if self.player.velocity_y < 0:
            self.player.action = 'jump'
        elif self.player.velocity_y > 1:
            self.player.action = 'fall'
        elif self.player.velocity_x != 0:
            self.player.action = 'run'
        else:
            self.player.action = 'idle'
        
        self.player.frame += 0.2
        if self.player.frame >= len(self.player.animations[self.player.action]):
            self.player.frame = 0
        
        image = self.player.animations[self.player.action][int(self.player.frame)]
        if self.player.last_direction ==  "left":
            image = pygame.transform.flip(image, True, False)

        if self.player.invicible_timer > 0 and (self.player.invicible_timer//5)% 2 == 0:
            image.set_alpha(128)
        else :
            image.set_alpha(255)
        
        self.screen.blit(image, (self.player.x - self.camera_x, self.player.y - self.camera_y))
        
        bar_width = 50
        bar_height = 8
        health_width = (self.player.health / self.player.max_health) * bar_width
        pygame.draw.rect(self.screen, (100, 0, 0), (10, 30, bar_width, bar_height))
        pygame.draw.rect(self.screen, (0, 255, 0), (10, 30, health_width, bar_height))
    
    def draw_ui(self):
         score_text = self.font.render(f"Kills: {self.player.kills}", True, (255, 255, 255))
         self.screen.blit(score_text, (10, 10))
    
         health_text = self.font.render(f"Health: {self.player.health}", True, (255, 255, 255))
         self.screen.blit(health_text, (10, 45))

         total_coins = self.total_coins
         stats_text = self.font.render(f"Score: {self.player.score}  Coins: {self.collected_coins}/{total_coins}", True, (255, 215, 0))
         self.screen.blit(stats_text, (10, 70))
        
       
         if self.editor_mode:
            mode_text = self.font.render("EDITOR MODE | ESC to Play | Arrow Keys to Scroll", True, (255, 255, 0))
            self.screen.blit(mode_text, (10, 95))
            pos_text = self.font.render(f"Camera: ({self.camera_x}, {self.camera_y})", True, (255, 255, 0))
            self.screen.blit(pos_text, (10, 120))

    def draw_win_screen(self):
        overlay = pygame.Surface((800, 600))
        overlay.set_alpha(200)
        overlay.fill((0, 100, 0))
        self.screen.blit(overlay, (0, 0))
        
        win_text = self.big_font.render("YOU WIN!", True, (255, 255, 0))
        text_rect = win_text.get_rect(center=(400, 250))
        self.screen.blit(win_text, text_rect)
        
        restart_text = self.font.render("Press R to Restart or ESC to Editor", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(400, 350))
        self.screen.blit(restart_text, restart_rect)
    
    def draw_lose_screen(self):
        overlay = pygame.Surface((800, 600))
        overlay.set_alpha(200)
        overlay.fill((100, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        lose_text = self.big_font.render("GAME OVER!", True, (255, 0, 0))
        text_rect = lose_text.get_rect(center=(400, 250))
        self.screen.blit(lose_text, text_rect)
        
        restart_text = self.font.render("Press R to Restart or ESC to Editor", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(400, 350))
        self.screen.blit(restart_text, restart_rect)
    
    def save_map(self):
        with open('map_data.txt', 'w') as f:
            for (x, y), tile_type in self.tilemap.items():
                f.write(f"{x},{y},{tile_type}\n")
        
        with open('decorations_data.txt', 'w') as f:
            for deco in self.decorations:
                f.write(f"{deco['type']},{deco['rect'].x},{deco['rect'].y}\n")
        
        with open('enemies_data.txt', 'w') as f:
            for enemy in self.enemies:
                if isinstance(enemy, Bat):
                    f.write(f"bat,{enemy.x},{enemy.y},{enemy.move_range[0]},{enemy.move_range[1]}\n")
                elif isinstance(enemy, Snail):
                    f.write(f"snail,{enemy.x},{enemy.y},{enemy.move_range[0]},{enemy.move_range[1]}\n")
                elif isinstance(enemy, AngryBlock):
                    f.write(f"angryblock,{enemy.x},{enemy.y}\n")

        with open('coins_data.txt', 'w') as f:
            for coin in self.coins:
                f.write(f"{coin.x},{coin.original_y}\n")
        
        print(f"Berhasil menyimpan {len(self.coins)} koin ke coins_data.txt")
        print("Map, dekorasi, koin dan musuh tersimpan!")
    
    def load_map(self):
        try:
            with open('map_data.txt', 'r') as f:
                for line in f:
                    x, y, tile_type = line.strip().split(',')
                    self.tilemap[(int(x), int(y))] = tile_type
        except:
            for x in range(50):
                self.tilemap[(x, 20)] = 'grass_top'
                self.tilemap[(x, 21)] = 'dirt'
        
        self.decorations = []
        try:
            with open('decorations_data.txt', 'r') as f:
                for line in f:
                    deco_type, x, y = line.strip().split(',')
                    self.decorations.append({
                        'type': deco_type,
                        'rect': pygame.Rect(float(x), float(y), 32, 32)
                    })
        except:
            pass
        
        self.enemies = []
        try:
            with open('enemies_data.txt', 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if parts[0] == 'bat':
                        self.spawn_bat(float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]))
                    elif parts[0] == 'snail':
                        self.spawn_snail(float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]))
                    elif parts[0] == 'angryblock':
                        self.spawn_angry_block(float(parts[1]), float(parts[2]))
        except:
            self.spawn_bat(300, 200, 200, 400)
            self.spawn_snail(400, 350, 300, 500)
            self.spawn_angry_block(200, 350)

        self.coins = []
        try:
            with open('coins_data.txt', 'r') as f:
              for line in f:
                 parts = line.strip().split(',')
                 if len(parts) == 2: 
                    x = float(parts[0])
                    original_y = float(parts[1])
                    coin = Coin(x, original_y)
                    self.coins.append(coin)
                 elif len(parts) == 3:  
                    x = float(parts[0])
                    original_y = float(parts[1])
                    coin = Coin(x, original_y)

                    self.coins.append(coin)

            print(f"Berhasil load {len(self.coins)} koin")
        except FileNotFoundError:
          print('Tidak ada file koin, mulai dengan koin kosong')
        except Exception as e:
          print(f"Error loading coins: {e}")  

        self.total_coins = len(self.coins)  
    
    def run(self):
        running = True
        while running:

            if not self.editor_mode and self.game_state == "playing":
                target_x = int(self.player.x + 16 - 400)
                target_y = int(self.player.y + 16 - 300)
                
                target_x = max(0, min(target_x, self.map_width - 800))
                target_y = max(0, min(target_y, self.map_height - 600))
                
                self.camera_x = target_x
                self.camera_y = target_y

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_map()
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_state == "playing":
                            self.editor_mode = not self.editor_mode
                        else:
                            self.reset_game()
                            self.editor_mode = True
                    
                    if self.game_state != "playing":
                        if event.key == pygame.K_r:
                            self.reset_game()
                    
                    if self.editor_mode:
                        if event.key == pygame.K_LEFT:
                            self.scroll_left = True
                        if event.key == pygame.K_RIGHT:
                            self.scroll_right = True
                        if event.key == pygame.K_UP:
                            self.scroll_up = True
                        if event.key == pygame.K_DOWN:
                            self.scroll_down = True
                    
                    if self.editor_mode and self.game_state == "playing":
                        if event.key == pygame.K_1:
                            self.selected_tile = 'grass_top'
                        elif event.key == pygame.K_2:
                            self.selected_tile = 'grass_dirt'
                        elif event.key == pygame.K_3:
                            self.selected_tile = 'dirt'
                        elif event.key == pygame.K_4:
                            self.selected_tile = 'stone'
                        
                        elif event.key == pygame.K_b:
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            world_x = (mouse_x + self.camera_x) // 32 * 32
                            world_y = (mouse_y + self.camera_y) // 32 * 32
                            self.spawn_bat(world_x, world_y, world_x - 100, world_x + 100)
                        elif event.key == pygame.K_n:
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            world_x = (mouse_x + self.camera_x) // 32 * 32
                            world_y = (mouse_y + self.camera_y) // 32 * 32
                            self.spawn_snail(world_x, world_y, world_x - 100, world_x + 100)
                        elif event.key == pygame.K_v:
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            world_x = (mouse_x + self.camera_x) // 32 * 32
                            world_y = (mouse_y + self.camera_y) // 32 * 32
                            self.spawn_angry_block(world_x, world_y)
                        
                        elif event.key == pygame.K_m:
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            world_x = (mouse_x + self.camera_x) // 32 * 32
                            world_y = (mouse_y + self.camera_y) // 32 * 32
                            self.decorations.append({
                                'type': 'mushroom_red',
                                'rect': pygame.Rect(world_x, world_y, 32, 32)
                            })
                            print(f"Dekorasi Jamur di ({world_x}, {world_y})")
                        elif event.key == pygame.K_p:
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            world_x = (mouse_x + self.camera_x) // 32 * 32
                            world_y = (mouse_y + self.camera_y) // 32 * 32
                            self.decorations.append({
                                'type': 'pine_tree',
                                'rect': pygame.Rect(world_x, world_y, 32, 32)
                            })
                            print(f"Dekorasi Pohon di ({world_x}, {world_y})")
                        elif event.key == pygame.K_g:
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            world_x = (mouse_x + self.camera_x) // 32 * 32
                            world_y = (mouse_y + self.camera_y) // 32 * 32
                            self.decorations.append({
                                'type': 'long_grass',
                                'rect': pygame.Rect(world_x, world_y, 32, 32)
                            })
                            print(f"Dekorasi Rumput di ({world_x}, {world_y})")

                        elif event.key == pygame.K_k: 
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            world_x = (mouse_x + self.camera_x) // 32 * 32
                            world_y = (mouse_y + self.camera_y) // 32 * 32
                            self.spawn_coin(world_x, world_y)
                        
                        elif event.key == pygame.K_s:
                            self.save_map()
                        elif event.key == pygame.K_c:
                            self.enemies.clear()
                            print("Semua enemy dihapus!")
                        elif event.key == pygame.K_x:
                            if self.enemies:
                                closest = min(self.enemies, key=lambda e: abs(e.x - self.player.x) + abs(e.y - self.player.y))
                                self.enemies.remove(closest)
                                print(f"Enemy terdekat dihapus!")
                    
                    if not self.editor_mode and self.game_state == "playing":
                        if event.key == pygame.K_a:
                            self.player.velocity_x = -self.player.speed
                        if event.key == pygame.K_d:
                            self.player.velocity_x = self.player.speed
                        if event.key == pygame.K_w:
                            if self.player.jump():
                                self.play_jump_sound()
                
                if event.type == pygame.KEYUP:
                    if self.editor_mode:
                        if event.key == pygame.K_LEFT:
                            self.scroll_left = False
                        if event.key == pygame.K_RIGHT:
                            self.scroll_right = False
                        if event.key == pygame.K_UP:
                            self.scroll_up = False
                        if event.key == pygame.K_DOWN:
                            self.scroll_down = False
                    
                    if not self.editor_mode and self.game_state == "playing":
                        if event.key == pygame.K_a and self.player.velocity_x < 0:
                            self.player.velocity_x = 0
                        if event.key == pygame.K_d and self.player.velocity_x > 0:
                            self.player.velocity_x = 0
                
                if self.editor_mode and event.type == pygame.MOUSEBUTTONDOWN:
                    tile_x = (pygame.mouse.get_pos()[0] + self.camera_x) // 32
                    tile_y = (pygame.mouse.get_pos()[1] + self.camera_y) // 32
                    mouse_world_x = pygame.mouse.get_pos()[0] + self.camera_x
                    mouse_world_y = pygame.mouse.get_pos()[1] + self.camera_y
                    
                    if event.button == 1: 
                        if 0 <= tile_x < self.map_width // 32 and 0 <= tile_y < self.map_height // 32:
                            self.tilemap[(tile_x, tile_y)] = self.selected_tile
                    
                    elif event.button == 3: 
                        deco_deleted = False
                        for deco in self.decorations[:]:
                            if deco['rect'].collidepoint(mouse_world_x, mouse_world_y):
                                self.decorations.remove(deco)
                                deco_deleted = True
                                print("Dekorasi dihapus!")
                                break

                        coin_deleted = False
                        if not deco_deleted:
                            for coin in self.coins[:]:
                             if coin.rect.collidepoint(mouse_world_x, mouse_world_y):
                                self.coins.remove(coin)
                                self.total_coins -= 1 
                                coin_deleted = True
                                print("Koin dihapus!")
                                break
                        
                        if not deco_deleted and not coin_deleted:
                          for enemy in self.enemies[:]:
                            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                            if enemy_rect.collidepoint(mouse_world_x, mouse_world_y):
                              self.enemies.remove(enemy)
                              print("Enemy dihapus!")
                              break
                          else:

                             if (tile_x, tile_y) in self.tilemap:
                               del self.tilemap[(tile_x, tile_y)]
                               print("Tile dihapus!")
            
            if self.editor_mode:
                if self.scroll_left:
                    self.camera_x -= self.editor_scroll_speed
                if self.scroll_right:
                    self.camera_x += self.editor_scroll_speed
                if self.scroll_up:
                    self.camera_y -= self.editor_scroll_speed
                if self.scroll_down:
                    self.camera_y += self.editor_scroll_speed
                
                self.camera_x = max(0, min(self.camera_x, self.map_width - 800))
                self.camera_y = max(0, min(self.camera_y, self.map_height - 600))
            
            if not self.editor_mode and self.game_state == "playing":
                self.player.update(self.tilemap, self.map_width, self.map_height)
                self.update_enemies()
                self.update_coins()
                self.check_win_lose()
        
            self.draw()
            
            pygame.display.update()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()
