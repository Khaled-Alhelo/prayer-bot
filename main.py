import os
import datetime
from threading import Thread
import discord
from discord.ext import commands, tasks
import requests
from flask import Flask

# إنشاء تطبيق Flask
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

TOKEN = os.getenv("DISCORD_TOKEN")

CITIES = {
    "عمان": {"lat": 31.9539, "lng": 35.9106},
    "دونا أوفاروش": {"lat": 46.9619, "lng": 18.9355}
}

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_prayer_times(lat, lng):
    url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lng}&method=3"
    response = requests.get(url).json()
    timings = response["data"]["timings"]
    return {
        "الفجر": timings["Fajr"],
        "الظهر": timings["Dhuhr"],
        "العصر": timings["Asr"],
        "المغرب": timings["Maghrib"],
        "العشاء": timings["Isha"]
    }

sent_today = set()

@tasks.loop(seconds=30)
async def check_prayer_times():
    now = datetime.datetime.now()
    current_time_str = now.strftime("%H:%M")
    today_str = now.strftime("%Y-%m-%d")

    # البحث عن القناة المسماة "أوقات الصلاة" أو "أوقات-الصلاة" في كافة السيرفرات
    for guild in bot.guilds:
        target_channel = None
        for channel in guild.text_channels:
            if channel.name in ["أوقات-الصلاة", "أوقات_الصلاة", "أوقات الصلاة", "اوقات-الصلاة", "اوقات_الصلاة", "اوقات الصلاة"]:
                target_channel = channel
                break
        
        if not target_channel:
            continue

        for city, coords in CITIES.items():
            try:
                times = get_prayer_times(coords["lat"], coords["lng"])
                for prayer, prayer_time in times.items():
                    event_key = f"{today_str}_{city}_{prayer}_{guild.id}"
                    if current_time_str == prayer_time and event_key not in sent_today:
                        await target_channel.send(f"🕌 حان الآن موعد صلاة **{prayer}** في مدينة **{city}**")
                        sent_today.add(event_key)
            except Exception as e:
                print(f"خطأ في جلب المواقيت: {e}")

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")
    check_prayer_times.start()

keep_alive()
bot.run(TOKEN)