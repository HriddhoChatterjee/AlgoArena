// js/ws.js
const WS_BASE_URL = 'ws://localhost:8000'; // Change for production

class ArenaWebSocket {
    constructor(matchId, userId) {
        this.matchId = matchId;
        this.userId = userId;
        this.ws = null;
        this.onMessage = null;
    }

    connect() {
        if (!this.userId) return;
        this.ws = new WebSocket(`${WS_BASE_URL}/ws/arena/${this.matchId}/${this.userId}`);
        
        this.ws.onopen = () => {
            console.log(`Connected to WS: ${this.matchId}`);
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (this.onMessage) this.onMessage(data);
            } catch (e) {
                console.error("WS Parse error", e);
            }
        };

        this.ws.onclose = () => {
            console.log("WS Disconnected");
        };
        
        this.ws.onerror = (err) => {
            console.error("WS Error", err);
        };
    }

    send(messageObj) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(messageObj));
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}
