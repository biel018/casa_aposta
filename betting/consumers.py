import json
from channels.generic.websocket import AsyncWebsocketConsumer


class OddsConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer para atualização de odds em tempo real."""

    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs'].get('event_id', 'all')
        self.room_group_name = f'odds_{self.event_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Recebe mensagem do WebSocket."""
        pass

    async def odds_update(self, event):
        """Envia atualização de odds para o cliente."""
        await self.send(text_data=json.dumps({
            'type': 'odds_update',
            'data': event['data'],
        }))

    async def score_update(self, event):
        """Envia atualização de placar para o cliente."""
        await self.send(text_data=json.dumps({
            'type': 'score_update',
            'data': event['data'],
        }))
