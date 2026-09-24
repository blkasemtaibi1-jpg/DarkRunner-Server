import socket
import threading
import json
import os


HOST = "0.0.0.0"

PORT = int(
    os.environ.get(
        "PORT",
        "5000"
    )
)


clients = {}
players = {}

next_id = 1

lock = threading.Lock()


# =========================================================
# SEND
# =========================================================

def send(client, data):

    try:

        message = json.dumps(data) + "\n"

        client.sendall(
            message.encode("utf-8")
        )

        return True

    except:

        return False


# =========================================================
# BROADCAST
# =========================================================

def broadcast():

    with lock:

        message = json.dumps({
            "type": "players",
            "players": players
        }) + "\n"

        data = message.encode("utf-8")

        disconnected = []

        for player_id, client in list(
            clients.items()
        ):

            try:

                client.sendall(data)

            except:

                disconnected.append(
                    player_id
                )

        for player_id in disconnected:

            clients.pop(
                player_id,
                None
            )

            players.pop(
                str(player_id),
                None
            )


# =========================================================
# CLIENT
# =========================================================

def handle_client(
    client,
    player_id
):

    buffer = ""

    try:

        send(
            client,
            {
                "type": "welcome",
                "id": player_id
            }
        )

        while True:

            data = client.recv(8192)

            if not data:
                break

            buffer += data.decode(
                "utf-8"
            )

            while "\n" in buffer:

                line, buffer = buffer.split(
                    "\n",
                    1
                )

                if not line:
                    continue

                try:

                    message = json.loads(
                        line
                    )

                except:

                    continue

                if message.get(
                    "type"
                ) != "update":

                    continue

                x = float(
                    message.get(
                        "x",
                        100
                    )
                )

                y = float(
                    message.get(
                        "y",
                        490
                    )
                )

                level = int(
                    message.get(
                        "level",
                        1
                    )
                )

                state = message.get(
                    "state",
                    "playing"
                )

                # Basic limits

                x = max(
                    -100,
                    min(
                        1200,
                        x
                    )
                )

                y = max(
                    -300,
                    min(
                        900,
                        y
                    )
                )

                level = max(
                    1,
                    min(
                        3,
                        level
                    )
                )

                with lock:

                    players[
                        str(player_id)
                    ] = {

                        "x": x,

                        "y": y,

                        "level": level,

                        "state": state
                    }

                broadcast()

    except Exception as error:

        print(
            "Player error:",
            error
        )

    finally:

        with lock:

            clients.pop(
                player_id,
                None
            )

            players.pop(
                str(player_id),
                None
            )

        broadcast()

        try:

            client.close()

        except:

            pass

        print(
            "Player",
            player_id,
            "disconnected"
        )


# =========================================================
# SERVER
# =========================================================

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
print("================================")
print("       DARK RUNNER ONLINE")
print("================================")
print()
print("Server is running.")
print("Port:", PORT)
print()


while True:

    client, address = server.accept()

    with lock:

        player_id = next_id

        next_id += 1

        clients[player_id] = client

        players[
            str(player_id)
        ] = {

            "x": 80,

            "y": 490,

            "level": 1,

            "state": "playing"
        }

    print(
        "Player",
        player_id,
        "connected:",
        address
    )

    threading.Thread(
        target=handle_client,
        args=(
            client,
            player_id
        ),
        daemon=True
    ).start()