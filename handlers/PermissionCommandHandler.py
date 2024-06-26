from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.statuses import PAY_STATUS
from db.tables import PlatfeUser, PlatfeNicknameStatus, PlatfeAccounts
from handlers.AbstractHandler import AbstractHandler
from web.PlatfeNotifier import PlatfeNotifier


class PermissionHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "permission"

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
            if not await usr.has_permission(session, "platfe.change_permissions"):
                print("not perms")
                return

            e_user = await PlatfeUser.get_by_name(session, data["$user_name"])

            for i, j in data.items():
                if i[:3] == "add":
                    e_user.add_permission(session, j)
                elif i[:3] == "del":
                    e_user.del_permission(session, j)

            await session.commit()
            await PlatfeNotifier.send(c, destination, {"message": "Permission changed"})
