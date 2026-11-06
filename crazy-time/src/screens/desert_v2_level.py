"""Segundo nivel del desierto, situado entre el bosque y la cueva."""

from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pygame

from src.entities.collectible import GoldCoin, find_platform_positions
from src.entities.enemy import Enemy
from src.entities.player import Player
from src.screens.cave_level import CaveLevel
from src.screens.main_menu import MainMenu


class DesertV2Level:
    """Nivel desértico con mapa, decoración y transición a la cueva."""

    TILE_SIZE = 32

    def __init__(self, game):
        self.game = game
        root_path = Path(__file__).resolve().parents[2]
        self.map_path = root_path / "levels" / "desert_v2.tmx"
        self.assets_path = root_path / "assets" / "levels" / "desert_v2"
        self.map_width, self.map_height, self.tiles, self.solid_tiles = (
            self._load_map()
        )
        background = pygame.image.load(
            self.assets_path / "background.png"
        ).convert()
        self.background = pygame.transform.smoothscale(
            background, self.game.screen.get_size()
        )
        self.decoration = pygame.image.load(
            self.assets_path / "decoration.png"
        ).convert_alpha()

        player_assets = root_path / "assets" / "images" / "player"
        self.player = Player((64, 480), player_assets)
        enemy_assets = (
            root_path / "assets" / "images" / "enemies" / "forest_skeleton_yellow"
        )
        self.enemies = [
            Enemy((850, 480), enemy_assets),
            Enemy((1750, 480), enemy_assets),
            Enemy((2850, 480), enemy_assets),
            Enemy((3800, 480), enemy_assets),
        ]
        coin_image = pygame.image.load(
            root_path / "assets" / "images" / "collectibles" / "gold_coin.png"
        ).convert_alpha()
        coin_positions = find_platform_positions(
            self.solid_tiles,
            self.map_width * self.TILE_SIZE,
            self.TILE_SIZE,
            12,
        )
        self.collectibles = [
            GoldCoin(position, coin_image) for position in coin_positions
        ]
        self.camera_x = 0

    def _load_map(self):
        root = ET.parse(self.map_path).getroot()
        layer = root.find("layer")
        if layer is None:
            raise ValueError("El mapa Desert V2 no tiene ninguna capa.")
        width = int(root.get("width"))
        height = int(root.get("height"))
        tileset_ref = root.find("tileset")
        if tileset_ref is None:
            raise ValueError("El mapa Desert V2 no tiene tileset.")
        tileset_root = ET.parse(
            self.map_path.parent / tileset_ref.get("source")
        ).getroot()
        image_definition = tileset_root.find("image")
        if image_definition is None:
            raise ValueError("El tileset Desert V2 no tiene imagen.")
        image = pygame.image.load(
            self.assets_path / Path(image_definition.get("source")).name
        ).convert_alpha()
        columns = int(tileset_root.get("columns", 1))
        tile_count = int(tileset_root.get("tilecount", 0))
        first_gid = int(tileset_ref.get("firstgid", 1))
        values = [
            int(value)
            for value in re.findall(r"\d+", layer.find("data").text or "")
        ]

        tiles = []
        solid_tiles = []
        for index, raw_gid in enumerate(values):
            gid = raw_gid & 0x1FFFFFFF
            if gid == 0:
                continue
            tile_index = gid - first_gid
            if tile_index < 0 or tile_index >= tile_count:
                raise ValueError(f"GID Desert V2 no válido: {raw_gid}")
            destination = pygame.Rect(
                (index % width) * self.TILE_SIZE,
                (index // width) * self.TILE_SIZE,
                self.TILE_SIZE,
                self.TILE_SIZE,
            )
            source = pygame.Rect(
                (tile_index % columns) * self.TILE_SIZE,
                (tile_index // columns) * self.TILE_SIZE,
                self.TILE_SIZE,
                self.TILE_SIZE,
            )
            tiles.append((image, source, destination))
            solid_tiles.append(destination)
        return width, height, tiles, solid_tiles

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.current_screen = MainMenu(self.game)

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.solid_tiles)
        world_width = self.map_width * self.TILE_SIZE
        world_height = self.map_height * self.TILE_SIZE
        if self.player.rect.top > world_height:
            self.game.current_screen = MainMenu(self.game)
            return

        attack_rect = self.player.get_attack_rect()
        alive_enemies = []
        for enemy in self.enemies:
            enemy.update(self.solid_tiles, self.player)
            if attack_rect.colliderect(enemy.rect):
                enemy.take_damage(1)
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
        if self.player.rect.right >= world_width and self.all_collectibles_collected:
            self.game.current_screen = CaveLevel(self.game)
            return
        self.player.rect.left = max(
            0, min(self.player.rect.left, world_width - self.player.rect.width)
        )
        target = self.player.rect.centerx - self.game.screen.get_width() // 2
        self.camera_x = max(
            0, min(target, world_width - self.game.screen.get_width())
        )

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        screen.blit(self.decoration, (-self.camera_x, 0))
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
        return all(collectible.collected for collectible in self.collectibles)

    def draw_collectible_counter(self, screen):
        font = pygame.font.Font(None, 32)
        collected = sum(coin.collected for coin in self.collectibles)
        text = font.render(
            f"Monedas: {collected}/{len(self.collectibles)}",
            True,
            (245, 245, 245),
        )
        screen.blit(text, (screen.get_width() - text.get_width() - 24, 20))
