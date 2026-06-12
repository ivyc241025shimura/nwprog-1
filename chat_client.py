```python
import asyncio
import json
import websockets

SERVER_URI = "ws://localhost:8765"


def print_board(board):

    print("\n")

    for i in range(16):

        value = board[i]

        if value is None:
            cell = f"{i:2}"
        else:
            cell = f" {value}"

        print(cell, end=" ")

        if (i + 1) % 4 == 0:
            print()

    print()


async def play():

    my_role = None

    try:

        async with websockets.connect(SERVER_URI) as ws:

            print("サーバーへ接続しました")

            while True:

                raw = await ws.recv()

                msg = json.loads(raw)

                msg_type = msg["type"]

                if msg_type == "assigned_role":

                    my_role = msg["role"]

                    print(f"あなたは {my_role}")

                elif msg_type == "game_start":

                    print("\nゲーム開始")

                    print_board(msg["board"])

                    print("スコア")
                    print(msg["scores"])

                    if msg["turn"] == my_role:

                        index = int(
                            input("めくるカード番号 > ")
                        )

                        await ws.send(json.dumps({
                            "type": "flip",
                            "index": index
                        }))

                elif msg_type == "board_update":

                    print_board(msg["board"])

                    print("スコア")
                    print(msg["scores"])

                    print("現在の手番")
                    print(msg["turn"])

                    if msg["turn"] == my_role:

                        index = int(
                            input("めくるカード番号 > ")
                        )

                        await ws.send(json.dumps({
                            "type": "flip",
                            "index": index
                        }))

                elif msg_type == "pair_found":

                    print("\nペア成立！")

                    print_board(msg["board"])

                    print("スコア")
                    print(msg["scores"])

                elif msg_type == "game_over":

                    print("\nゲーム終了")

                    print("最終スコア")
                    print(msg["scores"])

                    winner = msg["winner"]

                    if winner == "draw":
                        print("引き分け")
                    elif winner == my_role:
                        print("あなたの勝ち！")
                    else:
                        print("あなたの負け")

                    break

                elif msg_type == "error":

                    print("エラー")
                    print(msg["message"])

    except ConnectionRefusedError:

        print("サーバーに接続できません")

    except websockets.exceptions.ConnectionClosed:

        print("接続が切断されました")


if __name__ == "__main__":
    asyncio.run(play())
```
