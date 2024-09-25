import asyncio
import pygame
from os.path import join
from random import randint, uniform

# Initialize pygame
pygame.init()
screenWidth, screenHeight = 1280, 700
display_surface = pygame.display.set_mode((screenWidth, screenHeight))
pygame.display.set_caption("vinveli")
clock = pygame.time.Clock()
run = True

# Game variables
health = 5
game_state = 'start'

# Assets
stars_surf = pygame.image.load(join("images", "star.png")).convert_alpha()
laser_surf = pygame.image.load(join("images", "laser.png")).convert_alpha()
meteor = pygame.image.load(join("images", "meteor.png")).convert_alpha()
font = pygame.font.Font(join("images", "Oxanium-Bold.ttf"), 30)
fontsize = pygame.font.Font(join("images", "Oxanium-Bold.ttf"), 30)

explosion_frames = [pygame.image.load(join("images", "explosion", f'{i}.png')).convert_alpha() for i in range(21)]

laser_sound = pygame.mixer.Sound(join("audio", "laser.wav"))
laser_sound.set_volume(.2)

explosion_sound = pygame.mixer.Sound(join("audio", "explosion.wav"))
explosion_sound.set_volume(.2)

damage_sound = pygame.mixer.Sound(join("audio", "damage.ogg"))
damage_sound.set_volume(.5)

pygame.mixer.music.load(join("audio", "game_music.wav"))
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1)  # Loop the music indefinitely

# Define classes
class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.image.load(join('images', 'player.png')).convert_alpha()
        self.rect = self.image.get_rect(center=(screenWidth / 2, screenHeight / 2))
        self.direction = pygame.math.Vector2()
        self.speed = 300
        self.can_shoot = True
        self.shoot_time = 0
        self.cooldown_time = 200
        self.mask = pygame.mask.from_surface(self.image)

    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.cooldown_time:
                self.can_shoot = True

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        self.direction = self.direction.normalize() if self.direction else self.direction

        self.rect.center += self.direction * self.speed * dt

        # Boundary checking
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screenWidth:
            self.rect.right = screenWidth
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > screenHeight:
            self.rect.bottom = screenHeight

        # Shooting logic
        if keys[pygame.K_SPACE] and self.can_shoot:
            Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()
            laser_sound.play()

        # Cooldown handling
        if not self.can_shoot:
            self.laser_timer()

class Stars(pygame.sprite.Sprite):
    def __init__(self, stars_surf, groups):
        super().__init__(groups)
        self.image = stars_surf
        self.rect = self.image.get_rect(center=(randint(0, screenWidth), randint(0, screenHeight)))

class Laser(pygame.sprite.Sprite):
    def __init__(self, laser_surf, pos, groups):
        super().__init__(groups)
        self.image = laser_surf
        self.rect = self.image.get_rect(midbottom=pos)
        self.speed = 400  # Define speed explicitly

    def update(self, dt):
        self.rect.centery -= self.speed * dt
        if self.rect.bottom < 0:
            self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, meteor_surf, pos, groups):
        super().__init__(groups)
        self.original_surf = meteor
        self.image = meteor_surf
        self.rect = self.image.get_frect(center = pos)

        self.direction = pygame.Vector2(uniform(-0.5,0.5),1)
        self.speed = randint(100, 700)
        
        self.random_speed = randint(80,160)
        self.speed = randint(100,400)
        self.rotation = 0

        #mask
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if self.rect.top > screenHeight:
            self.kill()

        self.rotation += self.random_speed * dt
        self.image = pygame.transform.rotate(self.original_surf, self.rotation)
        self.rect = self.image.get_frect(center = self.rect.center)

class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frames_index = 0
        self.image = frames[self.frames_index]
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        self.frames_index += 20 * dt
        if self.frames_index < len(self.frames):
            self.image = self.frames[int(self.frames_index)]
        else:
            self.kill()

def collisions():
    global run, health, game_state
    collision_sprites = pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask)
    if collision_sprites:
        health -= 1
        if health <= 0:
            show_start_screen()
            health = 5
            game_state = 'start'
        else:
            run = True
    if collision_sprites:
        damage_sound.play()

    display_health(health)

    collided_sprites = pygame.sprite.groupcollide(laser_sprites, meteor_sprites, True, True)
    for laser, meteors in collided_sprites.items():
        for i in meteors:
            i.kill()
            explosion_sound.play()
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)

def display_health(health):
    font_surf = fontsize.render(f"You have {health} lives", True, ("white"))
    font_rect = font_surf.get_rect(topleft=(10, 10))
    display_surface.blit(font_surf, font_rect)

def display_scores():
    current_time = pygame.time.get_ticks() // 100
    font_surf = font.render(f'SCORE is {current_time}', True, ("#f0f0f0"))
    font_rect = font_surf.get_rect(midbottom=(screenWidth / 2, screenHeight - 50))
    display_surface.blit(font_surf, font_rect)
    pygame.draw.rect(display_surface, "white", font_rect.inflate(30, 20).move(0, -5), 4, 5)

def show_start_screen():
    title_font = pygame.font.Font(None, 90)
    font = pygame.font.Font(None, 40)
    text = font.render('Press X to Start', True, (255, 255, 255))
    text_rect = text.get_rect(center=(screenWidth / 2, 600))

    text2 = font.render('Press Backspace to exit', True, (255, 255, 255))
    text2_rect = text2.get_rect(center=(screenWidth / 2, 650))

    text3 = title_font.render('The SpaceShip...', True, ('white'))
    text3_rect = text.get_rect(center=(screenWidth / 2 - 110, 70))

    image = pygame.image.load(join('images', 'download.jpeg')).convert_alpha()
    image_rect = pygame.transform.scale(image, (screenWidth, screenHeight))

    display_surface.blit(image_rect, (0, 0))  # Fill the screen with black
    display_surface.blit(text, text_rect)
    display_surface.blit(text2, text2_rect)
    display_surface.blit(text3, text3_rect)

    pygame.display.update()

# Create sprite groups
all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
for i in range(40):
    Stars(stars_surf, all_sprites)
player = Player(all_sprites)

# Custom event for meteors
meteor_amount = 800
meteor_event = pygame.event.custom_type()
pygame.time.set_timer(meteor_event, meteor_amount)

async def main():
    global run, health, game_state

    while run:
        dt = clock.tick() / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if game_state == 'start':
                if event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                    game_state = 'playing'
                if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                    run = False
            elif game_state == 'playing':
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    run = False  # Allow quitting during gameplay with 'Q'

            if event.type == meteor_event:
                x, y = (randint(0, screenWidth), randint(-100, -100))
                Meteor(meteor, (x, y), [all_sprites, meteor_sprites])

        if game_state == 'start':
            show_start_screen()
        elif game_state == 'playing':
            # Update
            all_sprites.update(dt)
            collisions()
            # Draw
            display_surface.fill("#451d6e")  # HEX color value
            display_scores()
            display_health(health)
            all_sprites.draw(display_surface)

            pygame.display.update()

        await asyncio.sleep(0)  # Yield control back to the event loop

    pygame.quit()

# Run the game loop
asyncio.run(main())
