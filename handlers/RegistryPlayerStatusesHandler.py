from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.tables import PlatfeNicknameStatus
from handlers.AbstractHandler import AbstractHandler
from utils import registry_statuses
from web.PlatfeNotifier import PlatfeNotifier


class RegistryPlayerStatusesHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "player_statuses_registry"

    async def handle(self, c, jsn: dict):
        try:
            validate(jsn.get("data"), {
                "type": "object",
                "required": ["$hash", "$destination"],
                "properties": {
                    "$hash": {
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

        async with session_maker() as session:
            hsh = registry_statuses.get("status")
            if jsn["data"]["$hash"] == str(hsh):
                return

            p = {}
            statuses = [o for o in await PlatfeNicknameStatus.get_all_statuses(session)]
            for s in statuses:
                pp = await (await PlatfeNicknameStatus.get_by_nickname(session, s.nickname)).get_prefixes(session)
                for i in range(len(pp)):
                    p[s.nickname + '_' + str(i)] = chr(pp[i].r) + chr(pp[i].g) + chr(pp[i].b) + pp[i].body
            p["$hash"] = hsh
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], p)
