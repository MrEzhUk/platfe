import asyncio
import typing

from discord import User

from db.tables import PlatfeUser
from platfe_discord.bot import bot
from web.connections import connections

if typing.TYPE_CHECKING:
    from web.app import PlatfeConnection


class PlatfeNotifier:

    @staticmethod
    async def send_to_users(usr: typing.List[PlatfeUser], destination, data):
        ids = [u.id for u in usr]
        disids = [u.disid for u in usr]
        # Возможно стоит убрать дубликаты в ids и disids.
        cors = []
        c: PlatfeConnection
        for c in connections:
            if c.user_id in ids:
                cors.append(PlatfeNotifier.send(c, destination, data))
                ids.remove(c.user_id)
                disids.remove(c.didid)

        for d in disids:
            cors.append(PlatfeNotifier.send_to_discord(d, destination, data))

        await asyncio.gather(*cors)

    @staticmethod
    async def send(c: "PlatfeConnection", destination, data):
        try:
            await asyncio.gather(
                PlatfeNotifier.send_to_discord(c.didid, destination, data),
                PlatfeNotifier.send_to_connection(c, destination, data)
            )
        except Exception as e:
            print(e)

    @staticmethod
    async def send_to_discord(didid: typing.Optional[int], destination, data):
        if destination != "chat_notify":
            return

        if didid is not None:
            u: User | None = bot.get_user(didid)
            if u:
                await u.send(content=str(data.get("message")))

    @staticmethod
    async def send_to_connection(c: "PlatfeConnection", destination, data):
        try:
            await c.ws.send_json({
                "id": destination,
                "timestamp": 0,
                "data": data
            })
        except Exception as e:
            print(str(e))

    @staticmethod
    async def send_all(destination, data):
        await asyncio.gather(*[PlatfeNotifier.send(c, destination, data) for c in connections])
