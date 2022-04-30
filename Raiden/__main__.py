
import contextlib
import importlib
import sys
import re
import time
import json
import traceback
import html
import os
from sys import argv
from typing import Optional
import Raiden.modules.sql.users_sql as sql

from telegram import Message, Chat, User, Update
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import (
    TelegramError,
    Unauthorized,
    BadRequest,
    TimedOut,
    ChatMigrated,
    NetworkError,
)
from telegram.ext import (
    Filters,
    MessageHandler,
    CallbackQueryHandler,
    CallbackContext,
)
from telegram.ext.dispatcher import DispatcherHandlerStop
from telegram.utils.helpers import escape_markdown
from pyrogram import Client, idle
from telethon import Button

from Raiden import (
    dispatcher,
    updater,
    StartTime,
    TOKEN,
    WEBHOOK,
    CERT_PATH,
    MESSAGE_DUMP,
    PORT,
    SUPPORT_CHAT,
    URL,
    client as telethn,
    LOGGER,
    BLACKLIST_CHATS,
    WHITELIST_CHATS,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from Raiden.modules import ALL_MODULES
from Raiden.modules.disable import DisableAbleCommandHandler
from Raiden.modules.helper_funcs.chat_status import is_user_admin
from Raiden.modules.helper_funcs.misc import paginate_modules


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += f"{time_list.pop()}, "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


RAIDEN_IMG = "https://telegra.ph//file/6bcfa7906c19acd6aca6b.mp4"
RAIDEN_START = "https://telegra.ph/file/4f73cf9c1d1bad7dc679f.mp4"

PM_START_TEXT = """
────「 [{}](https://telegra.ph//file/a814af57a80c825a18d4a.mp4) 」────
ᴋᴏɴ'ɴɪᴄʜɪᴡᴀ {} - sᴀɴ!  
ɪ'ᴍ [𝙍𝙖𝙞𝙙𝙚𝙣 𝙎𝙝𝙤𝙜𝙪𝙣](https://genshin-impact.fandom.com/wiki/Raiden_Shogun) ᴀɴ ɢʀᴏᴜᴘ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ʙᴏᴛ ғʀᴏᴍ [ɢᴇɴsʜɪɴ ɪᴍᴘᴀᴄᴛ](https://genshin.hoyoverse.com/m/en/).
➖➖➖➖➖➖➖➖➖➖➖➖➖
» ᴜᴘᴛɪᴍᴇ {} 
» ᴜsᴇʀs {} ᴀᴄʀᴏss {} ᴄʜᴀᴛs 
➖➖➖➖➖➖➖➖➖➖➖➖➖
ʜɪᴛ /help ᴛᴏ sᴇᴇ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅs ᴀᴠᴀɪʟᴀʙʟᴇ ᴀғᴛᴇʀ ᴍʏ ᴇʟᴇᴍᴇɴᴛᴀʟ ʙᴜғғ. ××  
𝙋𝙤𝙬𝙚𝙧𝙚𝙙 𝘽𝙮 [𝙉𝙂𝘼](https://t.me/New_Generation_Anime).
"""

buttons = [
    [
        InlineKeyboardButton(
            text="➕️ ᴀᴅᴅ ʀᴀɪᴅᴇɴ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕️",
            url="t.me/RaidenXRobot?startgroup=true",
        ),
    ],
    [
        InlineKeyboardButton(
            text="ᴍʏ ʜᴏᴍᴇ",
            url="t.me/RaidenSupport",
        ),
        InlineKeyboardButton(
            text="ᴋᴀᴢᴜʜᴀ",
            url="https://t.me/Kaedehara_Kaazuha",
        ),
    ],
    [
        InlineKeyboardButton(
            text="ʜᴇʟᴘ",
            callback_data="help_back",
        ),
        InlineKeyboardButton(
            text="𝙉𝙂𝘼"
            url="https://t.me/New_Generation_Anime",
        ),
    ],
]

HELP_STRINGS = """
Hey there! Myself [Raiden](https://telegra.ph//file/98614588d823bda52551d.jpg).
Have a look at the following for an idea of some of the things I can help you with.
*Main* commands available:
 ➛ /help: PM's you this message.
 ➛ /help <module name>: PM's you info about that module.
 ➛ /bug <error name> : inform support about that error 
 ➛ /donate: information on how to donate!
 ➛ /settings: 
   ❂ in PM: will send you your settings for all supported modules.
   ❂ in a group: will redirect you to pm, with all that chat's settings.\n• *ʀᴇᴀᴄʜ ᴏᴜᴛ ғᴏʀ sᴜᴘᴘᴏʀᴛ:* [sᴜᴘᴘᴏʀᴛ](https://t.me/RaidenSupport)
"""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

GDPR = []

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Raiden.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__gdpr__"):
        GDPR.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


def test(update: Update, _: CallbackContext):
    # pprint(ast.literal_eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


def start(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text="[•༶B𝚊𝚌k༶•]", callback_data="help_back"
                                )
                            ]
                        ]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_text(
                PM_START_TEXT.format(
                    escape_markdown(context.bot.first_name),
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats(),
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        message.reply_video(
            RAIDEN_IMG,
            caption="Kon'nichiwa, Raiden Here To Help!\n Have been slaying bosses since: <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ᴍʏ ʜᴏᴍᴇ",
                            url="https://t.me/RaidenSupport",
                        ),
                        InlineKeyboardButton(
                            text="ʜᴇʟᴘ",
                            url=f"https://t.me/RaidenXRobot?start=help",
                        ),
                    ]
                ]
            ),
        )


def error_handler(_: Update, context: CallbackContext):
    """for test purposes"""
    try:
        raise context.error
    except (Unauthorized, BadRequest):
        pass
        # remove update.message.chat_id from conversation list
    except TimedOut:
        pass
        # handle slow connection problems
    except NetworkError:
        pass
        # handle other connection problems
    except ChatMigrated:
        pass
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        pass
        # handle all other telegram related errors


def help_button(update: Update, context: CallbackContext):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    with contextlib.suppress(BadRequest):
        if mod_match:
            module = mod_match.group(1)
            text = (
                "╒═══≼ ᴍᴇɴᴜ ᴏғ「 *{}* 」ᴍᴏᴅᴜʟᴇ:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="[•༶B𝚊𝚌k༶•]", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)


def rai_cb(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "rai_":
        query.message.edit_text(
            text="""Your Callback Data""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="rai_back")]]
            ),
        )
    elif query.data == "rai_back":
        first_name = update.effective_user.first_name
        query.message.edit_text(
                PM_START_TEXT.format(
                escape_markdown(context.bot.first_name),
                escape_markdown(first_name),
                escape_markdown(uptime),
                sql.num_users(),
                sql.num_chats(),
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
        )


def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:

        update.effective_message.reply_video(
            RAIDEN_IMG,
 caption= "Baka!! Click the button below to get help to know my abilities.",
                reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Open In Private Chat",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ]
                ]
            ),
        )
        
    return

    if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="[•༶B𝚊𝚌k༶•]", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    elif CHAT_SETTINGS:
        chat_name = dispatcher.bot.getChat(chat_id).title
        dispatcher.bot.send_message(
            user_id,
            text=f"Which module would you like to check {chat_name}'s settings for?",
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
            ),
        )

    else:
        dispatcher.bot.send_message(
            user_id,
            "Seems like there aren't any chat settings available :'(\nSend this "
            "in a group chat you're admin in to find its current settings!",
            parse_mode=ParseMode.MARKDOWN,
        )


def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="[•༶B𝚊𝚌k༶•]", callback_data=f"stngs_back({chat_id})"
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.edit_text(
                f"Hi there! There are quite a few settings for {chat.title} - go ahead and pick what you're interested in.",
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.edit_text(
                f"Hi there! There are quite a few settings for {chat.title} - go ahead and pick what you're interested in.",
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.edit_text(
                text=f"Hi there! There are quite a few settings for {escape_markdown(chat.title)} - go ahead and pick what you're interested in.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type == chat.PRIVATE:
        send_settings(chat.id, user.id, True)

    elif is_user_admin(chat, user.id):
        text = "Click here to get this chat's settings, as well as yours."
        msg.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Settings",
                            url=f"t.me/{context.bot.username}?start=stngs_{chat.id}",
                        )
                    ]
                ]
            ),
        )

    else:
        "Click here to check your settings."


def migrate_chats(update: Update, _: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        with contextlib.suppress(KeyError, AttributeError):
            mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def is_chat_allowed(update: Update, context: CallbackContext):
    if len(WHITELIST_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id not in WHITELIST_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id, text="Unallowed chat! Leaving..."
            )
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    if len(BLACKLIST_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id in BLACKLIST_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id, text="Unallowed chat! Leaving..."
            )
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    if 0 not in (len(WHITELIST_CHATS), len(BLACKLIST_CHATS)):
        chat_id = update.effective_message.chat_id
        if chat_id in BLACKLIST_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id, text="Unallowed chat, leaving"
            )
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop


def main():
    # test_handler = DisableAbleCommandHandler("test", test, run_async=True)
    start_handler = DisableAbleCommandHandler(
        "start", start, pass_args=True, run_async=True
    )
    home_callback_handler = CallbackQueryHandler(
        rai_cb, pattern=r"rai_", run_async=True
    )
    help_handler = DisableAbleCommandHandler("help", get_help, run_async=True)
    help_callback_handler = CallbackQueryHandler(
        help_button, pattern=r"help_", run_async=True
    )

    settings_handler = DisableAbleCommandHandler(
        "settings", get_settings, run_async=True
    )
    settings_callback_handler = CallbackQueryHandler(
        settings_button, pattern=r"stngs_", run_async=True
    )

    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)
    is_chat_allowed_handler = MessageHandler(Filters.chat_type.groups, is_chat_allowed)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(is_chat_allowed_handler)
    dispatcher.add_handler(home_callback_handler)

    dispatcher.add_error_handler(error_handler)

    if WEBHOOK:
        LOGGER.info("[Raiden] Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)
            client.run_until_disconnected()

    else:
        LOGGER.info("[Raiden] Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, drop_pending_updates=True)
    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.send_photo(
                "@Raidensupport",
                "https://telegra.ph/file/4f73cf9c1d1bad7dc679f.mp4",
                "Am Alive Again To Slay Some Mf Bosses!!",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == '__main__':
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    main()
    idle()
