
"""Nivel de la cueva, con mapa y cámara horizontal."""

from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pygame

from src.entities.player import Player
from src.entities.enemy import Enemy
from src.entities.collectible import Amethyst, find_platform_positions
from src.screens.main_menu import MainMenu


class CaveLevel:
    """Nivel jugable de la cueva que cierra la progresión principal."""

    TILE_SIZE = 32

    def __init__(self, game):
        self.game = game

        root_path = Path(__file__).resolve().parents[2]

        self.map_path = root_path / "levels" / "cave.tmx"
        self.tileset_path = root_path / "assets" / "levels" / "cave"

        # Cargamos el mapa y sus colisiones.
        self.map_width, self.map_height, self.tiles, self.solid_tiles = (
            self._load_map()
        )

        background_path = root_path / "assets" / "levels" / "cave" / "background.png"
        background = pygame.image.load(background_path).convert()
        self.background = pygame.transform.smoothscale(
            background, self.game.screen.get_size()
        )

        # Creamos al jugador.
        player_assets = root_path / "assets" / "images" / "player"
        self.player = Player((64, 500), player_assets)
        enemy_assets = root_path / "assets" / "images" / "enemies" / "cave_skeleton_purple"
        self.enemies = [
            Enemy((700, 500), enemy_assets, sprite_size=96),
            Enemy((1450, 500), enemy_assets, sprite_size=96),
            Enemy((2250, 500), enemy_assets, sprite_size=96),
            Enemy((3100, 500), enemy_assets, sprite_size=96),
            Enemy((3900, 500), enemy_assets, sprite_size=96),
            Enemy((1120, 276), enemy_assets, sprite_size=96),
            Enemy((2700, 244), enemy_assets, sprite_size=96),
            Enemy((3500, 180), enemy_assets, sprite_size=96),
        ]
        collectible_image = pygame.image.load(
            root_path / "assets" / "images" / "collectibles" / "amethyst.png"
        ).convert_alpha()
        crystal_positions = find_platform_positions(
            self.solid_tiles,
            self.map_width * self.TILE_SIZE,
            self.TILE_SIZE,
            12,
        )
        self.collectibles = [
            Amethyst(position, collectible_image)
            for position in crystal_positions
        ]

        self.camera_x = 0

    def _load_map(self):
        """Carga los tiles del mapa de Tiled."""
        root = ET.parse(self.map_path).getroot()

        width = int(root.get("width"))
        height = int(root.get("height"))

        layer = root.find("layer")

        if layer is None:
            raise ValueError("El mapa de la cueva no tiene ninguna capa.")

        tileset_ref = root.find("tileset")

        if tileset_ref is None:
            raise ValueError("El mapa de la cueva no tiene ningún tileset.")

        tileset_file = self.map_path.parent / tileset_ref.get("source")
        tileset_root = ET.parse(tileset_file).getroot()

        image_definition = tileset_root.find("image")

        if image_definition is None:
            raise ValueError("El tileset de la cueva no tiene una imagen.")

        image_path = self.tileset_path / Path(image_definition.get("source")).name
        image = pygame.image.load(image_path).convert_alpha()

        columns = int(
            tileset_root.get("columns")
            or image.get_width() // self.TILE_SIZE
        )

        first_gid = int(tileset_ref.get("firstgid", 1))

        values = [
            int(value)
            for value in re.findall(
                r"\d+",
                layer.find("data").text or ""
            )
        ]

        tiles = []
        solid_tiles = []

        for index, raw_gid in enumerate(values):
            # Quitamos las marcas de giro y volteo de Tiled.
            gid = raw_gid & 0x1FFFFFFF

            if gid == 0:
                continue

            tile_index = gid - first_gid
            tile_count = int(tileset_root.get("tilecount", 0))
            if tile_index < 0 or tile_index >= tile_count:
                raise ValueError(f"GID de cueva no válido: {raw_gid}")

            source = pygame.Rect(
                (tile_index % columns) * self.TILE_SIZE,
                (tile_index // columns) * self.TILE_SIZE,
                self.TILE_SIZE,
                self.TILE_SIZE,
            )

            destination = pygame.Rect(
                (index % width) * self.TILE_SIZE,
                (index // width) * self.TILE_SIZE,
                self.TILE_SIZE,
                self.TILE_SIZE,
            )

            tiles.append((image, source, destination))

            solid_rect = pygame.Rect(destination.x, destination.y + 16, 32, 16)

            solid_tiles.append(solid_rect)

        return width, height, tiles, solid_tiles

    def handle_event(self, event):
        """Gestiona los eventos del nivel."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.current_screen = MainMenu(self.game)

    def update(self):
        """Actualiza al jugador y la cámara."""
        keys = pygame.key.get_pressed()

        self.player.update(keys, self.solid_tiles)

        world_height = self.map_height * self.TILE_SIZE
        world_width = self.map_width * self.TILE_SIZE

        # Volvemos al menú si el jugador cae fuera del mapa.
        if self.player.rect.top > world_height:
            self.game.current_screen = MainMenu(self.game)
            return

        # Volvemos al menú si el jugador pierde toda su vida.
        if self.player.health <= 0:
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
        # Evitamos que el jugador salga por los laterales.
        self.player.rect.left = max(
            0,
            min(
                self.player.rect.left,
                world_width - self.player.rect.width
            )
        )

        # Cámara horizontal.
        target = (
            self.player.rect.centerx
            - self.game.screen.get_width() // 2
        )

        self.camera_x = max(
            0,
            min(
                target,
                world_width - self.game.screen.get_width()
            )
        )

    def draw(self, screen):
        """Dibuja el fondo, el mapa y al jugador."""

        # Dibujamos el fondo estático.
        screen.blit(self.background, (0, 0))

        # Dibujamos los tiles del mapa.
        for image, source, destination in self.tiles:
            screen.blit(
                image,
                (destination.x - self.camera_x, destination.y),
                source
            )

        for enemy in self.enemies:
            enemy.draw(screen, self.camera_x)
        for collectible in self.collectibles:
            collectible.draw(screen, self.camera_x)

        # Dibujamos al jugador y su barra de vida.
        self.player.draw(screen, self.camera_x)
        self.player.draw_health_bar(screen)
        self.draw_collectible_counter(screen)

    def draw_collectible_counter(self, screen):
        """Dibuja el progreso de amatistas en la esquina superior derecha."""
        font = pygame.font.Font(None, 32)
        collected = sum(collectible.collected for collectible in self.collectibles)
        text = font.render(
            f"Amatistas: {collected}/{len(self.collectibles)}",
            True,
            (245, 245, 245),
        )
        screen.blit(text, (screen.get_width() - text.get_width() - 24, 20))
