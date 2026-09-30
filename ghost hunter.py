import pygame
import heapq
import math

pygame.init()

# ============================================================
# SETTINGS
# ============================================================

TILE = 50

COLS = 18
ROWS = 11

GAME_WIDTH = COLS * TILE
GAME_HEIGHT = ROWS * TILE
HUD_HEIGHT = 80

WIDTH = GAME_WIDTH
HEIGHT = GAME_HEIGHT + HUD_HEIGHT

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ghost Hunter - AI Haunted Maze")

clock = pygame.time.Clock()

# ============================================================
# FONTS
# ============================================================

font = pygame.font.SysFont("arial", 22)
small_font = pygame.font.SysFont("arial", 17)
big_font = pygame.font.SysFont("arial", 52, bold=True)

# ============================================================
# COLORS
# ============================================================

BLACK = (8, 8, 15)
DARK_FLOOR = (18, 18, 28)
WALL = (55, 45, 65)
WALL_EDGE = (90, 70, 105)

WHITE = (240, 240, 245)
BLUE = (70, 150, 255)

PURPLE = (170, 70, 220)
PURPLE_LIGHT = (210, 120, 255)

CYAN = (50, 230, 255)
GREEN = (60, 220, 110)
RED = (235, 60, 70)

YELLOW = (255, 220, 70)

# ============================================================
# MAZE
# 1 = WALL
# 0 = WALKABLE
# ============================================================

maze = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1],
    [1,0,1,1,1,0,1,0,1,1,1,0,1,0,1,1,0,1],
    [1,0,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,1],
    [1,0,1,0,1,1,1,1,1,0,1,1,1,0,1,0,1,1],
    [1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1],
    [1,1,1,1,1,1,1,0,1,1,1,0,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def tile_center(row, col):
    return (
        col * TILE + TILE // 2,
        row * TILE + TILE // 2
    )


def pixel_to_tile(x, y):
    return (
        int(y // TILE),
        int(x // TILE)
    )


# ============================================================
# A* PATHFINDING
# ============================================================

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors(node):

    row, col = node

    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]

    result = []

    for dr, dc in directions:

        nr = row + dr
        nc = col + dc

        if 0 <= nr < ROWS and 0 <= nc < COLS:

            if maze[nr][nc] == 0:
                result.append((nr, nc))

    return result


def a_star(start, goal):

    if start == goal:
        return [start]

    open_list = []

    heapq.heappush(
        open_list,
        (0, start)
    )

    came_from = {}

    cost = {
        start: 0
    }

    while open_list:

        current_priority, current = heapq.heappop(open_list)

        if current == goal:
            path = []

            while current in came_from:

                path.append(current)
                current = came_from[current]

            path.append(start)

            path.reverse()

            return path

        for next_node in neighbors(current):

            new_cost = cost[current] + 1

            if (
                next_node not in cost
                or new_cost < cost[next_node]
            ):

                cost[next_node] = new_cost

                priority = (
                    new_cost
                    + heuristic(next_node, goal)
                )

                heapq.heappush(
                    open_list,
                    (priority, next_node)
                )

                came_from[next_node] = current

    return []


# ============================================================
# PLAYER
# ============================================================

player_x, player_y = tile_center(1, 1)

PLAYER_SPEED = TILE * 4       # 4 tiles per second
PLAYER_SIZE = 26

player_health = 100


# ============================================================
# GHOST
# ============================================================

ghost_x, ghost_y = tile_center(9, 16)

NORMAL_GHOST_SPEED = TILE * 3     # 3 tiles/sec
CHASE_GHOST_SPEED = TILE * 4       # 4 tiles/sec

GHOST_SIZE = 30

ghost_path = []

path_timer = 0

PATH_UPDATE_TIME = 0.25


# ============================================================
# CRYSTALS
# ============================================================

crystals = [
    (1, 4),
    (3, 8),
    (5, 5),
    (7, 13),
    (9, 8)
]

collected_crystals = set()


# ============================================================
# EXIT
# ============================================================

exit_tile = (9, 16)


# ============================================================
# GAME STATE
# ============================================================

game_won = False
game_over = False


# ============================================================
# COLLISION WITH WALL
# ============================================================

def can_move(x, y, size):

    rect = pygame.Rect(
        int(x - size // 2),
        int(y - size // 2),
        size,
        size
    )

    # Outside screen

    if rect.left < 0:
        return False

    if rect.right > GAME_WIDTH:
        return False

    if rect.top < 0:
        return False

    if rect.bottom > GAME_HEIGHT:
        return False

    # Check walls

    for row in range(ROWS):

        for col in range(COLS):

            if maze[row][col] == 1:

                wall_rect = pygame.Rect(
                    col * TILE,
                    row * TILE,
                    TILE,
                    TILE
                )

                if rect.colliderect(wall_rect):
                    return False

    return True


# ============================================================
# MOVE PLAYER
# ============================================================

def update_player(dt):

    global player_x
    global player_y

    keys = pygame.key.get_pressed()

    dx = 0
    dy = 0

    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx -= 1

    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx += 1

    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy -= 1

    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy += 1

    # Prevent diagonal movement from being faster

    if dx != 0 and dy != 0:

        factor = 0.7071

        dx *= factor
        dy *= factor

    new_x = player_x + dx * PLAYER_SPEED * dt
    new_y = player_y + dy * PLAYER_SPEED * dt

    if can_move(
        new_x,
        player_y,
        PLAYER_SIZE
    ):
        player_x = new_x

    if can_move(
        player_x,
        new_y,
        PLAYER_SIZE
    ):
        player_y = new_y


# ============================================================
# UPDATE GHOST PATH
# ============================================================

def update_ghost_path():

    global ghost_path

    ghost_tile = pixel_to_tile(
        ghost_x,
        ghost_y
    )

    player_tile = pixel_to_tile(
        player_x,
        player_y
    )

    ghost_path = a_star(
        ghost_tile,
        player_tile
    )


# ============================================================
# MOVE GHOST
# ============================================================

def update_ghost(dt):

    global ghost_x
    global ghost_y
    global path_timer

    path_timer += dt

    if path_timer >= PATH_UPDATE_TIME:

        update_ghost_path()

        path_timer = 0

    if len(ghost_path) < 2:
        return

    # Next tile in path

    next_tile = ghost_path[1]

    target_x, target_y = tile_center(
        next_tile[0],
        next_tile[1]
    )

    # Distance from player

    distance = math.sqrt(
        (player_x - ghost_x) ** 2
        + (player_y - ghost_y) ** 2
    )

    # Ghost becomes faster when close

    if distance < TILE * 6:

        speed = CHASE_GHOST_SPEED

    else:

        speed = NORMAL_GHOST_SPEED

    dx = target_x - ghost_x
    dy = target_y - ghost_y

    distance_to_target = math.sqrt(
        dx * dx + dy * dy
    )

    if distance_to_target > 2:

        dx /= distance_to_target
        dy /= distance_to_target

        ghost_x += dx * speed * dt
        ghost_y += dy * speed * dt


# ============================================================
# CHECK CRYSTALS
# ============================================================

def collect_crystals():

    player_tile = pixel_to_tile(
        player_x,
        player_y
    )

    for crystal in crystals:

        if crystal == player_tile:

            collected_crystals.add(
                crystal
            )


# ============================================================
# GHOST COLLISION
# ============================================================

damage_timer = 0


def check_ghost_collision(dt):

    global player_health
    global damage_timer
    global game_over

    distance = math.sqrt(
        (player_x - ghost_x) ** 2
        + (player_y - ghost_y) ** 2
    )

    damage_timer -= dt

    # Ghost has caught the player
    if distance < 35:

        if damage_timer <= 0:

            player_health -= 25
            damage_timer = 0.5

        # Player dies
        if player_health <= 0:

            player_health = 0
            game_over = True


# ============================================================
# CHECK WIN
# ============================================================

def check_win():

    global game_won

    player_tile = pixel_to_tile(
        player_x,
        player_y
    )

    if (
        len(collected_crystals) == len(crystals)
        and player_tile == exit_tile
    ):

        game_won = True


# ============================================================
# DRAW MAZE
# ============================================================

def draw_maze():

    for row in range(ROWS):

        for col in range(COLS):

            x = col * TILE
            y = row * TILE

            if maze[row][col] == 1:

                # Wall

                pygame.draw.rect(
                    screen,
                    WALL,
                    (
                        x,
                        y,
                        TILE,
                        TILE
                    )
                )

                pygame.draw.rect(
                    screen,
                    WALL_EDGE,
                    (
                        x + 2,
                        y + 2,
                        TILE - 4,
                        TILE - 4
                    ),
                    2
                )

            else:

                # Floor

                pygame.draw.rect(
                    screen,
                    DARK_FLOOR,
                    (
                        x,
                        y,
                        TILE,
                        TILE
                    )
                )

                pygame.draw.rect(
                    screen,
                    (28, 28, 40),
                    (
                        x,
                        y,
                        TILE,
                        TILE
                    ),
                    1
                )


# ============================================================
# DRAW PLAYER
# ============================================================

def draw_player():

    # Slight bobbing animation

    bob = math.sin(
        pygame.time.get_ticks() * 0.008
    ) * 2

    x = int(player_x)
    y = int(player_y + bob)

    # Glow

    glow = pygame.Surface(
        (70, 70),
        pygame.SRCALPHA
    )

    pygame.draw.circle(
        glow,
        (70, 150, 255, 35),
        (35, 35),
        32
    )

    screen.blit(
        glow,
        (x - 35, y - 35)
    )

    # Body

    pygame.draw.circle(
        screen,
        BLUE,
        (x, y),
        14
    )

    # Face

    pygame.draw.circle(
        screen,
        WHITE,
        (x - 5, y - 4),
        3
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (x + 5, y - 4),
        3
    )


# ============================================================
# DRAW GHOST
# ============================================================

def draw_ghost():

    # Floating animation

    bob = math.sin(
        pygame.time.get_ticks() * 0.006
    ) * 5

    x = int(ghost_x)
    y = int(ghost_y + bob)

    # Glow

    glow = pygame.Surface(
        (100, 100),
        pygame.SRCALPHA
    )

    pygame.draw.circle(
        glow,
        (180, 60, 255, 35),
        (50, 50),
        45
    )

    screen.blit(
        glow,
        (x - 50, y - 50)
    )

    # Ghost head

    pygame.draw.circle(
        screen,
        PURPLE,
        (x, y - 5),
        19
    )

    # Body

    pygame.draw.rect(
        screen,
        PURPLE,
        (
            x - 19,
            y - 5,
            38,
            23
        )
    )

    # Ghost bottom waves

    pygame.draw.circle(
        screen,
        PURPLE,
        (x - 10, y + 17),
        9
    )

    pygame.draw.circle(
        screen,
        PURPLE,
        (x + 10, y + 17),
        9
    )

    # Eyes

    pygame.draw.circle(
        screen,
        WHITE,
        (x - 7, y - 8),
        5
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (x + 7, y - 8),
        5
    )

    pygame.draw.circle(
        screen,
        BLACK,
        (x - 7, y - 8),
        2
    )

    pygame.draw.circle(
        screen,
        BLACK,
        (x + 7, y - 8),
        2
    )


# ============================================================
# DRAW CRYSTALS
# ============================================================

def draw_crystals():

    pulse = (
        math.sin(
            pygame.time.get_ticks() * 0.006
        ) + 1
    ) * 2

    for crystal in crystals:

        if crystal in collected_crystals:
            continue

        x, y = tile_center(
            crystal[0],
            crystal[1]
        )

        # Glow

        glow = pygame.Surface(
            (70, 70),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow,
            (50, 230, 255, 35),
            (35, 35),
            25 + int(pulse)
        )

        screen.blit(
            glow,
            (x - 35, y - 35)
        )

        # Diamond

        points = [
            (x, y - 13),
            (x + 9, y),
            (x, y + 13),
            (x - 9, y)
        ]

        pygame.draw.polygon(
            screen,
            CYAN,
            points
        )


# ============================================================
# DRAW EXIT
# ============================================================

def draw_exit():

    x, y = tile_center(
        exit_tile[0],
        exit_tile[1]
    )

    # Locked / unlocked

    if len(collected_crystals) == len(crystals):

        color = GREEN

    else:

        color = RED

    pygame.draw.rect(
        screen,
        color,
        (
            x - 17,
            y - 22,
            34,
            44
        )
    )

    pygame.draw.rect(
        screen,
        BLACK,
        (
            x - 10,
            y - 15,
            20,
            30
        )
    )


# ============================================================
# DRAW HUD
# ============================================================

def draw_hud():

    pygame.draw.rect(
        screen,
        (12, 12, 20),
        (
            0,
            GAME_HEIGHT,
            WIDTH,
            HUD_HEIGHT
        )
    )

    # Health

    health_text = font.render(
        f"HEALTH: {player_health}",
        True,
        WHITE
    )

    screen.blit(
        health_text,
        (20, GAME_HEIGHT + 15)
    )

    # Crystals

    crystal_text = font.render(
        f"SOULS: {len(collected_crystals)}/{len(crystals)}",
        True,
        CYAN
    )

    screen.blit(
        crystal_text,
        (230, GAME_HEIGHT + 15)
    )

    # Instructions

    instruction = small_font.render(
        "WASD / ARROW KEYS  •  Collect all souls and escape",
        True,
        (170, 170, 180)
    )

    screen.blit(
        instruction,
        (20, GAME_HEIGHT + 48)
    )


# ============================================================
# DRAW GAME OVER
# ============================================================

def draw_game_over():

    overlay = pygame.Surface(
        (WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (0, 0, 0, 180)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    text = big_font.render(
        "GAME OVER",
        True,
        RED
    )

    screen.blit(
        text,
        (
            WIDTH // 2 - text.get_width() // 2,
            GAME_HEIGHT // 2 - 40
        )
    )


# ============================================================
# DRAW WIN
# ============================================================

def draw_win():

    overlay = pygame.Surface(
        (WIDTH, GAME_HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (0, 0, 0, 170)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    text = big_font.render(
        "YOU ESCAPED!",
        True,
        GREEN
    )

    screen.blit(
        text,
        (
            WIDTH // 2 - text.get_width() // 2,
            GAME_HEIGHT // 2 - 40
        )
    )


# ============================================================
# MAIN LOOP
# ============================================================

running = True

while running:

    # Delta time

    dt = clock.tick(60) / 1000.0

    # Limit huge time jumps

    dt = min(dt, 0.05)

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

    # --------------------------------------------------------
    # GAME UPDATE
    # --------------------------------------------------------

    if not game_over and not game_won:

        update_player(dt)

        collect_crystals()

        update_ghost(dt)

        check_ghost_collision(dt)

        check_win()

        if player_health <= 0:

            game_over = True

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    screen.fill(BLACK)

    draw_maze()
    draw_crystals()
    draw_exit()
    draw_player()
    draw_ghost()
    draw_hud()

    if game_over:

        draw_game_over()

    if game_won:

        draw_win()

    pygame.display.flip()


pygame.quit()
