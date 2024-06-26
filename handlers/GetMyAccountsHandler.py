from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.tables import *
from handlers.AbstractHandler import AbstractHandler
from web.PlatfeNotifier import PlatfeNotifier


class GetMyAccountsHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "get_my_accounts"

    async def handle(self, c, jsn: dict):
        try:
            validate(jsn.get("data"), {
                "type": "object",
                "required": ["$destination"],
                "properties": {
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
            t = {a.name: str(a.balance) + (await PlatfeCurrencies.get_by_id(session, a.currency_id)).short_name for a in await PlatfeAccounts.get_all_user_accounts(session, await PlatfeUser.get_by_id(session, c.user_id))}
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], t)
