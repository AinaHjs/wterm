import makeWASocket, {useMultiFileAuthState, DisconnectReason} from "@whiskeysockets/baileys";
import { WebSocketServer } from "ws";
import pino from 'pino';


/**
 * - La première chose à faire c'est initialiser une connexion Websockets et gérer les connexions entrantes.
 * - 
 */

/** INITIALISATION DU WEBSOCKET POUR PYTHON ET NODE */
const wss = new WebSocketServer({port:8088});
console.log(`[+] The node server is listenning on port : 8088`)
let pythonClient = null;

/** Manage inbound connexion */
wss.on('connection', async (ws) => {
    console.log(`[+] Python client connected successfully...`);
    pythonClient = ws

    // On message
    ws.on('message', async (message) => {
        try {
            const parsed_message = JSON.parse(message); 
            
            if (parsed_message.action === 'SEND_MESSAGE' && parsed_message.to && parsed_message.text) {
                await sock.sendMessage(parsed_message.to, {text:parsed_message.text})
                console.log(`[+] Message sent to : ${parsed_message.to}`);
            }
        } catch (error) {
            console.error(`[!] An error occured : ${error}`);
        }
    });

    // On close
    ws.on('close', () => {
        console.log(`[-] Python client disconnected successfully...`);
        pythonClient = null;
    });

});

/** INITIALISATION DU WEBSOCKET WA AVEC BAILEYS */
const {state, saveCreds} = await useMultiFileAuthState('auth_info_baileys');

const sock = makeWASocket({
    auth: state,
    printQRInTerminal: true,
    logger: pino({level : 'silent'}),
})


