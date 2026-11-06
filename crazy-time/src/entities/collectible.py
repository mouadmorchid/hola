"""Coleccionables que el jugador puede recoger durante un nivel."""

import pygame


def find_platform_positions(solid_tiles, world_width, tile_size, count):
    """Encuentra posiciones distribuidas con dos tiles de espacio libre."""
    surfaces = {}
    for tile in solid_tiles:
        surfaces.setdefault(tile.top, []).append(tile)

    candidates = []
    for surface_y, tiles in surfaces.items():
        tiles.sort(key=lambda tile: tile.left)
        runs = []
        current = []
        for tile in tiles:
            if current and tile.left > current[-1].right:
                runs.append(current)
                current = []
            current.append(tile)
        if current:
            runs.append(current)

        for run in runs:
            left = run[0].left
            right = run[-1].right
            for x in range(left, right - Collectible.SIZE + 1, tile_size):
                position = pygame.Rect(x, surface_y - Collectible.SIZE, Collectible.SIZE, Collectible.SIZE)
                if (
                    position.left >= 0
                    and position.right <= world_width
                    and position.top >= 0
                    and not any(position.colliderect(tile) for tile in solid_tiles)
                ):
                    candidates.append((x, surface_y))

    candidates.sort()
    if len(candidates) <= count:
        return candidates
    step = (len(candidates) - 1) / (count - 1)
    return [candidates[round(index * step)] for index in range(count)]


class Collectible:
    """Objeto recogible colocado sobre una plataforma."""

    SIZE = 56
    FRAME_COUNT = 1
    FRAME_DELAY = 8

    def __init__(self, position, image):
        self.rect = pygame.Rect(
            position[0],
            position[1] - self.SIZE,
            self.SIZE,
            self.SIZE,
        )
        self.frames = self._load_frames(image)
        self.image = pygame.transform.smoothscale(
            self.frames[0], self.rect.size
        )
        self.animation_frame = 0
        self.animation_timer = 0
        self.collected = False

    def try_collect(self, player):
        """Marca el objeto como recogido cuando toca al jugador."""
        if not self.collected and self.rect.colliderect(player.rect):
            self.collected = True

    def draw(self, screen, camera_x):
        """Dibuja el objeto en su posición del mundo."""
        if not self.collected:
            self.animation_timer += 1
            if self.animation_timer >= self.FRAME_DELAY:
                self.animation_timer = 0
                self.animation_frame = (
                    self.animation_frame + 1
                ) % len(self.frames)
                self.image = pygame.transform.smoothscale(
                    self.frames[self.animation_frame], self.rect.size
                )
            screen.blit(
                self.image,
                (self.rect.x - camera_x, self.rect.y),
            )

    def _load_frames(self, sheet):
        """Divide la hoja horizontal en el número de frames de la clase."""
        if self.FRAME_COUNT == 1:
            return [sheet]
        frame_width = sheet.get_width() // self.FRAME_COUNT
        return [
            sheet.subsurface(
                pygame.Rect(index * frame_width, 0, frame_width, sheet.get_height())
            ).copy()
            for index in range(self.FRAME_COUNT)
        ]


class GoldCoin(Collectible):
    """Moneda dorada recogible del nivel del bosque."""

    FRAME_COUNT = 4


class Amethyst(Collectible):
    """Amatista recogible del nivel de la cueva."""

    FRAME_COUNT = 2
