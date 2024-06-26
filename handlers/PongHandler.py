from handlers.AbstractHandler import AbstractHandler


class PongHandler(AbstractHandler):
    def __init__(self):
        super().__init__()
        self.id = "pong"

    async def handle(self, c, jsn):
        c.refresh()
        return

