import os
import json
from passlib import pwd


class UpdateHashRegistry:
    def __init__(self, filename: str):
        self.filename = filename
        self.path = "tmp/" + self.filename

    def create_files(self):

        if not os.path.exists("tmp/"):
            os.mkdir("tmp/")

        if not os.path.exists(self.path):
            with open(self.path, "w") as fp:
                fp.write("{}")

    def update(self, key: str, value: str):
        self.create_files()
        data = {}
        with open(self.path) as fp:
            data = json.load(fp)

        data[key] = value
        with open(self.path, "w") as fp:
            json.dump(data, fp)

    def get(self, key: str):
        self.create_files()
        data = {}
        with open(self.path) as fp:
            data = json.load(fp)
        if data.get(key) is None:
            return self.change_to_random(key)
        else:
            return data[key]

    def change_to_random(self, key: str):
        p = pwd.genword(length=12)
        self.update(key, p)
        return p

