"""Nivel jugable del bosque, incluyendo mapa y cámara."""

from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pygame

from src.entities.player import Player
from src.entities.boss import BossEnemy
from src.entities.enemy import Enemy
from src.entities.collectible import GoldCoin, find_platform_positions
from src.screens.cave_level import CaveLevel
from src.screens.main_menu import MainMenu


def find_enemy_positions(solid_tiles, world_width, tile_size, count):
    """Encuentra posiciones de enemigos repartidas por las plataformas."""
    surfaces = {}
    for tile in solid_tiles:
        surfaces.setdefault(tile.top, []).append(tile)

    candidates = []
    enemy_width = 28
    enemy_height = 44
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
            right = run[-1].right - enemy_width
            for x in range(left, right + 1, tile_size):
                position = pygame.Rect(x, surface_y - enemy_height, enemy_width, enemy_height)
                if (
                    position.left >= 320
                    and position.right <= world_width - 360
                    and position.top >= 0
                    and not any(position.colliderect(tile) for tile in solid_tiles)
                ):
                    candidates.append((x - 14, surface_y - enemy_height))

    candidates.sort(key=lambda position: (position[0], position[1]))
    if len(candidates) <= count:
        return candidates

    selected = []
    step = (len(candidates) - 1) / (count - 1)
    for index in range(count):
        candidate = candidates[round(index * step)]
        if candidate not in selected:
            selected.append(candidate)
    return selected


class ForestLevel:
    """Nivel de prueba: dibuja el TMX y permite probar el movimiento."""

    TILE_SIZE = 32
    MAP_SIZE = (150, 23)

    def __init__(self, game):
        self.game = game
        root_path = Path(__file__).resolve().parents[2]
        self.map_path = root_path / "levels" / "forest.tmx"
        self.tileset_path = root_path / "assets" / "levels" / "forest"
        background_path = root_path / "assets" / "levels" / "forest" / "background.png"
        background = pygame.image.load(background_path).convert()
        self.background = pygame.transform.smoothscale(
            background, self.game.screen.get_size()
        )
        self.tiles, self.solid_tiles = self._load_map()
        assets_path = root_path / "assets" / "images" / "player"
        self.player = Player((64, 500), assets_path)
        enemy_assets_path = (
            root_path / "assets" / "images" / "enemies" / "forest_skeleton_yellow"
        )
        enemy_positions = find_enemy_positions(
            self.solid_tiles,
            self.MAP_SIZE[0] * self.TILE_SIZE,
            self.TILE_SIZE,
            14,
        )
        self.enemies = [
            Enemy(position, enemy_assets_path) for position in enemy_positions
        ]
        boss_assets_path = (
            root_path / "assets" / "images" / "enemies" / "forest_mushroom_boss"
        )
        self.boss = BossEnemy((4660, 500), boss_assets_path)
        self.enemies.append(self.boss)
        collectible_image = pygame.image.load(
            root_path / "assets" / "images" / "collectibles" / "gold_coin.png"
        ).convert_alpha()
        coin_positions = find_platform_positions(
            self.solid_tiles,
            self.MAP_SIZE[0] * self.TILE_SIZE,
            self.TILE_SIZE,
            12,
        )
        self.collectibles = [
            GoldCoin(position, collectible_image) for position in coin_positions
        ]
        self.camera_x = 0

    def _load_map(self):
        """Carga el TMX y convierte sus celdas en sprites y hitboxes."""
        root = ET.parse(self.map_path).getroot()
        tilesets = []
        for tileset_reference in root.findall("tileset"):
            # Cada tileset puede tener una ruta relativa distinta dentro del TMX.
            tileset_file = self.map_path.parent / tileset_reference.get("source")
            tileset_root = ET.parse(tileset_file).getroot()
            image = pygame.image.load(
                self.tileset_path / Path(tileset_root.find("image").get("source")).name
            ).convert_alpha()
            columns = tileset_root.get("columns")
            columns = int(columns) if columns else image.get_width() // self.TILE_SIZE
            tilesets.append(
                (
                    int(tileset_reference.get("firstgid", 1)),
                    int(tileset_root.get("tilecount", 0)),
                    columns,
                    image,
                )
            )
        tilesets.sort(key=lambda tileset: tileset[0])

        layer = root.find("layer")
        values = [int(value) for value in re.findall(r"\d+", layer.find("data").text)]

        tiles = []
        solid_tiles = []
        for index, gid in enumerate(values):
            if gid == 0:
                # En TMX, un GID cero representa una celda vacía.
                continue
            tileset = next(
                (
                    tileset
                    for tileset in reversed(tilesets)
                    if gid >= tileset[0]
                ),
                None,
            )
            if tileset is None:
                raise ValueError(f"GID de tileset no válido: {gid}")
            firstgid, tilecount, columns, tileset_image = tileset
            tile_index = gid - firstgid
            if tile_index >= tilecount:
                raise ValueError(f"GID fuera del tileset: {gid}")
            map_x = index % self.MAP_SIZE[0]
            map_y = index // self.MAP_SIZE[0]
            destination = pygame.Rect(
                map_x * self.TILE_SIZE,
                map_y * self.TILE_SIZE,
                self.TILE_SIZE,
                self.TILE_SIZE,
            )
            # El índice local empieza en cero dentro del tileset seleccionado.
            source = pygame.Rect(
                (tile_index % columns) * self.TILE_SIZE,
                (tile_index // columns) * self.TILE_SIZE,
                self.TILE_SIZE,
                self.TILE_SIZE,
            )
            tiles.append((tileset_image, source, destination))
            solid_tiles.append(destination)
        return tiles, solid_tiles

    def handle_event(self, event):
        """Permite volver al menú con Escape."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.current_screen = MainMenu(self.game)

    def update(self):
        """Actualiza el nivel y devuelve al menú si el jugador cae al vacío."""
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.solid_tiles)
        world_height = self.MAP_SIZE[1] * self.TILE_SIZE
        if self.player.rect.top > world_height:
            self.game.current_screen = MainMenu(self.game)
            return

        attack_rect = self.player.get_attack_rect()
        alive_enemies = []
        for enemy in self.enemies:
            enemy.update(self.solid_tiles, self.player)
            if attack_rect.colliderect(enemy.rect):
                enemy.take_damage(5 if enemy is self.boss else 1)
            if enemy.death_finished:
                self.player.heal(self.player.max_health)
            if not enemy.death_finished:
                alive_enemies.append(enemy)
        self.enemies = alive_enemies
        for collectible in self.collectibles:
            collectible.try_collect(self.player)
        if self.player.health <= 0:
            self.game.current_screen = MainMenu(self.game)
            return
        world_width = self.MAP_SIZE[0] * self.TILE_SIZE
        if (
            self.player.rect.right >= world_width
            and self.all_collectibles_collected
            and self.boss.death_finished
        ):
            self.game.current_screen = CaveLevel(self.game)
            return
        # El jugador no puede salir por los laterales del mundo.
        self.player.rect.left = max(0, min(self.player.rect.left, world_width - self.player.rect.width))
        target = self.player.rect.centerx - self.game.screen.get_width() // 2
        max_camera = world_width - self.game.screen.get_width()
        # La cámara sigue al jugador, pero nunca muestra fuera del mapa.
        self.camera_x = max(0, min(target, max_camera))

    def draw(self, screen):
        """Pinta el fondo, las celdas visibles y el jugador."""
        screen.blit(self.background, (0, 0))
        for image, source, destination in self.tiles:
            screen.blit(image, (destination.x - self.camera_x, destination.y), source)

        for enemy in self.enemies:
            enemy.draw(screen, self.camera_x)
        for collectible in self.collectibles:
            collectible.draw(screen, self.camera_x)
        self.player.draw(screen, self.camera_x)
        self.player.draw_health_bar(screen)
        self.draw_collectible_counter(screen)

    @property
    def all_collectibles_collected(self):
        """Indica si el jugador ha recogido todas las monedas del nivel."""
        return all(collectible.collected for collectible in self.collectibles)

    def draw_collectible_counter(self, screen):
        """Dibuja el progreso de monedas en la esquina superior derecha."""
        font = pygame.font.Font(None, 32)
        collected = sum(collectible.collected for collectible in self.collectibles)
        text = font.render(
            f"Monedas: {collected}/{len(self.collectibles)}",
            True,
            (245, 245, 245),
        )
        screen.blit(text, (screen.get_width() - text.get_width() - 24, 20))
