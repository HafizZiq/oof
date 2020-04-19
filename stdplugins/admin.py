# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.b (the "License");
# you may not use this file except in compliance with the License.
"""
Uniborg module to help you manage a group
"""

from asyncio import sleep
from os import remove

from telethon.errors import (BadRequestError, ChatAdminRequiredError,
                             ImageProcessFailedError, PhotoCropSizeSmallError,
                             UserAdminInvalidError)
from telethon.errors.rpcerrorlist import (UserIdInvalidError,
                                          MessageTooLongError)
from telethon.tl.functions.channels import (EditAdminRequest,
                                            EditBannedRequest,
                                            EditPhotoRequest)
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from telethon.tl.types import (ChannelParticipantsAdmins, ChatAdminRights,
                               ChatBannedRights, MessageEntityMentionName,
                               MessageMediaPhoto)

from uniborg.util import admin_cmd

# =================== CONSTANT ===================
PP_TOO_SMOL = "`The image is too small`"
PP_ERROR = "`Failure while processing image`"
NO_ADMIN = "`I am not an admin!`"
NO_PERM = "`I don't have sufficient permissions!`"
NO_SQL = "`Running on Non-SQL mode!`"

CHAT_PP_CHANGED = "`Chat Picture Changed`"
CHAT_PP_ERROR = "`Some issue with updating the pic,`" \
                "`maybe coz I'm not an admin,`" \
                "`or don't have the desired rights.`"
INVALID_MEDIA = "`Invalid Extension`"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

KICK_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True
)

MUTE_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=True
)

UNMUTE_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=False
)
# ================================================


@borg.on(admin_cmd(pattern="sgp", outgoing=True))
async def set_group_photo(gpic):
    """ For .setgrouppic command, changes the picture of a group """
    if not gpic.text[0].isalpha() and gpic.text[0] not in ("/", "#", "@", "!"):
        replymsg = await gpic.get_reply_message()
        chat = await gpic.get_chat()
        admin = chat.admin_rights
        creator = chat.creator
        photo = None

        if not chat.admin_rights or chat.creator:
            await gpic.edit(NO_ADMIN)
            return

        if replymsg and replymsg.media:
            if isinstance(replymsg.media, MessageMediaPhoto):
                photo = await bot.download_media(message=replymsg.photo)
            elif "image" in replymsg.media.document.mime_type.split('/'):
                photo = await bot.download_file(replymsg.media.document)
            else:
                await gpic.edit(INVALID_MEDIA)

        if photo:
            try:
                await EditPhotoRequest(
                    gpic.chat_id,
                    await bot.upload_file(photo)
                )
                await gpic.edit(CHAT_PP_CHANGED)

            except PhotoCropSizeSmallError:
                await gpic.edit(PP_TOO_SMOL)
            except ImageProcessFailedError:
                await gpic.edit(PP_ERROR)


@borg.on(admin_cmd(pattern="ban(?: |$)(.*)", outgoing=True))
async def ban(bon):
    """ For .ban command, do "thanos" at targeted person """
    if not bon.text[0].isalpha() and bon.text[0] not in ("/", "#", "@", "!"):
        # Here laying the sanity check
        chat = await bon.get_chat()
        admin = chat.admin_rights
        creator = chat.creator

        # Well
        if not admin and not creator:
            await bon.edit(NO_ADMIN)
            return

        user = await get_user_from_event(bon)
        if user:
            pass
        else:
            return


        # Announce that we're going to whack the pest
        await bon.edit("`Whacking the pest!`")

        try:
            await bon.client(
                EditBannedRequest(
                    bon.chat_id,
                    user.id,
                    BANNED_RIGHTS
                )
            )
        except BadRequestError:
            await bon.edit(NO_PERM)
            return
        # Helps ban group join spammers more easily
        try:
            reply = await bon.get_reply_message()
            if reply:
                await reply.delete()
        except BadRequestError:
            await bon.edit("`I dont have message nuking rights! But still he was banned!`")
            return
        # Delete message and then tell that the command
        # is done gracefully
        # Shout out the ID, so that fedadmins can fban later

        await bon.edit("`{}` was banned!".format(str(user.id)))

        # Announce to the logging group if we have demoted successfully
        if Config.PRIVATE_GROUP_BOT_API_ID is not None:
            await bon.client.send_message(
                Config.PRIVATE_GROUP_BOT_API_ID,
                "#BAN\n"
                f"*User:* [{user.first_name}](tg://user?id={user.id})\n"
                f"*Chat:* {bon.chat.title} `{bon.chat_id}`"
            )


@borg.on(admin_cmd(pattern="unban(?: |$)(.*)", outgoing=True))
async def nothanos(unbon):
    """ For .unban command, undo "thanos" on target """
    if not unbon.text[0].isalpha() and unbon.text[0] \
            not in ("/", "#", "@", "!"):

        # Here laying the sanity check
        chat = await unbon.get_chat()
        admin = chat.admin_rights
        creator = chat.creator

        # Well
        if not admin and not creator:
            await unbon.edit(NO_ADMIN)
            return

        # If everything goes well...
        await unbon.edit("`Unbanning...`")

        user = await get_user_from_event(unbon)
        if user:
            pass
        else:
            return

        try:
            await unbon.client(EditBannedRequest(
                unbon.chat_id,
                user.id,
                UNBAN_RIGHTS
            ))
            await unbon.edit("```Unbanned Successfully```")

            if Config.PRIVATE_GROUP_BOT_API_ID is not None:
                await unbon.client.send_message(
                    Config.PRIVATE_GROUP_BOT_API_ID,
                    "#UNBAN\n"
                    f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                    f"CHAT: {unbon.chat.title}(`{unbon.chat_id}`)"
                )
        except UserIdInvalidError:
            await unbon.edit("`Uh oh my unban logic broke!`")


@borg.on(admin_cmd(pattern="mute(?: |$)(.*)", outgoing=True))
async def spider(spdr):
    """
    This function is basically muting peeps
    """
    if not spdr.text[0].isalpha() and spdr.text[0] not in ("/", "#", "@", "!"):
        
        # Admin or creator check
        chat = await spdr.get_chat()
        admin = chat.admin_rights
        creator = chat.creator

        # If not admin and not creator, return
        if not admin and not creator:
            await spdr.edit(NO_ADMIN)
            return

        user = await get_user_from_event(spdr)
        if user:
            pass
        else:
            return

        self_user = await spdr.client.get_me()

        if user.id == self_user.id:
        	await spdr.edit("`Mute Error! You are not supposed to mute yourself!`")
        	return


        # If everything goes well, do announcing and mute
        await spdr.edit("`Gets a tape!`")
        try:
            await spdr.client(
                EditBannedRequest(
                    spdr.chat_id,
                    user.id,
                    MUTE_RIGHTS
                )
            )

            # Announce that the function is done
            await spdr.edit("`Safely taped!`")

            # Announce to logging group
            if Config.PRIVATE_GROUP_BOT_API_ID is not None:
                await spdr.client.send_message(
                    Config.PRIVATE_GROUP_BOT_API_ID,
                    "#MUTE\n"
                    f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                    f"CHAT: {spdr.chat.title}(`{spdr.chat_id}`)"
                )
        except UserIdInvalidError:
            await spdr.edit("`Uh oh my unban logic broke!`")


@borg.on(admin_cmd(pattern="unmute(?: |$)(.*)", outgoing=True))
async def unmoot(unmot):
    """ For .unmute command, unmute the target """
    if not unmot.text[0].isalpha() and unmot.text[0] \
            not in ("/", "#", "@", "!"):

        # Admin or creator check
        chat = await unmot.get_chat()
        admin = chat.admin_rights
        creator = chat.creator

        # If not admin and not creator, return
        if not admin and not creator:
            await unmot.edit(NO_ADMIN)
            return

        # If admin or creator, inform the user and start unmuting
        await unmot.edit('```Unmuting...```')
        user = await get_user_from_event(unmot)
        if user:
            pass
        else:
            return

        try:
            await unmot.client(
                EditBannedRequest(
                    unmot.chat_id,
                    user.id,
                    UNBAN_RIGHTS
                )
            )
            await unmot.edit("```Unmuted Successfully```")
        except UserIdInvalidError:
            await unmot.edit("`Uh oh my unmute logic broke!`")
            return

        if Config.PRIVATE_GROUP_BOT_API_ID is not None:
            await unmot.client.send_message(
                Config.PRIVATE_GROUP_BOT_API_ID,
                "#UNMUTE\n"
                f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {unmot.chat.title}(`{unmot.chat_id}`)"
            )


@borg.on(admin_cmd(pattern="delusers(?: |$)(.*)", outgoing=True))
async def rm_deletedacc(show):
    """ For .adminlist command, list all of the admins of the chat. """
    if not show.text[0].isalpha() and show.text[0] not in ("/", "#", "@", "!"):
        con = show.pattern_match.group(1)
        del_u = 0
        del_status = "`No deleted accounts found, Group is cleaned as Hell`"

        if not show.is_group:
            await show.edit("`This command is only for groups!`")
            return

        if con != "clean":
            await show.edit("`Searching for zombie accounts...`")
            async for user in show.client.iter_participants(
                    show.chat_id
            ):
                if user.deleted:
                    del_u += 1

            if del_u > 0:
                del_status = f"found **{del_u}** deleted account(s) in this group \
                \nclean them by using `.delusers clean`"
            await show.edit(del_status)
            return

        # Here laying the sanity check
        chat = await show.get_chat()
        admin = chat.admin_rights
        creator = chat.creator

        # Well
        if not admin and not creator:
            await show.edit("`I am not an admin here!`")
            return

        await show.edit("`Cleaning deleted accounts...`")
        del_u = 0
        del_a = 0

        async for user in show.client.iter_participants(
                show.chat_id
        ):
            if user.deleted:
                try:
                    await show.client(
                        EditBannedRequest(
                            show.chat_id,
                            user.id,
                            BANNED_RIGHTS
                        )
                    )
                except ChatAdminRequiredError:
                    await show.edit("`I don't have ban rights in this group`")
                    return
                except UserAdminInvalidError:
                    del_u -= 1
                    del_a += 1
                await show.client(
                    EditBannedRequest(
                        show.chat_id,
                        user.id,
                        UNBAN_RIGHTS
                    )
                )
                del_u += 1

        if del_u > 0:
            del_status = f"cleaned **{del_u}** deleted account(s)"

        if del_a > 0:
            del_status = f"cleaned **{del_u}** deleted account(s) \
            \n**{del_a}** deleted admin accounts are not removed"

        await show.edit(del_status)


@borg.on(admin_cmd(pattern="kick(?: |$)(.*)", outgoing=True))
async def kick(usr):
    """ For .kick command, kick someone from the group using the userbot. """
    if not usr.text[0].isalpha() and usr.text[0] not in ("/", "#", "@", "!"):
        # Admin or creator check
        chat = await usr.get_chat()
        admin = chat.admin_rights
        creator = chat.creator

        # If not admin and not creator, return
        if not admin and not creator:
            await usr.edit(NO_ADMIN)
            return

        user = await get_user_from_event(usr)
        if not user:
            await usr.edit("`Couldn't fetch user.`")
            return


        await usr.edit("`Kicking...`")

        try:
            await usr.client(
                EditBannedRequest(
                    usr.chat_id,
                    user.id,
                    KICK_RIGHTS
                )
            )
            await sleep(.5)
        except BadRequestError:
            await usr.edit(NO_PERM)
            return
        await usr.client(
            EditBannedRequest(
                usr.chat_id,
                user.id,
                ChatBannedRights(until_date=None)
            )
        )

        await usr.edit(f"`Kicked` [{user.first_name}](tg://user?id={user.id})`!`")

        if Config.PRIVATE_GROUP_BOT_API_ID is not None:
            await usr.client.send_message(
                Config.PRIVATE_GROUP_BOT_API_ID,
                "#KICK\n"
                f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {usr.chat.title}(`{usr.chat_id}`)\n"
            )


@borg.on(admin_cmd(pattern="userslist(?: |$)(.*)", outgoing=True))
async def get_users(show):
    """ For .userslist command, list all of the users of the chat. """
    if not show.text[0].isalpha() and show.text[0] not in ("/", "#", "@", "!"):
        if not show.is_group:
            await show.edit("Are you sure this is a group?")
            return
        info = await show.client.get_entity(show.chat_id)
        title = info.title if info.title else "this chat"
        mentions = 'Users in {}: \n'.format(title)
        try:
            if not show.pattern_match.group(1):
                async for user in show.client.iter_participants(show.chat_id):
                    if not user.deleted:
                        mentions += f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    else:
                        mentions += f"\nDeleted Account `{user.id}`"
            else:
                searchq = show.pattern_match.group(1)
                async for user in show.client.iter_participants(show.chat_id, search=f'{searchq}'):
                    if not user.deleted:
                        mentions += f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    else:
                        mentions += f"\nDeleted Account `{user.id}`"
        except ChatAdminRequiredError as err:
            mentions += " " + str(err) + "\n"
        try:
            await show.edit(mentions)
        except MessageTooLongError:
            await show.edit("Damn, this is a huge group. Uploading users lists as file.")
            file = open("userslist.txt", "w+")
            file.write(mentions)
            file.close()
            await show.client.send_file(
                show.chat_id,
                "userslist.txt",
                caption='Users in {}'.format(title),
                reply_to=show.id,
            )
            remove("userslist.txt")


async def get_user_from_event(event):
    """ Get the user from argument or replied message. """
    if event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        user_obj = await event.client.get_entity(previous_message.from_id)
    else:
        user = event.pattern_match.group(1)

        if user.isnumeric():
            user = int(user)

        if not user:
            await event.edit("`Pass the user's username, id or reply!`")
            return

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                user_obj = await event.client.get_entity(user_id)
                return user_obj
        try:
            user_obj = await event.client.get_entity(user)
        except (TypeError, ValueError) as err:
            await event.edit(str(err))
            return None

    return user_obj

async def get_user_from_id(user, event):
    if isinstance(user, str):
        user = int(user)

    try:
        user_obj = await event.client.get_entity(user)
    except (TypeError, ValueError) as err:
        await event.edit(str(err))
        return None

    return user_obj
