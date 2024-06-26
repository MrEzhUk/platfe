import traceback

from jsonschema.exceptions import ValidationError

from db.db import session_maker
from db.tables import PlatfeUser
from handlers.AbstractHandler import AbstractHandler
from jsonschema import validate

from web.PlatfeNotifier import PlatfeNotifier


class LoginHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "login"

    async def handle(self, c, jsn: dict):
        try:
            validate(jsn.get("data"), {
                "type": "object",
                "required": ["$nickname", "$token", "$destination"],
                "properties": {
                    "$nickname": {
                        "type": "string",
                        "maxLength": 32,
                        "mixLength": 1
                    },
                    "$token": {
                        "type": "string",
                        "maxLength": 200,
                        "minLength": 200
                    },
                    "$destination": {
                        "type": "string"
                    }
                }
            })
        except ValidationError:
            # traceback.print_exc()
            c.authed = False
            destination = jsn["data"].get("$destination")
            if not destination:
                destination = "chat_notify"
            await PlatfeNotifier.send(c, destination, {
                "message": "Auth error[0]."
            })
            return

        async with session_maker() as session:
            authed = await PlatfeUser.check_auth(session, jsn["data"]["$nickname"], jsn["data"]["$token"])
            if authed:
                c.user_id = authed.id
                c.didid = authed.disid
                c.authed = True
                await PlatfeNotifier.send(c, jsn["data"]["$destination"], {
                    "message": "You authed!"
                })
                await PlatfeNotifier.send(c, "login", {
                    "status": "1"
                })

            else:
                c.authed = False
                await PlatfeNotifier.send(c, jsn["data"]["$destination"], {
                    "message": "Auth error[1]."
                })
                await PlatfeNotifier.send(c, "login", {
                    "status": "0"
                })


