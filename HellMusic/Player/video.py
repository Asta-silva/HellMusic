import os
import re
import asyncio
import aiohttp
import aiofiles

from Config import ASSISTANT_NAME, BOT_USERNAME, IMG_1, IMG_2, IMG_6
from HellMusic.inline import stream_markup
from Process.fonts import CHAT_TITLE
from PIL import Image, ImageDraw, ImageFont
from Process.filters import command, other_filters
from Process.queues import QUEUE, add_to_queue
from ImageFont.main import call_py, user
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioVideoPiped
from pytgcalls.types.input_stream.quality import (
    HighQualityAudio,
    HighQualityVideo,
    LowQualityVideo,
    MediumQualityVideo,
)
from youtubesearchpython import VideosSearch


def ytsearch(query: str):
    try:
        search = VideosSearch(query, limit=1).result()
        data = search["result"][0]
        songname = data["title"]
        url = data["link"]
        duration = data["duration"]
        thumbnail = f"https://i.ytimg.com/vi/{data['id']}/hqdefault.jpg"
        return [songname, url, duration, thumbnail]
    except Exception as e:
        print(e)
        return 0


async def ytdl(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "best[height<=?720][width<=?1280]",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()

def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw", 
        format="s16le", 
        acodec="pcm_s16le", 
        ac=2, 
        ar="48k"
    ).overwrite_output().run()
    os.remove(filename)

def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)

def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))



def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def generate_cover(thumbnail, title, userid, ctitle):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open(f"thumb{userid}.png", mode="wb")
                await f.write(await resp.read())
                await f.close()
    image1 = Image.open(f"thumb{userid}.png")
    image2 = Image.open("ImageFont/raichux.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save(f"temp{userid}.png")
    img = Image.open(f"temp{userid}.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("ImageFont/finalfont.ttf", 60)
    font2 = ImageFont.truetype("ImageFont/finalfont.ttf", 70)     
    draw.text((20, 45), f"{title[:30]}...", fill= "white", stroke_width = 1, stroke_fill="white", font=font2)
    draw.text((120, 595), f"Playing on: {ctitle[:20]}...", fill="white", stroke_width = 1, stroke_fill="white" ,font=font)
    img.save(f"final{userid}.png")
    os.remove(f"temp{userid}.png")
    os.remove(f"thumb{userid}.png") 
    final = f"final{userid}.png"
    return final


@Client.on_message(command(["vplay", f"vplay@{BOT_USERNAME}"]) & other_filters)
async def vplay(c: Client, m: Message):
    await m.delete()
    replied = m.reply_to_message
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text("you're an __Anonymous__ Admin !\n\n» revert back to user account from admin rights.")
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"error:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status != "administrator":
        await m.reply_text(
            f"💡 To use me, I need to be an **Administrator** with the following **permissions**:\n\n» ❌ __Delete messages__\n» ❌ __Invite users__\n» ❌ __Manage video chat__\n\nOnce done, type /reload"
        )
        return
    if not a.can_manage_voice_chats:
        await m.reply_text(
        "💡 To use me, Give me the following permission below:"
        + "\n\n» ❌ __Manage video chat__\n\nOnce done, try again.")
        return
    if not a.can_delete_messages:
        await m.reply_text(
        "💡 To use me, Give me the following permission below:"
        + "\n\n» ❌ __Delete messages__\n\nOnce done, try again.")
        return
    if not a.can_invite_users:
        await m.reply_text(
        "💡 To use me, Give me the following permission below:"
        + "\n\n» ❌ __Add users__\n\nOnce done, try again.")
        return
    try:
        ubot = (await user.get_me()).id
        b = await c.get_chat_member(chat_id, ubot) 
        if b.status == "kicked":
            await c.unban_chat_member(chat_id, ubot)
            invitelink = await c.export_chat_invite_link(chat_id)
            if invitelink.startswith("https://t.me/+"):
                    invitelink = invitelink.replace(
                        "https://t.me/+", "https://t.me/joinchat/"
                    )
            await user.join_chat(invitelink)
    except UserNotParticipant:
        try:
            invitelink = await c.export_chat_invite_link(chat_id)
            if invitelink.startswith("https://t.me/+"):
                    invitelink = invitelink.replace(
                        "https://t.me/+", "https://t.me/joinchat/"
                    )
            await user.join_chat(invitelink)
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            return await m.reply_text(
                f"❌ **userbot failed to join**\n\n**reason**: `{e}`"
            )

    if replied:
        if replied.video or replied.document:
            loser = await replied.reply("📥 **downloading video...**")
            dl = await replied.download()
            link = replied.link
            if len(m.command) < 2:
                Q = 720
            else:
                pq = m.text.split(None, 1)[1]
                if pq == "720" or "480" or "360":
                    Q = int(pq)
                else:
                    Q = 720
                    await loser.edit(
                        "» __only 720, 480, 360 allowed__ \n💡 **now streaming video in 720p**"
                    )
            try:
                if replied.video:
                    songname = replied.video.file_name[:70]
                elif replied.document:
                    songname = replied.document.file_name[:70]
            except BaseException:
                songname = "Video"

            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, songname, dl, link, "Video", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=thumbnail,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"💡 **Track added to queue »** `{pos}`\n\n🗂 **Name:** [{songname}]({link}) | `video`\n💭 **Chat:** `{chat_id}`\n🧸 **Request by:** {requester}",
                )
            else:
                if Q == 720:
                    amaze = HighQualityVideo()
                elif Q == 480:
                    amaze = MediumQualityVideo()
                elif Q == 360:
                    amaze = LowQualityVideo()
                await loser.edit("🔄 **Joining vc...**")
                await call_py.join_group_call(
                    chat_id,
                    AudioVideoPiped(
                        dl,
                        HighQualityAudio(),
                        amaze,
                    ),
                    stream_type=StreamType().local_stream,
                )
                add_to_queue(chat_id, songname, dl, link, "Video", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=thumbnail,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"🗂 **Name:** [{songname}]({link}) | `video`\n💭 **Chat:** `{chat_id}`\n🧸 **Request by:** {requester}",
                )
        else:
            if len(m.command) < 2:
                await m.reply_photo(
                     photo=f"{IMG_6}",
                    caption="💬**Usage: /play Give a Title Song To Play Music or /vplay for Video Play**"
                    ,
                      reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("💭 Support", url=f"https://t.me/Freia_Support")
                        ],
                        [
                            InlineKeyboardButton("🗑 Close", callback_data="cls")
                        ]
                    ]
                )
            )
            else:
                loser = await c.send_message(chat_id, "🔍 **Searching...**")
                query = m.text.split(None, 1)[1]
                search = ytsearch(query)
                Q = 720
                amaze = HighQualityVideo()
                if search == 0:
                    await loser.edit("❌ **no results found.**")
                else:
                    songname = search[0]
                    title = search[0]
                    url = search[1]
                    duration = search[2]
                    thumbnail = search[3]
                    userid = m.from_user.id
                    gcname = m.chat.title
                    ctitle = await CHAT_TITLE(gcname)
                    image = await thumb(thumbnail, title, userid, ctitle)
                    abhi, ytlink = await ytdl(url)
                    if abhi == 0:
                        await loser.edit(f"❌ yt-dl issues detected\n\n» `{ytlink}`")
                    else:
                        if chat_id in QUEUE:
                            pos = add_to_queue(
                                chat_id, songname, ytlink, url, "Video", Q
                            )
                            await loser.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            buttons = stream_markup(user_id)
                            await m.reply_photo(
                                photo=image,
                                reply_markup=InlineKeyboardMarkup(buttons),
                                caption=f"💡 **Track added to queue »** `{pos}`\n\n🗂 **Name:** [{songname}]({url}) | `video`\n⏱ **Duration:** `{duration}`\n🧸 **Request by:** {requester}",
                            )
                        else:
                            try:
                                await loser.edit("🔄 **Joining vc...**")
                                await call_py.join_group_call(
                                    chat_id,
                                    AudioVideoPiped(
                                        ytlink,
                                        HighQualityAudio(),
                                        amaze,
                                    ),
                                    stream_type=StreamType().local_stream,
                                )
                                add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                                await loser.delete()
                                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                                buttons = stream_markup(user_id)
                                await m.reply_photo(
                                    photo=image,
                                    reply_markup=InlineKeyboardMarkup(buttons),
                                    caption=f"🗂 **Name:** [{songname}]({url}) | `video`\n⏱ **Duration:** `{duration}`\n🧸 **Request by:** {requester}",
                                )
                            except Exception as ep:
                                await loser.delete()
                                await m.reply_text(f"🚫 error: `{ep}`")

    else:
        if len(m.command) < 2:
            await m.reply_photo(
                     photo=f"{IMG_6}",
                    caption="💬**Usage: /play Give a Title Song To Play Music or /vplay for Video Play**"
                    ,
                      reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("💭 Support", url=f"https://t.me/Freia_Support")
                        ],
                        [
                            InlineKeyboardButton("🗑 Close", callback_data="cls")
                        ]
                    ]
                )
            )
        else:
            loser = await c.send_message(chat_id, "🔍 **Searching...**")
            query = m.text.split(None, 1)[1]
            search = ytsearch(query)
            Q = 720
            amaze = HighQualityVideo()
            if search == 0:
                await loser.edit("❌ **no results found.**")
            else:
                songname = search[0]
                title = search[0]
                url = search[1]
                duration = search[2]
                thumbnail = search[3]
                userid = m.from_user.id
                gcname = m.chat.title
                ctitle = await CHAT_TITLE(gcname)
                image = await generate_cover(thumbnail, title, userid, ctitle)
                abhi, ytlink = await ytdl(url)
                if abhi == 0:
                    await loser.edit(f"❌ yt-dl issues detected\n\n» `{ytlink}`")
                else:
                    if chat_id in QUEUE:
                        pos = add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                        await loser.delete()
                        requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                        buttons = stream_markup(user_id)
                        await m.reply_photo(
                            photo=image,
                            reply_markup=InlineKeyboardMarkup(buttons),
                            caption=f"💡 **Track added to queue »** `{pos}`\n\n🗂 **Name:** [{songname}]({url}) | `video`\n⏱ **Duration:** `{duration}`\n🧸 **Request by:** {requester}",
                        )
                    else:
                        try:
                            await loser.edit("🔄 **Joining vc...**")
                            await call_py.join_group_call(
                                chat_id,
                                AudioVideoPiped(
                                    ytlink,
                                    HighQualityAudio(),
                                    amaze,
                                ),
                                stream_type=StreamType().local_stream,
                            )
                            add_to_queue(chat_id, songname, ytlink, url, "Video", Q)
                            await loser.delete()
                            requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                            buttons = stream_markup(user_id)
                            await m.reply_photo(
                                photo=image,
                                reply_markup=InlineKeyboardMarkup(buttons),
                                caption=f"🗂 **Name:** [{songname}]({url}) |`video`\n⏱ **Duration:** `{duration}`\n🧸 **Request by:** {requester}",
                            )
                        except Exception as ep:
                            await loser.delete()
                            await m.reply_text(f"🚫 error: `{ep}`")


@Client.on_message(command(["vstream", f"vstream@{BOT_USERNAME}"]) & other_filters)
async def vstream(c: Client, m: Message):
    await m.delete()
    chat_id = m.chat.id
    user_id = m.from_user.id
    if m.sender_chat:
        return await m.reply_text("you're an __Anonymous__ Admin !\n\n» revert back to user account from admin rights.")
    try:
        aing = await c.get_me()
    except Exception as e:
        return await m.reply_text(f"error:\n\n{e}")
    a = await c.get_chat_member(chat_id, aing.id)
    if a.status != "administrator":
        await m.reply_text(
            f"💡 To use me, I need to be an **Administrator** with the following **permissions**:\n\n» ❌ __Delete messages__\n» ❌ __Invite users__\n» ❌ __Manage video chat__\n\nOnce done, type /reload"
        )
        return
    if not a.can_manage_voice_chats:
        await m.reply_text(
        "💡 To use me, Give me the following permission below:"
        + "\n\n» ❌ __Manage video chat__\n\nOnce done, try again.")
        return
    if not a.can_delete_messages:
        await m.reply_text(
        "💡 To use me, Give me the following permission below:"
        + "\n\n» ❌ __Delete messages__\n\nOnce done, try again.")
        return
    if not a.can_invite_users:
        await m.reply_text(
        "💡 To use me, Give me the following permission below:"
        + "\n\n» ❌ __Add users__\n\nOnce done, try again.")
        return
    try:
        ubot = (await user.get_me()).id
        b = await c.get_chat_member(chat_id, ubot) 
        if b.status == "kicked":
            await c.unban_chat_member(chat_id, ubot)
            invitelink = await c.export_chat_invite_link(chat_id)
            if invitelink.startswith("https://t.me/+"):
                    invitelink = invitelink.replace(
                        "https://t.me/+", "https://t.me/joinchat/"
                    )
            await user.join_chat(invitelink)
    except UserNotParticipant:
        try:
            invitelink = await c.export_chat_invite_link(chat_id)
            if invitelink.startswith("https://t.me/+"):
                    invitelink = invitelink.replace(
                        "https://t.me/+", "https://t.me/joinchat/"
                    )
            await user.join_chat(invitelink)
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            return await m.reply_text(
                f"❌ **userbot failed to join**\n\n**reason**: `{e}`"
            )

    if len(m.command) < 2:
        await m.reply("» give me a live-link/m3u8 url/youtube link to stream.")
    else:
        if len(m.command) == 2:
            link = m.text.split(None, 1)[1]
            Q = 720
            loser = await c.send_message(chat_id, "🔄 **processing stream...**")
        elif len(m.command) == 3:
            op = m.text.split(None, 1)[1]
            link = op.split(None, 1)[0]
            quality = op.split(None, 1)[1]
            if quality == "720" or "480" or "360":
                Q = int(quality)
            else:
                Q = 720
                await m.reply(
                    "» __only 720, 480, 360 allowed__ \n💡 **now streaming video in 720p**"
                )
            loser = await c.send_message(chat_id, "🔄 **processing stream...**")
        else:
            await m.reply("**/vstream {link} {720/480/360}**")

        regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
        match = re.match(regex, link)
        if match:
            abhi, livelink = await ytdl(link)
        else:
            livelink = link
            abhi = 1

        if abhi == 0:
            await loser.edit(f"❌ yt-dl issues detected\n\n» `{livelink}`")
        else:
            if chat_id in QUEUE:
                pos = add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
                await loser.delete()
                requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                buttons = stream_markup(user_id)
                await m.reply_photo(
                    photo=f"{IMG_1}",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"💡 **Track added to queue »** `{pos}`\n\n💭 **Chat:** `{chat_id}`\n🧸 **Request by:** {requester}",
                )
            else:
                if Q == 720:
                    amaze = HighQualityVideo()
                elif Q == 480:
                    amaze = MediumQualityVideo()
                elif Q == 360:
                    amaze = LowQualityVideo()
                try:
                    await loser.edit("🔄 **Joining vc...**")
                    await call_py.join_group_call(
                        chat_id,
                        AudioVideoPiped(
                            livelink,
                            HighQualityAudio(),
                            amaze,
                        ),
                        stream_type=StreamType().live_stream,
                    )
                    add_to_queue(chat_id, "Live Stream", livelink, link, "Video", Q)
                    await loser.delete()
                    requester = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
                    buttons = stream_markup(user_id)
                    await m.reply_photo(
                        photo=f"{IMG_2}",
                        reply_markup=InlineKeyboardMarkup(buttons),
                        caption=f"💡 **[Video Live]({link}) stream started.**\n\n💭 **Chat:** `{chat_id}`\n🧸 **Request by:** {requester}",
                    )
                except Exception as ep:
                    await loser.delete()
                    await m.reply_text(f"🚫 error: `{ep}`")
#
#WHAT'S UP KANGERS
