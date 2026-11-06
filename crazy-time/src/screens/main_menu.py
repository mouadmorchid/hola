"""Pantalla inicial y botones de navegación del juego."""

from pathlib import Path

import pygame


class MainMenu:
    """Pantalla inicial con los botones principales del juego."""

    IMAGE_SIZE = (1536, 1024)

    def __init__(self, game):
        self.game = game
        # Estas coordenadas pertenecen al diseño original de 1536x1024.
        # Los métodos de escala las adaptan al tamaño real de la ventana.
        self.buttons = {
            "play": pygame.Rect(540, 435, 460, 105),
            "options": pygame.Rect(540, 560, 460, 105),
            "exit": pygame.Rect(540, 685, 460, 105),
        }
        image_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "images"
            / "menu"
            / "main_menu_background.png"
        )
        self.background = pygame.image.load(image_path).convert()
        self.background = pygame.transform.smoothscale(
            self.background, self.game.screen.get_size()
        )
        # Se actualiza con el movimiento del ratón para dibujar el resaltado.
        self.hovered_button = None

    def handle_event(self, event):
        """Convierte eventos de Pygame en acciones del menú."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered_button = self._button_at(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            button = self._button_at(event.pos)
            if button == "exit":
                self.game.running = False
            elif button == "play":
                self.game.show_final_level()
            elif button == "options":
                print("Las opciones todavía no están creadas.")

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.running = False

    def update(self):
        """Reserva el punto de actualización para futuras animaciones del menú."""
        pass

    def draw(self, screen):
        """Dibuja el fondo y el efecto visual del botón bajo el cursor."""
        screen.blit(self.background, (0, 0))

        if self.hovered_button:
            button = self._scaled_button(self.buttons[self.hovered_button])
            overlay = pygame.Surface(button.size, pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 35))
            screen.blit(overlay, button.topleft)

    def _button_at(self, position):
        """Devuelve el nombre del botón que contiene una posición de pantalla."""
        scale_x = self.game.screen.get_width() / self.IMAGE_SIZE[0]
        scale_y = self.game.screen.get_height() / self.IMAGE_SIZE[1]

        for name, source_rect in self.buttons.items():
            button = pygame.Rect(
                int(source_rect.x * scale_x),
                int(source_rect.y * scale_y),
                int(source_rect.width * scale_x),
                int(source_rect.height * scale_y),
            )
            if button.collidepoint(position):
                return name
        return None

    def _scaled_button(self, source_rect):
        """Transforma un rectángulo del diseño original a la ventana actual."""
        scale_x = self.game.screen.get_width() / self.IMAGE_SIZE[0]
        scale_y = self.game.screen.get_height() / self.IMAGE_SIZE[1]
        return pygame.Rect(
            int(source_rect.x * scale_x),
            int(source_rect.y * scale_y),
            int(source_rect.width * scale_x),
            int(source_rect.height * scale_y),
        )
