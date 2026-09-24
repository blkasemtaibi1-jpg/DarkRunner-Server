import socket
import threading
import json
import os
import time

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "5000"))

clients = {}
players = {}
traps = {}

next_id = 1
lock = threading.Lock()


def send(client, data):

    try:
        client.sendall(
            (json.dumps(data) + "\n").encode()
        )
        return True
    except:
        return False


def get_state():

    now = time.monotonic()

    with lock:

        expired = []

        for key, expire in traps.items():

            if expire <= now:
                expired.append(key)

        for key in expired:
            traps.pop(key, None)

        trap_data = {}

        for key, expire in traps.items():

            trap_data[key] = {
                "remaining": round(
                    expire - now,
                    3
                )
            }

        return {
            "type": "state",
            "players": dict(players),
            "traps": trap_data
        }


def broadcast():

    packet = get_state()

    dead = []

    with lock:

        for pid, client in list(
            clients.items()
        ):

            if not send(client, packet):
                dead.append(pid)

        for pid in dead:
            clients.pop(pid, None)
            players.pop(str(pid), None)


def trigger_trap(pid, level, index):

    locations = {

        1: [
            (220, 560, 80),
            (500, 560, 90),
            (850, 560, 100)
        ],

        2: [
            (180, 560, 150),
            (490, 560, 160),
            (800, 560, 150)
        ],

        3: [
            (150, 560, 150),
            (440, 560, 160),
            (730, 560, 170)
        ]
    }

    if level not in locations:
        return

    if index < 0 or index >= len(locations[level]):
        return

    with lock:

        p = players.get(str(pid))

        if not p:
            return

        if int(p.get("level", 1)) != level:
            return

        x, y, width = locations[level][index]

        player_x = float(
            p.get("x", 0)
        )

        center = x + width / 2

        # player must actually be near trap
        if abs(player_x - center) > 180:
            return

        key = f"{level}:{index}"

        # spikes stay up briefly
        traps[key] = (
            time.monotonic() + 1.35
        )


def client_thread(client, pid):

    buffer = ""

    try:

        send(
            client,
            {
                "type": "welcome",
                "id": pid
            }
        )

        while True:

            data = client.recv(8192)

            if not data:
                break

            buffer += data.decode()

            while "\n" in buffer:

                line, buffer = buffer.split(
                    "\n",
                    1
                )

                if not line:
                    continue

                try:
                    packet = json.loads(line)
                except:
                    continue

                if packet.get("type") == "player":

                    try:

                        x = float(
                            packet.get(
                                "x",
                                60
                            )
                        )

                        y = float(
                            packet.get(
                                "y",
                                490
                            )
                        )

                        level = int(
                            packet.get(
                                "level",
                                1
                            )
                        )

                    except:
                        continue

                    with lock:

                        players[str(pid)] = {
                            "x": max(
                                -100,
                                min(1200, x)
                            ),
                            "y": max(
                                -300,
                                min(900, y)
                            ),
                            "level": max(
                                1,
                                min(3, level)
                            )
                        }

                elif packet.get(
                    "type"
                ) == "trigger_trap":

                    trigger_trap(
                        pid,
                        int(packet.get("level", 1)),
                        int(packet.get("index", 0))
                    )

    except Exception as e:
        print("Player error:", e)

    finally:

        with lock:
            clients.pop(pid, None)
            players.pop(str(pid), None)

        try:
            client.close()
        except:
            pass

        print("Player", pid, "left")


def broadcast_loop():

    while True:
        broadcast()
        time.sleep(0.05)


server = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

server.bind(
    (HOST, PORT)
)

server.listen(50)

print()
print("==============================")
print("    DARK RUNNER ONLINE")
print("==============================")
print("Server running...")
print("Port:", PORT)
print()

threading.Thread(
    target=broadcast_loop,
    daemon=True
).start()


while True:

    client, address = server.accept()

    with lock:

        pid = next_id
        next_id += 1

        clients[pid] = client

        players[str(pid)] = {
            "x": 60,
            "y": 490,
            "level": 1
        }

    print(
        "Player",
        pid,
        "connected:",
        address
    )

    threading.Thread(
        target=client_thread,
        args=(client, pid),
        daemon=True
    ).start()