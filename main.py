import webbrowser
import requests
import os
import time
import asyncio
import threading
import random
import socket
import edge_tts
from datetime import datetime
from kivy.app import App
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
    Build_VERSION = autoclass('android.os.Build$VERSION')
    ANDROID_AVAILABLE = True
except Exception as e:
    print(f"Android module not available: {e}")
    ANDROID_AVAILABLE = False

# --- Setup ---
GEMINI_API_KEY = "PASTE_YOUR_GEMINI_KEY_HERE"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
WEATHER_API_KEY = "PASTE_YOUR_OPENWEATHERMAP_KEY_HERE"
VOICE = "en-US-GuyNeural"

reminders = []
notes = []
flashlight_on = False
Window.clearcolor = (0.02, 0.08, 0.08, 1)

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I would tell you a UDP joke, but you might not get it.",
    "There are 10 types of people: those who understand binary, and those who don't.",
]

APP_PACKAGES = {
    "whatsapp": "com.whatsapp",
    "tiktok": "com.zhiliaoapp.musically",
    "instagram": "com.instagram.android",
    "facebook": "com.facebook.katana",
    "twitter": "com.twitter.android",
    "spotify": "com.spotify.music",
    "gmail": "com.google.android.gm",
    "youtube": "com.google.android.youtube",
    "chrome": "com.android.chrome",
    "maps": "com.google.android.apps.maps",
    "play store": "com.android.vending",
}


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
        url = f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={WEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=10)
        data = r.json()
        if r.status_code != 200:
            return f"Weather error: {data.get('message', 'unknown')}"
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return f"It's {temp}°C with {desc}."
    except Exception as e:
        return f"Couldn't fetch weather: {e}"


def toggle_flashlight(turn_on):
    global flashlight_on
    if not ANDROID_AVAILABLE:
        return False
    try:
        context = PythonActivity.mActivity
        cam_manager = cast(CameraManager, context.getSystemService(Context.CAMERA_SERVICE))
        cam_id = cam_manager.getCameraIdList()[0]
        cam_manager.setTorchMode(cam_id, turn_on)
        flashlight_on = turn_on
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


def handle_command(command):
    global flashlight_on
    command = command.lower()

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

    elif "weather" in command:
        report = get_weather()
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

    elif "joke" in command:
        joke = random.choice(JOKES)
        speak(joke)
        return joke

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
        self.text_input = TextInput(hint_text="Or type here...", multiline=False, font_size='16sp')
        send_btn = Button(text="SEND", size_hint=(0.3, 1))
        send_btn.bind(on_press=self.on_send)
        input_row.add_widget(self.text_input)
        input_row.add_widget(send_btn)
        self.add_widget(input_row)

        if ANDROID_AVAILABLE:
            activity.bind(on_activity_result=self.on_activity_result)

        Clock.schedule_once(
            lambda dt: threading.Thread(target=speak, args=("Systems online. Good day, DEATHSTORM.",),
                                         daemon=True).start(), 1)

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
        result = handle_command(command)
        Clock.schedule_once(lambda dt: self.update_response(result), 0)

    def update_response(self, result):
        self.response_label.text = result
        self.status_label.text = "LISTENING: OFF"


class JarvisApp(App):
    def build(self):
        return JarvisUI()


if __name__ == "__main__":
    JarvisApp().run()