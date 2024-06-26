import asyncio
import json
import typing

import aiohttp
from aiohttp import web
from datetime import datetime

from handlers.AbstractHandler import AbstractHandler
from handlers import PongHandler, LoginHandler, CreatePrefixHandler, RegistryPrefixesUpdateHandler, \
    GetAllCurrenciesHandler, GetMyAccountsHandler, PayHandler, GetPermissionHandler, RegistryPlayerStatusesHandler, \
    AddPrefixToPlayerHandler, ClearAllPrefixesHandler, RegistryAccounts
from web.connections import connections

registered_handlers: typing.List[AbstractHandler] = [
    PongHandler.PongHandler(),
    LoginHandler.LoginHandler(),
    CreatePrefixHandler.CreatePrefixHandler(),
    ClearAllPrefixesHandler.ClearAllPrefixesHandler(),
    RegistryPrefixesUpdateHandler.RegistryPrefixesUpdateHandler(),
    RegistryPlayerStatusesHandler.RegistryPlayerStatusesHandler(),
    RegistryAccounts.RegistryAccounts(),
    AddPrefixToPlayerHandler.AddPrefixToPlayerHandler(),
    GetAllCurrenciesHandler.GetAllCurrenciesHandler(),
    GetMyAccountsHandler.GetMyAccountsHandler(),
    PayHandler.PayHandler(),
    GetPermissionHandler.GetPermissionHandler()
]


CHECK_TIME = 20


class PlatfeConnection:
    ws: web.WebSocketResponse
    last_check_time: datetime
    mark: bool
    authed: bool
    user_id: typing.Optional[int]
    didid: typing.Optional[int]

    def __init__(self, ws: web.WebSocketResponse):
        self.ws = ws
        self.last_check_time = datetime.now()
        self.mark = False
        self.authed = False
        self.user_id = None
        self.didid = None

    async def check_active(self):
        if self.mark:
            await self.ws.close()
        else:
            await self.ws.send_json({
                "id": "ping",
                "data": {},
                "timestamp": 0
            })

            self.last_check_time = datetime.now()
            self.mark = True

    def refresh(self):
        self.mark = False


async def checker():
    while 1:
        for i in range(len(connections)):
            await connections[i].check_active()

        await asyncio.sleep(CHECK_TIME)


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    try:
        await ws.prepare(request)

        c = PlatfeConnection(ws)
        connections.append(c)

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                jsn = json.loads(msg.data)
                if jsn.get("id") is None:
                    continue

                for handler in registered_handlers:
                    if jsn["id"] == handler.get_id():
                        await handler.handle(c, jsn)

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())

        print('websocket connection closed')
        connections.remove(c)

        return ws
    except Exception as e:
        print(str(e))


def init_func():
    app = web.Application()
    app.add_routes([web.get('/ws', websocket_handler)])
    return app



