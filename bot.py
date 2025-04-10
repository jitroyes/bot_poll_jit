#!/usr/bin/env python3

import random
import string

import asyncio
import telegram

import logging
from telegram import Update, LinkPreviewOptions
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

from act2poll import parse_file, str_action

from config import CFG

DELETE_POLL_MSG = True

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def links(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='\n'.join(f'{k} : {v}' for k,v in CFG['JI_Urls'].items()),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

async def pad(update: Update, context: ContextTypes.DEFAULT_TYPE):

    length = 30
    link = CFG['JI_Urls']['pad_base_url']
    pad = random_string = ''.join(random.choices(string.ascii_letters, k=length))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=link+pad)

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create poll from command argument"""

    if DELETE_POLL_MSG:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.id
        )

    title, questions = parse_file(update.message.text[5:])

    message = await context.bot.send_poll(
        update.effective_chat.id,
        title,
        questions,
        is_anonymous=False,
        allows_multiple_answers=True,
    )
    # # Save some info about the poll the bot_data for later use in receive_poll_answer
    # payload = {
    #     message.poll.id: {
    #         "questions": questions,
    #         "message_id": message.message_id,
    #         "chat_id": update.effective_chat.id,
    #         "answers": 0,
    #     }
    # }
    # context.bot_data.update(payload)


if __name__ == '__main__':
    application = ApplicationBuilder().token(CFG['Bot']['token']).build()

    application.add_handler(CommandHandler("links", links))
    application.add_handler(CommandHandler("pad", pad))
    application.add_handler(CommandHandler("poll", poll))

    application.run_polling()

