#!/usr/bin/env python3

"""
Title: ActionPop2Poll
Author: Daguhh
Date: 2025-11-11
Version: unreleased
Description: Create telegram poll from action populaire agenda
Usage: python actionpop2poll.py [config_path.json]
Dependencies: requests, tkinter
License: The Unlicense
Repository: https://github.com/jitroyes/bot_poll_jit
"""

import sys
import re
from datetime import datetime
import locale
import json

import tkinter as tk
import requests


#https://core.telegram.org/bots/tutorial#obtain-your-bot-token
def create_config():
    config = {
        "TOKEN": "xxxxxxxxxxxxxxx",
        "CHAT": -100000000,
        "TOPIC": None
    }
    with open('credentials.json', 'w') as fp:
        json.dump(config, fp, indent=4)

locale.setlocale(locale.LC_TIME, "fr_FR.utf8")

CHAR_LIMIT = {
    "title" : 300,
    "question" : 100
}

DATE_OUT_FORMAT = "%A %d %B"

def format_date(date_str:str) -> str :
    d = datetime.strptime(date_str.strip().title(), '%d %B %Y')
    return datetime.strftime(d, DATE_OUT_FORMAT)

ABREVIATIONS = {
    "📃 Diffusion de tracts - info et mobilisation - " : "📃 Tractage ",
    "📃 Diffusion de tracts : " : "📃 Tractage ",
    "manifestation" : "manif",
    "Restaurant universitaire Les Courtines (Fac de droit)" : "Resto U Fac (centre ville)",
    "Resto U IUT / UTT" : "Resto U UTT"
}

def abreviation(s: str) -> str:
    for k, v in ABREVIATIONS.items():
        s = s.replace(k, v)
    return s

def format_action(date, name, hours, location, url) -> str:
    date = format_date(date)
    return f"{date} | {hours} | {abreviation(name)} -- {abreviation(location)}"

def send_poll(description, action_list):

    r = requests.post(f"https://api.telegram.org/bot{CREDENTIALS['TOKEN']}/sendPoll", json={
        "chat_id": CREDENTIALS['CHAT'],
        "message_thread_id": None,
        "question": description,
        "options": action_list,
        "is_anonymous": False,
        "allows_multiple_answers": True,
    })
    if r.status_code != 200:
        print(r.json())

def parse_actions(text: str) -> list[str]:

    # strip all before first "---"
    m =re.search("---", text)
    if m is None: # Wrong format
        return []
    text = text[m.start():]

    # Parse all actions
    r = re.compile(r'\s*(?:--- (.* \d{4}) ---\s+)?(.*)\n➙ (.*)\n➙ Lieu : (.*)\n➙ (\S*)')

    action_list = []
    previousDate = None # get date for actions block
    while m := r.match(text):
        text = text[m.end():]
        (date, name, hours, location, url) = m.groups()
        previousDate = date = date or previousDate

        action_list.append(format_action(date, name, hours, location, url))

    return action_list


############### GUI ###############

FRAME_WARN = {'highlightbackground':"red", 'highlightcolor':"red", 'highlightthickness':6}
FRAME_NORMAL = {'highlightbackground':"gray", 'highlightcolor':"gray", 'highlightthickness':6}

class FakeEvent:
    def __init__(self, wdg):
        self.widget = wdg

class Gui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ActionPop2Poll")
        self.create_widgets()

    def create_widgets(self):

        label1 = tk.Label(self, text="Description:")
        self.text1 = tk.Text(self, height=5, width=40)
        label2 = tk.Label(self, text="Planing action pop:")

        text2_frame = tk.Frame(self)
        self.text2 = tk.Text(text2_frame, height=20, width=40)
        scrollbar = tk.Scrollbar(text2_frame, orient=tk.VERTICAL, command=self.text2.yview)

        self.text2.configure(yscrollcommand=scrollbar.set)

        label1.grid(row=0, column=0, pady=2, sticky='nsew')
        self.text1.grid(row=1,column=0, sticky='nsew')
        label2.grid(row=2, column=0, pady=2, sticky='nsew')
        text2_frame.grid(row=3,column=0, sticky='nsew')
        self.text2.grid(row=0,column=0, sticky='nsew')
        scrollbar.grid(row=0,column=1, sticky='ns')

        button_frame = tk.Frame(self)
        button_frame.grid(row=5,column=0, sticky='nsew')

        validate_button = tk.Button(button_frame, text="Prévisualiser", command=self.on_preview)
        cancel_button = tk.Button(button_frame, text="Fermer", command=self.on_cancel)

        validate_button.pack(side=tk.LEFT, padx=5)
        cancel_button.pack(side=tk.LEFT, padx=5)

        # make widget expand when resize window
        self.grid_rowconfigure(1, minsize=100, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        text2_frame.grid_rowconfigure(0, weight=1)
        text2_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Ensure the row containing the frame expands
        self.grid_columnconfigure(0, weight=1)

    def check_text_length(self, event):

        # get correct object (if
        wdg = event.widget
        text_content = wdg.get("1.0", tk.END).strip()  # Get text inside widget
        char_limit = CHAR_LIMIT.get(wdg.id_, 10000)  # Get content max char

        if len(text_content) > char_limit:
            wdg.config(**FRAME_WARN)
            wdg.is_length_ok = False
        else:
            wdg.config(**FRAME_NORMAL)
            wdg.is_length_ok = True

        if all([wdg.is_length_ok for wdg in self.actions_wdg_list + [self.poll_msg]]):
            self.validate_button.config(state='normal')
        else:
            self.validate_button.config(state='disabled')

    def show_preview(self, description, action_list):
        popup = tk.Toplevel()
        popup.title("Prévisualisation")
        popup.geometry("500x800")  # Set window size

        tk.Label(popup, text="Message du questionnaire").pack()
        label = tk.Text(popup, height=10, width=40)
        label.insert("1.0", description)
        label.bind("<KeyRelease>", self.check_text_length)
        label.id_ = "title"
        label.pack()
        label.is_length_ok = False
        self.poll_msg = label

        self.answer_label = tk.Label(popup, text="Réponses du questionnaire")
        self.answer_label.pack()
        frame = VerticalScrolledFrame(popup)
        frame.pack(expand=True, fill="y")
        self.actions_wdg_list = []
        for i, action in enumerate(action_list):

            wdg = tk.Text(frame.scrollable_frame, height=5, width=40)
            wdg.pack(padx=2, pady=2)
            wdg.insert("1.0", action)
            wdg.bind("<KeyRelease>", self.check_text_length)
            wdg.id_ = "question"
            wdg.is_length_ok = False
            self.actions_wdg_list.append(wdg)

        self.validate_button = tk.Button(popup, text="Valider", command=self.on_validate)
        self.validate_button.pack(side="left", padx=10, pady=10)

        close_button = tk.Button(popup, text="Annuler", command=popup.destroy)
        close_button.pack(side="left", padx=10, pady=10)

        # Check length at start
        self.check_text_length(FakeEvent(label))
        for wdg in self.actions_wdg_list:
            self.check_text_length(FakeEvent(wdg))

    def on_preview(self):

        poll_msg_txt = self.text1.get("1.0", tk.END).strip()
        actions_list = self.text2.get("1.0", tk.END).strip()
        actions_list = parse_actions(actions_list)

        self.show_preview(poll_msg_txt, actions_list)
        if not actions_list :
            self.answer_label.config(text="No event found, check format")
            print("No event found, check format")

    def on_validate(self):

        poll_msg_txt = self.poll_msg.get("1.0", "end-1c")
        actions_list_txt = [wdg.get("1.0", "end-1c") for wdg in self.actions_wdg_list]
        send_poll(poll_msg_txt, actions_list_txt)
        self.destroy()

    def on_cancel(self):
        self.destroy()

class VerticalScrolledFrame(tk.Frame):
    def __init__(self, container):
        super().__init__(container)
        canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        # Bind mouse wheel scrolling
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-int(e.delta / 120), "units"))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class AskConfigPopup(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Configuration")
        tk.Label(self, text="Fichier de configuration non trouvé.\nPlacez le dans le dossier du script.\nVoulez vous générer un fichier de configration vide?").pack()

        tk.Button(self, text="Oui", command=self.create_config).pack()
        tk.Button(self, text="Annuler", command=self.destroy).pack()

    def create_config(self):
        create_config()
        self.destroy()

def get_config():

    if len(sys.argv) == 2:
        config_path = sys.argv[1]
    else:
        config_path = "credentials.json"

    try:
        with open(config_path, "r") as fp:
            return json.load(fp)
    except FileNotFoundError:
        popup = AskConfigPopup()
        popup.mainloop()
        sys.exit(0)

if __name__ == "__main__":

    CREDENTIALS = get_config()

    gui = Gui()
    gui.mainloop()
