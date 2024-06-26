import asyncio
import datetime as dt
import typing

import sqlalchemy as sa

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.orm import Mapped
from passlib import pwd
import fnmatch as fn

create_string_param = {"collation": "utf8mb4_0900_as_cs"}


class Base(DeclarativeBase):
    pass


# Total per record: 296 byte
class PlatfeUser(Base):
    __tablename__ = "platfe_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    disid: Mapped[int] = mapped_column(sa.BigInteger)
    name: Mapped[str] = mapped_column(sa.String(32, **create_string_param))
    token: Mapped[str] = mapped_column(sa.String(200, **create_string_param))
    disabled: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    @staticmethod
    async def create(session: AsyncSession, disid, name):
        token = pwd.genword(length=200, charset="ascii_62")
        await session.execute(
            sa.insert(PlatfeUser)
            .values(disid=disid, name=name, token=token)
        )
        return token

    async def reset_token(self, session: AsyncSession):
        self.token = pwd.genword(length=200, charset="ascii_62")
        await session.execute(
            sa.update(PlatfeUser)
            .values(token=self.token)
            .where(PlatfeUser.id == self.id)
        )
        return self.token

    async def add_permission(self, session: AsyncSession, permission_string):
        await session.execute(
            sa.insert(PlatfePermissions)
            .values(user_id=self.id, permission_string=permission_string)
        )

    async def get_all_permission(self, session: AsyncSession):
        r = await session.execute(
            sa.select(PlatfePermissions)
            .where(PlatfePermissions.user_id == self.id)
        )
        return r.scalars().all()

    async def del_permission(self, session: AsyncSession, permission_string):
        await session.execute(
            sa.delete(PlatfePermissions)
            .where(sa.and_(
                PlatfePermissions.permission_string == permission_string,
                PlatfePermissions.user_id == self.id
            ))
        )

    async def has_permission(self, session: AsyncSession, permission_string):
        r = await session.execute(
            sa.select(PlatfePermissions.permission_string)
            .where(PlatfePermissions.user_id == self.id)
        )
        perms = r.scalars().all()
        return any([fn.fnmatch(permission_string, perm_str) for perm_str in perms])

    @staticmethod
    async def check_auth(session: AsyncSession, nickname, token):
        r = await session.execute(
            sa.select(PlatfeUser)
            .where(sa.and_(
                PlatfeUser.name == nickname,
                PlatfeUser.token == token,
                not PlatfeUser.disabled
            ))
        )
        return r.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id):
        r = await session.execute(
            sa.select(PlatfeUser)
            .where(PlatfeUser.id == user_id)
        )
        return r.scalar()

    @staticmethod
    async def get_by_name(session: AsyncSession, name):
        r = await session.execute(
            sa.select(PlatfeUser)
            .where(PlatfeUser.name == name)
        )
        return r.scalar_one_or_none()


# Total per record: 264 byte
class PlatfePermissions(Base):
    __tablename__ = "platfe_permissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_users.id"))
    permission_string: Mapped[str] = mapped_column(sa.String(256, **create_string_param))


class PlatfeWorlds(Base):
    __tablename__ = "platfe_worlds"
    id: Mapped[int] = mapped_column(primary_key=True)
    server_name: Mapped[str] = mapped_column(sa.String(64, **create_string_param))
    ip: Mapped[str] = mapped_column(sa.String(4, **create_string_param))
    world: Mapped[str] = mapped_column(sa.String(128, **create_string_param))

    @staticmethod
    async def get_world(session: AsyncSession, world):
        r = await session.execute(
            sa.select(PlatfeWorlds)
            .where(PlatfeWorlds.world == world)
        )
        return r.scalar_one_or_none()


# Total per record: 44 byte
class PlatfeCurrencies(Base):
    __tablename__ = "platfe_currencies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(32, **create_string_param))
    short_name: Mapped[str] = mapped_column(sa.String(8, **create_string_param))

    # std_box_sided_rent_tax: Mapped[int] = mapped_column(sa.Integer, default=0)
    # std_rent_period: Mapped[dt.timedelta] = mapped_column(sa.Interval, default=dt.timedelta(days=7))

    # std_buy_tax: Mapped[int] = mapped_column(sa.Integer, default=0)
    # std_buy_percent_tax: Mapped[int] = mapped_column(sa.Integer, default=0)

    # main_account_id: Mapped[int] = mapped_column(sa.BigInteger, default=None, nullable=True)

    @staticmethod
    async def create(session: AsyncSession, name: str, short_name: str):
        if '$' in name or '$' in short_name:
            return None

        await session.execute(
            sa.insert(PlatfeCurrencies)
            .values(name=name, short_name=short_name)
        )

        r = await session.execute(
            sa.select(PlatfeCurrencies)
            .where(PlatfeCurrencies.name == name)
        )

        cur = r.scalar()
        return cur

    @staticmethod
    async def get_all(session: AsyncSession):
        r = await session.execute(
            sa.select(PlatfeCurrencies)
        )
        return r.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, cur_id: int):
        r = await session.execute(
            sa.select(PlatfeCurrencies)
            .where(PlatfeCurrencies.id == cur_id)
        )
        return r.scalar_one_or_none()

    '''
    async def get_main_account(self, session: AsyncSession):
        if self.main_account_id == None:
            return None
        return await PlatfeAccounts.get_by_id(session, self.main_account_id)
    '''


class PlatfeAccountUserBridge(Base):
    __tablename__ = "platfe_account_user"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_users.id"))
    account_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_accounts.id"))


class PlatfeMoneyTransferLog(Base):
    __tablename__ = "platfe_money_transfer_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[int] = mapped_column(sa.DateTime, default=dt.datetime.now())
    doer_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_users.id"), nullable=True)
    doer_account_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_accounts.id"))
    destination_account_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_accounts.id"))
    count: Mapped[int] = mapped_column(sa.Integer)
    is_rollback: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    @staticmethod
    async def create(
            session: AsyncSession, doer: typing.Optional[PlatfeUser], doer_acc: "PlatfeAccounts", des: "PlatfeAccounts",
            count: int
    ):
        r = await session.execute(
            sa.insert(PlatfeMoneyTransferLog)
            .values(
                doer_id=doer.id,
                doer_account_id=doer_acc.id,
                destination_account_id=des.id,
                count=count
            )
        )
        return r.inserted_primary_key[0] if r.is_insert else 0

    @staticmethod
    async def get_by_id(session: AsyncSession, log_id: int):
        r = await session.execute(
            sa.select(PlatfeMoneyTransferLog)
            .where(PlatfeMoneyTransferLog.id == log_id)
        )
        return r.scalar_one_or_none()

    @staticmethod
    def check_create(log_id):
        return log_id != 0

    @staticmethod
    async def rollback(session: AsyncSession, doer: PlatfeUser, time: dt.datetime = None, acc: "PlatfeAccounts" = None, usr: PlatfeUser = None):
        # откаты других инстанций
        await PlatfeBothSidedBoxLogs.rollback(session, doer, time, acc, usr)

        # откаты самих переводов
        wr = []
        if time is not None:
            wr.append(PlatfeMoneyTransferLog.timestamp >= time)

        if acc is not None:
            wr.append(PlatfeMoneyTransferLog.doer_account_id == acc.id)

        if usr is not None:
            wr.append(PlatfeMoneyTransferLog.doer_id == usr.id)

        records = await session.execute(
            sa.select(PlatfeMoneyTransferLog)
            .where(sa.and_(*wr))
        )
        cors = []
        for record in records.scalars().all():
            cors.append(record.self_rollback(session, doer))
        await asyncio.gather(*cors)

    async def self_rollback(self, session: AsyncSession, doer: PlatfeUser):
        acc1 = await PlatfeAccounts.get_force_by_id(session, self.doer_account_id)
        acc2 = await PlatfeAccounts.get_force_by_id(session, self.destination_account_id)

        if acc1 is None or acc2 is None:
            return

        await acc2.transfer(session, doer, acc1, self.count)

        if acc2.balance < 0:
            await acc2.block(session)

        await session.execute(
            sa.update(PlatfeMoneyTransferLog)
            .values(is_rollback=True)
            .where(PlatfeMoneyTransferLog.id == self.id)
        )


# Total per record: 52 byte
class PlatfeAccounts(Base):
    __tablename__ = "platfe_accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(32))
    balance: Mapped[int] = mapped_column(sa.Integer, default=0)
    currency_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_currencies.id"))
    blocked: Mapped[int] = mapped_column(sa.Integer, default=0)
    disabled: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    @staticmethod
    async def get_all_user_accounts(session: AsyncSession, user: PlatfeUser):
        r = await session.execute(
            sa.select(PlatfeAccounts).join(PlatfeAccountUserBridge)
            .where(sa.and_(
                PlatfeAccountUserBridge.user_id == user.id,
                not PlatfeAccounts.disabled
            ))
        )
        return r.scalars().all()

    @staticmethod
    async def get_by_name(session: AsyncSession, acc_name):
        r = await session.execute(
            sa.select(PlatfeAccounts)
            .where(sa.and_(
                PlatfeAccounts.name == acc_name,
                not PlatfeAccounts.disabled
            ))
        )
        return r.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, payer_id):
        r = await session.execute(
            sa.select(PlatfeAccounts)
            .where(sa.and_(
                PlatfeAccounts.id == payer_id,
                not PlatfeAccounts.disabled
            ))
        )
        return r.scalar_one_or_none()

    @staticmethod
    async def get_force_by_id(session: AsyncSession, acc_id):
        r = await session.execute(
            sa.select(PlatfeAccounts)
            .where(PlatfeAccounts.id == acc_id)
        )
        return r.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, user: PlatfeUser, name: str, currency: PlatfeCurrencies):

        if '$' in name or len(name) > 32:
            return None

        r = await session.execute(
            sa.select(PlatfeAccounts)
            .where(PlatfeAccounts.name == name)
        )

        if r.scalar_one_or_none() is None:
            return await PlatfeAccounts._create(session, user, name, currency)
        else:
            return None

    @staticmethod
    async def _create(session: AsyncSession, user: PlatfeUser, name: str, currency: PlatfeCurrencies):
        await session.execute(
            sa.insert(PlatfeAccounts)
            .values(name=name, currency_id=currency.id)
        )

        r1 = await session.execute(
            sa.select(PlatfeAccounts)
            .where(PlatfeAccounts.name == name)
        )

        acc = r1.scalar_one_or_none()

        if not acc:
            return None
        r2 = await session.execute(
            sa.insert(PlatfeAccountUserBridge)
            .values(account_id=acc.id, user_id=user.id)
        )

        if not r2.inserted_primary_key:
            await session.rollback()
            return None

        return acc

    @staticmethod
    async def get_all_accounts(session):
        r = await session.execute(
            sa.select(PlatfeAccounts)
        )
        return r.scalars().all()

    async def get_owners(self, session: AsyncSession):
        r = await session.execute(
            sa.select(PlatfeUser).join(PlatfeAccountUserBridge)
            .where(
                PlatfeAccountUserBridge.account_id == self.id
            )
        )
        return r.scalars().all()

    async def transfer(self, session: AsyncSession, usr: typing.Optional[PlatfeUser], acc: "PlatfeAccounts",
                       count: int) -> int:
        if count <= 0:
            return -1

        if self.currency_id != acc.currency_id:
            return -3

        await session.execute(
            sa.update(PlatfeAccounts)
            .values(balance=PlatfeAccounts.balance - count)
            .where(PlatfeAccounts.id == self.id)
        )

        await session.execute(
            sa.update(PlatfeAccounts)
            .values(balance=PlatfeAccounts.balance + count)
            .where(PlatfeAccounts.id == acc.id)
        )
        log_id = await PlatfeMoneyTransferLog.create(session, usr, self, acc, count)
        if PlatfeMoneyTransferLog.check_create(log_id):
            return log_id
        else:
            return -5

    async def system_transfer(self, session: AsyncSession, acc: "PlatfeAccounts", count: int) -> int:
        return await self.transfer(session, None, acc, count)

    async def pay(self, session: AsyncSession, usr: PlatfeUser, acc: "PlatfeAccounts", count: int) -> int:
        if count <= 0:
            return -1

        if self.blocked:
            return -4

        if self.id == acc.id:
            return -7

        if self.currency_id != acc.currency_id:
            return -3

        if self.balance - count < 0:
            return -2

        if not (usr in (await self.get_owners(session))):
            return -6

        return await self.transfer(session, usr, acc, count)

    async def block(self, session: AsyncSession):
        await session.execute(
            sa.update(PlatfeAccounts)
            .values(blocked=1)
            .where(PlatfeAccounts.id == self.id)
        )

    async def delete(self, session: AsyncSession):
        await session.execute(
            sa.update(PlatfeAccounts)
            .values(disabled=True)
            .where(PlatfeAccounts.id == self.id)
        )


# Total per record: 812 byte
class PlatfeMap(Base):
    __tablename__ = "platfe_map"
    id: Mapped[int] = mapped_column(primary_key=True)
    world: Mapped[int] = mapped_column(sa.ForeignKey("platfe_worlds.id"))
    chunk_x: Mapped[int] = mapped_column(sa.Integer)
    chunk_y: Mapped[int] = mapped_column(sa.Integer)
    tile_hash: Mapped[str] = mapped_column(sa.String(32, **create_string_param))
    tile: Mapped[str] = mapped_column(sa.String(768, **create_string_param))


# Total per record: 20 byte
class PlatfeMapConfirmations(Base):
    __tablename__ = "platfe_map_confirmations"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[dt.datetime] = mapped_column(sa.DateTime, default=dt.datetime.now())
    transaction_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_map.id"))
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_users.id"))


# Total per record: 52 byte

class PlatfePrefix(Base):
    __tablename__ = "platfe_prefixes"
    id: Mapped[int] = mapped_column(primary_key=True)
    r: Mapped[int] = mapped_column(sa.SmallInteger)
    g: Mapped[int] = mapped_column(sa.SmallInteger)
    b: Mapped[int] = mapped_column(sa.SmallInteger)
    body: Mapped[str] = mapped_column(sa.String(8, **create_string_param))
    short_name: Mapped[str] = mapped_column(sa.String(24, **create_string_param))

    @staticmethod
    async def create(session: AsyncSession, short_name: str, r: int, g: int, b: int, body: str):
        await session.execute(
            sa.insert(PlatfePrefix)
            .values(
                short_name=short_name,
                r=r, g=g, b=b,
                body=body
            )
        )

    @staticmethod
    async def get_by_id(session: AsyncSession, prefix_id: int):
        r = await session.execute(
            sa.select(PlatfePrefix)
            .where(
                PlatfePrefix.id == prefix_id
            )
        )
        return r.scalar()

    @staticmethod
    async def get_by_short_name(session: AsyncSession, short_name: str):
        r = await session.execute(
            sa.select(PlatfePrefix)
            .where(
                PlatfePrefix.short_name == short_name
            )
        )
        return r.scalar_one_or_none()

    async def delete(self, session: AsyncSession):
        await session.execute(
            sa.delete(PlatfePrefix)
            .where(PlatfePrefix.short_name == self.short_name)
        )

    @staticmethod
    async def get_all(session: AsyncSession):
        r = await session.execute(
            sa.select(PlatfePrefix)
        )
        return r.scalars().all()

    def serialize_string(self):
        return chr(self.r) + chr(self.g) + chr(self.b) + self.body


class PlatfePrefixStatusBridge(Base):
    __tablename__ = "platfe_prefix_status_bridge"
    id: Mapped[int] = mapped_column(primary_key=True)
    prefix_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_prefixes.id"))
    status_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_nickname_status.id"))


class PlatfeNicknameStatus(Base):
    __tablename__ = "platfe_nickname_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str] = mapped_column(sa.String(32, **create_string_param))

    @staticmethod
    async def create(session: AsyncSession, nickname: str):
        await session.execute(
            sa.insert(PlatfeNicknameStatus)
            .values(nickname=nickname)
        )
        r2 = await session.execute(
            sa.select(PlatfeNicknameStatus)
            .where(PlatfeNicknameStatus.nickname == nickname)
        )
        return r2.scalar()

    async def delete(self, session: AsyncSession):
        await session.execute(
            sa.delete(PlatfePrefixStatusBridge)
            .where(PlatfePrefixStatusBridge.status_id == self.id)
        )
        await session.execute(
            sa.delete(PlatfeNicknameStatus)
            .where(PlatfeNicknameStatus.id == self.id)
        )

    async def add_prefix(self, session: AsyncSession, prf: PlatfePrefix):
        await session.execute(
            sa.insert(PlatfePrefixStatusBridge)
            .values(prefix_id=prf.id, status_id=self.id)
        )

    async def del_prefix(self, session: AsyncSession, prf: PlatfePrefix):
        await session.execute(
            sa.delete(PlatfePrefixStatusBridge)
            .where(sa.and_(
                PlatfePrefixStatusBridge.status_id == self.id,
                PlatfePrefixStatusBridge.prefix_id == prf.id
            ))
        )

    @staticmethod
    async def get_all_statuses(session: AsyncSession):
        r = await session.execute(
            sa.select(PlatfeNicknameStatus)
        )
        return r.scalars().all()

    @staticmethod
    async def get_by_nickname(session: AsyncSession, nickname: str):
        r = await session.execute(
            sa.select(PlatfeNicknameStatus)
            .where(PlatfeNicknameStatus.nickname == nickname)
        )
        return r.scalar_one_or_none()

    async def get_prefixes(self, session: AsyncSession):
        r = await session.execute(
            sa.select(PlatfePrefix).join(PlatfePrefixStatusBridge)
            .where(PlatfePrefixStatusBridge.status_id == self.id)
        )
        return r.scalars().all()


class PlatfeDuty(Base):
    __tablename__ = "platfe_duty"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_timestamp: Mapped[dt.datetime] = mapped_column(sa.DateTime, default=dt.datetime.now())
    last_duty_timestamp: Mapped[dt.datetime] = mapped_column(sa.DateTime, default=dt.datetime.now())
    payer_account_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_accounts.id"), default=None, nullable=True)
    owner_account_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_accounts.id"))
    period: Mapped[dt.timedelta] = mapped_column(sa.Interval)
    tax_amount: Mapped[int] = mapped_column(sa.Integer, default=0)

    @staticmethod
    async def create(session: AsyncSession, owner_account: PlatfeAccounts, period: dt.timedelta, tax_amount: int = 0):
        r = await session.execute(
            sa.insert(PlatfeDuty)
            .values(
                owner_account_id=owner_account.id,
                period=period,
                tax_amount=tax_amount
            )
        )
        return r.inserted_primary_key if r.is_insert else None

    @staticmethod
    async def get_by_id(session: AsyncSession, duty_id: int):
        r = await session.execute(
            sa.select(PlatfeDuty)
            .where(PlatfeDuty.id == duty_id)
        )
        return r.scalar_one_or_none()

    @staticmethod
    async def get_all_duties(session: AsyncSession):
        r = await session.execute(
            sa.select(PlatfeDuty)
        )
        return r.scalars().all()

    async def set_payer(self, session: AsyncSession, payer_account: PlatfeAccounts):
        r = await session.execute(
            sa.update(PlatfeDuty)
            .values(payer_account_id=payer_account.id)
            .where(PlatfeDuty.id == self.id)
        )
        return r.rowcount() != 0

    async def check(self, session: AsyncSession) -> bool:
        r = await session.execute(
            sa.select(PlatfeDuty)
            .where(PlatfeDuty.id == self.id)
        )
        r = r.scalar_one_or_none()
        if not r or not r.payer_account_id:
            return True

        if not r.owner_account_id:
            return False

        payer_acc = await PlatfeAccounts.get_by_id(session, r.payer_account_id)
        owner_acc = await PlatfeAccounts.get_by_id(session, r.owner_account_id)

        if payer_acc is None or owner_acc is None:
            return False

        while payer_acc.balance - r.tax_amount >= 0 and r.last_duty_timestamp + r.period < dt.datetime.now():
            r.last_duty_timestamp += r.period
            await payer_acc.system_transfer(session, owner_acc, r.tax_amount)

        if payer_acc.balance - r.tax_amount < 0 and r.last_duty_timestamp + r.period < dt.datetime.now():
            return False
        else:
            return True


class PlatfeBothSidedBoxLogs(Base):
    __tablename__ = "platfe_both_sided_box_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    transfer_log_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_money_transfer_log.id"))
    both_sided_box_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_both_sided_box.id"))
    count: Mapped[int] = mapped_column(sa.Integer)
    price_one: Mapped[int] = mapped_column(sa.Integer)
    is_rollback: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    async def set_rollback(self, session: AsyncSession):
        await session.execute(
            sa.update(PlatfeBothSidedBoxLogs)
            .values(is_rollback=True)
            .where(PlatfeBothSidedBoxLogs.id == self.id)
        )

    @staticmethod
    async def rollback(session: AsyncSession, doer: PlatfeUser, time: dt.datetime = None, acc: PlatfeAccounts = None, usr: PlatfeUser = None):
        wr = []
        if time is not None:
            wr.append(PlatfeMoneyTransferLog.timestamp >= time)

        if acc is not None:
            wr.append(PlatfeMoneyTransferLog.doer_account_id == acc.id)

        if usr is not None:
            wr.append(PlatfeMoneyTransferLog.doer_id == usr.id)

        records = await session.execute(
            sa.select(PlatfeBothSidedBoxLogs).join(PlatfeMoneyTransferLog)
            .where(sa.and_(*wr))
        )
        cors = []
        for record in records.scalars().all():
            t = await PlatfeMoneyTransferLog.get_by_id(session, record.transfer_log_id)
            cors.append(t.self_rollback(session, doer))
            await record.set_rollback(session)

        await asyncio.gather(*cors)


class PlatfeBothSidedBox(Base):
    __tablename__ = "platfe_both_sided_box"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_timestamp: Mapped[dt.datetime] = mapped_column(sa.DateTime, default=dt.datetime.now())
    x: Mapped[int] = mapped_column(sa.Integer)
    y: Mapped[int] = mapped_column(sa.Integer)
    z: Mapped[int] = mapped_column(sa.Integer)
    world_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_worlds.id"))

    # cyclic duty block
    last_duty_timestamp: Mapped[dt.datetime] = mapped_column(sa.DateTime, default=dt.datetime.now())
    payer_acc_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_accounts.id"))
    main_acc_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_accounts.id"))
    period: Mapped[int] = mapped_column(sa.Interval)
    tax_amount: Mapped[int] = mapped_column(sa.Integer)

    mc_item_id: Mapped[str] = mapped_column(sa.String(256, **create_string_param))
    mc_item_tag: Mapped[str] = mapped_column(sa.String(2048, **create_string_param))

    count: Mapped[int] = mapped_column(sa.Integer)
    price_buy: Mapped[int] = mapped_column(sa.Integer, default=None, nullable=True)
    price_sell: Mapped[int] = mapped_column(sa.Integer, default=None, nullable=True)

    blocked: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    disabled: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    @staticmethod
    async def get_by_coordinates(session: AsyncSession, x, y, z, world: PlatfeWorlds):
        r = await session.execute(
            sa.select(PlatfeBothSidedBox)
            .where(sa.and_(
                PlatfeBothSidedBox.x == x,
                PlatfeBothSidedBox.y == y,
                PlatfeBothSidedBox.z == z,
                PlatfeBothSidedBox.world_id == world.id,
                not PlatfeBothSidedBox.disabled
            ))
        )
        return r.scalar_one_or_none()

    @staticmethod
    async def check_xyz(session: AsyncSession, x, y, z, world: PlatfeWorlds):
        return PlatfeBothSidedBox.get_by_coordinates(session, x, y, z, world) is None

    @staticmethod
    async def create(
            session: AsyncSession,
            x: int, y: int, z: int,
            world: PlatfeWorlds,
            payer_acc: PlatfeAccounts, main_acc: PlatfeAccounts,
            mc_item_id: str, mc_item_tag: str,
            count: int,
            price_buy: int, price_sell: typing.Optional[int] = None
    ):

        if len(mc_item_id) > 256 or len(mc_item_tag) > 2048:
            return -2

        if not await PlatfeBothSidedBox.check_xyz(session, x, y, z, world):
            return -4

        box = PlatfeBothSidedBox(
            x=x, y=y, z=z,
            world_id=world.id,
            payer_acc_id=payer_acc.id,
            main_acc_id=main_acc.id,
            mc_item_id=mc_item_id,
            mc_item_tag=mc_item_tag,
            count=count,
            price_buy=price_buy,
            price_sell=price_sell
        )
        session.add(box)
        await session.refresh(box)
        return box.id

    @staticmethod
    async def get_by_id(session: AsyncSession, box_id):
        r = await session.execute(
            sa.select(PlatfeBothSidedBox)
            .where(PlatfeBothSidedBox.id == box_id)
        )
        return r.scalar_one_or_none()

    @staticmethod
    async def get_all_not_blocked(session: AsyncSession):
        r = await session.execute(
            sa.select(PlatfeBothSidedBox)
            .where(sa.and_(
                not PlatfeBothSidedBox.disabled,
                not PlatfeBothSidedBox.blocked
            ))
        )
        return r.scalars().all()

    @staticmethod
    async def get_all_box_acc(session: AsyncSession, acc: PlatfeAccounts):
        r = await session.execute(
            sa.select(PlatfeBothSidedBox)
            .where(sa.and_(
                not PlatfeBothSidedBox.disabled,
                PlatfeBothSidedBox.payer_acc_id == acc.id
            ))
        )
        return r.scalars().all()

    async def disable(self, session: AsyncSession):
        await session.execute(
            sa.update(PlatfeBothSidedBox)
            .values(disabled=True)
            .where(PlatfeBothSidedBox.id == self.id)
        )

    async def block(self, session: AsyncSession):
        await session.execute(
            sa.update(PlatfeBothSidedBox)
            .values(blocked=True)
            .where(PlatfeBothSidedBox.id == self.id)
        )

    async def check(self, session: AsyncSession):
        payer_acc = await PlatfeAccounts.get_by_id(session, self.payer_acc_id)
        owner_acc = await PlatfeAccounts.get_by_id(session, self.main_acc_id)

        if payer_acc is None or owner_acc is None:
            await self.disable(session)

        while payer_acc.balance - self.tax_amount >= 0 and self.last_duty_timestamp + self.period < dt.datetime.now():
            self.last_duty_timestamp += self.period
            await payer_acc.system_transfer(session, owner_acc, self.tax_amount)

        if payer_acc.balance - self.tax_amount < 0 and self.last_duty_timestamp + self.period < dt.datetime.now():
            await self.block(session)

    @staticmethod
    async def check_all(session: AsyncSession):
        cors = []
        for record in await PlatfeBothSidedBox.get_all_not_blocked(session):
            cors.append(record.check(session))

        await asyncio.gather(*cors)
        await session.commit()



'''
class PlatfeSignTransaction(Base):
    __tablename__ = "platfe_sign_transaction"
    id: Mapped[int] = mapped_column(primary_key=True)
    x: Mapped[int] = mapped_column(sa.Integer)
    y: Mapped[int] = mapped_column(sa.Integer)
    z: Mapped[int] = mapped_column(sa.Integer)
    world_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_worlds.id"))
    duty_id: Mapped[int] = mapped_column(sa.ForeignKey("platfe_duty.id", ondelete='cascade'))
    name: Mapped[str] = mapped_column(sa.String(13))
    price_buy: Mapped[int] = mapped_column(sa.Integer, default=None, nullable=True)
    price_sell: Mapped[int] = mapped_column(sa.Integer, default=None, nullable=True)
    
'''
