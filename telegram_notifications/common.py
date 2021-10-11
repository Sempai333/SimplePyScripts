#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import enum
import functools
import logging
import sys

from pathlib import Path

from telegram import Update
from telegram.ext import CallbackContext

from telegram_notifications import config


class AutoName(enum.Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class TypeEnum(AutoName):
    INFO = enum.auto()
    ERROR = enum.auto()

    @property
    def emoji(self) -> str:
        return {
            self.INFO: 'ℹ️',
            self.ERROR: '⚠️',
        }[self]


def get_logger(file_name: str, dir_name='logs'):
    dir_name = Path(dir_name).resolve()
    dir_name.mkdir(parents=True, exist_ok=True)

    file_name = str(dir_name / Path(file_name).resolve().name) + '.log'

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] %(filename)s[LINE:%(lineno)d] %(levelname)-8s %(message)s')

    fh = logging.FileHandler(file_name, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.DEBUG)

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    log.addHandler(fh)
    log.addHandler(ch)

    return log


def log_func(log: logging.Logger):
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(update: Update, context: CallbackContext):
            if update:
                chat_id = user_id = first_name = last_name = username = language_code = None

                if update.effective_chat:
                    chat_id = update.effective_chat.id

                if update.effective_user:
                    user_id = update.effective_user.id
                    first_name = update.effective_user.first_name
                    last_name = update.effective_user.last_name
                    username = update.effective_user.username
                    language_code = update.effective_user.language_code

                try:
                    message = update.effective_message.text
                except:
                    message = ''

                try:
                    query_data = update.callback_query.data
                except:
                    query_data = ''

                msg = f'[chat_id={chat_id}, user_id={user_id}, ' \
                      f'first_name={first_name!r}, last_name={last_name!r}, ' \
                      f'username={username!r}, language_code={language_code}, ' \
                      f'message={message!r}, query_data={query_data!r}]'
                msg = func.__name__ + msg

                log.debug(msg)

            return func(update, context)

        return wrapper
    return actual_decorator


def reply_error(log: logging.Logger, update: Update, context: CallbackContext):
    log.exception('Error: %s\nUpdate: %s', context.error, update, exc_info=context.error)
    if update:
        update.effective_message.reply_text(config.ERROR_TEXT)
