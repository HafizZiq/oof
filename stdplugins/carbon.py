"""@CarbonNowShBot for @UniBorg
"""

from telethon import events
from telethon.errors.rpcerrorlist import YouBlockedUserError
from uniborg.util import admin_cmd
import random


@borg.on(admin_cmd(pattern="carbon ?(.*)"))
async def _(event):
    if event.fwd_from:
        return
    #
    input_str = event.pattern_match.group(1)
    to_rip_mesg = event
    if event.reply_to_msg_id and (not input_str or input_str == "reply"):
        rep_mesg = await event.get_reply_message()
        input_str = rep_mesg.message
        to_rip_mesg = rep_mesg
    #
    chat = "@CarbonNowShBot"
    chat_e = await event.client.get_entity(chat)
    #
    await event.edit("creating a carbon")
    async with event.client.conversation(chat_e, timeout=180) as conv:
        try:
            await conv.send_message(input_str)
            response = await conv.wait_event(events.MessageEdited(
                incoming=True,
                from_users=chat_e.id
            ))
            # await conv.send_read_acknowledge(response)
            # we got a response with buttons
            # decide to click on a random button
            row = random.randint(0, 8)
            logger.info(row)
            column = random.randint(0, 2)
            logger.info(column)
            #
            await response.click(row, column)
            response = await conv.wait_event(events.NewMessage(
                incoming=True,
                from_users=chat_e.id
            ))
            response_caption = response.message.message
            response_caption_sp = response_caption.split("\n")
            # the above string has channel usernames,
            # remove the useless advertisements
            response_caption = "\n".join(response_caption_sp[0:2])
            carbon_media = response.message.media
            await to_rip_mesg.reply(response_caption, file=carbon_media)
            # cleaning up
            # await conv.send_read_acknowledge(response)
            await event.delete()
        except YouBlockedUserError:
            await event.reply("Please unblock me (@CarbonNowShBot)")
            return

