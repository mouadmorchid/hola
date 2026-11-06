"""Coordinador principal del ciclo de vida y del bucle del juego."""

import pygame

from src.screens.main_menu import MainMenu
from src.screens.forest_level import ForestLevel
from src.screens.cave_level import CaveLevel
from src.screens.final_level import FinalLevel


class Game:
    """Inicializa Pygame y delega la entrada, actualización y dibujo a una pantalla."""

    def __init__(self):
        # La ventana y el reloj se crean una sola vez y son compartidos por las pantallas.
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("Crazy Time")
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_screen = MainMenu(self)

    def show_forest_level(self):
        """Cambia la pantalla activa al nivel del bosque."""
        self.current_screen = ForestLevel(self)

    def show_final_level(self):
        """Cambia temporalmente al nivel final para realizar pruebas."""
        self.current_screen = FinalLevel(self)

    def show_cave_level(self):
        """Cambia la pantalla activa al nivel de la cueva."""
        self.current_screen = CaveLevel(self)

    def run(self):
        """Ejecuta el bucle principal hasta que el usuario cierre el juego."""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    # Cada pantalla decide cómo interpretar sus propios eventos.
                    self.current_screen.handle_event(event)

            # El orden update -> draw separa la lógica de la presentación.
            self.current_screen.update()
            self.current_screen.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
