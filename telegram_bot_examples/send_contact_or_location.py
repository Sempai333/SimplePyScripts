#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import os
import time

# pip install python-telegram-bot
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackContext

import config
from common import get_logger, log_func, reply_error


contact_keyboard = KeyboardButton('Send contact', request_contact=True)
location_keyboard = KeyboardButton('Send location', request_location=True)
custom_keyboard = [[contact_keyboard, location_keyboard]]
REPLY_KEYBOARD_MARKUP = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)


log = get_logger(__file__)


@log_func(log)
def on_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Write something',
        reply_markup=REPLY_KEYBOARD_MARKUP
    )


@log_func(log)
def on_request(update: Update, context: CallbackContext):
    message = update.message

    message.reply_text(
        'Echo: ' + message.text,
        reply_markup=REPLY_KEYBOARD_MARKUP
    )


@log_func(log)
def on_contact_or_location(update: Update, context: CallbackContext):
    message = update.message

    text = ''
    if message.contact:
        text += str(message.contact)

    if message.location:
        text += str(message.location)

    message.reply_text(
        text,
        reply_markup=REPLY_KEYBOARD_MARKUP
    )


def on_error(update: Update, context: CallbackContext):
    reply_error(log, update, context)


def main():
    cpu_count = os.cpu_count()
    workers = cpu_count
    log.debug('System: CPU_COUNT=%s, WORKERS=%s', cpu_count, workers)

    log.debug('Start')

    updater = Updater(
        config.TOKEN,
        workers=workers,
        use_context=True
    )

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', on_start, run_async=True))
    dp.add_handler(MessageHandler(Filters.text, on_request, run_async=True))
    dp.add_handler(MessageHandler(Filters.contact | Filters.location, on_contact_or_location, run_async=True))

    dp.add_error_handler(on_error)

    updater.start_polling()
    updater.idle()

    log.debug('Finish')


if __name__ == '__main__':
    while True:
        try:
            main()
        except:
            log.exception('')

            timeout = 15
            log.info(f'Restarting the bot after {timeout} seconds')
            time.sleep(timeout)
