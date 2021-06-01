#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import os
import time
import traceback

from threading import Thread

# pip install python-telegram-bot
from telegram import Update, Bot, ParseMode
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackContext
from telegram.ext.dispatcher import run_async

import config
import db

from common import get_logger, log_func, reply_error


DATA = {
    'BOT': None,
    'IS_WORKING': True,
}


log = get_logger(__file__)


def sending_notifications():
    while True:
        try:
            if not DATA['IS_WORKING']:
                continue

            bot: Bot = DATA['BOT']
            if not bot or not config.CHAT_ID:
                continue

            for notif in db.Notification.get_unsent():
                text = notif.get_html()
                bot.send_message(config.CHAT_ID, text, parse_mode=ParseMode.HTML)
                notif.set_as_send()

                time.sleep(1)

        except:
            log.exception('')

            if config.CHAT_ID:
                text = f'⚠ При отправке уведомления возникла ошибка:\n{traceback.format_exc()}'
                bot.send_message(config.CHAT_ID, text)
                time.sleep(60)

        finally:
            time.sleep(1)


@run_async
@log_func(log)
def on_start(update: Update, context: CallbackContext):
    if not config.CHAT_ID:
        update.message.reply_text('Введите что-нибудь для получения chat_id')


@run_async
@log_func(log)
def on_request(update: Update, context: CallbackContext):
    message = update.message

    if not config.CHAT_ID:
        text = f'CHAT_ID: {update.effective_chat.id}'
    else:
        command = message.text.lower()
        if command == 'start':
            DATA['IS_WORKING'] = True
        elif command == 'stop':
            DATA['IS_WORKING'] = False

        is_working = DATA['IS_WORKING']
        text = (
            f'Поддерживаемые комманды: <b>start</b>, <b>stop</b>\n'
            f'Рассылка уведомлений: <b>' + ('запущена' if is_working else 'остановлена') + '</b>'
        )

    message.reply_html(text)


def on_error(update: Update, context: CallbackContext):
    reply_error(log, update, context)


def main():
    cpu_count = os.cpu_count()
    workers = cpu_count
    log.debug('System: CPU_COUNT=%s, WORKERS=%s', cpu_count, workers)
    log.debug('CHAT_ID=%s', config.CHAT_ID)

    log.debug('Start')

    updater = Updater(
        config.TOKEN,
        workers=workers,
        use_context=True
    )
    DATA['BOT'] = updater.bot

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', on_start))
    dp.add_handler(MessageHandler(Filters.text, on_request))

    dp.add_error_handler(on_error)

    updater.start_polling()
    updater.idle()

    log.debug('Finish')


if __name__ == '__main__':
    Thread(target=sending_notifications).start()

    while True:
        try:
            main()
        except:
            log.exception('')

            timeout = 15
            log.info(f'Restarting the bot after {timeout} seconds')
            time.sleep(timeout)
