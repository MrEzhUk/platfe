import discord
from discord.ext.commands import Bot

bot = Bot(command_prefix="-", intents=discord.Intents.all())

async def start_bot():
    await bot.start("TOKEN")
