import makeWASocket, { useMultiFileAuthState, DisconnectReason, cleanMessage } from '@whiskeysockets/baileys';
import qrcode, { error } from 'qrcode-terminal';


async function connectToWterm() {


    // Configuration and session
    const {state,saveCreds} = await useMultiFileAuthState ('auth_info_baileys');

    // Initialize W socket
    const sock = makeWASocket.default({
        auth= state,
        printQRInTerminal= false,
    });


    // Listen on connection update
    sock.ev.on('connection.update', (update) => {
        const {connection,lastDisconnect,qr} = update;

        // Check QRCode
        if (qr) {
            console.clear();
            console.log("---------------");
            console.log("# Scan QRCode #");
            console.log("---------------");
            qrcode.generate(qr, {small:true});
        }

        // Check connection state changes
        if (connection === 'close') {

            //check why is it closed
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;

            console.log('Connection closed because of :',lastDisconnect?.error,' reconnect',shouldReconnect);

            if (shouldReconnect) {
                console.log("Trying to reconnect...");
                connectToWterm();
            }
        } else if (connection === 'open') {
            console.clear();
            console.log("You're now connected to WTerm");
        }
    });


    // Listen to inbox
    sock.ev.on('message.upsert', async (message) => {
        console.log('--- New message ---');
        console.log(JSON.stringify(message,null,2));
    });

    // Save credentials
    sock.ev.on('creds.update', saveCreds);
};

connectToWterm().catch( err => {
    console.error("An error occured : ", err)
})
