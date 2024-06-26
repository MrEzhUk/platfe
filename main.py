import asyncio
from aiohttp import web

from db.db import init_db, session_maker
from platfe_discord.bot import start_bot
from web.app import init_func, checker


async def test_db():
    async with session_maker() as session:
        await session.commit()


async def main():
    await asyncio.gather(
        init_db(),
        web._run_app(init_func(), host="0.0.0.0", port=8381),
        checker(),
        start_bot()
    )


if __name__ == "__main__":
    asyncio.run(main())
