from fastapi import WebSocket
from typing import Dict

class Connection_Manager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f'User {user_id} connected via Websocket')

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f'User {user_id} disconnected from Websocket')

    async def send_message(self, message: str, user_id: int):
        if(user_id in self.active_connections):
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)

manager = Connection_Manager()