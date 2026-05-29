import websockets
import asyncio
import qrcode
import json


async def connect_to_server():
    uri = 'ws://localhost:8088'

    # Se connecter au websocket génerer par le backend
    async with websockets.connect(uri) as ws:
        print(f"[+] Connected to the backend")

        while True:
            message = await ws.recv()
            data = json.loads(message)

            if (data['type'] == 'QR'):
                print(f"[+] Please scan QR code\n\n")
                
                # Afficher le code QR en utilisant le module qrcode
                qr = qrcode.QRCode()
                qr.add_data(data['data'])
                qr.make()
                qr.print_ascii()
            elif (data['type'] == 'STATUS'):
                print(f"[+] Status : {data['data']}")

asyncio.run(connect_to_server())