#!/usr/bin/env python3

import sys
import re

from config import CFG

def main():
    path = sys.argv[1]

    with open(path, 'r', encoding="utf8") as f:
       action_list = parse_file(f.read())

    with open("telegram_poll.txt", 'w', encoding="utf8") as f:
        for action in action_list:
#            print(action)
            f.write(f"{action}\n")

def parse_file(in_str: str) -> list[str]:
    r = re.compile(r'\s*(?:--- (.*) \d{4} ---\s+)?(.*)\n➙ (.*)\n➙ Lieu : (.*)\n➙ (\S*)')

    title, in_str = get_title(in_str)

    action_list = []
    previousDate = None
    while m := r.match(in_str):
        in_str = in_str[m.end():]
        (date, name, hours, location, url) = m.groups()
        previousDate = date = date or previousDate

        action_list.append(str_action(date, name, hours, location, url))

    return title, action_list

def str_action(date, name, hours, location, url) -> str:

    location = abreviation(location)
    name_max_len = 93 - sum(len(x) for x in (date, hours, location)) # 100 - " | " - " " - " - " = 93
    name = abreviation(name)[:name_max_len]

    return  f"{date} | {hours} {name} - {location}"

def get_title(in_str):
    """Get text introductiong poll"""

    ind = re.search('---', in_str).start()
    return in_str[:ind] or "Actions du mois", in_str[ind:]


def abreviation(s: str) -> str:
    for k, v in CFG['ABREVIATIONS'].items():
        s = s.replace(k, v)
    return s

if __name__ == "__main__":
    main()

