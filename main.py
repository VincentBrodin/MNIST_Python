import tensorflow as tf
import numpy as np
import math
import pygame
import sys


if len(sys.argv) != 2:
    sys.exit("Usage: python ./main.py model")
model = tf.keras.models.load_model(sys.argv[1])

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

pygame.init()
clock = pygame.time.Clock()
width = 500
height = 500
size = width, height

screen = pygame.display.set_mode(size)

OPEN_SANS = "assets/fonts/OpenSans-Regular.ttf"
smallFont = pygame.font.Font(OPEN_SANS, 20)
largeFont = pygame.font.Font(OPEN_SANS, 40)

ROWS, COLS = 28, 28

OFFSET = 20
CELL_SIZE = 10

handwriting = [[0] * COLS for _ in range(ROWS)]


def draw(x, y):
    if x + 1 >= ROWS or y + 1 >= COLS:
        return
    handwriting[x][y] = 250 / 255
    if x + 1 < ROWS:
        handwriting[x + 1][y] = 220 / 255
    if y + 1 < COLS:
        handwriting[x][y + 1] = 220 / 255
    if x + 1 < ROWS and y + 1 < COLS:
        handwriting[x + 1][y + 1] = 190 / 255


def lerp(a, b, t):
    return a + (b - a) * t


def draw_line(last_x, last_y, gridX, gridY):
    # Longest axis determines the number of steps
    distance = max(abs(gridX - last_x), abs(gridY - last_y))

    if distance == 0:
        draw(gridX, gridY)
        return

    for step in range(distance + 1):
        t = step / distance  # Normalized step value [0, 1]
        x = round(lerp(last_x, gridX, t))
        y = round(lerp(last_y, gridY, t))
        draw(x, y)


classification = None
last_x = None
last_y = None
has_guessed = False

while True:

    clock.tick(30)
    # Check if game quit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

    screen.fill(BLACK)

    # Check for mouse press
    click, _, _ = pygame.mouse.get_pressed()
    if click == 1:
        screenY, screenX = pygame.mouse.get_pos()
        gridX, gridY = math.floor(
            (screenX - OFFSET) / CELL_SIZE), math.floor((screenY - OFFSET) / CELL_SIZE)

        if last_x is None:
            last_x = gridX
            last_y = gridY

        draw_line(last_x, last_y, gridX, gridY)
        last_x = gridX
        last_y = gridY
        has_guessed = False
    else:
        last_x = None
        last_y = None
        if not has_guessed:
            prediction = model.predict(
                [np.array(handwriting).reshape(1, 28, 28, 1)]
            )[0]

            classification = []
            for number, odds in enumerate(prediction):
                classification.append((number, odds))
            classification.sort(key=lambda tup: tup[1])
            classification.reverse()
            has_guessed = True

    # Draw each grid cell

    cells = []
    for i in range(ROWS):
        row = []
        for j in range(COLS):
            rect = pygame.Rect(
                OFFSET + j * CELL_SIZE,
                OFFSET + i * CELL_SIZE,
                CELL_SIZE, CELL_SIZE
            )

            # If cell has been written on, darken cell
            if handwriting[i][j]:
                channel = 255 - (handwriting[i][j] * 255)
                pygame.draw.rect(screen, (channel, channel, channel), rect)

            # Draw blank cell
            else:
                pygame.draw.rect(screen, WHITE, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)

    # Reset button
    resetButton = pygame.Rect(
        30, OFFSET + ROWS * CELL_SIZE + 30,
        100, 30
    )
    resetText = smallFont.render("Reset", True, BLACK)
    resetTextRect = resetText.get_rect()
    resetTextRect.center = resetButton.center
    pygame.draw.rect(screen, WHITE, resetButton)
    screen.blit(resetText, resetTextRect)

    if classification is not None:
        i = 25
        for number, odds in classification:
            c = (odds * 255, odds * 255, odds * 255)
            classificationText = largeFont.render(
                f"{number}: {round(odds*100)}%", True, c)
            classificationRect = classificationText.get_rect()
            grid_size = OFFSET * 2 + CELL_SIZE * COLS
            classificationRect.center = (
                grid_size + ((width - grid_size) / 2),
                i
            )
            i += 50
            screen.blit(classificationText, classificationRect)

    # Reset drawing
    if click and resetButton.collidepoint((screenY, screenX)):
        handwriting = [[0] * COLS for _ in range(ROWS)]
        classification = None
        has_guessed = True

    pygame.display.flip()
