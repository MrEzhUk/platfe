from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.statuses import PAY_STATUS
from db.tables import PlatfeUser, PlatfeNicknameStatus, PlatfeAccounts
from handlers.AbstractHandler import AbstractHandler
from web.PlatfeNotifier import PlatfeNotifier


class GetPermissionHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "get_permissions"

    async def handle(self, c, jsn):
        try:
            validate(jsn.get("data"), {
                "type": "object",
                "required": ["$user_name", "$destination"],
                "properties": {
                    "$user_name": {
                        "type": "string"
                    },
                    "$destination": {
                        "type": "string"
                    }
                }
            })
        except ValidationError:
            return

        data = jsn["data"]
        destination = data["$destination"]

        if not c.authed:
            await PlatfeNotifier.send(c, destination, {"message": "Error you don't authed."})
            return

        async with session_maker() as session:
            usr = await PlatfeUser.get_by_id(session, c.user_id)
            if not await usr.has_permission(session, "platfe.get_permissions"):
                print("not perms")
                return

            e_user = await PlatfeUser.get_by_name(session, data["$user_name"])
            t = e_user.name + " perms:\n"
            for p in await e_user.get_all_permission(session):
                t += p.permission_string + '\n'

            t = t[:len(t)-1]
            await PlatfeNotifier.send(c, destination, {"message": t})
