import websockets  # Pour la gestion du websocket
import asyncio  # Pour les fonctions asynchrone
import qrcode  # Pour manipuler les QRCode
import json  # Pour les traitements JSON
import threading  # Pour la gestion des threads
import cmd  # Pour la création d'un CLI
import os  # Pour intéragir avec le système
import subprocess  # Pour le lancement d'une commande system
import getpass  # Pour récupérer le nome d'utilisateur


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
    USER = getpass.getuser()
    prompt = f"┌──({USER}㉿wterminal)-[~]\n└─$ "

    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.contact_file = os.path.join(self.current_dir, "contacts.json")
        self.message_folder_path = os.path.join(self.current_dir, "Messages")
        self.ws = None
        self.loop = asyncio.new_event_loop()
        self.net_threading = None
        self.qr_locked = False
        self.contacts = self.load_contacts()
        self.create_m_folder()

    # Create message folder
    def create_m_folder(self):
        os.makedirs(self.message_folder_path, exist_ok=True)

    """ IMPLEMENT CONTACT SYSTEM """

    # Load contact
    def load_contacts(self):
        if os.path.exists(self.contact_file):
            try:
                with open(self.contact_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"\n[!] Can't read contact : {e}")
        return {}

    # Save contact
    def save_contact(self):
        try:
            with open(self.contact_file, "w", encoding="utf-8") as f:
                # Write change in the file, f or contact_file
                json.dump(self.contacts, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"\n[!] Error occured when trying to save : {e}")

    # Get name from id
    def get_name_from_id(self, sender_id):
        for aliase, jID in self.contacts.items():
            if jID == sender_id:
                return f"{aliase.upper()}"
        return sender_id

    """ CONNECT TO THE BACKEND """

    # Start network loop using asyncio
    def start_net_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_to_backend())

    # Connect to the back end using websocket
    async def connect_to_backend(self):
        uri = "ws://localhost:8088"

        try:
            # Connect to websocket
            self.ws = await websockets.connect(uri)
            print("\n[-] The app is now connected to the backend\n")

            while True:
                try:
                    # Listen to inbound message
                    message = await self.ws.recv()
                    data = json.loads(message)

                    # Check the type of the message
                    if data["type"] == "QR":
                        if self.qr_locked:
                            return

                        # Only print one QRCode on the screen
                        self.qr_locked = True
                        print("\n[+] Please scan QR code\n")

                        # Draw QRCode usin qrcode module
                        qr = qrcode.QRCode(border=1)
                        qr.add_data(data["data"])
                        qr.make(fit=True)
                        qr.print_ascii(invert=False)

                    elif data["type"] == "STATUS":
                        print(f"[+] Status : {data['data']}")

                except Exception as e:
                    print(f"\n[!] Error occured : {e}\n")
                    break

        except Exception as e:
            print(f"\n[-] Connection failed : {e}")

        # Clean and reconnect when an error is occured
        await self.clean_and_reconnect()

    async def clean_and_reconnect(self):
        if self.ws:
            await self.ws.close()
        self.ws = None
        await asyncio.sleep(2)
        print("[+] Reconnecting to the backend...")
        await self.connect_to_backend()

    # Alert for new message
    async def alert_for_new_message(self):
        try:
            async for message in self.ws:
                data = json.loads(message)

                if data.get["event"] == "NEW_MESSAGE":
                    user_name = data["sender_name"]
                    user_id = data["sender_id"]
                    text = data["text"]
                    date = data["date"]

                    print(f"""
                    New message\n
                    >>> {date} : {user_name} : {user_id}
                    >>> {text}
                    """)
                    print(self.prompt, end="", flush=True)

        except Exception as e:
            print(f"\n[!] Error occured : {e}\n")

    """ TERMINAL IMPLEMENTATION FOR FRONT END """

    # List of message or contact
    def do_Show(self, arg):
        # Create a list of argument by using split() method
        commandSpliter = arg.split(" ", 1)
        command = commandSpliter[0]
        # Check if syntax is correct or not
        if len(commandSpliter) < 1:
            print("\n[!] Syntax error : Try Show message or Show contact instead.")
        # Show result depending on what user
        # want me do show. If this is a message or a contact.
        if command == "message" or command == "Message":
            print("Voici la liste de vos messages.")
        elif command == "Contacts" or command == "contacts":
            print("Voici la liste de vos contacts.")
        elif command == "Chats" or command == "chats":
            print("Voici la liste de vos conversation")
        else:
            return

    # Add contact
    def do_Add(self, arg):
        # Creat a list of argument by using split() method
        commandSpliter = arg.split(" ", 1)
        user_name, user_jid = commandSpliter[0], commandSpliter[1]
        newUser_message_file_path = os.path.join(self.message_folder_path, f"{user_name}.txt")
        # Check if the syntax is correct or not.
        if len(commandSpliter) < 2:
            print("\n[!] Syntax error : Try Add name jid instead.")
            return
        # Add key-value and save using save_contact() methode
        self.contacts[user_name] = user_jid
        self.save_contact()
        # Create the message file for the new user added
        with open(newUser_message_file_path, "w", encoding="utf-8") as f:
            pass

    # Connect to the backend
    def do_Connect(self, arg):
        try:
            self.net_threading = threading.Thread(
                target=self.start_net_loop, daemon=True
            )
            self.net_threading.start()
        except Exception as e:
            print(f"\n[!] Error occured : {e}\n")

    # Read message [read 1]
    def do_Read(self, arg):
        if not arg:
            print("\n[!] Syntax error : Try Read 1 instead.\n")
            return

        print("[-] Lists of message :")

    # Send message [send 1 salut]
    def do_Send(self, arg):
        parts = arg.split(" ", 1)

        if len(parts) < 2:
            print("\n[!] Syntax error : Try Send 1 message instead.\n")
            return

        target, message = parts[0], parts[1]

        if self.ws:
            messageObject = {
                "action": "SEND_MESSAGE",
                "to": target,
                "text": message,
            }

            asyncio.run_coroutine_threadsafe(
                self.ws.send(json.dumps(messageObject)), self.loop
            )
            print(f"[+] Message sent to {target}")

        else:
            print("\n[!] Error occured : Message not sent \n")

    # Exit WTerminal
    def do_Exit(self, arg):
        print("\n[-] Closing WTerminal ...\n")

        if self.ws:
            asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)

        # Stop cmd loop
        return True

    # Clear console
    def do_Clear(self, arg):
        # Clear console using ANSI command
        subprocess.run(
            'cls' if os.name == 'nt' else 'clear', shell=True
        )

    # Create an aliase for do_command
    do_Quit = do_Exit
    do_quit = do_Exit
    do_exit = do_Exit
    do_add = do_Add
    do_show = do_Show
    do_connect = do_Connect
    do_send = do_Send
    do_cls = do_Clear
    do_clear = do_Clear


if __name__ == "__main__":
    try:
        WTerminal().cmdloop()
    except KeyboardInterrupt:
        print("\n[-] WTerminal is closed\n")
