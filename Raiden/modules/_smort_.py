import datetime
import html
import json
import textwrap
import bs4
import jikanpy
import requests
import random
import os

from bs4 import BeautifulSoup
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update, Message
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.utils.helpers import mention_html

from Raiden import OWNER_ID, REDIS, dispatcher
from Raiden.modules.disable import DisableAbleCommandHandler
from Raiden.modules.helper_funcs.alternate import typing_action
from Raiden.modules.helper_funcs.chat_status import callbacks_in_filters\


WAIFUS_PIC = (
    "ram",
    "rem"
    "asuna yuuki",
    "miku nakano",
    "emilia",
    "zero two",
    "tohru",
    "natsunagi nagisa",
    "mai sakurajima",
    "makinohara",
    "megumin",
    "kanna kamui"
    "umaru doma",
    "rikka takanashi",
    "enterprise",
    "sakura haruno",
    "hinata hyuuga",
    "kurumi tokisaki",
    "shinobu kochou",
    "nezuko kamado"
    "nami",
    "nico Robin",
    "boa Hancock",
    "viola",
    "yuno Gasai",
    "himawari uzumaki",
    "kaguya shinomiya",
    "kanae kochou",
    "yukinon",
    "marin",
    "siesta",
    "asia",
    "rias",
    "gabi",
    "mikasa",
    "komi",
    "akeno himejima",
    "nobara kugisaki",
    "daki",








)
url = "https://graphql.anilist.co"

character_query = """
    query ($query: String) {
        Character (search: $query) {
               id
               name {
                     first
                     last
                     full
               }
               siteUrl
               image {
                        large
               }
               description
        }
    }
"""


def animestuffs(update, context):
    query = update.callback_query
    user = update.effective_user
    splitter = query.data.split("=")
    query_match = splitter[0]
    callback_anime_data = splitter[1]


    if query_match == "xanime_waifu":
        fvrt_waifus = list(REDIS.sunion(f"anime_waifu{user.id}"))
        if not callback_anime_data in fvrt_waifus:
            REDIS.sadd(f"anime_waifu{user.id}", callback_anime_data)
            context.bot.answer_callback_query(
                query.id,
                text=f"{callback_anime_data} is successfully added to your Harem.",
                show_alert=True,
            )
        else:
            context.bot.answer_callback_query(
                query.id,
                text=f"{callback_anime_data} is already exists in your Harem!",
                show_alert=True,
            )

def guess(update, context):
    search = random.choice(WAIFUS_PIC)
    variables = {"query": search}
    json = requests.post(
        url, json={"query": character_query, "variables": variables}
    ).json()
    if json:
        f = json["data"]["Character"]
        char_name = f"{json.get('name').get('full')}"
        image = json.get("image", None)
        if image:
            image = image.get("large")
            update.effective_message.reply_photo(
                photo=image, caption= f"*A waifu/husbando appeared!*\nGuessed Correctly and add them to your harem by sending /uwu character name",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            update.effective_message.reply_text(
                "Oops Waifu/Husbando Ran Away",
                parse_mode=ParseMode.MARKDOWN,
            )

@typing_action
def uwu(update, context):
    message = update.effective_message
    user = update.effective_user
    search = message.text.split(" ", 1)
    if len(search) == 1:
        update.effective_message.reply_text("rip, that's not quite right...")
        return
    search = search[1]
    variables = {"query": search}
    json = requests.post(
        url, json={"query": character_query, "variables": variables}
    ).json()
    if "errors" in json.keys():
        update.effective_message.reply_text("rip, that's not quite right...")
        return
    if json:
        json = json["data"]["Character"]
        char_name = f"{json.get('name').get('full')}"
        if search in WAIFUS_PIC:
            REDIS.sadd(f"anime_waifu{user.id}", search)
            update.effective_message.reply_text(f"OwO you guessed {char_name}. This waifu/husbando has been added to your harem.")
        else:
            update.effective_message.reply_text("rip, that's not quite right...")

def fvrt_waifu(update, context):
    update.effective_chat
    user = update.effective_user
    message = update.effective_message
    buttons = [
                [
                    InlineKeyboardButton(
                        "Inline🌐", switch_inline_query_current_chat="harem"
                    )
                ]
            ]
    fvrt_char = list(REDIS.sunion(f"anime_waifu{user.id}"))
    fvrt_char.sort()
    fvrt_char = f"\n• ".join(fvrt_char)
    if fvrt_char: 
        lol = list(REDIS.sunion(f"anime_waifu{user.id}"))
        search = random.choice(lol)
        variables = {"query": search}
        json = requests.post(
        url, json={"query": character_query, "variables": variables}
        ).json()
        if json:
            json = json["data"]["Character"]
            image = json.get("image", None)
            loml = image.get("large")
            message.reply_document(
            document=loml,
            caption= "{}'s harem in {} \n• {}".format(user.username, update.effective_chat.title, fvrt_char),
            reply_markup=InlineKeyboardMarkup(buttons),
           )
            os.remove(loml)
    else:
        message.reply_text("You havn't guessed any waifu/husbando in your harem!")

def remove_waifu(update, context):
    user = update.effective_user
    message = update.effective_message
    removewaifu = message.text.split(" ", 1)
    args = context.args
    query = " ".join(args)
    if not query:
        message.reply_text("Please enter a your waifu name to remove from list.")
        return
    fvrt_char = list(REDIS.sunion(f"anime_waifu{user.id}"))
    removewaifu = removewaifu[1]

    if removewaifu not in fvrt_char:
        message.reply_text(
            f"<code>{removewaifu}</code> doesn't exist in your Harem",
            parse_mode=ParseMode.HTML,
        )
    else:
        message.reply_text(
            f"<code>{removewaifu}</code> has been removed from your List",
            parse_mode=ParseMode.HTML,
        )
        REDIS.srem(f"anime_waifu{user.id}", removewaifu)


WAIFU_HANDLER = DisableAbleCommandHandler("guess", guess, run_async=True)
PROTECC_HANDLER = DisableAbleCommandHandler("protecc", uwu, run_async=True)
HAREM_HANDLER = DisableAbleCommandHandler("harem", fvrt_waifu, run_async=True)
REMOVE_HANDLER = DisableAbleCommandHandler("removewaifu", remove_waifu, run_async=True)
ANIME_STUFFS_HANDLER = CallbackQueryHandler(
    animestuffs, pattern="xanime_.*", run_async=True
)

dispatcher.add_handler(WAIFU_HANDLER)
dispatcher.add_handler(HAREM_HANDLER)
dispatcher.add_handler(REMOVE_HANDLER)
dispatcher.add_handler(PROTECC_HANDLER)
dispatcher.add_handler(ANIME_STUFFS_HANDLER)


__mod_name__ = "Harem"
__command_list__ = [
    "guess",
    "uwu",
    "fvrt_waifu",
    "remove_waifu",
]
__handlers__ = [
    WAIFU_HANDLER,
    HAREM_HANDLER,
    REMOVE_HANDLER,
    PROTECC_HANDLER,
]


#Modified By @XtheAnonymous
