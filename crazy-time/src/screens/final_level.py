"""Nivel final usado temporalmente para pruebas."""

from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pygame

from src.entities.enemy import Enemy
from src.entities.player import Player
from src.screens.main_menu import MainMenu


class FinalLevel:
    """Carga el mapa final y permite probar movimiento, combate y colisiones."""

    TILE_SIZE = 32

    def __init__(self, game):
        self.game = game
        root_path = Path(__file__).resolve().parents[2]
        self.map_path = root_path / "levels" / "final.tmx"
        self.tileset_path = root_path / "assets" / "levels" / "final"
        self.map_width, self.map_height, self.tiles, self.solid_tiles = self._load_map()

        player_assets = root_path / "assets" / "images" / "player"
        enemy_assets = root_path / "assets" / "images" / "enemies" / "cave_skeleton_purple"
        self.player = Player((64, 500), player_assets)
        self.enemies = [
            Enemy((700, 500), enemy_assets, sprite_size=96, hitbox_width=24),
            Enemy((1450, 500), enemy_assets, sprite_size=96, hitbox_width=24),
            Enemy((2250, 500), enemy_assets, sprite_size=96, hitbox_width=24),
            Enemy((2900, 500), enemy_assets, sprite_size=96, hitbox_width=24),
        ]
        self.camera_x = 0

    def _load_map(self):
        root = ET.parse(self.map_path).getroot()
        width = int(root.get("width"))
        height = int(root.get("height"))
        layer = root.find("layer")
        tileset_ref = root.find("tileset")
        if layer is None or tileset_ref is None:
            raise ValueError("El mapa final debe tener una capa y un tileset.")
        tileset_file = self.map_path.parent / tileset_ref.get("source")
        tileset_root = ET.parse(tileset_file).getroot()
        image_definition = tileset_root.find("image")
        if image_definition is None:
            raise ValueError("El tileset final no tiene imagen.")
        image = pygame.image.load(
            self.tileset_path / Path(image_definition.get("source")).name
        ).convert_alpha()
        columns = int(tileset_root.get("columns") or image.get_width() // self.TILE_SIZE)
        tile_count = int(tileset_root.get("tilecount", 0))
        first_gid = int(tileset_ref.get("firstgid", 1))
        values = [int(value) for value in re.findall(r"\d+", layer.find("data").text or "")]

        tiles = []
        solid_tiles = []
        for index, raw_gid in enumerate(values):
            gid = raw_gid & 0x1FFFFFFF
            if gid == 0:
                continue
            tile_index = gid - first_gid
            if not 0 <= tile_index < tile_count:
                raise ValueError(f"GID del mapa final no válido: {raw_gid}")
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
            solid_tiles.append(pygame.Rect(destination.x, destination.y + 16, 32, 16))
        return width, height, tiles, solid_tiles

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.current_screen = MainMenu(self.game)

    def update(self):
        self.player.update(pygame.key.get_pressed(), self.solid_tiles)
        world_width = self.map_width * self.TILE_SIZE
        if self.player.rect.top > self.map_height * self.TILE_SIZE or self.player.health <= 0:
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
            else:
                alive_enemies.append(enemy)
        self.enemies = alive_enemies
        self.player.rect.left = max(0, min(self.player.rect.left, world_width - self.player.rect.width))
        target = self.player.rect.centerx - self.game.screen.get_width() // 2
        self.camera_x = max(0, min(target, world_width - self.game.screen.get_width()))

    def draw(self, screen):
        screen.fill((0, 0, 0))
        for image, source, destination in self.tiles:
            screen.blit(image, (destination.x - self.camera_x, destination.y), source)
        for enemy in self.enemies:
            enemy.draw(screen, self.camera_x)
        self.player.draw(screen, self.camera_x)
        self.player.draw_health_bar(screen)
