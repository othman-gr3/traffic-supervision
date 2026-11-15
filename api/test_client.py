"""Quick WebSocket test: start a 10-second simulation and print the first 3 metrics frames."""
import asyncio, json
import websockets
import urllib.request

# 1. Start simulation
req = urllib.request.Request(
    "http://localhost:8000/start",
    data=b'{"controller":"smart","seed":42,"duration":10}',
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as r:
    print("POST /start:", json.loads(r.read()))

# 2. Connect WebSocket and print first 3 frames
async def read_ws():
    async with websockets.connect("ws://localhost:8000/ws/metrics") as ws:
        for _ in range(3):
            msg = await asyncio.wait_for(ws.recv(), timeout=15)
            data = json.loads(msg)
            if "heartbeat" in data:
                print("heartbeat:", data)
                continue
            print(f"t={data['time']:>4}s  queues={[r['queue'] for r in data['roads']]}  light={data['light']['axis']}/{data['light']['stage']}")

asyncio.run(read_ws())
print("WebSocket test passed ✓")
