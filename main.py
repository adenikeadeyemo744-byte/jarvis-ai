import webbrowser
import requests
import os
import time
import asyncio
import threading
import random
import socket
import re
import imaplib
import difflib
import edge_tts
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line

try:
    from jnius import autoclass, cast
    from android import activity
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.RECORD_AUDIO,
        Permission.CALL_PHONE,
        Permission.CAMERA,
        Permission.ACCESS_FINE_LOCATION,
    ])
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    RecognizerIntent = autoclass('android.speech.RecognizerIntent')
    Settings = autoclass('android.provider.Settings')
    AlarmClock = autoclass('android.provider.AlarmClock')
    BatteryManager = autoclass('android.os.BatteryManager')
    Context = autoclass('android.content.Context')
    AudioManager = autoclass('android.media.AudioManager')
    Vibrator = autoclass('android.os.Vibrator')
    VibrationEffect = autoclass('android.os.VibrationEffect')
    StatFs = autoclass('android.os.StatFs')
    Environment = autoclass('android.os.Environment')
    CameraManager = autoclass('android.hardware.camera2.CameraManager')
    ANDROID_AVAILABLE = True
except Exception as e:
    print(f"Android module not available: {e}")
    ANDROID_AVAILABLE = False

# --- Setup ---
GEMINI_API_KEY = "PASTE_YOUR_GEMINI_KEY_HERE"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
WEATHER_API_KEY = "PASTE_YOUR_OPENWEATHERMAP_KEY_HERE"
NEWS_API_KEY = "PASTE_YOUR_NEWSAPI_KEY_HERE"
EMAIL_ADDRESS = "PASTE_YOUR_GMAIL_ADDRESS_HERE"
EMAIL_APP_PASSWORD = "PASTE_YOUR_16_CHAR_APP_PASSWORD_HERE"
VOICE = "en-US-GuyNeural"

reminders = []
notes = []
shopping_list = []
last_response = ""
weather_city = "London"
Window.clearcolor = (0.02, 0.08, 0.08, 1)
Window.softinput_mode = 'below_target'

KNOWN_TRIGGERS = [
    "remind me", "reminders", "clear reminders", "take a note", "my notes",
    "clear notes", "shopping list", "weather", "news", "battery", "flashlight on",
    "flashlight off", "volume up", "volume down", "mute", "unmute", "vibrate",
    "storage", "what time", "what date", "joke", "flip a coin", "roll a dice",
    "calculate", "define", "spell", "timer for", "translate", "convert",
    "who are you", "thank you", "hello", "goodbye", "jarvis wake up",
]

GIRL_JOKES = [
    "Are you Wi-Fi? Because I am feeling a strong connection here.",
    "Are you a keyboard? Because you are just my type.",
    "You must be a parking ticket, because you've got 'fine' written all over you.",
    "Are you French? Because Eiffel for you.",
    "Do you have a map? I just got lost in your eyes.",
    "Why don't scientists trust atoms? Because they make up everything!",
    "What do you call a fake noodle? An impasta!",
    "If you were a vegetable, you would be a cute-cumber.",
    "Why did the bicycle fall over? It was two-tired.",
    "What do you call a bear with no teeth? A gummy bear!",
]

JOKES = [
    "Wife: 'How would you describe me?' Husband: 'ABCDEFGHIJK.' Wife: 'What does that mean?' Husband: 'Adorable, beautiful, cute, delightful, elegant, fashionable, gorgeous, and hot.' Wife: 'Aw, thank you, but what about IJK?' Husband: 'I'm just kidding!'",
    "I told my computer I needed a break, and now it won't stop sending me vacation ads.",
    "Parallel lines have so much in common. It's a shame they'll never meet.",
    "I'm on a seafood diet. I see food, and I eat it.",
    "I used to be a banker, but I lost interest.",
    "Why don't scientists trust atoms? Because they make up everything.",
    "I invented a new word: plagiarism.",
    "I would tell you a chemistry joke, but I know I wouldn't get a reaction.",
    "I'm reading a book on anti-gravity. It's impossible to put down.",
    "I used to hate facial hair, but then it grew on me.",
    "I asked a gym instructor, 'Can you teach me to do the splits?' He asked, 'How flexible are you?' I said, 'I can't make Tuesdays.'",
    "Sherlock Holmes and Dr. Watson go camping. In the night, Holmes wakes Watson and asks what he sees. Watson says, 'Millions of stars.' Holmes says, 'And what does that mean?' Watson replies, 'It means astronomical and meteorological perfection.' Holmes says, 'Watson, you idiot. Someone stole our tent.'",
    "A man tells his doctor, 'I can't stop singing The Green Green Grass of Home.' The doctor says, 'That sounds like Tom Jones syndrome.' The man asks, 'Is it common?' The doctor replies, 'It's not unusual.'",
    "Three guys are on a desert island with a genie. The first two wish to go home. The third guy says, 'I'm lonely. I wish my friends were back here.'",
    "A drunk person calls a number by mistake to break up, saying, 'We can't go on this way.' The person who picked up says, 'You have the wrong number,' and the caller just laughs.",
    "Police arrested two kids yesterday. One was drinking battery acid, and the other was eating fireworks. They charged one and let the other one off.",
    "My wife left me because I am insecure. No wait, she's back. She just went to get coffee.",
    "My friend thinks he is smart. He told me an onion is the only food that makes you cry, so I threw a coconut at his face.",
    "What did the duck say when he bought lipstick? Put it on my bill.",
]

QUOTES = [
    "The only way to do great work is to love what you do.",
    "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    "Believe you can and you're halfway there.",
    "It always seems impossible until it's done.",
    "The future belongs to those who believe in the beauty of their dreams.",
]

APP_PACKAGES = {
    "whatsapp": "com.whatsapp",
    "tiktok": "com.zhiliaoapp.musically",
    "instagram": "com.instagram.android",
    "facebook": "com.facebook.katana",
    "twitter": "com.twitter.android",
    "spotify": "com.spotify.music",
    "gmail": "com.google.android.gm",
    "play store": "com.android.vending",
}

BROWSER_LINKS = {
    "youtube": "https://youtube.com",
    "chrome": "https://google.com",
    "maps": "https://maps.google.com",
    "chatgpt": "https://chat.openai.com",
}

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
}

LANG_CODES = {
    "spanish": "es", "french": "fr", "german": "de", "italian": "it",
    "portuguese": "pt", "yoruba": "yo", "hausa": "ha", "igbo": "ig",
    "arabic": "ar", "chinese": "zh", "japanese": "ja", "russian": "ru",
}


def fuzzy_correct(command):
    words = command.split()
    for size in [3, 2, 1]:
        for i in range(len(words) - size + 1):
            phrase = " ".join(words[i:i + size])
            match = difflib.get_close_matches(phrase, KNOWN_TRIGGERS, n=1, cutoff=0.75)
            if match:
                return command.replace(phrase, match[0])
    return command


def get_time_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


async def _generate_speech(text, filename="response.mp3"):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)


def speak(text):
    print(f"JARVIS: {text}")
    try:
        asyncio.run(_generate_speech(text))
        sound = SoundLoader.load("response.mp3")
        if sound:
            sound.play()
            while sound.state == 'play':
                time.sleep(0.1)
        os.remove("response.mp3")
    except Exception as e:
        print(f"Voice error: {e}")


def ask_gemini(question):
    try:
        payload = {"contents": [{"parts": [{"text": question}]}]}
        response = requests.post(GEMINI_URL, json=payload, timeout=15)
        data = response.json()
        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            return f"Gemini error {response.status_code}: {error_msg}"
        if "candidates" not in data:
            return f"No response from Gemini. Raw reply: {data}"
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"I couldn't reach my brain just now. Error: {e}"


def launch_app(package_name):
    if not ANDROID_AVAILABLE:
        return False
    try:
        context = PythonActivity.mActivity
        pm = context.getPackageManager()
        intent = pm.getLaunchIntentForPackage(package_name)
        if intent:
            context.startActivity(intent)
            return True
        return False
    except Exception as e:
        print(f"Launch error: {e}")
        return False


def get_battery_level():
    if not ANDROID_AVAILABLE:
        return None
    try:
        context = PythonActivity.mActivity
        bm = cast(BatteryManager, context.getSystemService(Context.BATTERY_SERVICE))
        return bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
    except Exception as e:
        print(f"Battery error: {e}")
        return None


def get_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={weather_city}&appid={WEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=10)
        data = r.json()
        if r.status_code != 200:
            return f"Weather error: {data.get('message', 'unknown')}"
        temp = data["main"]["temp"]
        main_condition = data["weather"][0]["main"].lower()

        condition_map = {
            "clear": "sunny",
            "clouds": "cloudy",
            "rain": "raining",
            "drizzle": "drizzling",
            "thunderstorm": "stormy",
            "snow": "snowing",
            "mist": "misty",
            "fog": "foggy",
            "haze": "hazy",
        }
        plain_condition = condition_map.get(main_condition, main_condition)

        return f"It's {temp}°C and {plain_condition} in {weather_city} right now, DEATHSTORM."
    except Exception as e:
        return f"Couldn't fetch weather: {e}"


def toggle_flashlight(turn_on):
    if not ANDROID_AVAILABLE:
        return False
    try:
        context = PythonActivity.mActivity
        cam_manager = cast(CameraManager, context.getSystemService(Context.CAMERA_SERVICE))
        cam_id = cam_manager.getCameraIdList()[0]
        cam_manager.setTorchMode(cam_id, turn_on)
        return True
    except Exception as e:
        print(f"Flashlight error: {e}")
        return False


def change_volume(direction):
    if not ANDROID_AVAILABLE:
        return False
    try:
        context = PythonActivity.mActivity
        am = cast(AudioManager, context.getSystemService(Context.AUDIO_SERVICE))
        if direction == "up":
            am.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_RAISE, AudioManager.FLAG_SHOW_UI)
        elif direction == "down":
            am.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_LOWER, AudioManager.FLAG_SHOW_UI)
        elif direction == "mute":
            am.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_MUTE, AudioManager.FLAG_SHOW_UI)
        elif direction == "unmute":
            am.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_UNMUTE, AudioManager.FLAG_SHOW_UI)
        return True
    except Exception as e:
        print(f"Volume error: {e}")
        return False


def do_vibrate():
    if not ANDROID_AVAILABLE:
        return False
    try:
        context = PythonActivity.mActivity
        vib = cast(Vibrator, context.getSystemService(Context.VIBRATOR_SERVICE))
        if hasattr(VibrationEffect, "createOneShot"):
            effect = VibrationEffect.createOneShot(500, VibrationEffect.DEFAULT_AMPLITUDE)
            vib.vibrate(effect)
        else:
            vib.vibrate(500)
        return True
    except Exception as e:
        print(f"Vibrate error: {e}")
        return False


def get_storage_info():
    if not ANDROID_AVAILABLE:
        return None
    try:
        path = Environment.getDataDirectory().getPath()
        stat = StatFs(path)
        total = (stat.getBlockCountLong() * stat.getBlockSizeLong()) / (1024 ** 3)
        free = (stat.getAvailableBlocksLong() * stat.getBlockSizeLong()) / (1024 ** 3)
        return round(free, 1), round(total, 1)
    except Exception as e:
        print(f"Storage error: {e}")
        return None


def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return f"Couldn't get IP: {e}"


def define_word(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return f"I couldn't find a definition for {word}, DEATHSTORM."
        data = r.json()
        meaning = data[0]["meanings"][0]["definitions"][0]["definition"]
        return f"{word}: {meaning}"
    except Exception as e:
        return f"Couldn't look that up: {e}"


def safe_calculate(expression):
    try:
        expression = expression.replace("plus", "+").replace("minus", "-") \
            .replace("times", "*").replace("divided by", "/").replace(" x ", "*")
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return None
        result = eval(expression, {"__builtins__": {}})
        return result
    except Exception:
        return None


def run_timer(seconds, label):
    time.sleep(seconds)
    speak(f"Time's up on your {label} timer, DEATHSTORM.")


def get_unread_email_count():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        mail.select("inbox")
        status, data = mail.search(None, "UNSEEN")
        unread_count = len(data[0].split())
        mail.logout()
        return unread_count
    except Exception as e:
        print(f"Email check error: {e}")
        return None


def translate_text(text, target_lang_name):
    try:
        target_code = LANG_CODES.get(target_lang_name.lower())
        if not target_code:
            return f"I don't know the language '{target_lang_name}' yet, DEATHSTORM."
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair=en|{target_code}"
        r = requests.get(url, timeout=10)
        data = r.json()
        translated = data["responseData"]["translatedText"]
        return f"{text} in {target_lang_name} is: {translated}"
    except Exception as e:
        return f"Couldn't translate that: {e}"


def convert_currency(amount, from_cur, to_cur):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_cur.upper()}"
        r = requests.get(url, timeout=10)
        data = r.json()
        rate = data["rates"].get(to_cur.upper())
        if rate is None:
            return None
        return round(amount * rate, 2)
    except Exception as e:
        print(f"Currency error: {e}")
        return None


def get_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&pageSize=3&apiKey={NEWS_API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("status") != "ok":
            return "I couldn't fetch the news right now, DEATHSTORM."
        headlines = [article["title"] for article in data["articles"][:3]]
        return "Here are the top headlines: " + ". ".join(headlines)
    except Exception as e:
        return f"Couldn't fetch news: {e}"


def parse_target_date(text):
    text = text.lower()
    day_match = re.search(r'\b(\d{1,2})\b', text)
    month_num = None
    for name, num in MONTHS.items():
        if name in text:
            month_num = num
            break
    if not day_match or not month_num:
        return None
    day = int(day_match.group(1))
    year = datetime.now().year
    try:
        target = datetime(year, month_num, day)
        if target < datetime.now():
            target = datetime(year + 1, month_num, day)
        return target
    except Exception:
        return None


def handle_command(command):
    global last_response, weather_city
    command = command.lower()
    command = fuzzy_correct(command)

    if "jarvis wake up" in command or "wake up jarvis" in command:
        greeting = get_time_greeting()
        speak(f"{greeting}, sir.")
        time.sleep(0.3)

        briefing_parts = []

        if reminders:
            briefing_parts.append(
                f"You have {len(reminders)} reminder{'s' if len(reminders) != 1 else ''}: "
                + ", ".join(reminders) + "."
            )
        else:
            briefing_parts.append("You have no pending reminders.")

        if notes:
            briefing_parts.append(f"You have {len(notes)} saved note{'s' if len(notes) != 1 else ''}.")

        level = get_battery_level()
        if level is not None:
            briefing_parts.append(f"Battery is at {level} percent.")

        now_str = datetime.now().strftime("%I:%M %p")
        briefing_parts.append(f"It's currently {now_str}.")

        briefing = " ".join(briefing_parts)
        speak(briefing)
        return f"{greeting}, sir. " + briefing

    for name, url in BROWSER_LINKS.items():
        if f"open {name}" in command or name in command:
            speak(f"Opening {name}, DEATHSTORM.")
            webbrowser.open(url)
            return f"Opening {name}."

    for name, package in APP_PACKAGES.items():
        if f"open {name}" in command or (name in command and "open" in command):
            if launch_app(package):
                speak(f"Opening {name}, DEATHSTORM.")
                return f"Opening {name}."
            else:
                msg = f"{name.title()} doesn't seem to be installed, DEATHSTORM."
                speak(msg)
                return msg

    if command.startswith("call "):
        number = command.replace("call", "").strip()
        if ANDROID_AVAILABLE:
            intent = Intent(Intent.ACTION_DIAL, Uri.parse(f"tel:{number}"))
            PythonActivity.mActivity.startActivity(intent)
            speak(f"Calling {number}, DEATHSTORM.")
            return f"Dialing {number}"
        return "Calling isn't available right now."

    elif command.startswith("text "):
        number = command.replace("text", "").strip()
        if ANDROID_AVAILABLE:
            intent = Intent(Intent.ACTION_SENDTO, Uri.parse(f"smsto:{number}"))
            PythonActivity.mActivity.startActivity(intent)
            speak(f"Opening a text to {number}, DEATHSTORM.")
            return f"Texting {number}"
        return "Texting isn't available right now."

    elif "battery" in command:
        level = get_battery_level()
        if level is not None:
            speak(f"Battery is at {level} percent, DEATHSTORM.")
            return f"Battery: {level}%"
        return "Couldn't read battery level."

    elif "set alarm" in command:
        if ANDROID_AVAILABLE:
            intent = Intent(AlarmClock.ACTION_SET_ALARM)
            PythonActivity.mActivity.startActivity(intent)
            speak("Opening the alarm screen, DEATHSTORM.")
            return "Opening alarm settings."
        return "Alarms aren't available right now."

    elif "camera" in command or "take a photo" in command:
        if ANDROID_AVAILABLE:
            intent = Intent("android.media.action.IMAGE_CAPTURE")
            PythonActivity.mActivity.startActivity(intent)
            speak("Opening the camera, DEATHSTORM.")
            return "Opening camera."
        return "Camera isn't available right now."

    elif "brightness" in command:
        if ANDROID_AVAILABLE:
            intent = Intent(Settings.ACTION_DISPLAY_SETTINGS)
            PythonActivity.mActivity.startActivity(intent)
            speak("Opening display settings, DEATHSTORM.")
            return "Opening display settings."
        return "Display settings aren't available right now."

    elif "open settings" in command:
        if ANDROID_AVAILABLE:
            intent = Intent(Settings.ACTION_SETTINGS)
            PythonActivity.mActivity.startActivity(intent)
            speak("Opening settings, DEATHSTORM.")
            return "Opening settings."
        return "Settings isn't available right now."

    elif "wifi" in command:
        if ANDROID_AVAILABLE:
            intent = Intent(Settings.ACTION_WIFI_SETTINGS)
            PythonActivity.mActivity.startActivity(intent)
            speak("Opening WiFi settings, DEATHSTORM.")
            return "Opening WiFi settings."
        return "WiFi settings aren't available right now."

    elif "bluetooth" in command:
        if ANDROID_AVAILABLE:
            intent = Intent(Settings.ACTION_BLUETOOTH_SETTINGS)
            PythonActivity.mActivity.startActivity(intent)
            speak("Opening Bluetooth settings, DEATHSTORM.")
            return "Opening Bluetooth settings."
        return "Bluetooth settings aren't available right now."

    elif "airplane mode" in command:
        if ANDROID_AVAILABLE:
            intent = Intent(Settings.ACTION_AIRPLANE_MODE_SETTINGS)
            PythonActivity.mActivity.startActivity(intent)
            speak("Opening Airplane mode settings, DEATHSTORM.")
            return "Opening Airplane mode settings."
        return "Airplane mode settings aren't available right now."

    elif "flashlight on" in command or "torch on" in command:
        if toggle_flashlight(True):
            speak("Flashlight on, DEATHSTORM.")
            return "Flashlight: ON"
        return "Couldn't control the flashlight."

    elif "flashlight off" in command or "torch off" in command:
        if toggle_flashlight(False):
            speak("Flashlight off, DEATHSTORM.")
            return "Flashlight: OFF"
        return "Couldn't control the flashlight."

    elif "volume up" in command:
        change_volume("up")
        speak("Volume up, DEATHSTORM.")
        return "Volume increased."

    elif "volume down" in command:
        change_volume("down")
        speak("Volume down, DEATHSTORM.")
        return "Volume decreased."

    elif "mute" in command and "unmute" not in command:
        change_volume("mute")
        speak("Muted, DEATHSTORM.")
        return "Muted."

    elif "unmute" in command:
        change_volume("unmute")
        speak("Unmuted, DEATHSTORM.")
        return "Unmuted."

    elif "vibrate" in command:
        do_vibrate()
        return "Vibrating."

    elif "storage" in command:
        info = get_storage_info()
        if info:
            free, total = info
            msg = f"You have {free} GB free out of {total} GB, DEATHSTORM."
            speak(msg)
            return msg
        return "Couldn't read storage info."

    elif "ip address" in command or "my ip" in command:
        ip = get_ip_address()
        msg = f"Your IP address is {ip}, DEATHSTORM."
        speak(msg)
        return msg

    elif "how many emails" in command or "check email" in command or "unread email" in command:
        count = get_unread_email_count()
        if count is not None:
            msg = f"You have {count} unread email{'s' if count != 1 else ''}, DEATHSTORM."
        else:
            msg = "I couldn't check your email right now, DEATHSTORM."
        speak(msg)
        return msg

    elif "where am i" in command or "current location" in command:
        speak("I don't have GPS wired up yet, DEATHSTORM.")
        return "Location tracking not yet enabled."

    elif "app version" in command or "about you" in command:
        msg = "I'm Jarvis, version 1.0, built for DEATHSTORM."
        speak(msg)
        return msg

    elif "clear all" in command or "reset everything" in command:
        reminders.clear()
        notes.clear()
        shopping_list.clear()
        speak("Everything cleared, DEATHSTORM. Fresh start.")
        return "All data cleared."

    elif "set my city" in command or "set city to" in command:
        city = command.replace("set my city to", "").replace("set city to", "").strip()
        if city:
            weather_city = city.title()
            speak(f"City set to {weather_city}, DEATHSTORM.")
            return f"City set: {weather_city}"
        return "Tell me the city name, DEATHSTORM."

    elif "take a note" in command or "note that" in command:
        note_text = command.replace("take a note", "").replace("note that", "").strip(": ").strip()
        notes.append(note_text)
        speak(f"Noted: {note_text}")
        return f"Note saved: {note_text}"

    elif "read my notes" in command or "my notes" in command:
        if notes:
            msg = "Your notes: " + ", ".join(notes)
        else:
            msg = "You have no notes, DEATHSTORM."
        speak(msg)
        return msg

    elif "clear notes" in command or "delete notes" in command:
        notes.clear()
        speak("All notes cleared, DEATHSTORM.")
        return "Notes cleared."

    elif "add" in command and "shopping list" in command:
        item = command.replace("add", "").replace("to shopping list", "").replace("to my shopping list", "").strip()
        shopping_list.append(item)
        speak(f"Added {item} to your shopping list, DEATHSTORM.")
        return f"Added: {item}"

    elif "shopping list" in command:
        if shopping_list:
            msg = "Your shopping list: " + ", ".join(shopping_list)
        else:
            msg = "Your shopping list is empty, DEATHSTORM."
        speak(msg)
        return msg

    elif "clear shopping list" in command:
        shopping_list.clear()
        speak("Shopping list cleared, DEATHSTORM.")
        return "Shopping list cleared."

    elif "weather" in command:
        report = get_weather()
        speak(report)
        return report

    elif "news" in command:
        report = get_news()
        speak(report)
        return report

    elif command.startswith("search for") or command.startswith("google"):
        query = command.replace("search for", "").replace("google", "").strip()
        speak(f"Searching for {query}, DEATHSTORM.")
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return f"Searching for: {query}"

    elif "wikipedia" in command:
        query = command.replace("wikipedia", "").replace("search", "").strip()
        speak(f"Looking up {query} on Wikipedia, DEATHSTORM.")
        webbrowser.open(f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}")
        return f"Opening Wikipedia: {query}"

    elif "translate" in command and " to " in command:
        try:
            parts = command.replace("translate", "").split(" to ")
            phrase = parts[0].strip()
            lang = parts[1].strip()
            result = translate_text(phrase, lang)
            speak(result)
            return result
        except Exception:
            return "Say it like: translate hello to spanish."

    elif "convert" in command and ("dollars" in command or "naira" in command or "euros" in command or "pounds" in command):
        try:
            nums = [float(s) for s in command.replace("-", " ").split() if s.replace('.', '', 1).isdigit()]
            amount = nums[0]
            currency_map = {"dollars": "USD", "naira": "NGN", "euros": "EUR", "pounds": "GBP"}
            found_currencies = [v for k, v in currency_map.items() if k in command]
            if len(found_currencies) >= 2:
                from_cur, to_cur = found_currencies[0], found_currencies[1]
                result = convert_currency(amount, from_cur, to_cur)
                if result is not None:
                    msg = f"{amount} {from_cur} is about {result} {to_cur}, DEATHSTORM."
                else:
                    msg = "I couldn't get that exchange rate, DEATHSTORM."
            else:
                msg = "Tell me both currencies, like: convert 10 dollars to naira."
            speak(msg)
            return msg
        except Exception:
            return "I need an amount and two currencies, DEATHSTORM."

    elif "convert" in command and ("km" in command or "miles" in command):
        try:
            nums = [float(s) for s in command.split() if s.replace('.', '', 1).isdigit()]
            value = nums[0]
            if "km" in command and "to miles" in command:
                result = round(value * 0.621371, 2)
                msg = f"{value} km is {result} miles, DEATHSTORM."
            elif "miles" in command and "to km" in command:
                result = round(value * 1.60934, 2)
                msg = f"{value} miles is {result} km, DEATHSTORM."
            else:
                msg = "Tell me the direction, like: convert 5 km to miles."
            speak(msg)
            return msg
        except Exception:
            return "I need a number to convert, DEATHSTORM."

    elif "convert" in command and ("kg" in command or "lbs" in command or "pounds" in command):
        try:
            nums = [float(s) for s in command.split() if s.replace('.', '', 1).isdigit()]
            value = nums[0]
            if "kg" in command and ("to lbs" in command or "to pounds" in command):
                result = round(value * 2.20462, 2)
                msg = f"{value} kg is {result} lbs, DEATHSTORM."
            elif ("lbs" in command or "pounds" in command) and "to kg" in command:
                result = round(value / 2.20462, 2)
                msg = f"{value} lbs is {result} kg, DEATHSTORM."
            else:
                msg = "Tell me the direction, like: convert 10 kg to lbs."
            speak(msg)
            return msg
        except Exception:
            return "I need a number to convert, DEATHSTORM."

    elif "convert" in command and ("celsius" in command or "fahrenheit" in command):
        try:
            nums = [float(s) for s in command.replace("-", " ").split() if s.replace('.', '', 1).isdigit()]
            value = nums[0]
            if "celsius" in command and "to fahrenheit" in command:
                result = (value * 9 / 5) + 32
                msg = f"{value}°C is {round(result, 1)}°F, DEATHSTORM."
            elif "fahrenheit" in command and "to celsius" in command:
                result = (value - 32) * 5 / 9
                msg = f"{value}°F is {round(result, 1)}°C, DEATHSTORM."
            else:
                msg = "Tell me which direction to convert, DEATHSTORM."
            speak(msg)
            return msg
        except Exception:
            return "I need a number to convert, DEATHSTORM."

    elif "pick between" in command or "choose between" in command:
        try:
            options_text = command.replace("pick between", "").replace("choose between", "").strip()
            options = [o.strip() for o in re.split(r"\bor\b|,", options_text) if o.strip()]
            if len(options) >= 2:
                choice = random.choice(options)
                speak(f"I'd go with {choice}, DEATHSTORM.")
                return f"Picked: {choice}"
            return "Give me at least two options, DEATHSTORM."
        except Exception:
            return "Give me at least two options, DEATHSTORM."

    elif "countdown to" in command or "days until" in command:
        date_text = command.replace("countdown to", "").replace("days until", "").strip()
        target = parse_target_date(date_text)
        if target:
            days_left = (target - datetime.now()).days
            msg = f"There are {days_left} days until {date_text}, DEATHSTORM."
        else:
            msg = "I couldn't understand that date, DEATHSTORM. Try like: countdown to december 25."
        speak(msg)
        return msg

    elif "remind me" in command:
        reminder_text = command.replace("remind me to", "").replace("remind me", "").strip()
        reminders.append(reminder_text)
        speak(f"Reminder noted: {reminder_text}")
        return f"Reminder noted: {reminder_text}"

    elif "reminders" in command:
        if reminders:
            msg = "Here are your reminders: " + ", ".join(reminders)
        else:
            msg = "You have no reminders, DEATHSTORM."
        speak(msg)
        return msg

    elif "clear reminders" in command:
        reminders.clear()
        speak("All reminders cleared, DEATHSTORM.")
        return "Reminders cleared."

    elif "what time" in command or "current time" in command:
        now_str = datetime.now().strftime("%I:%M %p")
        speak(f"It's {now_str}, DEATHSTORM.")
        return f"Time: {now_str}"

    elif "what date" in command or "what day" in command:
        date_str = datetime.now().strftime("%A, %d %B %Y")
        speak(f"Today is {date_str}, DEATHSTORM.")
        return f"Date: {date_str}"

    elif "flip a coin" in command:
        result = random.choice(["Heads", "Tails"])
        speak(f"{result}, DEATHSTORM.")
        return result

    elif "roll a dice" in command or "roll a die" in command:
        result = random.randint(1, 6)
        speak(f"You rolled a {result}, DEATHSTORM.")
        return f"Rolled: {result}"

    elif "random number between" in command:
        try:
            nums = [int(s) for s in command.split() if s.isdigit()]
            low, high = nums[0], nums[1]
            result = random.randint(low, high)
            speak(f"Your number is {result}, DEATHSTORM.")
            return f"Random number: {result}"
        except Exception:
            return "I need two numbers for that, DEATHSTORM."

    elif "calculate" in command:
        expr = command.replace("calculate", "").strip()
        result = safe_calculate(expr)
        if result is not None:
            speak(f"That's {result}, DEATHSTORM.")
            return f"{expr} = {result}"
        return "I couldn't calculate that, DEATHSTORM."

    elif "define" in command:
        word = command.replace("define", "").strip()
        definition = define_word(word)
        speak(definition)
        return definition

    elif "spell" in command:
        word = command.replace("spell", "").strip()
        if word:
            spelled = ", ".join(list(word.upper()))
            speak(spelled)
            return f"{word.upper()}: {spelled}"
        return "What would you like me to spell, DEATHSTORM?"

    elif "timer for" in command:
        try:
            nums = [int(s) for s in command.split() if s.isdigit()]
            minutes = nums[0]
            seconds = minutes * 60
            threading.Thread(target=run_timer, args=(seconds, f"{minutes}-minute"), daemon=True).start()
            speak(f"Timer set for {minutes} minutes, DEATHSTORM.")
            return f"Timer set: {minutes} min"
        except Exception:
            return "I need a number of minutes for that, DEATHSTORM."

    elif "repeat that" in command or "say that again" in command:
        if last_response:
            speak(last_response)
            return last_response
        return "I haven't said anything yet, DEATHSTORM."

    elif "inspire me" in command or command.strip() == "quote":
        quote = random.choice(QUOTES)
        speak(quote)
        return quote

    elif "joke for a girl" in command or "girl joke" in command:
        joke = random.choice(GIRL_JOKES)
        speak(joke)
        return joke

    elif "joke" in command:
        joke = random.choice(JOKES)
        speak(joke)
        return joke

    elif "how are you" in command:
        msg = "Running at full capacity and ready to help, DEATHSTORM."
        speak(msg)
        return msg

    elif "good night" in command:
        msg = "Good night, DEATHSTORM. Rest well."
        speak(msg)
        return msg

    elif "goodbye" in command or "bye jarvis" in command:
        msg = "Goodbye, DEATHSTORM. Standing by whenever you need me."
        speak(msg)
        return msg

    elif "who are you" in command:
        msg = "I am Jarvis, your personal assistant, DEATHSTORM."
        speak(msg)
        return msg

    elif "thank you" in command or "thanks" in command:
        msg = "You're welcome, DEATHSTORM."
        speak(msg)
        return msg

    elif "hello" in command:
        msg = "Hello, DEATHSTORM. How can I assist you?"
        speak(msg)
        return msg

    else:
        answer = ask_gemini(command)
        speak(answer)
        return answer


class ArcReactor(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0
        self.glow = True
        with self.canvas:
            self.core_color = Color(0, 1, 1, 1)
            self.core = Ellipse(pos=(self.center_x - 20, self.center_y - 20), size=(40, 40))
            self.ring_color1 = Color(0, 0.7, 1, 0.8)
            self.ring1 = Line(circle=(self.center_x, self.center_y, 55, 0, 90), width=2)
            self.ring_color2 = Color(0, 0.9, 1, 0.6)
            self.ring2 = Line(circle=(self.center_x, self.center_y, 75, 0, 140), width=2)
            self.ring_color3 = Color(0, 1, 1, 0.4)
            self.ring3 = Line(circle=(self.center_x, self.center_y, 95, 0, 60), width=2)
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        Clock.schedule_interval(self.animate, 0.03)

    def update_canvas(self, *args):
        self.core.pos = (self.center_x - 20, self.center_y - 20)

    def animate(self, dt):
        self.glow = not self.glow
        self.core_color.rgb = (0, 1, 1) if self.glow else (0, 0.75, 1)
        self.angle = (self.angle + 4) % 360
        cx, cy = self.center_x, self.center_y
        self.ring1.circle = (cx, cy, 55, self.angle, self.angle + 90)
        self.ring2.circle = (cx, cy, 75, -self.angle, -self.angle + 140)
        self.ring3.circle = (cx, cy, 95, self.angle * 2, self.angle * 2 + 60)


class BootScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()

        self.reactor = ArcReactor(
            pos_hint={'center_x': 0.5, 'center_y': 0.55},
            size_hint=(0.7, 0.35)
        )
        layout.add_widget(self.reactor)

        self.boot_label = Label(
            text="INITIALIZING JARVIS",
            font_size='20sp',
            color=(0.3, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.3},
            size_hint=(1, 0.08)
        )
        layout.add_widget(self.boot_label)

        self.dots_label = Label(
            text="",
            font_size='20sp',
            color=(0.3, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.25},
            size_hint=(1, 0.08)
        )
        layout.add_widget(self.dots_label)

        self.add_widget(layout)
        self.dot_count = 0

    def on_enter(self):
        Clock.schedule_interval(self.animate_dots, 0.4)
        Clock.schedule_once(self.go_to_main, 5)

    def animate_dots(self, dt):
        self.dot_count = (self.dot_count + 1) % 4
        self.dots_label.text = "." * self.dot_count
        return True

    def go_to_main(self, dt):
        Clock.unschedule(self.animate_dots)
        self.manager.current = "main"


class JarvisUI(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_widget(Label(text="J A R V I S", font_size='32sp', color=(0.2, 0.9, 0.9, 1),
                               pos_hint={'center_x': 0.5, 'top': 0.98}, size_hint=(1, 0.08)))

        self.status_label = Label(text="LISTENING: OFF", font_size='16sp', color=(0.5, 0.9, 0.9, 0.8),
                                   pos_hint={'center_x': 0.5, 'top': 0.90}, size_hint=(1, 0.05))
        self.add_widget(self.status_label)

        self.reactor = ArcReactor(pos_hint={'center_x': 0.5, 'center_y': 0.64}, size_hint=(0.6, 0.3))
        self.add_widget(self.reactor)

        self.clock_label = Label(text="", font_size='40sp', color=(0.6, 1, 1, 1),
                                  pos_hint={'center_x': 0.5, 'center_y': 0.66}, size_hint=(1, 0.15))
        self.add_widget(self.clock_label)

        self.date_label = Label(text="", font_size='16sp', color=(0.5, 0.9, 0.9, 0.9),
                                 pos_hint={'center_x': 0.5, 'center_y': 0.56}, size_hint=(1, 0.05))
        self.add_widget(self.date_label)

        Clock.schedule_interval(self.update_clock, 1)
        self.update_clock(0)

        self.response_label = Label(text="Say hello, DEATHSTORM.", font_size='16sp', color=(0.7, 1, 1, 1),
                                     pos_hint={'center_x': 0.5, 'center_y': 0.38}, size_hint=(0.85, 0.2),
                                     halign='center', valign='middle')
        self.response_label.bind(size=self.response_label.setter('text_size'))
        self.add_widget(self.response_label)

        self.mic_button = Button(text="[b]MIC[/b]", markup=True, font_size='16sp', size_hint=(None, None),
                                  size=(70, 70), pos_hint={'center_x': 0.5, 'y': 0.16},
                                  background_normal='', background_color=(0, 0.6, 0.7, 1), color=(1, 1, 1, 1))
        self.mic_button.bind(on_press=self.on_mic_press)
        self.add_widget(self.mic_button)

        input_row = BoxLayout(orientation='horizontal', pos_hint={'center_x': 0.5, 'y': 0.05},
                               size_hint=(0.9, 0.08), spacing=10)
        self.text_input = TextInput(
            hint_text="Or type here...",
            multiline=False,
            font_size='16sp',
            foreground_color=(0, 0, 0, 1),
            background_color=(1, 1, 1, 1),
            cursor_color=(0, 0.6, 0.7, 1),
            hint_text_color=(0.4, 0.4, 0.4, 1),
            padding=[10, 10, 10, 10],
            input_type='text'
        )
        send_btn = Button(text="SEND", size_hint=(0.3, 1))
        send_btn.bind(on_press=self.on_send)
        input_row.add_widget(self.text_input)
        input_row.add_widget(send_btn)
        self.add_widget(input_row)

        if ANDROID_AVAILABLE:
            activity.bind(on_activity_result=self.on_activity_result)

        Clock.schedule_once(
            lambda dt: threading.Thread(
                target=speak,
                args=(f"Systems online. {get_time_greeting()}, DEATHSTORM.",),
                daemon=True
            ).start(), 0.5)

    def update_clock(self, dt):
        now = datetime.now()
        self.clock_label.text = now.strftime("%I:%M:%S %p")
        self.date_label.text = now.strftime("%A, %d %B %Y")

    def on_mic_press(self, instance):
        if not ANDROID_AVAILABLE:
            self.response_label.text = "Voice recognition unavailable — please type instead."
            return
        try:
            self.status_label.text = "LISTENING: ON"
            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak now, DEATHSTORM...")
            PythonActivity.mActivity.startActivityForResult(intent, 1001)
        except Exception as e:
            self.status_label.text = "LISTENING: OFF"
            self.response_label.text = f"Mic error: {e}"

    def on_activity_result(self, request_code, result_code, intent):
        if request_code == 1001:
            try:
                results = intent.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                spoken_text = results.get(0) if results else ""
                self.status_label.text = "LISTENING: OFF"
                if spoken_text:
                    self.response_label.text = f"You: {spoken_text}"
                    threading.Thread(target=self.process_command, args=(spoken_text,), daemon=True).start()
            except Exception as e:
                self.status_label.text = "LISTENING: OFF"
                self.response_label.text = f"Couldn't read voice result: {e}"

    def on_send(self, instance):
        command = self.text_input.text.strip()
        if not command:
            return
        self.status_label.text = "LISTENING: PROCESSING..."
        self.response_label.text = f"You: {command}"
        self.text_input.text = ""
        threading.Thread(target=self.process_command, args=(command,), daemon=True).start()

    def process_command(self, command):
        global last_response
        result = handle_command(command)
        last_response = result
        Clock.schedule_once(lambda dt: self.update_response(result), 0)

    def update_response(self, result):
        self.response_label.text = result
        self.status_label.text = "LISTENING: OFF"


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(JarvisUI())


class JarvisApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(BootScreen(name="boot"))
        sm.add_widget(MainScreen(name="main"))
        sm.current = "boot"
        return sm


if __name__ == "__main__":
    JarvisApp().run()