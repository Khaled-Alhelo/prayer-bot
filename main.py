import os
import datetime
from threading import Thread
import discord
from discord.ext import commands, tasks
import requests
from flask import Flask
import zoneinfo

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()

TOKEN = os.getenv("DISCORD_TOKEN")

CITIES = {
    "عمان": {
        "lat": 31.9539, 
        "lng": 35.9106, 
        "method": 5,          # Egyptian General Authority (Standard in Jordan)
        "tz": "Asia/Amman"
    },
    "دونا أوفاروش": {
        "lat": 46.9619, 
        "lng": 18.9355, 
        "method": 3,          # Muslim World League (Standard in Europe)
        "tz": "Europe/Budapest"
    }
}

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True  # Required to read commands like !next

bot = commands.Bot(command_prefix="!", intents=intents)

def get_prayer_times(lat, lng, method):
    url = f"http://api.aladhan.com/v1/timings?latitude={lat}&longitude={lng}&method={method}"
    response = requests.get(url).json()
    timings = response["data"]["timings"]
    return {
        "الفجر": timings["Fajr"],
        "الظهر": timings["Dhuhr"],
        "العصر": timings["Asr"],
        "المغرب": timings["Maghrib"],
        "العشاء": timings["Isha"]
    }

def get_next_prayer_info(city, info):
    local_tz = zoneinfo.ZoneInfo(info["tz"])
    now_local = datetime.datetime.now(local_tz)
    
    times = get_prayer_times(info["lat"], info["lng"], info["method"])
    
    for prayer_name, time_str in times.items():
        prayer_hour, prayer_minute = map(int, time_str.split(':'))
        prayer_time_dt = now_local.replace(hour=prayer_hour, minute=prayer_minute, second=0, microsecond=0)
        
        if prayer_time_dt > now_local:
            time_diff = prayer_time_dt - now_local
            minutes_remaining = int(time_diff.total_seconds() // 60)
            hours = minutes_remaining // 60
            mins = minutes_remaining % 60
            
            time_left_str = f"{hours} ساعة و {mins} دقيقة" if hours > 0 else f"{mins} دقيقة"
            return prayer_name, time_str, time_left_str

    # If all prayers for today have passed, the next prayer is Fajr tomorrow
    fajr_hour, fajr_minute = map(int, times["الفجر"].split(':'))
    fajr_dt = (now_local + datetime.timedelta(days=1)).replace(hour=fajr_hour, minute=fajr_minute, second=0, microsecond=0)
    time_diff = fajr_dt - now_local
    minutes_remaining = int(time_diff.total_seconds() // 60)
    hours = minutes_remaining // 60
    mins = minutes_remaining % 60
    time_left_str = f"{hours} ساعة و {mins} دقيقة" if hours > 0 else f"{mins} دقيقة"
    
    return "الفجر (غداً)", times["الفجر"], time_left_str

sent_today = set()

@tasks.loop(seconds=30)
async def check_prayer_times():
    for city, info in CITIES.items():
        local_tz = zoneinfo.ZoneInfo(info["tz"])
        now_local = datetime.datetime.now(local_tz)
        
        current_time_str = now_local.strftime("%H:%M")
        today_str = now_local.strftime("%Y-%m-%d")

        try:
            times = get_prayer_times(info["lat"], info["lng"], info["method"])
            
            for prayer, prayer_time in times.items():
                if current_time_str == prayer_time:
                    for guild in bot.guilds:
                        target_channel = None
                        for channel in guild.text_channels:
                            if channel.name in ["أوقات-الصلاة", "أوقات_الصلاة", "أوقات الصلاة", "اوقات-الصلاة", "اوقات_الصلاة", "اوقات الصلاة"]:
                                target_channel = channel
                                break
                        
                        if not target_channel:
                            continue

                        event_key = f"{today_str}_{city}_{prayer}_{guild.id}"
                        if event_key not in sent_today:
                            await target_channel.send(f"🕌 حان الآن موعد صلاة **{prayer}** في مدينة **{city}**")
                            sent_today.add(event_key)
        except Exception as e:
            print(f"Error fetching times for {city}: {e}")

@bot.command(name="next", aliases=["الصلاة", "القادمة"])
async def next_prayer_cmd(ctx):
    """Command to get the next prayer time for both locations."""
    response = "📌 **مواقيت الصلاة القادمة:**\n\n"
    for city, info in CITIES.items():
        try:
            prayer_name, time_str, time_left = get_next_prayer_info(city, info)
            response += f"🔹 **{city}**: صلاة **{prayer_name}** الساعة **{time_str}** (متبقي {time_left})\n"
        except Exception as e:
            response += f"❌ تعذر جلب الوقت لـ {city}\n"
    
    await ctx.send(response)

@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user}")
    if not check_prayer_times.is_running():
        check_prayer_times.start()

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
