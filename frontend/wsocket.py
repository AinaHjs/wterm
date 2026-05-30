import websockets
import asyncio
import qrcode
import json
import threading
import cmd


class WTerminal(cmd.Cmd):
    intro = r""" 

██╗    ██╗████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗     
██║    ██║╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║     
██║ █╗ ██║   ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║     
██║███╗██║   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║     
╚███╔███╔╝   ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗
 ╚══╝╚══╝    ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝
                                                           
          
              [ WhatsApp Client for CLI ]  -  v1.0.0 (Alpha)

    
   +--------------------------------------------------------------------+
   |                                                                    |
   |           ---> Type /help to see available commands <---           |
   |                                                                    |
   +--------------------------------------------------------------------+

    """
    prompt = "WTerminal >_ : "

    def __init__(self):
        super().__init__()
        self.ws = None
        self.loop = asyncio.new_event_loop()
        self.net_threading = None
        self.qr_locked = False

    #
    def start_net_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_to_backend())

    # Connect to the back end using websocket
    async def connect_to_backend(self):
        uri = "ws://localhost:8088"

        # Se connecter au websocket génerer par le backend
        async with websockets.connect(uri) as ws:
            self.ws = ws
            print("\n\n[+] Connected to the backend")

            while True:
                try:
                    message = await ws.recv()
                    data = json.loads(message)

                    if data["type"] == "QR":

                        if self.qr_locked:
                            return

                        self.qr_locked = True

                        print("\n[+] Please scan QR code\n\n")

                        # Afficher le code QR en utilisant le module qrcode
                        qr = qrcode.QRCode(border=1)
                        qr.add_data(data["data"])
                        qr.make(fit=True)
                        qr.print_ascii(invert=False)
                    elif data["type"] == "STATUS":
                        print(f"[+] Status : {data['data']}")
                except Exception as e:
                    self.ws = None
                    await asyncio.sleep(2)
                    print(f"[!] Error occured : {e}")

    # Connect to backend
    def do_connect(self, arg):
        try:
            self.net_threading = threading.Thread(
                target=self.start_net_loop, daemon=True
            )
            self.net_threading.start()
        except Exception as e:
            print(f"[!] Error occured : {e}")

    # Chats as a list [chats]
    def do_chats(self, arg):
        print("[+] List of chats : ")

    # Read message [read 1]
    def do_read(self, arg):
        if not arg:
            print("[!] Syntax error : Try read 1 instead.")
            return

        print("[-] Lists of message :")

    # Send message [send 1 salut]
    def do_send(self, arg):
        parts = arg.split(" ", 1)

        if len(parts) < 2:
            print("[!] Syntax error : Try send 1 message instead.")
            return

        target, message = parts[0], parts[1]

        if self.ws:
            payload = {
                "action": "send_message",
                "to": target,
                "text": message,
            }

            asyncio.run_coroutine_threadsafe(
                self.ws.send(json.dumps(payload)), self.loop
            )
            print(f"[+] Message sent to {target}")
        else:
            print("[!] Error occured : Message not sent ")

    # Exit WTerminal
    def do_exit(self, arg):
        print("[-] Closing WTerminal ...")

        if self.ws:
            asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)

        # Stop cmd loop
        return True

    # Create an aliase for do_exit
    do_quit = do_exit


if __name__ == "__main__":
    try:
        WTerminal().cmdloop()
    except KeyboardInterrupt:
        print("[-] WTerminal is closed")
