"""Jefe del bosque."""

from pathlib import Path

import pygame


class BossEnemy:
    """Jefe fijo al final del mapa con embestida y recuperación vulnerable."""

    FRAME_WIDTH = 80
    FRAME_HEIGHT = 64
    SPRITE_SIZE = 112
    HEALTH = 10

    TRIGGER_DISTANCE = 280
    CHASE_SPEED = 2.2
    CHARGE_SPEED = 7
    CHARGE_DISTANCE = 320
    HIT_TIME = 30
    RECOVERY_TIME = 120
    CONTACT_DAMAGE = 3
    ATTACK_PUSH_SPEED = 10

    def __init__(self, position, sprites_path: Path):
        self.rect = pygame.Rect(position[0] + 14, position[1], 40, 48)
        self.velocity_y = 0
        self.gravity = 0.5
        self.health = self.HEALTH
        self.dying = False
        self.death_finished = False
        self.facing_right = False
        self.charge_direction = -1
        self.state = "idle"
        self.state_timer = 0
        self.animation_name = "idle"
        self.animation_frame = 0
        self.animation_timer = 0
        self.attack_push_applied = False
        self.charge_hit_applied = False
        self.charge_distance_traveled = 0
        self.animations = {
            "idle": self._load_animation(sprites_path / "idle.png", 7),
            "walk": self._load_animation(sprites_path / "walk.png", 8),
            "attack": self._load_animation(sprites_path / "attack.png", 10),
            "hit": self._load_animation(sprites_path / "hit.png", 5),
            "death": self._load_animation(sprites_path / "death.png", 15),
        }

    def update(self, solid_tiles, player):
        """Actualiza el jefe sin permitirle abandonar la zona final."""
        if self.dying:
            self._advance("death", 8, stop_at_end=True)
            if self.animation_frame == len(self.animations["death"]) - 1:
                self.death_finished = True
            return

        if self.state == "hit":
            self.velocity_y = 0
            self._advance("hit", 6, stop_at_end=True)
            self.state_timer -= 1
            if self.state_timer <= 0:
                self._face_player(player)
                self._start_attack()
            return

        if self.state == "recovery":
            self.velocity_y = 0
            self._advance("idle", 8)
            self.state_timer -= 1
            if self.state_timer <= 0:
                self._face_player(player)
                self._start_attack()
            return

        if self.state == "attack":
            self.velocity_y = 0
            self._advance("attack", 6, stop_at_end=True)
            if not self.attack_push_applied and self.animation_frame >= 1:
                self._push_player(solid_tiles, player)
                self.attack_push_applied = True
            if self.animation_frame == len(self.animations["attack"]) - 1:
                self._start_charge()
                return
            return

        if self.state == "charge":
            self._move_charge(solid_tiles, player)
            return

        distance = player.rect.centerx - self.rect.centerx
        if abs(distance) <= self.TRIGGER_DISTANCE:
            self.charge_direction = 1 if distance > 0 else -1
            self.facing_right = self.charge_direction > 0
            self._set_state("attack")
            return

        # El boss permanece en la zona final hasta que el jugador entra en
        # su radio de activación.
        self.velocity_y = 0
        self._advance("idle", 8)
        self._apply_vertical(solid_tiles)

    def _face_player(self, player):
        """Actualiza la dirección del boss antes de iniciar otro ataque."""
        distance = player.rect.centerx - self.rect.centerx
        if distance:
            self.charge_direction = 1 if distance > 0 else -1
            self.facing_right = self.charge_direction > 0

    def take_damage(self, damage):
        """Recibe daño durante cualquier estado salvo la embestida."""
        if self.dying or self.state != "recovery":
            return
        self.health = max(0, self.health - damage)
        if self.health == 0:
            self.dying = True
            self.state = "dead"
            self.animation_name = "death"
            self.animation_frame = 0
            self.animation_timer = 0
            return
        self.state = "hit"
        self.state_timer = self.HIT_TIME
        self._set_state("hit")

    def draw(self, screen, camera_x):
        """Dibuja la animación actual del jefe."""
        animation = self.animations[self.animation_name]
        image = animation[self.animation_frame]
        if self.facing_right:
            image = pygame.transform.flip(image, True, False)
        image = pygame.transform.scale(image, (self.SPRITE_SIZE, self.SPRITE_SIZE))
        position = (
            self.rect.centerx - image.get_width() // 2 - camera_x,
            self.rect.bottom - image.get_height(),
        )
        screen.blit(image, position)

    def _move_charge(self, solid_tiles, player):
        """Embestida horizontal que termina ante un obstáculo o un borde."""
        self._advance("walk", 4)
        movement = self.CHARGE_SPEED * self.charge_direction
        if not self._can_move_forward(solid_tiles, self.charge_direction):
            self._start_recovery()
            return
        if self._move_horizontal(solid_tiles, movement):
            self._start_recovery()
            return
        self.charge_distance_traveled += abs(movement)
        self._apply_vertical(solid_tiles)
        if not self.charge_hit_applied and self.rect.colliderect(player.rect):
            player.take_damage(self.CONTACT_DAMAGE)
            player.apply_knockback(self.charge_direction * self.ATTACK_PUSH_SPEED)
            self.charge_hit_applied = True
        if self.charge_distance_traveled >= self.CHARGE_DISTANCE:
            self._start_recovery()

    def _apply_vertical(self, solid_tiles):
        self.velocity_y = min(self.velocity_y + self.gravity, 12)
        self.rect.y += round(self.velocity_y)
        for tile in solid_tiles:
            if self.rect.colliderect(tile):
                if self.velocity_y > 0:
                    self.rect.bottom = tile.top
                elif self.velocity_y < 0:
                    self.rect.top = tile.bottom
                self.velocity_y = 0
                return

    def _move_horizontal(self, solid_tiles, movement):
        """Mueve al jefe y resuelve una colisión lateral con un bloque."""
        self.rect.x += round(movement)
        for tile in solid_tiles:
            if not self.rect.colliderect(tile):
                continue
            if movement > 0:
                self.rect.right = tile.left
            elif movement < 0:
                self.rect.left = tile.right
            return True
        return False

    def _can_move_forward(self, solid_tiles, direction):
        """Indica si hay espacio y suelo delante para continuar la embestida."""
        if not self._has_grounded_feet(solid_tiles):
            return False
        probe_x = self.rect.right + 2 if direction > 0 else self.rect.left - 6
        probe = pygame.Rect(probe_x, self.rect.bottom, 4, 4)
        return any(probe.colliderect(tile) for tile in solid_tiles)

    def _has_grounded_feet(self, solid_tiles):
        """Comprueba que el jefe esté apoyado sobre un bloque."""
        probe = pygame.Rect(self.rect.centerx, self.rect.bottom - 1, 2, 5)
        return any(probe.colliderect(tile) for tile in solid_tiles)

    def _start_attack(self):
        self.state = "attack"
        self.state_timer = 0
        self.animation_name = "attack"
        self.animation_frame = 0
        self.animation_timer = 0
        self.attack_push_applied = False

    def _start_recovery(self):
        self.state = "recovery"
        self.state_timer = self.RECOVERY_TIME
        self.animation_name = "idle"
        self.animation_frame = 0
        self.animation_timer = 0

    def _push_player(self, solid_tiles, player):
        """Abre espacio para la embestida empujando al jugador una sola vez."""
        attack_area = self.rect.inflate(32, 24)
        if not attack_area.colliderect(player.rect):
            return

        player.apply_knockback(self.charge_direction * self.ATTACK_PUSH_SPEED)

    def _start_charge(self):
        self.state = "charge"
        self.state_timer = 0
        self.charge_distance_traveled = 0
        self.charge_hit_applied = False
        self.animation_name = "walk"
        self.animation_frame = 0
        self.animation_timer = 0

    def _set_state_if_needed(self, state):
        if self.state != state or self.animation_name != state:
            self._set_state(state)

    def _set_state(self, state):
        self.state = state
        self.animation_name = state
        self.animation_frame = 0
        self.animation_timer = 0

    def _advance(self, animation_name, frame_delay, stop_at_end=False):
        if self.animation_name != animation_name:
            self.animation_name = animation_name
            self.animation_frame = 0
            self.animation_timer = 0
        self.animation_timer += 1
        if self.animation_timer < frame_delay:
            return
        self.animation_timer = 0
        last_frame = len(self.animations[animation_name]) - 1
        if stop_at_end:
            self.animation_frame = min(self.animation_frame + 1, last_frame)
        else:
            self.animation_frame = (self.animation_frame + 1) % (last_frame + 1)

    def _load_animation(self, path, frame_count):
        sheet = pygame.image.load(path).convert_alpha()
        expected_width = frame_count * self.FRAME_WIDTH
        if sheet.get_size() != (expected_width, self.FRAME_HEIGHT):
            raise ValueError(
                f"Animación de jefe inválida en {path}: "
                f"se esperaba {expected_width}x{self.FRAME_HEIGHT}, "
                f"se recibió {sheet.get_width()}x{sheet.get_height()}"
            )
        return [
            sheet.subsurface(
                pygame.Rect(
                    index * self.FRAME_WIDTH,
                    0,
                    self.FRAME_WIDTH,
                    self.FRAME_HEIGHT,
                )
            ).copy()
            for index in range(frame_count)
        ]
