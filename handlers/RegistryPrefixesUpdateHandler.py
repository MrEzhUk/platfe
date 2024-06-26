import typing

from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.tables import PlatfePrefix
from handlers.AbstractHandler import AbstractHandler
from utils import registry_prefixes
from web.PlatfeNotifier import PlatfeNotifier


class RegistryPrefixesUpdateHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "prefixes_registry"

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
            hsh = registry_prefixes.get("status")
            if jsn["data"]["$hash"] == str(hsh):
                return

            p = {}
            pp: typing.List[PlatfePrefix] = await PlatfePrefix.get_all(session)
            for u in pp:
                p[u.short_name] = u.serialize_string()

            p["$hash"] = hsh
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], p)
