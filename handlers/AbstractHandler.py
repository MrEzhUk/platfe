import time


class AbstractHandler:

    def __init__(self):
        self.id = "AbstractHandler"

    def generate_response(self, c, jsn):
        c.refresh()
        return {
            "id": self.id,
            "timestamp": int(time.time()),
            "data": self.generate_data(jsn)
        }

    def get_id(self):
        return self.id

    def generate_data(self, jsn):
        return {}

    def handle(self, c, jsn):
        return self.generate_response(c, jsn)
