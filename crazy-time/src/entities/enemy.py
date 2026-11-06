"""Enemigo reutilizable para los distintos mapas."""

import pygame


class Enemy:
    """Enemigo común cuyo único recurso variable es su conjunto de sprites."""

    CHASE_DISTANCE = 260
    VISION_VERTICAL_DISTANCE = 64
    ATTACK_DISTANCE = 44
    SPEED = 1.5
    ATTACK_COOLDOWN = 45
    TURN_COOLDOWN = 12
    FRAME_WIDTH = 96

    def __init__(
        self,
        position,
        sprites_path,
        sprite_size=64,
        frame_width=None,
        hitbox_width=28,
    ):
        self.rect = pygame.Rect(
            position[0] + (32 - hitbox_width) // 2,
            position[1],
            hitbox_width,
            44,
        )
        self.sprite_size = sprite_size
        self.frame_width = frame_width or self.FRAME_WIDTH
        self.start_x = self.rect.x
        self.velocity = pygame.Vector2(self.SPEED, 0)
        self.gravity = 0.5
        self.health = 5
        self.dying = False
        self.death_finished = False
        self.attack_cooldown = 0
        self.continue_attacking_during_cooldown = True
        self.turn_cooldown = 0
        self.attacking = False
        self.facing_right = True
        self.animation_name = "idle"
        self.animation_frame = 0
        self.animation_timer = 0
        self.animations = {
            "idle": self._load_animation(sprites_path / "idle.png")[:1],
            "walk": self._load_animation(sprites_path / "walk.png"),
            "attack": self._load_animation(sprites_path / "attack.png"),
            "death": self._load_animation(sprites_path / "death.png"),
        }
        self.stable_sprite = self.animations["idle"][0]
        self.animations["walk"] = self._stabilize_animation(
            self.animations["walk"]
        )
        self.animations["attack"] = self._stabilize_animation(
            self.animations["attack"]
        )
        self.animations["death"] = self._stabilize_animation(
            self.animations["death"]
        )

    def update(self, solid_tiles, player):
        """Persigue al jugador cercano, ataca y aplica colisiones con el mapa."""
        if self.dying:
            self._update_death_animation()
            return

        self.turn_cooldown = max(0, self.turn_cooldown - 1)
        distance = player.rect.centerx - self.rect.centerx
        can_see_player = (
            abs(distance) <= self.CHASE_DISTANCE
            and self._can_see_player(solid_tiles, player)
        )
        if can_see_player:
            if abs(distance) <= self.ATTACK_DISTANCE:
                self.velocity.x = 0
                self.attacking = (
                    self.continue_attacking_during_cooldown
                    or self.attack_cooldown == 0
                )
                if self.attack_cooldown == 0:
                    player.take_damage(1)
                    self.attack_cooldown = self.ATTACK_COOLDOWN
            else:
                self.attacking = False
                if self.velocity.x == 0:
                    self.velocity.x = self.SPEED if self.facing_right else -self.SPEED
                if self.turn_cooldown == 0:
                    self.velocity.x = self.SPEED if distance > 0 else -self.SPEED
                    self.facing_right = self.velocity.x > 0
        else:
            self.attacking = False
            if self.velocity.x == 0:
                self.velocity.x = self.SPEED if self.facing_right else -self.SPEED
        self.attacking = (
            self.attacking
            and can_see_player
            and abs(distance) <= self.ATTACK_DISTANCE
        )

        if (
            self.velocity.x
            and self._has_grounded_feet(solid_tiles)
            and not self._has_ground_ahead(solid_tiles)
        ):
            self._turn_around()

        self.attack_cooldown = max(0, self.attack_cooldown - 1)

        self.rect.x += round(self.velocity.x)
        for tile in solid_tiles:
            if self.rect.colliderect(tile):
                if self.velocity.x > 0:
                    self.rect.right = tile.left
                    self._turn_around()
                elif self.velocity.x < 0:
                    self.rect.left = tile.right
                    self._turn_around()
                break

        self.velocity.y = min(self.velocity.y + self.gravity, 12)
        self.rect.y += round(self.velocity.y)
        for tile in solid_tiles:
            if self.rect.colliderect(tile):
                if self.velocity.y > 0:
                    self.rect.bottom = tile.top
                elif self.velocity.y < 0:
                    self.rect.top = tile.bottom
                self.velocity.y = 0

        animation_name = "attack" if self.attacking else "walk"
        self._set_animation(animation_name)
        self.animation_timer += 1
        if self.animation_timer >= 8:
            self.animation_timer = 0
            self.animation_frame = (
                self.animation_frame + 1
            ) % len(self.animations[self.animation_name])

    def _has_ground_ahead(self, solid_tiles):
        """Comprueba que haya un bloque bajo el borde delantero del enemigo."""
        probe_x = self.rect.right + 2 if self.velocity.x > 0 else self.rect.left - 2
        probe = pygame.Rect(probe_x, self.rect.bottom, 4, 4)
        return any(probe.colliderect(tile) for tile in solid_tiles)

    def _turn_around(self):
        """Cambia de dirección y evita giros repetidos contra el mismo obstáculo."""
        self.velocity.x = -self.velocity.x or -self.SPEED
        self.facing_right = self.velocity.x > 0
        self.turn_cooldown = self.TURN_COOLDOWN

    def _can_see_player(self, solid_tiles, player):
        """Comprueba la altura y la línea de visión hasta el jugador."""
        enemy_center = pygame.Vector2(self.rect.center)
        player_center = pygame.Vector2(player.rect.center)
        if abs(player_center.y - enemy_center.y) > self.VISION_VERTICAL_DISTANCE:
            return False

        direction = player_center - enemy_center
        distance = direction.length()
        if distance == 0:
            return True

        step = direction.normalize() * 8
        point = enemy_center
        for _ in range(int(distance // 8)):
            point += step
            probe = pygame.Rect(round(point.x) - 1, round(point.y) - 1, 2, 2)
            if any(probe.colliderect(tile) for tile in solid_tiles):
                return False
        return True

    def _has_grounded_feet(self, solid_tiles):
        """Comprueba si el enemigo está apoyado sobre un bloque."""
        probe = pygame.Rect(self.rect.centerx, self.rect.bottom, 2, 4)
        return any(probe.colliderect(tile) for tile in solid_tiles)

    def take_damage(self, damage):
        """Reduce la vida del enemigo sin permitir valores negativos."""
        if self.dying:
            return
        self.health = max(0, self.health - damage)
        if self.health == 0:
            self.dying = True
            self.attacking = False
            self.velocity.x = 0
            self._set_animation("death")
            self.animation_frame = 0
            self.animation_timer = 0

    def _update_death_animation(self):
        """Reproduce la muerte una vez y marca el enemigo para retirarlo."""
        self.animation_timer += 1
        if self.animation_timer >= 8:
            self.animation_timer = 0
            if self.animation_frame >= len(self.animations["death"]) - 1:
                self.death_finished = True
            else:
                self.animation_frame += 1

    def _load_animation(self, path):
        """Divide hojas de 96x64 o 128x128 en frames."""
        sheet = pygame.image.load(path).convert_alpha()
        frame_height = sheet.get_height()
        frame_width = frame_height if frame_height == 128 else self.frame_width
        frames = []
        for index in range(sheet.get_width() // frame_width):
            frame = sheet.subsurface(
                pygame.Rect(index * frame_width, 0, frame_width, frame_height)
            ).copy()
            frames.append(frame)
        if not frames:
            raise ValueError(f"No valid animation frames found in {path}")
        return frames

    def _stabilize_animation(self, frames):
        """Alinea el cuerpo sin desplazar los VFX integrados en cada frame."""
        if frames[0].get_height() != 64 or frames[0].get_width() != 96:
            return frames
        stabilized = []
        for frame in frames:
            body_region = frame.subsurface(pygame.Rect(20, 8, 56, 56))
            bounds = body_region.get_bounding_rect()
            aligned = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
            aligned.blit(frame, (48 - (bounds.centerx + 20), 64 - (bounds.bottom + 8)))
            stabilized.append(aligned)
        return stabilized

    def draw(self, screen, camera_x):
        """Dibuja el enemigo compensando el desplazamiento de la cámara."""
        if self.dying:
            animation_name = "death"
        elif self.attacking:
            animation_name = "attack"
        elif self.velocity.x:
            animation_name = "walk"
        else:
            animation_name = "idle"
        self._set_animation(animation_name)
        if self.animation_name == "idle":
            image = self.stable_sprite
        else:
            animation = self.animations[self.animation_name]
            image = animation[self.animation_frame % len(animation)]
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
        image = pygame.transform.scale(
            image, (self.sprite_size, self.sprite_size)
        )
        position = (
            self.rect.centerx - image.get_width() // 2 - camera_x,
            self.rect.bottom - image.get_height(),
        )
        screen.blit(image, position)

    def _set_animation(self, animation_name):
        """Cambia de animación reiniciando el frame para evitar parpadeos."""
        if animation_name != self.animation_name:
            self.animation_name = animation_name
            self.animation_frame = 0
            self.animation_timer = 0
