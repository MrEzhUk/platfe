from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.tables import PlatfeUser, PlatfePrefix, PlatfeNicknameStatus
from handlers.AbstractHandler import AbstractHandler
from handlers.RegistryPlayerStatusesHandler import RegistryPlayerStatusesHandler
from utils import registry_prefixes, registry_statuses
from web.PlatfeNotifier import PlatfeNotifier
from web.connections import connections


class AddPrefixToPlayerHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "add_prefix_to_player"

    async def handle(self, c, jsn):
        try:
            validate(jsn.get("data"), {
                "type": "object",
                "required": ["$nickname", "$prefix", "$destination"],
                "properties": {
                    "$nickname": {
                        "type": "string"
                    },
                    "$prefix": {
                        "type": "string"
                    },
                    "$destination": {
                        "type": "string"
                    }
                }
            })
        except ValidationError:
            return

        if not c.authed:
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "you don't authed."})
            return

        nickname = jsn["data"]["$nickname"]
        prefix = jsn["data"]["$prefix"]

        async with session_maker() as session:
            usr = await PlatfeUser.get_by_id(session, c.user_id)
            if not await usr.has_permission(session, "platfe.add_prefix_to_player"):
                print("not perms")
                return
            pfx = await PlatfePrefix.get_by_short_name(session, prefix)
            if pfx is None:
                await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "Prefix not found!"})
                return

            pns = await PlatfeNicknameStatus.get_by_nickname(session, nickname)
            if pns is None:
                pns = await PlatfeNicknameStatus.create(session, nickname)

            await pns.add_prefix(session, pfx)
            await session.commit()
            registry_prefixes.change_to_random("status")
            registry_statuses.change_to_random("status")
            # можно сделать лучше
            r = RegistryPlayerStatusesHandler()
            for c_a in connections:
                await r.handle(c_a, {
                    "data": {
                        "$hash": "-",
                        "$destination": "player_statuses_registry"
                    }
                })
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "Prefix created!"})
