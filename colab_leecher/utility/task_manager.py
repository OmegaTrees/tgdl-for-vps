# copyright 2024 © Xron Trix | https://github.com/Xrontrix10


import pytz
import shutil
import logging
from time import time
from datetime import datetime
from asyncio import sleep
from os import makedirs, path as ospath, system, listdir
from colab_leecher import OWNER, colab_bot, DUMP_ID
from colab_leecher.downloader.manager import calDownSize, get_d_name, downloadManager
from colab_leecher.utility.helper import (
    getSize,
    applyCustomName,
    keyboard,
    sysINFO,
    is_google_drive,
    is_telegram,
    is_ytdl_link,
    is_mega,
    is_terabox,
    sizeUnit,
    is_torrent,
)
from colab_leecher.utility.handler import (
    Leech,
    Unzip_Handler,
    Zip_Handler,
    SendLogs,
    cancelTask,
)
from colab_leecher.utility.variables import (
    BOT,
    MSG,
    BotTimes,
    Messages,
    Paths,
    Aria2c,
    Transfer,
    TaskError,
)


async def task_starter(message, text):
    global BOT
    await message.delete()
    BOT.State.started = True
    if BOT.State.task_going == False:
        src_request_msg = await message.reply_text(text)
        return src_request_msg
    else:
        msg = await message.reply_text(
            "I am already working ! Please wait until I finish !!"
        )
        await sleep(15)
        await msg.delete()
        return None


async def taskScheduler():
    global BOT, MSG, BotTimes, Messages, Paths, Transfer, TaskError
    src_text = []
    is_dualzip, is_unzip, is_zip, is_dir = (
        BOT.Mode.type == "undzip",
        BOT.Mode.type == "unzip",
        BOT.Mode.type == "zip",
        BOT.Mode.mode == "dir-leech",
    )
    # Reset Texts
    Messages.download_name = ""
    Messages.task_msg = f"<b>🦞 TASK MODE » </b>"
    Messages.dump_task = (
        Messages.task_msg
        + f"<i>{BOT.Mode.type.capitalize()} {BOT.Mode.mode.capitalize()} as {BOT.Setting.stream_upload}</i>\n\n<b>🖇️ SOURCES » </b>"
    )
    Transfer.sent_file = []
    Transfer.sent_file_names = []
    Transfer.down_bytes = [0, 0]
    Transfer.up_bytes = [0, 0]
    Messages.download_name = ""
    Messages.task_msg = ""
    Messages.status_head = f"<b>📥 DOWNLOADING » </b>\n"

    if is_dir:
        if not ospath.exists(BOT.SOURCE[0]):
            TaskError.state = True
            TaskError.text = "Task Failed. Because: Provided Directory Path Not Exists"
            logging.error(TaskError.text)
            return
        if not ospath.exists(Paths.temp_dirleech_path):
            makedirs(Paths.temp_dirleech_path, exist_ok=True)
        Messages.dump_task += f"\n\n📂 <code>{BOT.SOURCE[0]}</code>"
        Transfer.total_down_size = getSize(BOT.SOURCE[0])
        Messages.download_name = ospath.basename(BOT.SOURCE[0])
    else:
        for link in BOT.SOURCE:
            if is_telegram(link):
                ida = "💬"
            elif is_google_drive(link):
                ida = "♻️"
            elif is_torrent(link):
                ida = "🧲"
                Messages.caution_msg = "\n\n⚠️<i><b> Torrents Are Strictly Prohibited in Google Colab</b>, Try to avoid Magnets !</i>"
            elif is_ytdl_link(link):
                ida = "🮐"
            elif is_terabox(link):
                ida = "💾"
            elif is_mega(link):
                ida = "💾"
            else:
                ida = "🔗"
            code_link = f"\n\n{ida} <code>{link}</code>"
            if len(Messages.dump_task + code_link) >= 4096:
                src_text.append(Messages.dump_task)
                Messages.dump_task = code_link
            else:
                Messages.dump_task += code_link

    # Get the current date and time in the specified time zone
    cdt = datetime.now(pytz.timezone("Asia/Kolkata"))
    dt = cdt.strftime(" %d-%m-%Y")
    Messages.dump_task += f"\n\n<b>📆 Task Date » </b><i>{dt}</i>"

    src_text.append(Messages.dump_task)

    if ospath.exists(Paths.WORK_PATH):
        shutil.rmtree(Paths.WORK_PATH)
        # makedirs(Paths.WORK_PATH, exist_ok=True)
        makedirs(Paths.down_path, exist_ok=True)
    else:
        makedirs(Paths.WORK_PATH, exist_ok=True)
        makedirs(Paths.down_path, exist_ok=True)
    Messages.link_p = str(DUMP_ID)[4:]

    try:
        system(f"aria2c -d {Paths.WORK_PATH} -o Hero.jpg {Aria2c.pic_dwn_url}")
    except Exception:
        Paths.HERO_IMAGE = Paths.DEFAULT_HERO

    MSG.sent_msg = await colab_bot.send_message(chat_id=DUMP_ID, text=src_text[0])

    if len(src_text) > 1:
        for lin in range(1, len(src_text)):
            MSG.sent_msg = await MSG.sent_msg.reply_text(text=src_text[lin], quote=True)

    Messages.src_link = f"https://t.me/c/{Messages.link_p}/{MSG.sent_msg.id}"
    Messages.task_msg += f"__[{BOT.Mode.type.capitalize()} {BOT.Mode.mode.capitalize()} as {BOT.Setting.stream_upload}]({Messages.src_link})__\n\n"

    await MSG.status_msg.delete()
    img = Paths.THMB_PATH if ospath.exists(Paths.THMB_PATH) else Paths.HERO_IMAGE
    MSG.status_msg = await colab_bot.send_photo(  # type: ignore
        chat_id=OWNER,
        photo=img,
        caption=Messages.task_msg
        + Messages.status_head
        + f"\n📍 __Starting DOWNLOAD...__"
        + sysINFO(),
        reply_markup=keyboard(),
    )

    await calDownSize(BOT.SOURCE)

    if not is_dir:
        await get_d_name(BOT.SOURCE[0])
    else:
        Messages.download_name = ospath.basename(BOT.SOURCE[0])

    if is_zip:
        Paths.down_path = ospath.join(Paths.down_path, Messages.download_name)
        if not ospath.exists(Paths.down_path):
            makedirs(Paths.down_path, exist_ok=True)

    BotTimes.current_time = time()

    if BOT.Mode.mode != "mirror":
        await Do_Leech(BOT.SOURCE, is_dir, BOT.Mode.ytdl, is_zip, is_unzip, is_dualzip)
    else:
        await Do_Mirror(BOT.SOURCE, BOT.Mode.ytdl, is_zip, is_unzip, is_dualzip)


async def Do_Leech(source, is_dir, is_ytdl, is_zip, is_unzip, is_dualzip):
    if is_dir:
        for s in source:
            if not ospath.exists(s):
                logging.error("Provided directory does not exist !")
                await cancelTask("Provided directory does not exist !")
                return
            
            # Check if it's a directory or a single file
            if ospath.isdir(s):
                # Get all items (files and folders) in the directory
                items = listdir(s)
                
                if is_zip:
                    # Process each item individually and zip it
                    for item in items:
                        item_path = ospath.join(s, item)
                        Messages.download_name = item
                        
                        if ospath.isfile(item_path):
                            file_size = ospath.getsize(item_path)
                            # Skip zipping for small files (< 10MB) - just upload directly
                            if file_size < 30 * 1024 * 1024:
                                logging.info(f"Skipping zip for small file: {item} ({sizeUnit(file_size)})")
                                Transfer.total_down_size = file_size
                                makedirs(Paths.temp_dirleech_path, exist_ok=True)
                                shutil.copy(item_path, Paths.temp_dirleech_path)
                                await Leech(Paths.temp_dirleech_path, True)
                            else:
                                # For larger files, copy to temp directory and zip
                                temp_item_dir = ospath.join(Paths.temp_dirleech_path, item)
                                makedirs(temp_item_dir, exist_ok=True)
                                shutil.copy(item_path, temp_item_dir)
                                await Zip_Handler(temp_item_dir, True, True)
                                await Leech(Paths.temp_zpath, True)
                                # Clean up temp directory
                                if ospath.exists(temp_item_dir):
                                    shutil.rmtree(temp_item_dir)
                        elif ospath.isdir(item_path):
                            # For directories, always zip them
                            await Zip_Handler(item_path, True, False)
                            await Leech(Paths.temp_zpath, True)
                            
                elif is_unzip:
                    # Process each item individually and unzip if applicable
                    for item in items:
                        item_path = ospath.join(s, item)
                        Messages.download_name = item
                        
                        if ospath.isfile(item_path):
                            temp_item_dir = ospath.join(Paths.temp_dirleech_path, item)
                            makedirs(temp_item_dir, exist_ok=True)
                            shutil.copy(item_path, temp_item_dir)
                            await Unzip_Handler(temp_item_dir, True)
                            await Leech(Paths.temp_unzip_path, True)
                            # Clean up temp directory
                            if ospath.exists(temp_item_dir):
                                shutil.rmtree(temp_item_dir)
                        elif ospath.isdir(item_path):
                            await Unzip_Handler(item_path, False)
                            await Leech(Paths.temp_unzip_path, True)
                            
                elif is_dualzip:
                    # Process each item individually: unzip then zip
                    for item in items:
                        item_path = ospath.join(s, item)
                        Messages.download_name = item
                        
                        if ospath.isfile(item_path):
                            temp_item_dir = ospath.join(Paths.temp_dirleech_path, item)
                            makedirs(temp_item_dir, exist_ok=True)
                            shutil.copy(item_path, temp_item_dir)
                            await Unzip_Handler(temp_item_dir, True)
                            await Zip_Handler(Paths.temp_unzip_path, True, True)
                            await Leech(Paths.temp_zpath, True)
                            # Clean up temp directory
                            if ospath.exists(temp_item_dir):
                                shutil.rmtree(temp_item_dir)
                        elif ospath.isdir(item_path):
                            await Unzip_Handler(item_path, False)
                            await Zip_Handler(Paths.temp_unzip_path, True, True)
                            await Leech(Paths.temp_zpath, True)
                else:
                    # Normal mode: process each item individually without zipping
                    for item in items:
                        item_path = ospath.join(s, item)
                        Messages.download_name = item
                        
                        if ospath.isfile(item_path):
                            Transfer.total_down_size = ospath.getsize(item_path)
                            makedirs(Paths.temp_dirleech_path, exist_ok=True)
                            shutil.copy(item_path, Paths.temp_dirleech_path)
                            await Leech(Paths.temp_dirleech_path, True)
                        elif ospath.isdir(item_path):
                            Transfer.total_down_size = getSize(item_path)
                            await Leech(item_path, False)
            else:
                # Single file processing (existing behavior)
                Paths.down_path = s
                if is_zip:
                    await Zip_Handler(Paths.down_path, True, False)
                    await Leech(Paths.temp_zpath, True)
                elif is_unzip:
                    await Unzip_Handler(Paths.down_path, False)
                    await Leech(Paths.temp_unzip_path, True)
                elif is_dualzip:
                    await Unzip_Handler(Paths.down_path, False)
                    await Zip_Handler(Paths.temp_unzip_path, True, True)
                    await Leech(Paths.temp_zpath, True)
                else:
                    Transfer.total_down_size = ospath.getsize(s)
                    makedirs(Paths.temp_dirleech_path, exist_ok=True)
                    shutil.copy(s, Paths.temp_dirleech_path)
                    Messages.download_name = ospath.basename(s)
                    await Leech(Paths.temp_dirleech_path, True)
    else:
        await downloadManager(source, is_ytdl)

        Transfer.total_down_size = getSize(Paths.down_path)

        # Renaming Files With Custom Name
        applyCustomName()

        # Preparing To Upload
        if is_zip:
            await Zip_Handler(Paths.down_path, True, True)
            await Leech(Paths.temp_zpath, True)
        elif is_unzip:
            await Unzip_Handler(Paths.down_path, True)
            await Leech(Paths.temp_unzip_path, True)
        elif is_dualzip:
            print("Got into un doubled zip")
            await Unzip_Handler(Paths.down_path, True)
            await Zip_Handler(Paths.temp_unzip_path, True, True)
            await Leech(Paths.temp_zpath, True)
        else:
            await Leech(Paths.down_path, True)

    await SendLogs(True)


async def Do_Mirror(source, is_ytdl, is_zip, is_unzip, is_dualzip):
    if not ospath.exists(Paths.MOUNTED_DRIVE):
        await cancelTask(
            "Google Drive is NOT MOUNTED ! Stop the Bot and Run the Google Drive Cell to Mount, then Try again !"
        )
        return

    if not ospath.exists(Paths.mirror_dir):
        makedirs(Paths.mirror_dir, exist_ok=True)

    await downloadManager(source, is_ytdl)

    Transfer.total_down_size = getSize(Paths.down_path)

    applyCustomName()

    #cdt = datetime.now()
    #cdt_ = cdt.strftime("Uploaded » %Y-%m-%d %H:%M:%S")
    #mirror_dir_ = ospath.join(Paths.mirror_dir, cdt_)
    mirror_dir_ = Paths.mirror_dir # Disabled time-based folder creation.

    if is_zip:
        await Zip_Handler(Paths.down_path, True, True)
        shutil.copytree(Paths.temp_zpath, mirror_dir_, dirs_exist_ok=True)
    elif is_unzip:
        await Unzip_Handler(Paths.down_path, True)
        shutil.copytree(Paths.temp_unzip_path, mirror_dir_, dirs_exist_ok=True)
    elif is_dualzip:
        await Unzip_Handler(Paths.down_path, True)
        await Zip_Handler(Paths.temp_unzip_path, True, True)
        shutil.copytree(Paths.temp_zpath, mirror_dir_, dirs_exist_ok=True)
    else:
        shutil.copytree(Paths.down_path, mirror_dir_, dirs_exist_ok=True)

    await SendLogs(False)
