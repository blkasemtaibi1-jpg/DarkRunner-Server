import pygame
import socket
import threading
import json
import tkinter as tk
from tkinter import simpledialog

pygame.init()

WIDTH, HEIGHT = 1100, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dark Runner Online")
clock = pygame.time.Clock()

# ---------- COLORS ----------
BG = (7, 8, 16)
GRID = (15, 18, 30)
GROUND = (35, 39, 56)
GROUND_TOP = (75, 82, 105)
WHITE = (240, 245, 255)
BLUE = (40, 160, 255)
PURPLE = (170, 80, 255)
CYAN = (40, 230, 255)
RED = (245, 50, 60)
GREEN = (50, 220, 120)
BLACK = (2, 3, 7)

# ---------- NETWORK ----------
sock = None
network_running = False
my_id = None
players = {}
server_traps = {}
lock = threading.Lock()


def send(data):
    try:
        sock.sendall((json.dumps(data) + "\n").encode())
    except:
        pass


def receive():
    global my_id, players, server_traps, network_running

    buffer = ""

    while network_running:
        try:
            data = sock.recv(16384)

            if not data:
                break

            buffer += data.decode()

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if not line:
                    continue

                try:
                    packet = json.loads(line)
                except:
                    continue

                if packet["type"] == "welcome":
                    my_id = packet["id"]

                elif packet["type"] == "state":
                    with lock:
                        players = packet.get("players", {})
                        server_traps = packet.get("traps", {})

        except:
            break

    network_running = False


def connect_window():
    root = tk.Tk()
    root.withdraw()

    address = simpledialog.askstring(
        "Dark Runner Online",
        "Server address:\nExample: 127.0.0.1"
    )

    if not address:
        root.destroy()
        return None, None

    port = simpledialog.askinteger(
        "Dark Runner Online",
        "Port:",
        initialvalue=5000,
        minvalue=1,
        maxvalue=65535
    )

    root.destroy()
    return address, port


def connect(address, port):
    global sock, network_running

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(8)
        sock.connect((address, port))
        sock.settimeout(None)

        network_running = True

        threading.Thread(
            target=receive,
            daemon=True
        ).start()

        return True

    except Exception as e:
        print("Connection error:", e)
        return False


# =========================================================
# 3 LEVELS
# =========================================================

LEVELS = {

    1: {
        "spawn": (60, 490),

        "platforms": [
            (0, 560, 1100, 90),
            (300, 440, 180, 30),
            (650, 350, 180, 30)
        ],

        "traps": [
            (220, 560, 80),
            (500, 560, 90),
            (850, 560, 100)
        ],

        "finish": (1010, 500, 45, 60)
    },

    2: {
        "spawn": (60, 490),

        "platforms": [
            (0, 560, 180, 90),
            (330, 560, 160, 90),
            (650, 560, 150, 90),
            (950, 560, 150, 90),

            (210, 430, 120, 30),
            (500, 350, 120, 30),
            (780, 270, 130, 30)
        ],

        "traps": [
            (180, 560, 150),
            (490, 560, 160),
            (800, 560, 150)
        ],

        "finish": (1030, 500, 45, 60)
    },

    3: {
        "spawn": (50, 490),

        "platforms": [
            (0, 560, 150, 90),
            (300, 560, 140, 90),
            (600, 560, 130, 90),
            (900, 560, 200, 90),

            (170, 430, 110, 30),
            (350, 330, 110, 30),
            (530, 230, 110, 30),
            (720, 330, 110, 30),
            (850, 430, 100, 30)
        ],

        "traps": [
            (150, 560, 150),
            (440, 560, 160),
            (730, 560, 170)
        ],

        "finish": (1020, 500, 45, 60)
    }
}


# =========================================================
# PLAYER
# =========================================================

player = pygame.Rect(60, 490, 38, 68)

velocity_y = 0
on_ground = False

SPEED = 6
GRAVITY = 0.75
JUMP = -14

level = 1
send_timer = 0
trap_cooldown = 0


def reset_player():
    global velocity_y

    x, y = LEVELS[level]["spawn"]

    player.x = x
    player.y = y
    velocity_y = 0


# =========================================================
# CHARACTER
# =========================================================

def draw_character(rect, color):

    # legs
    pygame.draw.rect(
        screen, PURPLE,
        (rect.x + 6, rect.y + 53, 10, 15),
        border_radius=4
    )

    pygame.draw.rect(
        screen, PURPLE,
        (rect.x + 22, rect.y + 53, 10, 15),
        border_radius=4
    )

    # body
    pygame.draw.rect(
        screen, color,
        (rect.x + 6, rect.y + 25, 26, 32),
        border_radius=8
    )

    # arms
    pygame.draw.rect(
        screen, color,
        (rect.x, rect.y + 30, 7, 21),
        border_radius=3
    )

    pygame.draw.rect(
        screen, color,
        (rect.x + 31, rect.y + 30, 7, 21),
        border_radius=3
    )

    # head
    pygame.draw.rect(
        screen, color,
        (rect.x + 3, rect.y, 32, 32),
        border_radius=11
    )

    # visor
    pygame.draw.rect(
        screen, BLACK,
        (rect.x + 8, rect.y + 9, 22, 10),
        border_radius=4
    )

    # eyes
    pygame.draw.rect(
        screen, CYAN,
        (rect.x + 11, rect.y + 12, 5, 4)
    )

    pygame.draw.rect(
        screen, CYAN,
        (rect.x + 22, rect.y + 12, 5, 4)
    )


# =========================================================
# TRAP
# =========================================================

def trap_key(index):
    return f"{level}:{index}"


def nearest_trap():

    best = None
    distance = 99999

    for i, trap in enumerate(
        LEVELS[level]["traps"]
    ):

        x, y, width = trap
        center = x + width / 2

        d = abs(player.centerx - center)

        if d < distance:
            distance = d
            best = i

    if distance <= 150:
        return best

    return None


def activate_trap():

    global trap_cooldown

    if trap_cooldown > 0:
        return

    index = nearest_trap()

    if index is None:
        return

    send({
        "type": "trigger_trap",
        "level": level,
        "index": index
    })

    trap_cooldown = 30


# =========================================================
# DRAW WORLD
# =========================================================

def draw_world():

    screen.fill(BG)

    # grid
    for x in range(0, WIDTH, 50):
        pygame.draw.line(
            screen, GRID,
            (x, 0), (x, HEIGHT)
        )

    for y in range(0, HEIGHT, 50):
        pygame.draw.line(
            screen, GRID,
            (0, y), (WIDTH, y)
        )

    data = LEVELS[level]

    # normal platforms
    for p in data["platforms"]:

        r = pygame.Rect(p)

        pygame.draw.rect(
            screen,
            GROUND,
            r,
            border_radius=5
        )

        pygame.draw.line(
            screen,
            GROUND_TOP,
            (r.left, r.top),
            (r.right, r.top),
            3
        )

    # traps
    for i, trap in enumerate(data["traps"]):

        x, y, width = trap

        state = server_traps.get(
            trap_key(i),
            {}
        )

        remaining = float(
            state.get("remaining", 0)
        )

        if remaining > 0:

            # THE FLOOR IS OPEN
            pygame.draw.rect(
                screen,
                BLACK,
                (x, y, width, 90)
            )

            # spikes rise FROM INSIDE THE HOLE
            progress = min(
                1.0,
                (1.35 - remaining) / 0.20
            )

            spike_height = int(
                48 * max(0, min(1, progress))
            )

            count = max(
                3,
                width // 25
            )

            sw = width / count

            for n in range(count):

                sx = x + n * sw

                points = [
                    (int(sx), int(y)),
                    (
                        int(sx + sw / 2),
                        int(y - spike_height)
                    ),
                    (
                        int(sx + sw),
                        int(y)
                    )
                ]

                pygame.draw.polygon(
                    screen,
                    RED,
                    points
                )

        else:

            # CLOSED FLOOR
            pygame.draw.rect(
                screen,
                GROUND,
                (x, y, width, 90)
            )

            pygame.draw.line(
                screen,
                GROUND_TOP,
                (x, y),
                (x + width, y),
                3
            )

    # finish
    finish = pygame.Rect(
        data["finish"]
    )

    pygame.draw.rect(
        screen,
        GREEN,
        finish,
        border_radius=8
    )


# =========================================================
# PHYSICS
# =========================================================

def update_player():

    global velocity_y, on_ground

    keys = pygame.key.get_pressed()

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player.x -= SPEED

    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player.x += SPEED

    velocity_y += GRAVITY
    player.y += velocity_y

    on_ground = False

    for p in LEVELS[level]["platforms"]:

        platform = pygame.Rect(p)

        if player.colliderect(platform):

            if velocity_y >= 0:

                player.bottom = platform.top
                velocity_y = 0
                on_ground = True

    # active spikes
    for i, trap in enumerate(
        LEVELS[level]["traps"]
    ):

        x, y, width = trap

        state = server_traps.get(
            trap_key(i),
            {}
        )

        if float(
            state.get("remaining", 0)
        ) <= 0:
            continue

        spikes = pygame.Rect(
            x,
            y - 48,
            width,
            48
        )

        if player.colliderect(spikes):
            reset_player()

    # fell through an opened hole
    if player.top > HEIGHT:
        reset_player()

    if player.left < 0:
        player.left = 0

    if player.right > WIDTH:
        player.right = WIDTH


# =========================================================
# LEVEL FINISH
# =========================================================

def check_finish():

    global level

    finish = pygame.Rect(
        LEVELS[level]["finish"]
    )

    if player.colliderect(finish):

        if level < 3:
            level += 1
            reset_player()
        else:
            level = 1
            reset_player()


# =========================================================
# NETWORK
# =========================================================

def network_update():

    global send_timer

    send_timer += 1

    if send_timer >= 3:

        send_timer = 0

        send({
            "type": "player",
            "x": player.x,
            "y": player.y,
            "level": level
        })


def draw_players():

    with lock:
        snapshot = dict(players)

    for pid, data in snapshot.items():

        if str(pid) == str(my_id):
            continue

        if int(data.get("level", 1)) != level:
            continue

        r = pygame.Rect(
            int(data.get("x", 100)),
            int(data.get("y", 490)),
            38,
            68
        )

        draw_character(
            r,
            PURPLE
        )


# =========================================================
# UI
# =========================================================

def draw_ui():

    font = pygame.font.Font(None, 38)

    screen.blit(
        font.render(
            "DARK RUNNER ONLINE",
            True,
            WHITE
        ),
        (25, 20)
    )

    screen.blit(
        font.render(
            f"LEVEL {level}",
            True,
            CYAN
        ),
        (25, 60)
    )

    small = pygame.font.Font(None, 25)

    screen.blit(
        small.render(
            "A/D = MOVE    SPACE/W = JUMP    E = TRAP",
            True,
            (170, 175, 190)
        ),
        (25, 98)
    )


# =========================================================
# START
# =========================================================

address, port = connect_window()

if not address:
    pygame.quit()
    raise SystemExit

if not connect(address, port):

    print("Could not connect to server.")

    pygame.quit()
    raise SystemExit


running = True

while running:

    clock.tick(60)

    if trap_cooldown > 0:
        trap_cooldown -= 1

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
                    velocity_y = JUMP

            if event.key == pygame.K_e:
                activate_trap()

    update_player()
    check_finish()
    network_update()

    draw_world()
    draw_players()
    draw_character(player, BLUE)
    draw_ui()

    pygame.display.flip()


network_running = False

try:
    sock.close()
except:
    pass

pygame.quit()