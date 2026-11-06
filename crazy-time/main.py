"""Punto de entrada del juego Crazy Time."""

from src.game import Game

if __name__ == "__main__":
    # Mantener esta condición permite importar el módulo sin arrancar el juego.
    game = Game()
    game.run()
