import os
import re
import random
from platform import python_version as kontol
from telethon import events, Button
from telegram import __version__ as telever
from telethon import __version__ as tlhver
from pyrogram import __version__ as pyrover
from Raiden.events import register
from Raiden import telethn as tbot
from Raiden import SUPPORT_CHAT

MARIN = "https://telegra.ph//file/bec5d30ae2b54c2a0421e.mp4"

@register(pattern=("/alive"))
async def awake(event):
  TEXT = f"Hey [{event.sender.first_name}](tg://user?id={event.sender.id})! I'm Marin Kitagawa♡\nI'm here to manage your groups so give enough rights\nFor any doubts realqted to Marin come to the support by clicking the button below.n\n"
  TEXT += "**Thanks for adding me in your group♡**"
  BUTTON = [[Button.url("Help", "https://t.me/MarinRobot?start=help"), Button.url("My Home", "https://t.me/MarinSupport")]]
  await tbot.send_file(event.chat_id, MARIN, caption=TEXT,  buttons=BUTTON)

@register(pattern=("/repo"))
async def repo(event):
    Nobara = f"**Hey [{event.sender.first_name}](tg://user?id={event.sender.id}), Click The Button Below To Get My Repo**\n\n"
    BUTTON = [[Button.url("sᴜᴘᴘᴏʀᴛ", "https://t.me/MarinSupport"), Button.url("ʀᴇᴘᴏ", "https://t.me/MarinSupport)]]
    await borg.send_file(event.chat_id, file="https://telegra.ph//file/bd6fb2f171846d16073e1.mp4", caption=Nobara, buttons=BUTTON)


@register(pattern=("/offchats"))
async def repo(event):
    Aogiri = f"**Hey [{event.sender.first_name}](tg://user?id={event.sender.id}), This is our Anime Chat**\n\n"
    BUTTON = [[Button.url("𝖠𝗇𝗂𝗆𝖾 𝖥𝗈𝗅𝗄𝗌", "https://t.me/Anime_Chat_Folks"), Button.url("𝖠𝗇𝗂𝗆𝖾 𝖠𝗂𝗇𝖼𝗋𝖺𝖽", "https://t.me/AnimeChatAincrad")]]
    await borg.send_file(event.chat_id, file="https://telegra.ph//file/bd6fb2f171846d16073e1.mp4", caption=Aogiri, buttons=BUTTON)
