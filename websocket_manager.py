from typing import Dict, List, Optional
from fastapi import WebSocket
import uuid

class ConnectionManager:
    def __init__(self):
        # Match ID -> List of active WebSockets
        self.active_matches: Dict[str, List[WebSocket]] = {}
        # Queue of waiting players: dict of user_id -> WebSocket
        self.waiting_queue: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, match_id: str):
        await websocket.accept()
        if match_id not in self.active_matches:
            self.active_matches[match_id] = []
        self.active_matches[match_id].append(websocket)

    def disconnect(self, websocket: WebSocket, match_id: str):
        if match_id in self.active_matches:
            if websocket in self.active_matches[match_id]:
                self.active_matches[match_id].remove(websocket)
            if not self.active_matches[match_id]:
                del self.active_matches[match_id]

    async def broadcast_to_match(self, match_id: str, message: dict):
        """Broadcasts a JSON message to all players in a match."""
        if match_id in self.active_matches:
            for connection in self.active_matches[match_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def join_matchmaking(self, websocket: WebSocket, user_id: str) -> Optional[tuple[str, str, WebSocket]]:
        """
        Adds a player to the queue. If another player is waiting, pairs them up and returns
        (match_id, opponent_id, opponent_ws)
        """
        if self.waiting_queue:
            # Pop the first waiting player
            opponent_id, opponent_ws = self.waiting_queue.popitem()
            if opponent_id == user_id:
                # Same player reconnected, put them back
                self.waiting_queue[user_id] = websocket
                return None
            
            match_id = str(uuid.uuid4())
            return match_id, opponent_id, opponent_ws
        else:
            self.waiting_queue[user_id] = websocket
            return None

manager = ConnectionManager()
