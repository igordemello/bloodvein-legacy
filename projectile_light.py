import pygame

class ProjectileLight:
    _cache = {}

    def __init__(self, color, radius=60, intensity=220, steps=12):
        """
        color: (r, g, b)
        radius: raio máximo da luz
        intensity: alpha máximo
        steps: suavidade do gradiente (player geralmente usa 10~16)
        """
        self.color = color
        self.radius = radius
        self.intensity = intensity
        self.steps = steps

        key = (color, radius, intensity, steps)
        if key not in ProjectileLight._cache:
            ProjectileLight._cache[key] = self._create_light()

        self.surface = ProjectileLight._cache[key]

    def _create_light(self):
        r = self.radius
        size = r * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = r

        cr, cg, cb = self.color

        # DE FORA PRA DENTRO (ESSENCIAL)
        for i in range(self.steps):
            t = i / (self.steps - 1)  # 0 → 1

            radius = int(r * (1 - t))
            alpha = int(self.intensity * (t ** 2))

            if alpha <= 0 or radius <= 0:
                continue

            pygame.draw.circle(
                surf,
                (cr, cg, cb, alpha),
                (cx, cy),
                radius
            )

        return surf


    def apply(self, darkness, x, y, offset=(0, 0)):
        ox, oy = offset
        r = self.radius
        darkness.blit(
            self.surface,
            (x - r + ox, y - r + oy),
            special_flags=pygame.BLEND_RGBA_SUB
        )
