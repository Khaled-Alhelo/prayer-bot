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
        "method": 5,          # Egyptian General Authority
        "tz": "Asia/Amman"
    },
    "دونا أوفاروش": {
        "lat": 46.9619, 
        "lng": 18.9355, 
        "method": 3,          # Muslim World League
        "tz": "Europe/Budapest"
    }
}

AZKAR_SABAH = (
    "☀️ **مختارات من أذكار الصباح**\n"
    "          **رددوها صباحاً**\n\n"
    "١- اللّهُـمَّ بِكَ أَصْـبَحْنا وَبِكَ أَمْسَـينا ، وَبِكَ نَحْـيا وَبِكَ نَمُـوتُ وَإِلَـيْكَ النُّـشُور.\n\n"
    "٢- أَصْبَـحْـنا عَلَى فِطْرَةِ الإسْلاَمِ، وَعَلَى كَلِمَةِ الإِخْلاَصِ، وَعَلَى دِينِ نَبِيِّنَا مُحَمَّدٍ صَلَّى اللهُ عَلَيْهِ وَسَلَّمَ، وَعَلَى مِلَّةِ أَبِينَا إبْرَاهِيمَ حَنِيفاً مُسْلِماً وَمَا كَانَ مِنَ المُشْرِكِينَ.\n\n"
    "٣- أَصْبَـحْـنا وَأَصْبَـحْ المُـلكُ للهِ رَبِّ العـالَمـين ، اللّهُـمَّ إِنِّـي أسْـأَلُـكَ خَـيْرَ هـذا الـيَوْم ، فَـتْحَهُ ، وَنَصْـرَهُ ، وَنـورَهُ وَبَـرَكَتَـهُ ، وَهُـداهُ ، وَأَعـوذُ بِـكَ مِـنْ شَـرِّ ما فـيهِ وَشَـرِّ ما بَعْـدَه.\n\n"
    "٤- رَضيـتُ بِاللهِ رَبَّـاً وَبِالإسْلامِ ديـناً وَبِمُحَـمَّدٍ صلى الله عليه وسلم نبياً (٣ مرات).\n\n"
    "٥- بسم الله الذي لا يضر مع اسمه شيئاً في الارض ولا في السماء وهو السميع العليم (٣ مرات).\n\n"
    "٦- **آية الكرسي:** اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ وَلَا يَئُودُهُ حِفْظُهُمَا وَهُوَ الْعَلِيُّ الْعَظِيمُ.\n\n"
    "٧- حسبي الله لا إله الا هو عليه توكلت وهو رب العرش العظيم (٧ مرات).\n\n"
    "✨ **دمتم في حفظ الله ورعايته**"
)

AZKAR_MASAA = (
    "🌙 **مختارات من أذكار المساء**\n"
    "          **رددوها مساءً**\n\n"
    "١- اللّهُـمَّ بِكَ أَمْسَـينا وَبِكَ أَصْـبَحْنا ، وَبِكَ نَحْـيا وَبِكَ نَمُـوتُ وَإِلَـيْكَ المَصِـير.\n\n"
    "٢- أَمْسَيْـنا عَلَى فِطْرَةِ الإسْلاَمِ، وَعَلَى كَلِمَةِ الإِخْلاَصِ، وَعَلَى دِينِ نَبِيِّنَا مُحَمَّدٍ صَلَّى اللهُ عَلَيْهِ وَسَلَّمَ، وَعَلَى مِلَّةِ أَبِينَا إبْرَاهِيمَ حَنِيفاً مُسْلِماً وَمَا كَانَ مِنَ المُشْرِكِينَ.\n\n"
    "٣- أَمْسَيْـنا وَأَمْسَـى المُـلكُ للهِ رَبِّ العـالَمـين ، اللّهُـمَّ إِنِّـي أسْـأَلُـكَ خَـيْرَ هـذهِ اللَّـيْلَةِ ، فَـتْحَها ، وَنَصْـرَها ، وَنـورَها وَبَـرَكَتَـها ، وَهُـداها ، وَأَعـوذُ بِـكَ مِـنْ شَـرِّ ما فـيها وَشَـرِّ ما بَعْـدَها.\n\n"
    "٤- رَضيـتُ بِاللهِ رَبَّـاً وَبِالإسْلامِ ديـناً وَبِمُحَـمَّدٍ صلى الله عليه وسلم نبياً (٣ مرات).\n\n"
    "٥- بسم الله الذي لا يضر مع اسمه شيئاً في الارض ولا في السماء وهو السميع العليم (٣ مرات).\n\n"
    "٦- **آية الكرسي:** اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ وَلَا يَئُودُهُ حِفْظُهُمَا وَهُوَ الْعَلِيُّ الْعَظِيمُ.\n\n"
    "٧- حسبي الله لا إله الا هو عليه توكلت وهو رب العرش العظيم (٧ مرات).\n\n"
    "✨ **دمتم في حفظ الله ورعايته**"
)

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

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

            if city == "عمان":
                for guild in bot.guilds:
                    target_channel = None
                    for channel in guild.text_channels:
                        if channel.name in ["أوقات-الصلاة", "أوقات_الصلاة", "أوقات الصلاة", "اوقات-الصلاة", "اوقات_الصلاة", "اوقات الصلاة"]:
                            target_channel = channel
                            break
                    
                    if not target_channel:
                        continue

                    # إرسال أذكار الصباح بعد الفجر بـ 5 دقائق
                    fajr_hour, fajr_minute = map(int, times["الفجر"].split(':'))
                    fajr_dt = now_local.replace(hour=fajr_hour, minute=fajr_minute, second=0, microsecond=0)
                    sabah_dt = fajr_dt + datetime.timedelta(minutes=5)
                    if current_time_str == sabah_dt.strftime("%H:%M"):
                        sabah_key = f"{today_str}_sabah_{guild.id}"
                        if sabah_key not in sent_today:
                            await target_channel.send(AZKAR_SABAH)
                            sent_today.add(sabah_key)

                    # إرسال أذكار المساء بعد العصر بـ 5 دقائق
                    asr_hour, asr_minute = map(int, times["العصر"].split(':'))
                    asr_dt = now_local.replace(hour=asr_hour, minute=asr_minute, second=0, microsecond=0)
                    masaa_dt = asr_dt + datetime.timedelta(minutes=5)
                    if current_time_str == masaa_dt.strftime("%H:%M"):
                        masaa_key = f"{today_str}_masaa_{guild.id}"
                        if masaa_key not in sent_today:
                            await target_channel.send(AZKAR_MASAA)
                            sent_today.add(masaa_key)

        except Exception as e:
            print(f"Error fetching times for {city}: {e}")

@bot.command(name="next", aliases=["الصلاة", "القادمة"])
async def next_prayer_cmd(ctx):
    response = "📌 **مواقيت الصلاة القادمة:**\n\n"
    for city, info in CITIES.items():
        try:
            prayer_name, time_str, time_left = get_next_prayer_info(city, info)
            response += f"🔹 **{city}**: صلاة **{prayer_name}** الساعة **{time_str}** (متبقي {time_left})\n"
        except Exception as e:
            response += f"❌ تعذر جلب الوقت لـ {city}\n"
    
    await ctx.send(response)

@bot.command(name="اذكار_الصباح", aliases=["أذكار_الصباح", "الصباح", "sabah"])
async def azkar_sabah_cmd(ctx):
    await ctx.send(AZKAR_SABAH)

@bot.command(name="اذكار_المساء", aliases=["أذكار_المساء", "المساء", "masaa"])
async def azkar_masaa_cmd(ctx):
    await ctx.send(AZKAR_MASAA)

@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user}")
    if not check_prayer_times.is_running():
        check_prayer_times.start()

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
