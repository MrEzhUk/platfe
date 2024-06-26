from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.tables import PlatfeUser, PlatfePrefix, PlatfeNicknameStatus
from handlers.AbstractHandler import AbstractHandler
from handlers.RegistryPlayerStatusesHandler import RegistryPlayerStatusesHandler
from utils import registry_prefixes, registry_statuses
from web.PlatfeNotifier import PlatfeNotifier


class ClearAllPrefixesHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "clear_all_prefixes"

    async def handle(self, c, jsn):
        try:
            validate(jsn.get("data"), {
                "type": "object",
                "required": ["$nickname", "$destination"],
                "properties": {
                    "$nickname": {
                        "type": "string"
                    },
                    "$destination": {
                        "type": "string"
                    }
                }
            })
        except ValidationError:
            print("!!!")
            return

        if not c.authed:
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "you don't authed."})
            return

        nickname = jsn["data"]["$nickname"]

        async with session_maker() as session:
            usr = await PlatfeUser.get_by_id(session, c.user_id)
            if not await usr.has_permission(session, "platfe.clear_all_prefixes"):
                print("not perms")
                return

            pns = await PlatfeNicknameStatus.get_by_nickname(session, nickname)
            if pns is None:
                await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "No nickname in db."})
                return

            for p in await pns.get_prefixes(session):
                await pns.del_prefix(session, p)
            await pns.delete(session)
            await session.commit()
            registry_statuses.change_to_random("status")
            await RegistryPlayerStatusesHandler().handle(c, {
                "data": {
                    "$hash": "-",
                    "$destination": "player_statuses_registry"
                }
            })

            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "Prefixes deleted!"})