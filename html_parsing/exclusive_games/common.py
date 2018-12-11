#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import re
import requests
from bs4 import BeautifulSoup


def get_game_list(root, class_name: str) -> list:
    def process_title(title: str) -> str:
        # Уберем лишнее, оставив только название игры
        title = re.sub('\[.+?\]', '', title)
        title = re.sub('\(.+\)', '', title)
        return title.strip()

    items = [x.text.strip() for x in root.select('.' + class_name)]

    # Названия игр оканчиваются на ")", например "Teslapunk (klutzGames)"
    return [process_title(x) for x in items if x.endswith(')')]


def get_game_list_from(url: str, *class_names) -> list:
    rs = requests.get(url)
    root = BeautifulSoup(rs.content, 'html.parser')

    exclusive_games = []

    for class_name in class_names:
        exclusive_games += get_game_list(root, class_name)

    exclusive_games.sort()

    return exclusive_games
