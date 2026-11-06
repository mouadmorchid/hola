# Crazy Time: guía del proyecto

Esta guía explica cómo está organizado **Crazy Time**, cómo se ejecuta y dónde
está cada parte importante del juego. Está escrita para personas que conocen lo
básico de Python, pero que todavía están aprendiendo a organizar un juego 2D
con Pygame.

## 1. Qué es Crazy Time

Crazy Time es un prototipo de juego 2D hecho con Python y Pygame. Actualmente
incluye:

- Un menú principal.
- Un nivel de bosque cargado desde un mapa creado con Tiled.
- Un nivel de cueva cargado desde otro mapa de Tiled.
- Un jugador que camina, salta y ataca.
- Una cámara horizontal que sigue al jugador.
- Enemigos que patrullan, detectan al jugador, lo persiguen y atacan.
- Colisiones entre el jugador, los enemigos y el mapa.
- Si el jugador cae por debajo del mapa, muere y vuelve al menú principal.
- Vida: el jugador empieza con 10 puntos, los enemigos comunes con 5 y el
  jefe del bosque con 50.
- Animaciones para idle, caminar, salto, ataque y muerte del enemigo.
- Un fondo de bosque que se dibuja detrás del mapa.

Todavía no hay una pantalla de opciones funcional, un sistema de victoria,
pantalla de derrota ni una interfaz que muestre la vida.

## 2. Cómo ejecutar el proyecto

### Requisitos

- Python 3.
- Pygame.

Las dependencias están en [requirements.txt](./requirements.txt).

### Instalación

Desde la carpeta raíz del proyecto:

```bash
python3 -m pip install -r requirements.txt
```

Es recomendable utilizar un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

En Windows, la activación suele hacerse con:

```text
.venv\Scripts\activate
```

### Inicio

```bash
python3 main.py
```

El programa empieza en el menú. Pulsa **Play** para entrar al bosque y
**Escape** para salir de la pantalla actual o cerrar el juego desde el menú.

## 3. Estructura de carpetas

```text
crazy-time/
├── main.py                         # Punto de entrada
├── requirements.txt                # Dependencias
├── DOCUMENTACION_PROYECTO.md      # Esta guía
├── assets/
│   ├── images/
│   │   ├── menu/                  # Fondo del menú
│   │   ├── player/                # Sprites del jugador
│   │   ├── enemies/               # Sprites organizados por nivel y enemigo
│   │   │   ├── cave_skeleton_white/   # Esqueleto blanco con VFX
│   │   │   └── forest_skeleton_yellow/ # Esqueleto amarillo con VFX
│   │   └── collectibles/          # Monedas y amatistas
│   └── levels/
│       ├── forest/
│       │   ├── background.png     # Fondo del bosque
│       │   ├── tileset.png        # Imagen del tileset del bosque
│       │   └── tileset.tsx        # Definición del tileset del bosque
│       └── cave/
│           ├── background.png     # Fondo de la cueva
│           ├── tileset.png        # Imagen del tileset de la cueva
│           └── tileset.tsx        # Definición del tileset de la cueva
├── levels/
│   ├── forest.tmx                 # Mapa del nivel del bosque
│   └── cave.tmx                   # Mapa del nivel de la cueva
└── src/
    ├── game.py                    # Ventana y bucle principal
    ├── entities/
    │   ├── collectible.py         # Lógica de objetos recogibles
    │   ├── enemy.py               # Lógica reutilizable de enemigos
    │   └── player.py              # Lógica del jugador
    └── screens/
        ├── main_menu.py           # Menú principal
        ├── forest_level.py        # Nivel, mapa, cámara y enemigos
        └── cave_level.py          # Nivel de la cueva
```

Las carpetas `__pycache__` y los archivos `.pyc` son generados por Python. No
contienen lógica escrita a mano y no deben editarse.

La moneda dorada está en `assets/images/collectibles/gold_coin.png` y se usa
en el bosque. La amatista está en `assets/images/collectibles/amethyst.png` y
se usa en la cueva.

## 4. Cómo funciona el programa

El punto de entrada es [main.py](./main.py):

```python
from src.game import Game

game = Game()
game.run()
```

### La clase `Game`

[src/game.py](./src/game.py) crea la ventana de `1280x720`, inicializa Pygame y
guarda cuál es la pantalla activa:

```python
self.current_screen = MainMenu(self)
```

Después ejecuta un bucle a 60 actualizaciones por segundo. En cada vuelta:

1. Lee los eventos de teclado, ratón y cierre de ventana.
2. Llama a `current_screen.handle_event(event)`.
3. Actualiza la lógica con `current_screen.update()`.
4. Dibuja la pantalla con `current_screen.draw(screen)`.
5. Muestra el resultado y espera hasta el siguiente frame.

Este orden es importante:

```text
eventos -> update -> draw -> mostrar pantalla
```

Una pantalla es una clase que normalmente implementa `handle_event`, `update` y
`draw`. Por eso el juego puede cambiar del menú al nivel sin duplicar el bucle
principal.

## 5. El menú principal

[src/screens/main_menu.py](./src/screens/main_menu.py) se encarga de:

- Cargar `assets/images/menu/main_menu_background.png`.
- Dibujar el fondo.
- Detectar cuándo el ratón pasa por encima de un botón.
- Entrar al bosque al pulsar **Play**.
- Cerrar el juego al pulsar **Exit**.

El botón **Options** todavía imprime un mensaje en la terminal porque esa
pantalla aún no está implementada.

## 6. El nivel del bosque

[src/screens/forest_level.py](./src/screens/forest_level.py) coordina todo lo
que ocurre dentro del nivel:

- Carga `levels/forest.tmx`.
- Carga `assets/levels/forest/background.png`.
- Crea al jugador.
- Crea los enemigos.
- Actualiza las colisiones.
- Actualiza la cámara.
- Dibuja fondo, mapa, enemigos y jugador.

El constructor crea los objetos principales. Para utilizar otro tipo de enemigo
solo se cambia la carpeta que se pasa a `Enemy`:

```python
enemy_assets_path = base_path / "assets" / "images" / "enemies" / "forest_skeleton_yellow"
Enemy((400, 500), enemy_assets_path)
```

Cuando el jugador cruza el borde derecho del bosque, el juego cambia
automáticamente a `CaveLevel` y lo coloca en la entrada izquierda de la cueva.

## 7. El nivel de la cueva

[src/screens/cave_level.py](./src/screens/cave_level.py) carga
[levels/cave.tmx](./levels/cave.tmx), un mapa de `135x23` celdas, junto con
[assets/levels/cave/tileset.tsx](./assets/levels/cave/tileset.tsx) y su imagen
[assets/levels/cave/tileset.png](./assets/levels/cave/tileset.png). El fondo está en
[assets/levels/cave/background.png](./assets/levels/cave/background.png).
La cueva reutiliza el jugador, la cámara y las reglas de caída y derrota del
resto de niveles.

Los niveles contienen amatistas sobre plataformas elevadas. El contador de
la esquina superior derecha muestra cuántas se han recogido. El jugador debe
recogerlas todas antes de poder cruzar la salida derecha y avanzar al siguiente
nivel.

## 8. Cómo se carga el mapa de Tiled

El archivo [levels/forest.tmx](./levels/forest.tmx) es un XML generado por
Tiled. Define un mapa ortogonal de `150x23` celdas, con tiles de `32x32`
píxeles. El mapa referencia
[assets/levels/forest/tileset.tsx](./assets/levels/forest/tileset.tsx), que referencia
[assets/levels/forest/tileset.png](./assets/levels/forest/tileset.png).

`ForestLevel._load_map()` hace lo siguiente:

1. Abre el XML del mapa.
2. Abre el archivo `.tsx` del tileset.
3. Carga la imagen del tileset con Pygame.
4. Lee los números de la capa CSV.
5. Ignora el GID `0`, que significa una celda vacía.
6. Convierte cada GID en un recorte de `32x32` de la imagen.
7. Calcula la posición del tile en el mundo.
8. Guarda cada tile para dibujarlo.
9. Guarda también su rectángulo en `solid_tiles`.

`solid_tiles` es la lista de bloques que se consideran sólidos. El jugador y los
enemigos la utilizan para no atravesar el terreno.

Si el jugador cae por debajo de la altura total del mapa (`23 * 32` píxeles), el
nivel lo considera muerto y cambia inmediatamente a `MainMenu`.

### Colisiones del mapa

Actualmente todos los tiles que aparecen en la capa se añaden a
`solid_tiles`. Si se añaden elementos decorativos que no deberían bloquear al
jugador, habrá que separar las capas visuales de las capas de colisión o añadir
una regla que distinga unos tiles de otros.

## 9. El jugador

[src/entities/player.py](./src/entities/player.py) contiene la clase `Player`.
El jugador tiene:

- Un `pygame.Rect` para la hitbox física.
- Una velocidad horizontal.
- Gravedad y velocidad de salto.
- Dirección hacia la izquierda o derecha.
- 10 puntos de vida.
- Animaciones cargadas desde `assets/images/player/`.

### Movimiento

En `Player.update()` se leen las teclas:

- `A` y `D`: movimiento horizontal.
- Flechas izquierda y derecha: movimiento horizontal con prioridad.
- `W`, `Espacio` o flecha arriba: salto.
- `F`: ataque.

El movimiento se resuelve por separado:

1. Se mueve la hitbox en X y se corrigen las paredes.
2. Se mueve la hitbox en Y y se corrigen suelo y techo.

Separar los ejes evita que una colisión lateral modifique accidentalmente la
caída del personaje.

### Animaciones del jugador

Cada PNG es una hoja horizontal. El código divide la imagen en cuadrados usando
la altura de la hoja como tamaño de frame:

```text
frame_size = altura de la imagen
numero_de_frames = ancho / altura
```

Se utilizan estos archivos:

- `player_idle.png`: personaje quieto.
- `player_walk.png`: caminar.
- `player_jump.png`: salto.
- `player_attack.png`: ataque al pulsar `F`.

Durante el ataque, `get_attack_rect()` devuelve una zona delante del jugador.
Si esa zona toca a un enemigo, se le quita 1 punto de vida.

## 10. Enemigos reutilizables

[src/entities/enemy.py](./src/entities/enemy.py) contiene una clase genérica
`Enemy`. Su comportamiento no depende de un mapa concreto. Cada nivel solo
debe proporcionar una posición y una carpeta de sprites.

La carpeta debe tener esta estructura:

```text
forest_skeleton_yellow/
├── idle.png
├── walk.png
├── attack.png
└── death.png
```

El enemigo amarillo del bosque está en
[assets/images/enemies/forest_skeleton_yellow/](./assets/images/enemies/forest_skeleton_yellow/).
La cueva utiliza el mismo formato en
[assets/images/enemies/cave_skeleton_white/](./assets/images/enemies/cave_skeleton_white/).
Ambas carpetas contienen spritesheets preparados a partir de `Skeleton_With_VFX`.
Los VFX están integrados en los frames de ataque y muerte y se muestran junto al
esqueleto; caminar e idle usan únicamente la pose del personaje.

### Comportamiento del enemigo

Cada enemigo:

1. Patrulla una zona.
2. Comprueba si tiene suelo delante para no caer por un borde.
3. Comprueba si el jugador está suficientemente cerca.
4. Comprueba si puede verlo.
5. Persigue al jugador si lo ve.
6. Ataca si está a distancia de ataque.
7. Pierde 1 punto de vida cuando recibe un ataque.
8. Reproduce la animación de muerte cuando llega a 0.
9. Desaparece cuando termina la animación de muerte.

### Detección visual

El enemigo no detecta automáticamente a cualquier jugador cercano. Para verlo:

- La distancia horizontal debe ser menor que `CHASE_DISTANCE`.
- La diferencia vertical debe ser menor que `VISION_VERTICAL_DISTANCE`.
- No puede haber un bloque sólido entre ambos.

Por eso un jugador situado en una plataforma muy alta no debería ser detectado
por un enemigo que está abajo.

### Añadir otro tipo de enemigo

No hay que copiar `enemy.py`. Se crea otra carpeta con las mismas animaciones:

```text
assets/images/enemies/another_enemy/
├── idle.png
├── walk.png
├── attack.png
└── death.png
```

Después, en el nivel correspondiente:

```python
sprites_path = base_path / "assets" / "images" / "enemies" / "forest_skeleton_yellow"
enemy = Enemy((800, 400), sprites_path)
```

El movimiento, la vida, la detección y el ataque seguirán siendo los mismos;
solo cambiará el aspecto.

## 11. La cámara

La cámara es horizontal y se guarda en `ForestLevel.camera_x`.

En cada actualización se intenta colocar al jugador en el centro de la ventana:

```python
target = player.rect.centerx - screen_width // 2
```

Después se limita el resultado:

- Nunca puede ser menor que `0`.
- Nunca puede superar el ancho del mundo menos el ancho de la ventana.

Al dibujar, las coordenadas del mundo se convierten en coordenadas de pantalla:

```python
screen_x = world_x - camera_x
```

El jugador y los enemigos se dibujan usando esa misma compensación, por lo que
parecen permanecer en el lugar correcto mientras el mapa se desplaza.

## 12. Orden de dibujo

El nivel dibuja los elementos en este orden:

1. Fondo del bosque.
2. Tiles del mapa.
3. Enemigos.
4. Jugador.

Lo que se dibuja después aparece por encima de lo anterior. Por ejemplo, el
jugador aparece delante de los enemigos si ambos ocupan la misma zona.

## 13. Dónde hacer cambios habituales

| Cambio | Archivo o carpeta |
|---|---|
| Cambiar tamaño de la ventana | `src/game.py` |
| Cambiar botones del menú | `src/screens/main_menu.py` |
| Cambiar el mapa | `levels/forest.tmx` |
| Cambiar la imagen del tileset | `assets/levels/<nivel>/tileset.png` |
| Cambiar controles o física del jugador | `src/entities/player.py` |
| Cambiar sprites del jugador | `assets/images/player/` |
| Cambiar comportamiento común de enemigos | `src/entities/enemy.py` |
| Crear un aspecto nuevo de enemigo | `assets/images/enemies/` |
| Colocar enemigos en el bosque | `src/screens/forest_level.py` |
| Cambiar la cámara | `src/screens/forest_level.py` |
| Cambiar el fondo | `assets/levels/<nivel>/background.png` |

## 14. Comprobaciones después de modificar el proyecto

Antes de dar por terminado un cambio:

1. Comprueba que las rutas de los archivos existen.
2. Ejecuta una comprobación de sintaxis:

   ```bash
   python3 -m compileall -q src main.py
   ```

3. Revisa que los nombres de los PNG coincidan con los que carga el código.
4. Ejecuta el juego:

   ```bash
   python3 main.py
   ```

5. Prueba especialmente las colisiones, las plataformas, los bordes del mapa,
   el ataque y la muerte de los enemigos.

## 15. Ideas para continuar

Algunas mejoras naturales para el proyecto son:

- Añadir una barra de vida.
- Mostrar una pantalla de derrota cuando el jugador llegue a 0.
- Añadir varios mapas y una transición entre niveles.
- Separar tiles decorativos y tiles sólidos.
- Añadir sonidos y música.
- Crear distintos tipos de enemigos usando diferentes carpetas de sprites.
- Añadir un sistema de victoria y contador de enemigos derrotados.
