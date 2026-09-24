import pygame
import socket
import threading
import json
import tkinter as tk
from tkinter import simpledialog

pygame.init()

WIDTH = 1100
HEIGHT = 650
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dark Runner Online")

clock = pygame.time.Clock()

# =========================================================
# COLORS
# =========================================================

BG = (7, 9, 18)
GRID = (15, 19, 34)
GROUND = (30, 34, 52)

WHITE = (240, 245, 255)
BLUE = (45, 150, 255)
CYAN = (40, 225, 255)
PURPLE = (160, 85, 255)

RED = (240, 55, 70)
DARK_RED = (120, 25, 35)

GREEN = (50, 220, 120)
YELLOW = (240, 210, 70)

# =========================================================
# NETWORK
# =========================================================

sock = None
my_id = None

other_players = {}

network_running = False


def send_data(data):
    global sock

    if sock is None:
        return

    try:
        message = json.dumps(data) + "\n"
        sock.sendall(message.encode("utf-8"))
    except:
        pass


def receive_network():
    global my_id
    global network_running
    global other_players

    buffer = ""

    while network_running:

        try:
            data = sock.recv(8192)

            if not data:
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:

                line, buffer = buffer.split("\n", 1)

                if not line:
                    continue

                try:
                    message = json.loads(line)
                except:
                    continue

                if message.get("type") == "welcome":

                    my_id = message.get("id")

                elif message.get("type") == "players":

                    players = message.get("players", {})

                    new_players = {}

                    for player_id, player in players.items():

                        if str(player_id) == str(my_id):
                            continue

                        new_players[player_id] = player

                    other_players = new_players

        except:
            break

    network_running = False


# =========================================================
# CONNECTION WINDOW
# =========================================================

def connection_window():

    root = tk.Tk()

    root.withdraw()

    server = simpledialog.askstring(
        "Dark Runner Online",
        "Server address:\nExample: 127.0.0.1"
    )

    if not server:
        root.destroy()
        return None, None

    port = simpledialog.askinteger(
        "Dark Runner Online",
        "Server port:\nExample: 5000",
        initialvalue=5000,
        minvalue=1,
        maxvalue=65535
    )

    root.destroy()

    if not port:
        return None, None

    return server, port


def connect_to_server(server, port):

    global sock
    global network_running

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.settimeout(8)

        sock.connect(
            (server, port)
        )

        sock.settimeout(None)

        network_running = True

        thread = threading.Thread(
            target=receive_network,
            daemon=True
        )

        thread.start()

        return True

    except Exception as error:

        print("Connection error:", error)

        return False


# =========================================================
# LEVEL DATA
# =========================================================

LEVELS = {

    1: {
        "spawn": (80, 490),

        "platforms": [
            (0, 560, 1100, 90),
            (300, 450, 180, 30),
            (650, 360, 180, 30)
        ],

        "traps": [
            {
                "x": 500,
                "y": 560,
                "width": 100,
                "delay": 120
            }
        ],

        "finish": (1000, 500, 50, 60)
    },

    2: {
        "spawn": (80, 490),

        "platforms": [
            (0, 560, 230, 90),
            (360, 560, 190, 90),
            (700, 560, 400, 90),

            (250, 420, 120, 30),
            (600, 350, 150, 30),
            (850, 280, 150, 30)
        ],

        "traps": [
            {
                "x": 230,
                "y": 560,
                "width": 130,
                "delay": 90
            },

            {
                "x": 550,
                "y": 560,
                "width": 150,
                "delay": 160
            }
        ],

        "finish": (1000, 220, 50, 60)
    },

    3: {
        "spawn": (80, 490),

        "platforms": [
            (0, 560, 180, 90),
            (300, 560, 160, 90),
            (600, 560, 150, 90),
            (900, 560, 200, 90),

            (200, 420, 120, 30),
            (400, 320, 120, 30),
            (600, 220, 120, 30),
            (800, 320, 120, 30)
        ],

        "traps": [
            {
                "x": 180,
                "y": 560,
                "width": 120,
                "delay": 70
            },

            {
                "x": 460,
                "y": 560,
                "width": 140,
                "delay": 110
            },

            {
                "x": 750,
                "y": 560,
                "width": 150,
                "delay": 150
            }
        ],

        "finish": (1000, 500, 50, 60)
    }
}


# =========================================================
# PLAYER
# =========================================================

player = pygame.Rect(
    80,
    490,
    40,
    70
)

velocity_y = 0

MOVE_SPEED = 5
GRAVITY = 0.8
JUMP_POWER = -15

on_ground = False

current_level = 1


# =========================================================
# TRAP STATE
# =========================================================

trap_states = {}

trap_timers = {}

for level_number, level in LEVELS.items():

    trap_states[level_number] = []

    trap_timers[level_number] = []

    for trap in level["traps"]:

        trap_states[level_number].append(False)

        trap_timers[level_number].append(
            trap["delay"]
        )


# =========================================================
# RESET
# =========================================================

def reset_player():

    global velocity_y

    spawn_x, spawn_y = LEVELS[current_level]["spawn"]

    player.x = spawn_x
    player.y = spawn_y

    velocity_y = 0


# =========================================================
# DRAW CHARACTER
# =========================================================

def draw_character(rect, color):

    # Shadow
    shadow = pygame.Rect(
        rect.x + 4,
        rect.bottom - 7,
        32,
        8
    )

    pygame.draw.ellipse(
        screen,
        (3, 4, 9),
        shadow
    )

    # Body
    body = pygame.Rect(
        rect.x + 7,
        rect.y + 27,
        26,
        30
    )

    pygame.draw.rect(
        screen,
        color,
        body,
        border_radius=8
    )

    # Head
    head = pygame.Rect(
        rect.x + 4,
        rect.y,
        32,
        32
    )

    pygame.draw.rect(
        screen,
        color,
        head,
        border_radius=11
    )

    # Visor
    visor = pygame.Rect(
        rect.x + 9,
        rect.y + 9,
        22,
        9
    )

    pygame.draw.rect(
        screen,
        BG,
        visor,
        border_radius=4
    )

    # Eye glow
    pygame.draw.rect(
        screen,
        CYAN,
        (
            rect.x + 12,
            rect.y + 11,
            5,
            4
        ),
        border_radius=2
    )

    pygame.draw.rect(
        screen,
        CYAN,
        (
            rect.x + 22,
            rect.y + 11,
            5,
            4
        ),
        border_radius=2
    )

    # Arms
    pygame.draw.rect(
        screen,
        color,
        (
            rect.x + 1,
            rect.y + 30,
            7,
            22
        ),
        border_radius=3
    )

    pygame.draw.rect(
        screen,
        color,
        (
            rect.x + 32,
            rect.y + 30,
            7,
            22
        ),
        border_radius=3
    )

    # Legs
    pygame.draw.rect(
        screen,
        PURPLE,
        (
            rect.x + 7,
            rect.y + 55,
            11,
            15
        ),
        border_radius=4
    )

    pygame.draw.rect(
        screen,
        PURPLE,
        (
            rect.x + 22,
            rect.y + 55,
            11,
            15
        ),
        border_radius=4
    )


# =========================================================
# DRAW WORLD
# =========================================================

def draw_world():

    screen.fill(BG)

    # Grid

    for x in range(0, WIDTH, 50):

        pygame.draw.line(
            screen,
            GRID,
            (x, 0),
            (x, HEIGHT)
        )

    for y in range(0, HEIGHT, 50):

        pygame.draw.line(
            screen,
            GRID,
            (0, y),
            (WIDTH, y)
        )

    level = LEVELS[current_level]

    # Platforms

    for index, platform_data in enumerate(level["platforms"]):

        rect = pygame.Rect(
            platform_data
        )

        pygame.draw.rect(
            screen,
            GROUND,
            rect,
            border_radius=7
        )

        pygame.draw.line(
            screen,
            (55, 65, 90),
            (rect.left, rect.top),
            (rect.right, rect.top),
            3
        )

    # Traps

    for index, trap in enumerate(level["traps"]):

        x = trap["x"]
        y = trap["y"]
        width = trap["width"]

        # Closed floor

        if not trap_states[current_level][index]:

            pygame.draw.rect(
                screen,
                GROUND,
                (
                    x,
                    y,
                    width,
                    90
                )
            )

        else:

            # Hole
            pygame.draw.rect(
                screen,
                (2, 3, 7),
                (
                    x,
                    y,
                    width,
                    90
                )
            )

            # Spikes

            spike_count = max(
                2,
                width // 25
            )

            spike_width = width / spike_count

            for s in range(spike_count):

                sx = x + s * spike_width

                points = [
                    (int(sx), int(y)),
                    (
                        int(sx + spike_width / 2),
                        int(y - 45)
                    ),
                    (
                        int(sx + spike_width),
                        int(y)
                    )
                ]

                pygame.draw.polygon(
                    screen,
                    RED,
                    points
                )

                pygame.draw.line(
                    screen,
                    DARK_RED,
                    points[0],
                    points[1],
                    2
                )

    # Finish

    finish = pygame.Rect(
        level["finish"]
    )

    pygame.draw.rect(
        screen,
        GREEN,
        finish,
        border_radius=8
    )

    pygame.draw.rect(
        screen,
        WHITE,
        (
            finish.x + 12,
            finish.y + 12,
            26,
            36
        ),
        2,
        border_radius=4
    )


# =========================================================
# TRAPS
# =========================================================

def update_traps():

    level = LEVELS[current_level]

    for index, trap in enumerate(level["traps"]):

        trap_timers[current_level][index] -= 1

        if trap_timers[current_level][index] <= 0:

            trap_states[current_level][index] = not trap_states[current_level][index]

            if trap_states[current_level][index]:

                trap_timers[current_level][index] = 120

            else:

                trap_timers[current_level][index] = 180


# =========================================================
# PLAYER COLLISION
# =========================================================

def update_player():

    global velocity_y
    global on_ground

    keys = pygame.key.get_pressed()

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:

        player.x -= MOVE_SPEED

    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:

        player.x += MOVE_SPEED

    # Gravity

    velocity_y += GRAVITY

    player.y += velocity_y

    on_ground = False

    level = LEVELS[current_level]

    # Ground / platforms

    for platform_data in level["platforms"]:

        platform = pygame.Rect(
            platform_data
        )

        if player.colliderect(platform):

            if velocity_y >= 0:

                if player.bottom <= platform.bottom:

                    player.bottom = platform.top

                    velocity_y = 0

                    on_ground = True

    # Trap collision

    for index, trap in enumerate(level["traps"]):

        if not trap_states[current_level][index]:

            continue

        spike_rect = pygame.Rect(
            trap["x"],
            trap["y"] - 45,
            trap["width"],
            45
        )

        if player.colliderect(spike_rect):

            reset_player()

    # Fell into hole

    if player.top > HEIGHT:

        reset_player()

    # Boundaries

    if player.left < 0:

        player.left = 0

    if player.right > WIDTH:

        player.right = WIDTH


# =========================================================
# LEVEL FINISH
# =========================================================

def check_finish():

    global current_level

    finish = pygame.Rect(
        LEVELS[current_level]["finish"]
    )

    if player.colliderect(finish):

        if current_level < 3:

            current_level += 1

            reset_player()

        else:

            current_level = 1

            reset_player()


# =========================================================
# NETWORK UPDATE
# =========================================================

send_timer = 0


def update_network():

    global send_timer

    send_timer += 1

    if send_timer >= 3:

        send_timer = 0

        send_data({
            "type": "update",
            "x": player.x,
            "y": player.y,
            "level": current_level,
            "state": "playing"
        })


# =========================================================
# DRAW OTHER PLAYERS
# =========================================================

def draw_other_players():

    for player_id, data in other_players.items():

        try:

            if int(data.get("level", 1)) != current_level:
                continue

            x = float(data.get("x", 100))
            y = float(data.get("y", 490))

            remote_rect = pygame.Rect(
                int(x),
                int(y),
                40,
                70
            )

            draw_character(
                remote_rect,
                PURPLE
            )

        except:
            pass


# =========================================================
# UI
# =========================================================

def draw_ui():

    font = pygame.font.Font(None, 38)

    title = font.render(
        "DARK RUNNER ONLINE",
        True,
        WHITE
    )

    screen.blit(
        title,
        (25, 20)
    )

    level_text = font.render(
        f"LEVEL {current_level}    PLAYERS: {len(other_players) + 1}",
        True,
        CYAN
    )

    screen.blit(
        level_text,
        (25, 60)
    )

    small = pygame.font.Font(None, 25)

    controls = small.render(
        "A/D or ARROWS = MOVE     SPACE = JUMP     ESC = EXIT",
        True,
        (150, 160, 180)
    )

    screen.blit(
        controls,
        (25, 105)
    )


# =========================================================
# MAIN
# =========================================================

server, port = connection_window()

if server is None:

    pygame.quit()

    raise SystemExit


if not connect_to_server(server, port):

    pygame.quit()

    raise SystemExit(
        "Could not connect to server."
    )


running = True

while running:

    clock.tick(FPS)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                running = False

            if event.key in (
                pygame.K_SPACE,
                pygame.K_w,
                pygame.K_UP
            ):

                if on_ground:

                    velocity_y = JUMP_POWER

    update_player()

    update_traps()

    check_finish()

    update_network()

    draw_world()

    draw_other_players()

    draw_character(
        player,
        BLUE
    )

    draw_ui()

    pygame.display.flip()


network_running = False

try:
    sock.close()
except:
    pass

pygame.quit()