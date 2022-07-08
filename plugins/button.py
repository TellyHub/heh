#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | @Tellybots

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import asyncio
import json
import math
import os
import shutil
import time
from datetime import datetime, timedelta
from pyrogram import enums 
from plugins.config import Config
from plugins.script import Translation
from plugins.thumbnail import *
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from pyrogram.types import InputMediaPhoto
from plugins.functions.display_progress import progress_for_pyrogram, humanbytes
from plugins.database.database import db
from PIL import Image
from plugins.functions.ran_text import random_char

async def youtube_dl_call_back(bot, update):
    cb_data = update.data
    # youtube_dl extractors
    tg_send_type, youtube_dl_format, youtube_dl_ext, ranom = cb_data.split("|")
    print(cb_data)
    random1 = random_char(5)
    
    save_ytdl_json_path = Config.DOWNLOAD_LOCATION + \
        "/" + str(update.from_user.id) + f'{ranom}' + ".json"
    try:
        with open(save_ytdl_json_path, "r", encoding="utf8") as f:
            response_json = json.load(f)
    except (FileNotFoundError) as e:
        await update.message.delete()
        return False
    youtube_dl_url = update.message.reply_to_message.text
    custom_file_name = str(response_json.get("title")) + \
        "_" + youtube_dl_format + "." + youtube_dl_ext
    youtube_dl_username = None
    youtube_dl_password = None
    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")
        if len(url_parts) == 2:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
        elif len(url_parts) == 4:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]
        else:
            for entity in update.message.reply_to_message.entities:
                if entity.type == "text_link":
                    youtube_dl_url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    youtube_dl_url = youtube_dl_url[o:o + l]
        if youtube_dl_url is not None:
            youtube_dl_url = youtube_dl_url.strip()
        if custom_file_name is not None:
            custom_file_name = custom_file_name.strip()
        # https://stackoverflow.com/a/761825/4723940
        if youtube_dl_username is not None:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password is not None:
            youtube_dl_password = youtube_dl_password.strip()
        logger.info(youtube_dl_url)
        logger.info(custom_file_name)
    else:
        for entity in update.message.reply_to_message.entities:
            if entity.type == "text_link":
                youtube_dl_url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                youtube_dl_url = youtube_dl_url[o:o + l]
    await update.message.edit_caption(
        caption=Translation.DOWNLOAD_START,
        parse_mode=enums.ParseMode.HTML
    )
    description = Translation.CUSTOM_CAPTION_UL_FILE
    if "fulltitle" in response_json:
        description = response_json["fulltitle"][0:1021]
        # escape Markdown and special characters
    tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + f'{random1}'
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)
    download_directory = tmp_directory_for_each_user + "/" + custom_file_name
    command_to_exec = []
    command_to_exec = []
    with open("backup.json", "r", encoding="utf8") as f:
                  b_json = json.load(f)
    if update.from_user.id in Config.ONE_BY_ONE:
      for users in b_json["users"]:
        user = users.get("user_id")
        exp_req = users.get("exp_req")
        if int(update.from_user.id) == int(user):
          if datetime.strptime(exp_req, '%Y-%m-%d %H:%M:%S.%f') > datetime.now():
            rem = datetime.strptime(exp_req, '%Y-%m-%d %H:%M:%S.%f') - datetime.now()
            await update.message.edit_text("😴 Please wait {} for next process.".format(datetime.strptime(str(rem), '%H:%M:%S.%f').strftime('%H Hrs %M Mins %S Sec')))
            return
    Config.ONE_BY_ONE.append(update.from_user.id)
    if not update.from_user.id in Config.TODAY_USERS:
       Config.TODAY_USERS.append(update.from_user.id)
       exp_date = datetime.now()
       exp_req = exp_date + timedelta(minutes=int(Config.TIME_GAP))
       fir = 0
       b_json["users"].append({
         "user_id": "{}".format(update.from_user.id),
         "total_req": "{}".format(fir),
         "exp_req": "{}".format(exp_req)
       })
       with open("backup.json", "w", encoding="utf8") as outfile:
               json.dump(b_json, outfile, ensure_ascii=False)
    user_count = 0
    for users in b_json["users"]:
      user = users.get("user_id")
      total_req = users.get("total_req")
      user_count = user_count + 1
      #if int(update.from_user.id) == int(user):
      # if int(total_req) > 3:
      #    await update.reply_text("😴 You reached per day limit. send /me to know renew time.")
      #    return
    b_json["users"].pop(user_count - 1)
    b_json["users"].append({
         "user_id": "{}".format(update.from_user.id),
         "total_req": "{}".format(int(total_req) + 1),
         "exp_req": "{}".format(datetime.now() + timedelta(minutes=int(Config.TIME_GAP)))
    })
    with open("backup.json", "w", encoding="utf8") as outfile:
          json.dump(b_json, outfile, ensure_ascii=False)
    if tg_send_type == "audio":
        command_to_exec = [
            "yt-dlp",
            "-c",
            "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
            "--prefer-ffmpeg",
            "--extract-audio",
            "--audio-format", youtube_dl_ext,
            "--audio-quality", youtube_dl_format,
            youtube_dl_url,
            "-o", download_directory
        
        ]
    else:

        command_to_exec = [
            "yt-dlp",
            "-c",
            "--geo-bypass",
            "--clean-info-json",
            "--ignore-no-formats-error",
            "--embed-subs",
            "-f",
            youtube_dl_format,
            "--prefer-ffmpeg",
            youtube_dl_url,
            "-o",
            download_directory,
        ]
 

    if Config.HTTP_PROXY != "":
        command_to_exec.append("--proxy")
        command_to_exec.append(Config.HTTP_PROXY)
    if youtube_dl_username is not None:
        command_to_exec.append("--username")
        command_to_exec.append(youtube_dl_username)
    if youtube_dl_password is not None:
        command_to_exec.append("--password")
        command_to_exec.append(youtube_dl_password)
    command_to_exec.append("--no-warnings")
    # command_to_exec.append("--quiet")
    logger.info(command_to_exec)
    start = datetime.now()
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    logger.info(e_response)
    logger.info(t_response)
    ad_string_to_replace = "please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output."
    if e_response and ad_string_to_replace in e_response:
        error_message = e_response.replace(ad_string_to_replace, "")
        await update.message.edit_caption(
            parse_mode=enums.ParseMode.HTML,
            text=error_message
        )
        Config.ONE_BY_ONE.remove(update.from_user.id)
        total_req_get = total_req
        b_json["users"].pop(user_count - 1)
        b_json["users"].append({
             "user_id": "{}".format(update.from_user.id),
             "total_req": "{}".format(int(total_req_get)),
             "exp_req": "{}".format(datetime.now())
        })
        with open("backup.json", "w", encoding="utf8") as outfile:
              json.dump(b_json, outfile, ensure_ascii=False)
        return False

    if t_response:
        logger.info(t_response)
        try:
            os.remove(save_ytdl_json_path)
        except FileNotFoundError as exc:
            pass
        
        end_one = datetime.now()
        time_taken_for_download = (end_one -start).seconds
        file_size = Config.TG_MAX_FILE_SIZE + 1
        try:
            file_size = os.stat(download_directory).st_size
        except FileNotFoundError as exc:
            download_directory = os.path.splitext(download_directory)[0] + "." + "mkv"
            # https://stackoverflow.com/a/678242/4723940
            file_size = os.stat(download_directory).st_size
        try:
            if tg_send_type == 'video' and 'webm' in download_directory:
                ownload_directory = download_directory.rsplit('.', 1)[0] + '.mkv'
                os.rename(download_directory, ownload_directory)
                download_directory = ownload_directory
        except:
            pass

        if file_size > Config.TG_MAX_FILE_SIZE:
        
            # Uploads the file to gofile.io
            upmsg = await bot.send_message(
                chat_id=c_id,
                text="`File Size is too large to send in telegram 🥶! Trying to upload this file to gofile.io now 😉!`"
            )
            try:
                ga = Async_Gofile()
                gfio = await ga.upload(doc_f)
                await bot.edit("**Your file has been uploaded to gofile! Click on the below button to download it 👇**", reply_markup=Buttons.GOFILE_BTN(gfio["downloadPage"]))
            except:
                await bot.edit("`Upload failed, Better luck next time 😔!`")
            os.remove(doc_f)
            return



        else:
            is_w_f = False
            '''images = await generate_screen_shots(
                download_directory,
                tmp_directory_for_each_user,
                is_w_f,
                Config.DEF_WATER_MARK_FILE,
                300,
                9
            )
            logger.info(images)'''
            await update.message.edit_caption(
                caption=Translation.UPLOAD_START,
                parse_mode=enums.ParseMode.HTML
            )

            # ref: message from @Sources_codes
            start_time = time.time()
            if (await db.get_upload_as_doc(update.from_user.id)) is False:
                thumbnail = await Gthumb01(bot, update)
                await update.message.reply_document(
                    #chat_id=update.message.chat.id,
                    document=download_directory,
                    thumb=thumbnail,
                    caption=description,
                    parse_mode=enums.ParseMode.HTML,
                    #reply_to_message_id=update.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time
                    )
                )
            else:
                 width, height, duration = await Mdata01(download_directory)
                 thumb_image_path = await Gthumb02(bot, update, duration, download_directory)
                 await update.message.reply_video(
                    #chat_id=update.message.chat.id,
                    video=download_directory,
                    caption=description,
                    duration=duration,
                    width=width,
                    height=height,
                    supports_streaming=True,
                    parse_mode=enums.ParseMode.HTML,
                    thumb=thumb_image_path,
                    #reply_to_message_id=update.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time
                    )
                )
            if tg_send_type == "audio":
                duration = await Mdata03(download_directory)
                thumbnail = await Gthumb01(bot, update)
                await update.message.reply_audio(
                    #chat_id=update.message.chat.id,
                    audio=download_directory,
                    caption=description,
                    parse_mode=enums.ParseMode.HTML,
                    duration=duration,
                    thumb=thumbnail,
                    #reply_to_message_id=update.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time
                    )
                )
            elif tg_send_type == "vm":
                width, duration = await Mdata02(download_directory)
                thumbnail = await Gthumb02(bot, update, duration, download_directory)
                await update.message.reply_video_note(
                    #chat_id=update.message.chat.id,
                    video_note=download_directory,
                    duration=duration,
                    length=width,
                    thumb=thumbnail,
                    #reply_to_message_id=update.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time
                    )
                )
            else:
                logger.info("Did this happen? :\\")
            end_two = datetime.now()
            time_taken_for_upload = (end_two - end_one).seconds
            try:
                shutil.rmtree(tmp_directory_for_each_user)
                os.remove(thumbnail)
            except:
                pass
            await update.message.edit_caption(
                caption=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(time_taken_for_download, time_taken_for_upload),
                parse_mode=enums.ParseMode.HTML
            )
            Config.ONE_BY_ONE.remove(update.from_user.id)
            total_req_get = total_req
            b_json["users"].pop(user_count - 1)
            b_json["users"].append({
                 "user_id": "{}".format(update.from_user.id),
                 "total_req": "{}".format(int(total_req_get)),
                 "exp_req": "{}".format(datetime.now())
            })
            with open("backup.json", "w", encoding="utf8") as outfile:
                  json.dump(b_json, outfile, ensure_ascii=False)
