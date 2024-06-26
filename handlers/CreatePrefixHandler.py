from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.tables import PlatfeUser, PlatfePrefix
from handlers.AbstractHandler import AbstractHandler
from handlers.RegistryPrefixesUpdateHandler import RegistryPrefixesUpdateHandler
from utils import registry_prefixes
from web.PlatfeNotifier import PlatfeNotifier
from web.connections import connections


class CreatePrefixHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "create_prefix"

    async def handle(self, c, jsn):
        try:
            validate(jsn.get("data"), {
                "type": "object",
                "required": ["$short_name", "$body", "$color", "$destination"],
                "properties": {
                    "$short_name": {
                        "type": "string"
                    },
                    "$color": {
                        "type": "string"
                    },
                    "$destination": {
                        "type": "string"
                    },
                    "$body": {
                        "type": "string"
                    }
                }
            })
        except ValidationError:
            return

        if not c.authed:
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "you don't authed."})
            return
        short_name = jsn["data"]["$short_name"]
        color = jsn["data"]["$color"]
        body = jsn["data"]["$body"]
        if len(short_name) > 24:
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "short_name > 24 symbols."})
            return

        if len(color) != 6:
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "hex_code != 6 symbols."})
            return

        if len(body) > 8:
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "body > 8 symbols."})
            return

        for cr in color:
            if not (ord("0") <= ord(cr) <= ord("f")):
                await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "color is not hex"})
                return

        async with session_maker() as session:
            usr = await PlatfeUser.get_by_id(session, c.user_id)
            if not await usr.has_permission(session, "platfe.create_prefix"):
                print("not perms")
                return

            await PlatfePrefix.create(session, short_name, int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16), body)
            await session.commit()
            registry_prefixes.change_to_random("status")
            for c_a in connections:
                await RegistryPrefixesUpdateHandler().handle(c_a, {
                    "data": {
                        "$hash": "-",
                        "$destination": "prefixes_registry"
                    }
                })
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "Prefix created!"})
