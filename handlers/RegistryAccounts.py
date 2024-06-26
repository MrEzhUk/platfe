from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.tables import PlatfeUser, PlatfeAccounts, PlatfeCurrencies
from handlers.AbstractHandler import AbstractHandler
from utils import registry_accounts
from web.PlatfeNotifier import PlatfeNotifier


class RegistryAccounts(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "accounts_registry"

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
            usr = await PlatfeUser.get_by_id(session, c.user_id)

            hsh = registry_accounts.get("status")
            if jsn["data"]["$hash"] == str(hsh):
                return

            p = {}
            acc_s = await PlatfeAccounts.get_all_accounts(session)

            for acc in acc_s:
                p[acc.name + '$' + (await PlatfeCurrencies.get_by_id(session, acc.currency_id)).short_name] = '$'.join([o.name for o in await acc.get_owners(session)])

            p["$hash"] = hsh
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], p)
