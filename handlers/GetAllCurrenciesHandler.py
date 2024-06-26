from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from db.db import session_maker
from db.tables import *
from handlers.AbstractHandler import AbstractHandler
from web.PlatfeNotifier import PlatfeNotifier


class GetAllCurrenciesHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "get_currencies"

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
            currencies = {c.name: c.short_name for c in await PlatfeCurrencies.get_all(session)}
            await PlatfeNotifier.send(c, jsn["data"]["$destination"], currencies)
