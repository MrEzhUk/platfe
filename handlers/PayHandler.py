from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.statuses import PAY_STATUS
from db.tables import *
from handlers.AbstractHandler import AbstractHandler
from web.PlatfeNotifier import PlatfeNotifier


class PayHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "pay"

    async def handle(self, c, jsn):
        try:
            validate(jsn.get("data"), {
                "type": "object",
                "required": ["$acc1", "$acc2", "$count", "$destination"],
                "properties": {
                    "$acc1": {
                        "type": "string"
                    },
                    "$acc2": {
                        "type": "string"
                    },
                    "$count": {
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

        if not c.authed:
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], {"message": "you don't authed."})
            return

        async with session_maker() as session:
            usr = await PlatfeUser.get_by_id(session, c.user_id)
            acc1 = await PlatfeAccounts.get_by_name(session, data["$acc1"])
            acc2 = await PlatfeAccounts.get_by_name(session, data["$acc2"])
            count = int(data["$count"])

            if acc1 is None:
                await PlatfeNotifier.send(c, data["$destination"], {"message": "Error acc1 not found."})
                return

            if acc2 is None:
                await PlatfeNotifier.send(c, data["$destination"], {"message": "Error acc2 not found."})
                return

            s = await acc1.pay(session, usr, acc2, count)
            if s > 0:
                await PlatfeNotifier.send_to_users(list(await acc1.get_owners(session)) + list(await acc2.get_owners(session)), data["$destination"], {
                    "message": acc1.name + "->" + acc2.name + "[" + str(count) +
                    (await PlatfeCurrencies.get_by_id(session, acc1.currency_id)).short_name + "]"
                })
                await session.commit()
                s = 0
            else:
                await session.rollback()

            await PlatfeNotifier.send(c, data["$destination"], {"message": PAY_STATUS[s]})
