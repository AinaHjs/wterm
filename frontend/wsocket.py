import websockets
import asyncio


async def connect_to_server():
    uri = 'ws://localhost:8088'
    async with websockets.connect(uri) as ws:
        print('test')
        await asyncio.Future()

asyncio.run(connect_to_server())

