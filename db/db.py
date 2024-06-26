from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncConnection
from tables import Base

engine: AsyncEngine = create_async_engine('mysql+aiomysql://user:password@ip3306/platfe', pool_recycle=20)
session_maker = async_sessionmaker(engine)


async def init_db():
    conn: AsyncConnection
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)