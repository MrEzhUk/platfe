from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.statuses import BOX_SIDED_CREATION_STATUSES
from db.tables import PlatfeUser, PlatfeAccounts, PlatfeBothSidedBox, PlatfeWorlds
from handlers.AbstractHandler import AbstractHandler

from web.PlatfeNotifier import PlatfeNotifier


class AddPrefixToPlayerHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "box_register_handler"

    async def handle(self, c, jsn):
        try:
            validate(jsn.get("data"), {
                "type": "object",
                "required": [
                    "$x", "$y", "$z", "$world",
                    "$acc_name", "$minecraft_item", "$minecraft_tag",
                    "$count", "$buy", "$sell"
                ],
                "properties": {
                    "$x": {
                        "type": "string"
                    },
                    "$y": {
                        "type": "string"
                    },
                    "$z": {
                        "type": "string"
                    },
                    "$world": {
                        "type": "string"
                    },
                    "$acc_name": {
                        "type": "string"
                    },
                    "$minecraft_item": {
                        "type": "string"
                    },
                    "$minecraft_tag": {
                        "type": "string"
                    },
                    "$count": {
                        "type": "string"
                    },
                    "$buy": {
                        "type": "string"
                    },
                    "$sell": {
                        "type": "string"
                    }
                }
            })
        except ValidationError:
            return

        if not c.authed:
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "You don't authed."})
            return

        data = jsn["data"]

        async with session_maker() as session:
            usr = await PlatfeUser.get_by_id(session, c.user_id)
            acc = await PlatfeAccounts.get_by_name(session, data["$acc_name"])
            if acc is None:
                await PlatfeNotifier.send(c, data["$destination"], {"message": "Account don't found."})
                return

            if usr not in acc.get_owners(session):
                await PlatfeNotifier.send(c, data["$destination"], {"message": "Account don't your."})
                return

            world = await PlatfeWorlds.get_world(session, data["$world"])

            if world is None:
                await PlatfeNotifier.send(c, data["$destination"], {"message": "Undefined world."})
                return
            try:
                x, y, z, count, buy, sell = list(map(int, [
                    data["$x"], data["$y"], data["$z"],
                    data["$count"],
                    data["$buy"], data["$sell"]
                ]))
            except:
                await PlatfeNotifier.send(c, data["$destination"], {"message": "Error request."})
                return

            r = await PlatfeBothSidedBox.create(
                session,
                x, y, z, world,
                acc, await PlatfeAccounts.get_by_id(session, 1),
                data["$minecraft_item"], data["$minecraft_tag"],
                count, buy, sell
            )
            if r < 0:
                await PlatfeNotifier.send(c, data["$destination"], {"message": BOX_SIDED_CREATION_STATUSES[r]})
                await session.rollback()
                return
            else:
                await PlatfeNotifier.send(c, data["$destination"], {"message": BOX_SIDED_CREATION_STATUSES[r]})
                await session.commit()
                return