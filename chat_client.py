#!/usr/bin/env python3
"""WebSocket チャットクライアント。サーバへ接続し、ユーザ入力を送信し、サーバからのメッセージを受信して表示する。"""

import argparse
import asyncio
import json

import websockets


# クライアント側のコードは、サーバからのメッセージを受信するタスクと、ユーザ入力を送信するタスクの2つを並行して動かす必要がある。
def parse_args() -> argparse.Namespace:
    # コマンドライン引数を処理する。--url を受け付ける。
    parser = argparse.ArgumentParser(description="WebSocketチャットクライアント")
    parser.add_argument(
        "--url",
        default="ws://127.0.0.1:8765",
        help="接続先URL (例: ws://172.16.5.25:8765)",
    )
    return parser.parse_args()


# サーバからのメッセージを受信するタスク。受信したメッセージは内容に応じて表示する。
async def receive_messages(ws) -> None:
    # サーバからのメッセージを受信するループ。サーバからのメッセージは type フィールドで種類を判別する。
    async for raw in ws:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(raw)
            continue

        # type フィールドでメッセージの種類を判別する。
        event_type = data.get("type")

        # type に応じて表示する内容を変える。type が不明な場合は生のデータを表示する。
        if event_type == "chat":
            print(f"[{data.get('name', 'unknown')}] {data.get('text', '')}")
        # system イベントはシステムメッセージで、これを受け取ったときは [system] プレフィックスをつけて表示する。
        elif event_type == "system":
            print(f"[system] {data.get('text', '')}")
        # error イベントはエラーメッセージで、これを受け取ったときは [error] プレフィックスをつけて表示する。
        elif event_type == "error":
            print(f"[error] {data.get('text', '')}")
        # それ以外の type の場合は生のデータを表示する。
        else:
            print(data)

# ユーザ入力を送信するタスク。ユーザが入力したテキストをサーバへ送信する。ユーザが /quit と入力したときは接続を閉じて終了する。
async def send_messages(ws) -> None:
    while True:
        # ユーザ入力を非同期に受け取る。input() はブロッキング関数なので、asyncio.to_thread() を使って別スレッドで実行する。
        text = await asyncio.to_thread(input, "")
        text = text.strip()

        # 入力が空の場合は無視する。
        if not text:
            continue

        # ユーザが /quit と入力したときは接続を閉じて終了する。
        if text == "/quit":
            await ws.close()
            return

        # ユーザが入力したテキストをサーバへ送信する。送信するデータは type フィールドと text フィールドを持つJSONオブジェクトにする。
        payload = {"type": "chat", "text": text}
        await ws.send(json.dumps(payload, ensure_ascii=False))


# メイン関数。コマンドライン引数を処理し、WebSocketサーバへ接続する。接続後は receive_messages タスクと send_messages タスクを並行して実行する。
async def main() -> None:
    args = parse_args()
    name = input("名前を入力してください: ").strip() or "anonymous"

    # WebSocketサーバへ接続する。接続が成功したら、まず join イベントを送信して自分の名前をサーバへ伝える。
    async with websockets.connect(args.url) as ws:
        join_payload = {"type": "join", "name": name}
        await ws.send(json.dumps(join_payload, ensure_ascii=False))

        # サーバからのメッセージを受信するタスクと、ユーザ入力を送信するタスクの2つを並行して動かす。どちらかのタスクが終了したときはもう一方のタスクもキャンセルして終了する。
        receiver = asyncio.create_task(receive_messages(ws))
        sender = asyncio.create_task(send_messages(ws))

        # どちらかのタスクが終了するまで待つ。どちらかのタスクが終了したときはもう一方のタスクもキャンセルして終了する。
        done, pending = await asyncio.wait(
            {receiver, sender},
            return_when=asyncio.FIRST_COMPLETED,
        )

        # どちらかのタスクが終了したときはもう一方のタスクもキャンセルして終了する。
        for task in pending:
            task.cancel()

        # タスクの例外を処理する。タスクが正常に終了した場合は何もしない。タスクが例外を発生させた場合は例外を再度発生させる。
        for task in done:
            if task.exception() is not None:
                raise task.exception()


if __name__ == "__main__":
    asyncio.run(main())
