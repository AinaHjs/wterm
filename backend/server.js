import makeWASocket, {useMultiFileAuthState, DisconnectReason} from "@whiskeysockets/baileys";
import { WebSocketServer } from "ws";
import pino from 'pino';
import QRCode from 'qrcode-terminal';


/**
 * - La première chose à faire c'est initialiser une connexion Websockets et gérer les connexions entrantes.
 * - 
 */

/** INITIALISATION DES VARIABLES GLOBALES */
let pythonClient = null;
let sock = null;



/** INITIALISATION DU WEBSOCKET WA AVEC BAILEYS */
async function connectToWA() {
    const {state, saveCreds} = await useMultiFileAuthState('auth_info_baileys');

    sock = makeWASocket({
        auth: state,
        printQRInTerminal: false,
        logger: pino({level : 'silent'}),
    })

    /** Gérer les connnections */
    sock.ev.on('connection.update', (update) => {
        const {connection, lastDisconnect, qr} = update;

        if(qr && pythonClient) {
            pythonClient.send(JSON.stringify({
                type: "QR",
                data: qr
            }))
        }

        // Vérifier l'état de la connexion
        if (connection === 'open' && pythonClient) {
            console.log(`[+] Link to WA established...`);
            console.log(`[+] Trying to send the connexion status to the python app`)
            pythonClient.send(JSON.stringify({
                type: 'STATUS',
                data: 'CONNECTED'
            }))
        } else if (connection === 'close') {
            const need_to_reconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;

            if(need_to_reconnect) {
                console.log(`[-] Connection to WA was lost...`);
                console.log(`[+] Trying to reconnect...`)
                connectToWA();
            }
        }
    })

    /** Sauvegarde automatique des creds */
    sock.ev.on('creds.update',saveCreds);
}

/** INITIALISATION DU WEBSOCKET POUR PYTHON ET NODE */
function create_ws() {
    const wss = new WebSocketServer({port:8088});
    console.log(`[+] The node server is listenning on port : 8088`)

    /** Manage inbound connexion */
    wss.on('connection', async (ws) => {
        console.log(`[+] Python client connected successfully...`);
        pythonClient = ws
        connectToWA();

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
}


create_ws();


