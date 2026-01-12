import pygame
import random
from utils import resource_path

class TorchParticle:
    def __init__(self, x, y, curta=False):
        self.x = x + random.randint(-4, 4)
        self.y = y + random.randint(-4, 4)

        self.vx = random.uniform(-0.2, 0.2)
        self.vy = random.uniform(-0.8, -0.3) if curta else random.uniform(-1.2, -0.5)

        self.life = random.randint(15, 30) if curta else random.randint(30, 60)
        self.radius = random.randint(1, 2) if curta else random.randint(2, 4)
        self.alpha = 160 if curta else 180

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.alpha = max(0, self.alpha - 4)

    def draw(self, surface, offset=(0, 0)):
        if self.life <= 0:
            return

        ox, oy = offset
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            s,
            (255, 140, 40, self.alpha),
            (self.radius, self.radius),
            self.radius
        )
        surface.blit(s, (self.x + ox, self.y + oy))


class Torch:
    SPRITE = None

    def __init__(self, x, y, criar_luz_func, inferior=False):
        self.x = x
        self.y = y
        self.inferior = inferior

        if not inferior:
            if Torch.SPRITE is None:
                original = pygame.image.load(
                    resource_path("assets/TileSet/tocha.png")
                ).convert_alpha()

                Torch.SPRITE = pygame.transform.scale(
                    original,
                    (original.get_width() * 3, original.get_height() * 3)
                )

            self.sprite = Torch.SPRITE
            self.rect = self.sprite.get_rect(midbottom=(x, y))
        else:
            self.sprite = None
            self.rect = pygame.Rect(x, y, 0, 0)

        # luz da tocha
        self.raio_luz = 330
        self.luz = criar_luz_func(self.raio_luz)

        self.particulas = []
        self.spawn_timer = 0

    def update(self):
        self.spawn_timer += 1

        if self.spawn_timer >= 3:
            self.spawn_timer = 0
            self.particulas.append(
                TorchParticle(
                    self.rect.centerx if self.sprite else self.x,
                    self.rect.top if self.sprite else self.y,
                    curta=self.inferior
                )
            )

        for p in self.particulas[:]:
            p.update()
            if p.life <= 0:
                self.particulas.remove(p)

    def aplicar_luz(self, darkness, offset=(0, 0)):
        ox, oy = offset
        r = self.raio_luz
        darkness.blit(
            self.luz,
            (self.x - r + ox, self.y - r + oy),
            special_flags=pygame.BLEND_RGBA_SUB
        )

    def draw_particles(self, screen, offset):
        for p in self.particulas:
            p.draw(screen, offset)

    def draw(self, screen, offset=(0, 0)):
        if self.sprite is None:
            return

        ox, oy = offset
        screen.blit(
            self.sprite,
            (self.rect.x + ox, self.rect.y + oy)
        )


class TorchManager:
    def __init__(self):
        self.tochas = []

    def add(self, torch):
        self.tochas.append(torch)

    def update(self):
        for t in self.tochas:
            t.update()

    def draw(self, screen, offset):
        for t in self.tochas:
            t.draw(screen, offset)

    def draw_particles(self, screen, offset):
        for t in self.tochas:
            t.draw_particles(screen, offset)

    def aplicar_luzes(self, darkness, offset):
        for t in self.tochas:
            t.aplicar_luz(darkness, offset)