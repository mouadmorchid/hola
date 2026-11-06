"""Personaje principal reutilizable en todos los niveles."""

import pygame


class Player:
    """Personaje controlable con movimiento horizontal, salto y animaciones."""

    def __init__(self, position, assets_path):
        # El rectángulo es la hitbox física; el sprite se escala por separado al dibujar.
        hitbox_width = 16
        hitbox_height = 28
        self.rect = pygame.Rect(
            position[0] + (32 - hitbox_width) // 2,
            position[1] + (32 - hitbox_height),
            hitbox_width,
            hitbox_height,
        )
        self.velocity = pygame.Vector2(0, 0)
        self.speed = 4
        self.jump_speed = -11
        self.gravity = 0.5
        self.max_health = 10
        self.health = self.max_health
        self.on_ground = False
        self.facing_right = True
        self.animation_name = "idle"
        self.animation_frame = 0
        self.animation_timer = 0
        self.attacking = False
        self.attack_active = False
        self.knockback_active = False
        self.animations = {
            "idle": self._load_animation(assets_path / "player_idle.png"),
            "walk": self._load_animation(assets_path / "player_walk.png"),
            "jump": self._load_animation(assets_path / "player_jump.png"),
            "attack": self._load_animation(assets_path / "player_attack.png"),
        }

    def update(self, keys, solid_tiles):
        """Actualiza controles, física y frame de animación durante un tick."""
        self.attack_active = False
        if self.knockback_active:
            self.velocity.x *= 0.92
        else:
            # El teclado WASD se calcula primero; las flechas tienen prioridad.
            self.velocity.x = (keys[pygame.K_d] - keys[pygame.K_a]) * self.speed
            if keys[pygame.K_a]:
                self.facing_right = False
            elif keys[pygame.K_d]:
                self.facing_right = True

            if keys[pygame.K_LEFT]:
                self.velocity.x = -self.speed
                self.facing_right = False
            elif keys[pygame.K_RIGHT]:
                self.velocity.x = self.speed
                self.facing_right = True

            if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
                self.velocity.y = self.jump_speed
                self.on_ground = False

        self.velocity.y = min(self.velocity.y + self.gravity, 12)
        # Separar los ejes evita que una pared modifique accidentalmente la caída.
        self._move_x(solid_tiles)
        self._move_y(solid_tiles)
        if self.knockback_active and self.on_ground and self.velocity.y >= 0:
            self.knockback_active = False
            self.velocity.x = 0
        if keys[pygame.K_f] and not self.knockback_active and not self.attacking:
            self.attacking = True
            self._set_animation("attack")

        if self.attacking:
            animation_name = "attack"
        elif not self.on_ground:
            animation_name = "jump"
        elif self.velocity.x:
            animation_name = "walk"
        else:
            animation_name = "idle"
        self._set_animation(animation_name)
        if self.animation_name == "idle":
            self.animation_frame = 0
            self.animation_timer = 0
        else:
            self.animation_timer += 1
            if self.animation_timer >= 8:
                self.animation_timer = 0
                self.animation_frame += 1
                if self.animation_name == "attack" and self.animation_frame == 1:
                    self.attack_active = True
                if self.animation_name == "attack" and self.animation_frame >= len(
                    self.animations["attack"]
                ):
                    self.attacking = False
                    self._set_animation("idle")
                else:
                    self.animation_frame %= len(self.animations[self.animation_name])

    def get_attack_rect(self):
        """Devuelve el área de impacto del ataque actual."""
        if not self.attack_active:
            return pygame.Rect(0, 0, 0, 0)
        if self.facing_right:
            return pygame.Rect(self.rect.right, self.rect.y, 28, self.rect.height)
        return pygame.Rect(self.rect.left - 28, self.rect.y, 28, self.rect.height)

    def take_damage(self, damage):
        """Reduce la vida del jugador sin permitir valores negativos."""
        self.health = max(0, self.health - damage)

    def apply_knockback(self, horizontal_velocity):
        """Lanza al jugador y bloquea sus controles hasta que vuelva al suelo."""
        self.velocity.x = horizontal_velocity
        self.velocity.y = self.jump_speed
        self.on_ground = False
        self.knockback_active = True
        self.attacking = False

    def heal(self, amount):
        """Recupera vida sin superar el máximo del jugador."""
        self.health = min(self.max_health, self.health + amount)

    def _load_animation(self, path):
        """Divide una hoja horizontal en imágenes cuadradas de un frame."""
        sheet = pygame.image.load(path).convert_alpha()
        frame_size = sheet.get_height()
        frame_count = sheet.get_width() // frame_size
        return [
            sheet.subsurface(
                pygame.Rect(index * frame_size, 0, frame_size, frame_size)
            ).copy()
            for index in range(frame_count)
        ]

    def _set_animation(self, animation_name):
        """Cambia de animación y reinicia su frame para evitar saltos visuales."""
        if animation_name != self.animation_name:
            self.animation_name = animation_name
            self.animation_frame = 0
            self.animation_timer = 0

    def _move_x(self, solid_tiles):
        """Mueve la hitbox horizontalmente y la separa de los sólidos."""
        self.rect.x += round(self.velocity.x)
        for tile in solid_tiles:
            if self.rect.colliderect(tile):
                if self.velocity.x > 0:
                    self.rect.right = tile.left
                elif self.velocity.x < 0:
                    self.rect.left = tile.right

    def _move_y(self, solid_tiles):
        """Aplica el movimiento vertical y detecta suelo, techo y colisiones."""
        movement = round(self.velocity.y)
        if self.velocity.y > 0:
            movement = max(1, movement)
        self.rect.y += movement
        self.on_ground = False
        for tile in solid_tiles:
            if self.rect.colliderect(tile):
                if self.velocity.y > 0:
                    self.rect.bottom = tile.top
                    self.on_ground = True
                elif self.velocity.y < 0:
                    self.rect.top = tile.bottom
                self.velocity.y = 0

    def draw(self, screen, camera_x):
        """Dibuja el frame actual compensando el desplazamiento de la cámara."""
        image = self.animations[self.animation_name][self.animation_frame]
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
        image = pygame.transform.scale(image, (64, 64))
        sprite_bottom_offset = 4
        position = (
            self.rect.centerx - image.get_width() // 2 - camera_x,
            self.rect.bottom - image.get_height() + sprite_bottom_offset,
        )
        screen.blit(image, position)

    def draw_health_bar(self, screen):
        """Dibuja una barra provisional de vida fija a la pantalla."""
        bar_rect = pygame.Rect(20, 20, 220, 24)
        fill_width = round(bar_rect.width * self.health / self.max_health)
        fill_rect = pygame.Rect(
            bar_rect.left,
            bar_rect.top,
            fill_width,
            bar_rect.height,
        )
        pygame.draw.rect(screen, (45, 45, 45), bar_rect)
        pygame.draw.rect(screen, (190, 35, 45), fill_rect)
        pygame.draw.rect(screen, (245, 245, 245), bar_rect, 2)
