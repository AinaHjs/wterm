import websockets
import asyncio
import qrcode
import json
import threading
import cmd


class WTerminal (cmd.Cmd):
    intro = """ Welcome to WTerminal """
    prompt = "wterminal >_ :"

    def __init__(self):
        super().__init__()
        self.ws = None
        self.loop = asyncio.new_event_loop()
        self.net_threading = threading.Thread(
            target=self.start_net_loop, daemon=True
        )
        self.net_threading.start()

    def start_net_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_to_backend)

    async def connect_to_backend(self):
        uri = 'ws://localhost:8088'

        # Se connecter au websocket génerer par le backend
        async with websockets.connect(uri) as ws:
            print("[+] Connected to the backend")

            while True:
                try:
                    message = await ws.recv()
                    data = json.loads(message)

                    if (data['type'] == 'QR'):
                        print("[+] Please scan QR code\n\n")
                        
                        # Afficher le code QR en utilisant le module qrcode
                        qr = qrcode.QRCode()
                        qr.add_data(data['data'])
                        qr.make()
                        qr.print_ascii()
                    elif (data['type'] == 'STATUS'):
                        print(f"[+] Status : {data['data']}")
                except Exception as e:
                    self.ws = None
                    asyncio.sleep(2)
                    print(f"[!] Error occured : {e}")

    def do_chats(self, arg):
        print("[+] List of chats : ")
    
    def do_read(self, arg):

        if not arg:
            print("[!] Syntax error : ")
            return



asyncio.run(connect_to_backend())