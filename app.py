import os
import re
import json
import html
import asyncio
import logging
import tempfile
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ChatJoinRequestHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError, RetryAfter
from telegram.request import HTTPXRequest

# =========================================================
# SETTINGS
# =========================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
TOKEN = "9201939195:AAH2pSkoJf8QgdmLBCp7lFjCU4OVuLicgZM"
ADMIN_ID = 7215059470
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "bot_config.json")
ADMIN_STATE = {}
ADMIN_DASHBOARD_ID = None
ADMIN_TRANSIENT_ID = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =========================================================
# ADMIN KEYBOARD
# =========================================================
ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📢 BROADCAST"),
         KeyboardButton("➕ MAIN CHANNEL")],
        [KeyboardButton("➕ EXTRA CHANNEL"),
         KeyboardButton("🗂 MANAGE CHANNELS")],
        [KeyboardButton("🖼 WELCOME"),
         KeyboardButton("🎁 FINAL CONTENT")],
        [KeyboardButton("📋 BOT STATUS"),
         KeyboardButton("🏠 ADMIN HOME")],
        [KeyboardButton("❌ CANCEL")],
    ],
    resize_keyboard=True,
    is_persistent=True,
    one_time_keyboard=False,
    input_field_placeholder="Select an admin option..."
)

# =========================================================
# CONFIG
# =========================================================
def default_config():
    return {
        "channels": [],
        "fake_channels": [],
        "subscribers": [],
        "welcome_message": None,
        "final_messages": [],
        "main_passed": [],
        "completed_users": [],
        "extra_requests": {}
    }

def load_config():
    config = default_config()
    try:
        if os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    config.update(data)
                old_final = data.get("final_message")
                if (
                    isinstance(old_final, dict)
                    and not config.get("final_messages")
                ):
                    config["final_messages"] = [old_final]
    except Exception:
        logger.exception("Could not load config")
    
    for key in ("channels", "fake_channels"):
        if not isinstance(config.get(key), list):
            config[key] = []
        config[key] = [
            item for item in config[key]
            if isinstance(item, dict)
            and item.get("chat_id") is not None
            and item.get("url")
        ]
    for key in (
        "subscribers",
        "final_messages",
        "main_passed",
        "completed_users"
    ):
        if not isinstance(config.get(key), list):
            config[key] = []
    if not isinstance(config.get("extra_requests"), dict):
        config["extra_requests"] = {}
    return config

def save_config(config):
    temp_path = None
    try:
        folder = os.path.dirname(os.path.abspath(CONFIG_FILE))
        fd, temp_path = tempfile.mkstemp(
            dir=folder,
            suffix=".tmp"
        )
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(
                config,
                file,
                indent=4,
                ensure_ascii=False
            )
        os.replace(temp_path, CONFIG_FILE)
        return True
    except Exception:
        logger.exception("Could not save config")
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return False

def get_all_channels(config):
    return config["channels"] + config["fake_channels"]

# =========================================================
# ADMIN DASHBOARD & CLEANUP CONTROLLER
# =========================================================
def admin_dashboard_text():
    config = load_config()
    main_names = [
        html.escape(str(c.get("name", c.get("chat_id"))))
        for c in config["channels"]
    ]
    extra_names = [
        html.escape(str(c.get("name", c.get("chat_id"))))
        for c in config["fake_channels"]
    ]
    main_preview = "\n".join(
        f" • {name}" for name in main_names[:8]
    ) or " • None"
    extra_preview = "\n".join(
        f" • {name}" for name in extra_names[:8]
    ) or " • None"
    request_count = sum(
        len(value)
        for value in config["extra_requests"].values()
        if isinstance(value, list)
    )
    return (
        "👑 <b>SAKIL BHAI — VIP CONTROL CENTER</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>ADMIN DASHBOARD</b>\n\n"
        "🟢 System: ONLINE\n"
        f"👥 Bot users: <b>{len(config['subscribers'])}</b>\n\n"
        f"📢 Main channels: <b>{len(config['channels'])}</b>\n"
        f"{main_preview}\n\n"
        f"🔒 Extra channels: <b>{len(config['fake_channels'])}</b>\n"
        f"{extra_preview}\n\n"
        f"📨 Requests received: <b>{request_count}</b>\n"
        f"🎁 Final messages: <b>{len(config['final_messages'])}</b>\n"
        f"✅ Completed users: <b>{len(config['completed_users'])}</b>\n\n"
        "⚡ Dashboard refreshes automatically after bot events.\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

async def refresh_admin_dashboard(bot):
    global ADMIN_DASHBOARD_ID
    if not ADMIN_DASHBOARD_ID:
        return
    try:
        await bot.edit_message_text(
            chat_id=ADMIN_ID,
            message_id=ADMIN_DASHBOARD_ID,
            text=admin_dashboard_text(),
            parse_mode="HTML"
        )
    except TelegramError as error:
        if "message is not modified" not in str(error).lower():
            logger.warning("Dashboard refresh: %s", error)

async def delete_message_safely(bot, chat_id, message_id):
    if not message_id:
        return
    try:
        await bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
    except TelegramError:
        pass

async def show_admin_dashboard(message, context):
    global ADMIN_DASHBOARD_ID, ADMIN_TRANSIENT_ID
    
    # Purono kono option ba message thakle seta delete kore dibe
    if ADMIN_TRANSIENT_ID:
        await delete_message_safely(context.bot, ADMIN_ID, ADMIN_TRANSIENT_ID)
        ADMIN_TRANSIENT_ID = None

    await delete_message_safely(
        context.bot,
        message.chat_id,
        message.message_id
    )
    
    if ADMIN_DASHBOARD_ID:
        try:
            await context.bot.edit_message_text(
                chat_id=ADMIN_ID,
                message_id=ADMIN_DASHBOARD_ID,
                text=admin_dashboard_text(),
                parse_mode="HTML",
                reply_markup=None
            )
            return
        except TelegramError:
            ADMIN_DASHBOARD_ID = None

    sent = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_dashboard_text(),
        parse_mode="HTML",
        reply_markup=ADMIN_KEYBOARD
    )
    ADMIN_DASHBOARD_ID = sent.message_id

async def admin_notice(message, context, text, parse_mode=None, reply_markup=None):
    global ADMIN_TRANSIENT_ID
    # Prothome ager option/message ti completely delete korbe
    if ADMIN_TRANSIENT_ID:
        await delete_message_safely(
            context.bot,
            ADMIN_ID,
            ADMIN_TRANSIENT_ID
        )
    
    sent = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup or ADMIN_KEYBOARD
    )
    ADMIN_TRANSIENT_ID = sent.message_id

# =========================================================
# MEMBERSHIP CHECK & TRACKING
# =========================================================
async def get_membership_status(user_id, context, channels):
    statuses = {}
    for channel in channels:
        chat_id = channel.get("chat_id")
        key = str(chat_id)
        try:
            member = await context.bot.get_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )
            joined = member.status not in ("left", "kicked")
            if member.status == "restricted":
                joined = bool(getattr(member, "is_member", False))
            statuses[key] = joined
        except TelegramError as error:
            logger.warning("Membership check failed for %s: %s", chat_id, error)
            statuses[key] = False
    return statuses

def get_user_extra_requests(config, user_id):
    values = config["extra_requests"].get(str(user_id), [])
    return set(str(x) for x in values)

def all_extra_requests_received(config, user_id):
    channels = config["fake_channels"]
    if not channels:
        return True
    received = get_user_extra_requests(config, user_id)
    required = {str(channel["chat_id"]) for channel in channels}
    return required.issubset(received)

# =========================================================
# USER KEYBOARD & MESSAGING
# =========================================================
def build_channel_keyboard(channels, statuses=None, request_mode=False):
    statuses = statuses or {}
    keyboard = []
    row = []
    for channel in channels:
        url = channel.get("url")
        if not url:
            continue
        chat_id = str(channel.get("chat_id"))
        if request_mode:
            label = "📨 REQUEST SENT" if statuses.get(chat_id) else "✨ JOIN CHANNEL"
        else:
            if statuses.get(chat_id) is True:
                label = "✅ JOINED"
            elif statuses.get(chat_id) is False:
                label = "🚫 NOT JOINED"
            else:
                label = "✨ JOIN CHANNEL"
        row.append(InlineKeyboardButton(label, url=url))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    if channels:
        keyboard.append([InlineKeyboardButton("🔄 VERIFY", callback_data="verify_membership")])
    return InlineKeyboardMarkup(keyboard) if keyboard else None

async def copy_saved_message(context, destination, saved_message, reply_markup=None):
    if not isinstance(saved_message, dict):
        return None
    source_chat = saved_message.get("chat_id")
    source_message = saved_message.get("message_id")
    if source_chat is None or source_message is None:
        return None
    try:
        return await context.bot.copy_message(
            chat_id=destination,
            from_chat_id=source_chat,
            message_id=source_message,
            reply_markup=reply_markup
        )
    except TelegramError:
        logger.exception("Message copy failed")
        return None

async def send_final_contents(context, user_id):
    config = load_config()
    if user_id in config["completed_users"]:
        return
    saved_messages = config["final_messages"]
    if not saved_messages:
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Verification complete.\nNo final content is configured yet."
        )
        return
    success = 0
    failed = 0
    for saved in saved_messages:
        result = await copy_saved_message(context, user_id, saved)
        if result:
            success += 1
        else:
            failed += 1
        await asyncio.sleep(0.15)
    if failed == 0:
        config = load_config()
        if user_id not in config["completed_users"]:
            config["completed_users"].append(user_id)
            save_config(config)
        await refresh_admin_dashboard(context.bot)
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "⚠️ Some content could not be delivered.\n"
                f"✅ Delivered: {success}\n"
                f"❌ Failed: {failed}\n"
                "Please press VERIFY again to retry."
            )
        )

# =========================================================
# USER STAGES
# =========================================================
def default_user_welcome():
    return (
        "👑 <b>WELCOME TO SAKIL BHAI VIP</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 <b>VIP ACCESS VERIFICATION</b>\n\n"
        "1️⃣ Join all channels shown below.\n"
        "2️⃣ Press VERIFY to check.\n"
        "3️⃣ Complete all channel verification steps.\n\n"
        "🎁 Your content will unlock automatically.\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

async def send_stage_message(context, user_id, channels, statuses, request_mode=False):
    config = load_config()
    keyboard = build_channel_keyboard(channels, statuses, request_mode)
    welcome = config.get("welcome_message")
    if welcome:
        copied = await copy_saved_message(context, user_id, welcome, reply_markup=keyboard)
        if copied:
            return
    if request_mode:
        text = (
            "👑 <b>VIP ACCESS VERIFICATION</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "✨ Open every channel below and complete the joining step.\n\n"
            "📨 Your request will be recorded automatically.\n"
            "🔄 Press VERIFY after completing all channels."
        )
    else:
        text = default_user_welcome()
    await context.bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def show_current_stage(context, user_id):
    config = load_config()
    if user_id in config["completed_users"]:
        return
    main_channels = config["channels"]
    main_status = await get_membership_status(user_id, context, main_channels)
    if not all(main_status.values()):
        config = load_config()
        if user_id in config["main_passed"]:
            config["main_passed"].remove(user_id)
            save_config(config)
        await send_stage_message(context, user_id, main_channels, main_status)
        return
    
    config = load_config()
    if user_id not in config["main_passed"]:
        config["main_passed"].append(user_id)
        save_config(config)
    
    config = load_config()
    extra_channels = config["fake_channels"]
    if not extra_channels:
        await send_final_contents(context, user_id)
        return
    if all_extra_requests_received(config, user_id):
        await send_final_contents(context, user_id)
        return
    
    requests = get_user_extra_requests(config, user_id)
    extra_status = {
        str(channel["chat_id"]): str(channel["chat_id"]) in requests
        for channel in extra_channels
    }
    await send_stage_message(context, user_id, extra_channels, extra_status, request_mode=True)

# =========================================================
# START & HANDLERS
# =========================================================
async def start(update, context):
    if not update.message:
        return
    user = update.effective_user
    if not user:
        return
    if user.id == ADMIN_ID:
        ADMIN_STATE.pop(user.id, None)
        await show_admin_dashboard(update.message, context)
        return
    
    user_id = user.id
    config = load_config()
    if user_id not in config["subscribers"]:
        config["subscribers"].append(user_id)
        save_config(config)
        await refresh_admin_dashboard(context.bot)
    
    if user_id in config["completed_users"]:
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Your VIP verification is already completed."
        )
        return
    await show_current_stage(context, user_id)

async def extra_join_request_handler(update, context):
    request = update.chat_join_request
    if not request:
        return
    user_id = request.from_user.id
    chat_id = str(request.chat.id)
    config = load_config()
    matched = any(
        str(channel.get("chat_id")) == chat_id
        for channel in config["fake_channels"]
    )
    if not matched:
        return
    if user_id not in config["subscribers"]:
        config["subscribers"].append(user_id)
    requests = config["extra_requests"].setdefault(str(user_id), [])
    if chat_id not in requests:
        requests.append(chat_id)
    if not save_config(config):
        logger.error("Could not save Join Request")
        return
    await refresh_admin_dashboard(context.bot)
    
    config = load_config()
    main_status = await get_membership_status(user_id, context, config["channels"])
    if not all(main_status.values()):
        return
    if user_id not in config["main_passed"]:
        config["main_passed"].append(user_id)
        save_config(config)
    
    config = load_config()
    if all_extra_requests_received(config, user_id):
        await send_final_contents(context, user_id)
        return
    
    received = get_user_extra_requests(config, user_id)
    total = len(config["fake_channels"])
    await context.bot.send_message(
        chat_id=user_id,
        text=(
            f"📨 Channel verification: {len(received)}/{total}\n"
            "Complete the remaining channels to continue."
        )
    )

async def verify_handler(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if user_id == ADMIN_ID:
        return
    config = load_config()
    if user_id in config["completed_users"]:
        await query.answer("Already verified.", show_alert=True)
        return
    
    main_channels = config["channels"]
    main_status = await get_membership_status(user_id, context, main_channels)
    if not all(main_status.values()):
        config = load_config()
        if user_id in config["main_passed"]:
            config["main_passed"].remove(user_id)
            save_config(config)
        keyboard = build_channel_keyboard(main_channels, main_status)
        try:
            await query.message.edit_reply_markup(reply_markup=keyboard)
        except TelegramError:
            pass
        await query.answer("Please join all channels first.", show_alert=True)
        return
    
    config = load_config()
    if user_id not in config["main_passed"]:
        config["main_passed"].append(user_id)
        save_config(config)
    
    config = load_config()
    extra_channels = config["fake_channels"]
    if extra_channels:
        if not all_extra_requests_received(config, user_id):
            requests = get_user_extra_requests(config, user_id)
            extra_status = {
                str(channel["chat_id"]): str(channel["chat_id"]) in requests
                for channel in extra_channels
            }
            keyboard = build_channel_keyboard(extra_channels, extra_status, request_mode=True)
            try:
                await query.message.edit_reply_markup(reply_markup=keyboard)
            except TelegramError:
                pass
            await query.answer(f"Completed: {len(requests)}/{len(extra_channels)}", show_alert=True)
            return
    
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except TelegramError:
        pass
    await send_final_contents(context, user_id)

# =========================================================
# ADMIN CALLBACKS & MENUS
# =========================================================
async def show_broadcast_targets(message, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 ALL BOT USERS", callback_data="target_users")],
        [InlineKeyboardButton("📢 ALL CHANNELS", callback_data="target_channels")],
        [InlineKeyboardButton("🚀 USERS + CHANNELS", callback_data="target_both")],
    ])
    global ADMIN_TRANSIENT_ID
    if ADMIN_TRANSIENT_ID:
        await delete_message_safely(context.bot, ADMIN_ID, ADMIN_TRANSIENT_ID)
    
    sent = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="📢 <b>BROADCAST CENTER</b>\n\nChoose where to publish:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    ADMIN_TRANSIENT_ID = sent.message_id

async def show_manage_channels(chat_id, context):
    config = load_config()
    rows = [
        [InlineKeyboardButton(f"📢 MAIN ({len(config['channels'])})", callback_data="manage_main")],
        [InlineKeyboardButton(f"🔒 EXTRA ({len(config['fake_channels'])})", callback_data="manage_extra")],
    ]
    global ADMIN_TRANSIENT_ID
    if ADMIN_TRANSIENT_ID:
        await delete_message_safely(context.bot, ADMIN_ID, ADMIN_TRANSIENT_ID)
    
    sent = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="🗂 <b>CHANNEL MANAGER</b>\nChoose which group to view or delete.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows)
    )
    ADMIN_TRANSIENT_ID = sent.message_id

async def show_channel_list(query, context, group):
    config = load_config()
    key = "channels" if group == "main" else "fake_channels"
    channels = config[key]
    title = "MAIN CHANNELS" if group == "main" else "EXTRA CHANNELS"
    rows = []
    for index, channel in enumerate(channels):
        name = str(channel.get("name") or channel.get("chat_id"))[:35]
        rows.append([InlineKeyboardButton(f"🗑 {index + 1}. {name}", callback_data=f"askdel:{group}:{index}")])
    rows.append([InlineKeyboardButton("🔙 BACK", callback_data="manage_back")])
    body = f"📋 <b>{title}</b> — Total: <b>{len(channels)}</b>\n\n"
    if channels:
        body += "Tap a channel to request deletion. It will not be deleted until you confirm."
    else:
        body += "No channel added in this group."
    await query.edit_message_text(body, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))

async def button_handler(update, context):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    if data == "verify_membership":
        await verify_handler(update, context)
        return
    if user_id != ADMIN_ID:
        await query.answer("Unauthorized.", show_alert=True)
        return
    await query.answer()

    if data == "manage_main":
        await show_channel_list(query, context, "main")
        return
    if data == "manage_extra":
        await show_channel_list(query, context, "extra")
        return
    if data == "manage_back":
        config = load_config()
        rows = [
            [InlineKeyboardButton(f"📢 MAIN ({len(config['channels'])})", callback_data="manage_main")],
            [InlineKeyboardButton(f"🔒 EXTRA ({len(config['fake_channels'])})", callback_data="manage_extra")],
        ]
        await query.edit_message_text("🗂 <b>CHANNEL MANAGER</b>\nChoose a group:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return
    if data.startswith("askdel:"):
        try:
            _, group, raw_index = data.split(":", 2)
            index = int(raw_index)
            key = "channels" if group == "main" else "fake_channels"
            config = load_config()
            channel = config[key][index]
        except (ValueError, IndexError, KeyError):
            await query.edit_message_text("⚠️ Channel list changed. Open Manage Channels again.")
            return
        label = html.escape(str(channel.get('name') or channel.get('chat_id')))
        confirm = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ CONFIRM DELETE", callback_data=f"confirmdel:{group}:{index}")],
            [InlineKeyboardButton("❌ CANCEL", callback_data=f"canceldelete:{group}")],
        ])
        await query.edit_message_text(
            f"⚠️ <b>DELETE CONFIRMATION</b>\n\nChannel: <b>{label}</b>\nID: <code>{html.escape(str(channel.get('chat_id')))}</code>\n\nAre you sure you want to delete this channel?",
            parse_mode="HTML",
            reply_markup=confirm
        )
        return
    if data.startswith("canceldelete:"):
        group = data.split(":", 1)[1]
        await show_channel_list(query, context, group)
        return
    if data.startswith("confirmdel:"):
        try:
            _, group, raw_index = data.split(":", 2)
            index = int(raw_index)
            key = "channels" if group == "main" else "fake_channels"
            config = load_config()
            removed = config[key].pop(index)
            if not save_config(config):
                raise OSError("Could not save config")
        except (ValueError, IndexError, KeyError, OSError):
            await query.edit_message_text("❌ Delete failed. Refresh Manage Channels.")
            return
        await refresh_admin_dashboard(context.bot)
        await query.edit_message_text(
            f"✅ Deleted: <b>{html.escape(str(removed.get('name') or removed.get('chat_id')))}</b>\nUpdated channel count: {len(config[key])}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 CHANNEL MANAGER", callback_data="manage_back")]])
        )
        return
    if data in ("target_users", "target_channels", "target_both"):
        target = data.replace("target_", "")
        ADMIN_STATE[user_id] = {"type": "waiting_broadcast", "target": target}
        
        # Purono option delete kore notun prompt ashbe
        global ADMIN_TRANSIENT_ID
        if ADMIN_TRANSIENT_ID:
            await delete_message_safely(context.bot, ADMIN_ID, ADMIN_TRANSIENT_ID)
        
        sent = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="📢 Send the broadcast message now.\nText, photo, video, GIF and document are supported.",
            reply_markup=ADMIN_KEYBOARD
        )
        ADMIN_TRANSIENT_ID = sent.message_id
        return
    if data == "final_done":
        state = ADMIN_STATE.get(user_id, {})
        if state.get("type") != "waiting_final":
            await admin_notice(query.message, context, "⚠️ No active Final Content collection.")
            return
        ADMIN_STATE.pop(user_id, None)
        config = load_config()
        await refresh_admin_dashboard(context.bot)
        await admin_notice(
            query.message,
            context,
            f"👑 <b>FINAL CONTENT SAVED</b>\n\n🎁 Total items: <b>{len(config['final_messages'])}</b>\nAll items will be sent after verification.",
            parse_mode="HTML"
        )
        return

async def handle_admin_menu(message, context):
    user_id = message.from_user.id
    text = (message.text or "").strip()
    await delete_message_safely(context.bot, message.chat_id, message.message_id)

    if text == "🏠 ADMIN HOME":
        ADMIN_STATE.pop(user_id, None)
        await show_admin_dashboard(message, context)
        return
    if text == "❌ CANCEL":
        ADMIN_STATE.pop(user_id, None)
        await admin_notice(message, context, "❌ Current operation cancelled.")
        return
    if text == "📢 BROADCAST":
        ADMIN_STATE.pop(user_id, None)
        await show_broadcast_targets(message, context)
        return
    if text == "🗂 MANAGE CHANNELS":
        ADMIN_STATE.pop(user_id, None)
        await refresh_admin_dashboard(context.bot)
        await show_manage_channels(ADMIN_ID, context)
        return
    if text == "➕ MAIN CHANNEL":
        ADMIN_STATE[user_id] = {"type": "waiting_main_channel"}
        await admin_notice(message, context, "📢 ADD MAIN CHANNEL\n\nSend:\nhttps://t.me/channelname | -100123456789")
        return
    if text == "➕ EXTRA CHANNEL":
        ADMIN_STATE[user_id] = {"type": "waiting_extra_channel"}
        await admin_notice(message, context, "🔒 ADD EXTRA CHANNEL\n\nPrivate Join-Request invite link required.\n\nSend:\nhttps://t.me/+INVITECODE | -100123456789")
        return
    if text == "🖼 WELCOME":
        ADMIN_STATE[user_id] = {"type": "waiting_welcome"}
        await admin_notice(message, context, "🖼 Send your Welcome Message now.\nText, photo, video, GIF or document supported.")
        return
    if text == "🎁 FINAL CONTENT":
        config = load_config()
        config["final_messages"] = []
        if not save_config(config):
            await admin_notice(message, context, "❌ Could not reset Final Content.")
            return
        ADMIN_STATE[user_id] = {"type": "waiting_final"}
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ DONE / FINISH", callback_data="final_done")]])
        
        global ADMIN_TRANSIENT_ID
        if ADMIN_TRANSIENT_ID:
            await delete_message_safely(context.bot, ADMIN_ID, ADMIN_TRANSIENT_ID)
        sent = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="🎁 <b>MULTIPLE FINAL CONTENT MODE</b>\n\nSend every item one by one.\nWhen finished, press DONE / FINISH.\n\n⚠️ This replaces the previous collection.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        ADMIN_TRANSIENT_ID = sent.message_id
        await refresh_admin_dashboard(context.bot)
        return
    if text == "📋 BOT STATUS":
        config = load_config()
        await refresh_admin_dashboard(context.bot)
        await admin_notice(
            message,
            context,
            f"📊 BOT STATUS\n\n👥 Users: {len(config['subscribers'])}\n📢 Main channels: {len(config['channels'])}\n🔒 Extra channels: {len(config['fake_channels'])}\n🎁 Final items: {len(config['final_messages'])}\n✅ Completed: {len(config['completed_users'])}"
        )
        return

async def admin_message_handler(update, context):
    message = update.message
    user = update.effective_user
    if not message or not user or user.id != ADMIN_ID:
        return
    menu_buttons = {
        "📢 BROADCAST", "➕ MAIN CHANNEL", "➕ EXTRA CHANNEL",
        "🗂 MANAGE CHANNELS", "🖼 WELCOME", "🎁 FINAL CONTENT",
        "📋 BOT STATUS", "🏠 ADMIN HOME", "❌ CANCEL"
    }
    if message.text in menu_buttons:
        await handle_admin_menu(message, context)
        return

    state_data = ADMIN_STATE.get(user.id, {})
    state = state_data.get("type")

    if state == "waiting_welcome":
        config = load_config()
        config["welcome_message"] = {"chat_id": message.chat_id, "message_id": message.message_id}
        if save_config(config):
            ADMIN_STATE.pop(user.id, None)
            await admin_notice(message, context, "✅ Welcome Message saved successfully.")
        else:
            await admin_notice(message, context, "❌ Could not save Welcome Message.")
        return

    if state == "waiting_final":
        config = load_config()
        config["final_messages"].append({"chat_id": message.chat_id, "message_id": message.message_id})
        if save_config(config):
            await refresh_admin_dashboard(context.bot)
            await admin_notice(message, context, f"✅ Final item #{len(config['final_messages'])} saved.\nSend next item or press DONE / FINISH.")
        else:
            await admin_notice(message, context, "❌ Could not save this item.")
        return

    if state == "waiting_broadcast":
        target = state_data.get("target", "users")
        ADMIN_STATE.pop(user.id, None)
        config = load_config()
        destinations = []
        if target in ("users", "both"):
            destinations.extend(("user", uid) for uid in config["subscribers"])
        if target in ("channels", "both"):
            destinations.extend(("channel", channel["chat_id"]) for channel in get_all_channels(config))
        if not destinations:
            await admin_notice(message, context, "⚠️ No broadcast destinations found.")
            return
        
        progress = await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 Broadcast started: {len(destinations)} destinations.")
        success = 0
        failed = 0
        blocked_users = []
        for destination_type, destination_id in destinations:
            ok = await broadcast_copy(context, destination_id, message.chat_id, message.message_id)
            if ok:
                success += 1
            else:
                failed += 1
                if destination_type == "user":
                    blocked_users.append(destination_id)
            await asyncio.sleep(0.05)
        
        if blocked_users:
            config = load_config()
            config["subscribers"] = [uid for uid in config["subscribers"] if uid not in blocked_users]
            save_config(config)
        
        await delete_message_safely(context.bot, message.chat_id, message.message_id)
        await refresh_admin_dashboard(context.bot)
        try:
            await progress.edit_text(
                f"🚀 <b>BROADCAST COMPLETE</b>\n\n🎯 Targets: {len(destinations)}\n✅ Success: {success}\n❌ Failed: {failed}\n🧹 Removed unreachable: {len(blocked_users)}",
                parse_mode="HTML"
            )
        except TelegramError:
            pass
        return

    if state in ("waiting_main_channel", "waiting_extra_channel"):
        raw = message.text or ""
        if "|" not in raw:
            await admin_notice(message, context, "❌ Invalid format.\n\nhttps://t.me/channelname | -100123456789")
            return
        url, chat_id = [part.strip() for part in raw.split("|", 1)]
        if not re.match(r"^https?://t\.me/[^\s]+$", url):
            await admin_notice(message, context, "❌ Invalid Telegram URL.")
            return
        if not re.match(r"^(-100\d+|@\w+|\d+)$", chat_id):
            await admin_notice(message, context, "❌ Invalid Channel ID.")
            return
        stored_id = int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id
        config = load_config()
        duplicate = any(str(channel.get("chat_id")) == str(stored_id) for channel in get_all_channels(config))
        if duplicate:
            ADMIN_STATE.pop(user.id, None)
            await refresh_admin_dashboard(context.bot)
            await admin_notice(message, context, "⚠️ This channel is already saved.\nUse MANAGE CHANNELS to view or delete it.")
            return
        
        key = "channels" if state == "waiting_main_channel" else "fake_channels"
        name = url.rstrip("/").split("/")[-1]
        try:
            chat = await context.bot.get_chat(stored_id)
            if getattr(chat, "title", None):
                name = chat.title
        except TelegramError:
            pass
        
        config[key].append({"name": name, "url": url, "chat_id": stored_id})
        if save_config(config):
            ADMIN_STATE.pop(user.id, None)
            await delete_message_safely(context.bot, message.chat_id, message.message_id)
            await refresh_admin_dashboard(context.bot)
            await admin_notice(message, context, f"✅ Channel added successfully.\n📢 Main total: {len(config['channels'])}\n🔒 Extra total: {len(config['fake_channels'])}")
        else:
            await admin_notice(message, context, "❌ Could not save channel.")
        return

async def broadcast_copy(context, destination, source_chat, source_message):
    for attempt in range(2):
        try:
            await context.bot.copy_message(
                chat_id=destination,
                from_chat_id=source_chat,
                message_id=source_message
            )
            return True
        except RetryAfter as error:
            if attempt == 0:
                await asyncio.sleep(float(error.retry_after) + 1)
        except TelegramError as error:
            logger.warning("Broadcast failed for %s: %s", destination, error)
            return False
    return False

async def cancel_command(update, context):
    user = update.effective_user
    if not user or user.id != ADMIN_ID:
        return
    ADMIN_STATE.pop(user.id, None)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="❌ Current operation cancelled.",
        reply_markup=ADMIN_KEYBOARD
    )

async def error_handler(update, context):
    logger.exception("Unhandled bot error: %s", context.error)

# =========================================================
# MAIN
# =========================================================
def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is missing.")
    request = HTTPXRequest(connect_timeout=30, read_timeout=60, write_timeout=60, pool_timeout=30)
    app = ApplicationBuilder().token(TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(ChatJoinRequestHandler(extra_join_request_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, admin_message_handler))
    app.add_error_handler(error_handler)

    print("==========================================")
    print(" SAKIL BHAI VIP TELEGRAM BOT READY")
    print("==========================================")
    app.run_polling(drop_pending_updates=False, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
