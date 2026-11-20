import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import time
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import threading
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# โหลดไฟล์ .env (แก้ปัญหามองไม่เห็น .env เพราะเป็นไฟล์ซ่อน)
load_dotenv()

# --- CONFIG ---
BASE_DIR = Path(__file__).parent
BOSSES_FILE = BASE_DIR / "bosses.json"
TIMERS_FILE = BASE_DIR / "boss_timers.json"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
CHANNEL_ID_STR = os.getenv("CHANNEL_ID", "0").strip()
try:
    NOTIFY_CHANNEL_ID = int(CHANNEL_ID_STR) if CHANNEL_ID_STR else 0
except:
    NOTIFY_CHANNEL_ID = 0

# ICT timezone แบบ timezone-aware (แก้ DeprecationWarning utcnow)
ICT = timezone(timedelta(hours=7))

print("=== Granado Espada M Boss Timer ===")
print(f"BASE_DIR: {BASE_DIR}")
print(f".env loaded: DISCORD_TOKEN={'มี' if DISCORD_TOKEN else 'ไม่มี'} | CHANNEL_ID={NOTIFY_CHANNEL_ID}")

# --- LOAD BOSSES ---
with open(BOSSES_FILE, "r", encoding="utf-8") as f:
    BOSSES = json.load(f)

BOSSES_MAP = {b["id"]: b for b in BOSSES}

def load_timers():
    if TIMERS_FILE.exists():
        try:
            with open(TIMERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    # init all to now + respawn
    now = datetime.now(ICT)
    timers = {}
    for b in BOSSES:
        next_spawn = now + timedelta(minutes=b["respawn_min"])
        timers[b["id"]] = {
            "next_spawn": next_spawn.isoformat(),
            "notified_10m": False,
            "notified_spawn": False,
            "last_kill": None
        }
    save_timers(timers)
    return timers

def save_timers(timers):
    with open(TIMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(timers, f, ensure_ascii=False, indent=2)

timers_data = load_timers()

# --- DISCORD BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=["!", "."], intents=intents)

def format_time_left(delta):
    if delta.total_seconds() <= 0:
        return "เกิดแล้ว!"
    h = int(delta.total_seconds() // 3600)
    m = int((delta.total_seconds() % 3600) // 60)
    s = int(delta.total_seconds() % 60)
    if h > 0:
        return f"{h}ชม {m}น {s}วิ"
    else:
        return f"{m}น {s}วิ"

def make_ansi_boss_block(boss):
    th = boss["name_th"]
    en = boss["name_en"]
    map_th = boss["map_th"]
    city_th = boss["city_th"]
    return f"""```ansi
\x1b[2;31m{th}\x1b[0m  \x1b[2;37m| {map_th} | {city_th}\x1b[0m
\x1b[2;33m{en}\x1b[0m  \x1b[2;37m| {boss['map_en']} | {boss['city_en']}\x1b[0m
```"""

def make_discord_message(boss, mode="spawn"):
    if mode == "10m":
        title = "⏰ บอสจะเกิดใน 10 นาที!"
        color = 0xFFAA00
    else:
        title = "🔥 บอสเกิดแล้ว!"
        color = 0xFF0000

    th_large = f"## {boss['name_th']}"
    en_small = f"-# {boss['name_en']}"

    desc = f"""{th_large}
{en_small}
**แผนที่:** {boss['map_th']} ({boss['map_en']})
**เมือง:** {boss['city_th']} ({boss['city_en']})
**รีเกิด:** ทุก {boss['respawn_min']} นาที
"""

    ansi_block = make_ansi_boss_block(boss)
    embed = discord.Embed(title=title, description=desc + "\n" + ansi_block, color=color)
    embed.set_footer(text=f"ID: {boss['id']} | {datetime.now(ICT).strftime('%H:%M:%S ICT')}")
    return embed

# Autocomplete สำหรับชื่อบอส
async def boss_autocomplete(interaction: discord.Interaction, current: str):
    current = current.lower()
    choices = []
    for b in BOSSES:
        if current in b["id"].lower() or current in b["name_th"].lower() or current in b["name_en"].lower():
            choices.append(app_commands.Choice(name=f"{b['name_th']} / {b['name_en']}", value=b["id"]))
    return choices[:25]

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} | Bosses: {len(BOSSES)} | Real TH Times")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands (/boss list/info/kill)")
    except Exception as e:
        print(f"Sync error: {e}")
    if not check_boss_loop.is_running():
        check_boss_loop.start()
        print("🔄 Boss loop started (30s)")

@tasks.loop(seconds=30)
async def check_boss_loop():
    global timers_data
    now = datetime.now(ICT)
    for boss in BOSSES:
        bid = boss["id"]
        data = timers_data.get(bid)
        if not data:
            continue
        try:
            next_spawn = datetime.fromisoformat(data["next_spawn"])
        except:
            continue
        delta = (next_spawn - now).total_seconds()

        if 590 <= delta <= 610 and not data.get("notified_10m"):
            embed = make_discord_message(boss, mode="10m")
            for guild in bot.guilds:
                channels = []
                if NOTIFY_CHANNEL_ID != 0:
                    ch = bot.get_channel(NOTIFY_CHANNEL_ID)
                    if ch:
                        channels = [ch]
                else:
                    channels = [c for c in guild.text_channels if c.permissions_for(guild.me).send_messages][:1]
                for ch in channels:
                    try:
                        await ch.send(content="@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))
                    except Exception as e:
                        print(f"Send fail {ch}: {e}")
            data["notified_10m"] = True
            save_timers(timers_data)

        if -30 <= delta <= 30 and not data.get("notified_spawn"):
            embed = make_discord_message(boss, mode="spawn")
            for guild in bot.guilds:
                channels = []
                if NOTIFY_CHANNEL_ID != 0:
                    ch = bot.get_channel(NOTIFY_CHANNEL_ID)
                    if ch:
                        channels = [ch]
                else:
                    channels = [c for c in guild.text_channels if c.permissions_for(guild.me).send_messages][:1]
                for ch in channels:
                    try:
                        await ch.send(content="@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))
                    except Exception as e:
                        print(e)
            data["notified_spawn"] = True
            save_timers(timers_data)

# === SLASH COMMAND GROUP /boss ===
boss_group = app_commands.Group(name="boss", description="คำสั่งบอส Granado Espada M")

@boss_group.command(name="list", description="ดูรายชื่อบอส 12 ตัวและเวลาเกิด")
async def boss_list_slash(interaction: discord.Interaction):
    now = datetime.now(ICT)
    embed = discord.Embed(title="📋 รายชื่อบอส 12 ตัว (Reboldoeux / Coimbra / Auch)", color=0x00FFAA)
    desc = ""
    for boss in BOSSES:
        data = timers_data.get(boss["id"])
        if data and data.get("next_spawn"):
            ns = datetime.fromisoformat(data["next_spawn"])
            left = ns - now
            left_text = format_time_left(left)
        else:
            left_text = "-"
            ns = now
        desc += f"**{boss['name_th']}** `{left_text}`\n-# {boss['name_en']} | {boss['map_th']} | เกิด {ns.strftime('%H:%M')}\n"
    embed.description = desc[:4000]
    await interaction.response.send_message(embed=embed)

@boss_group.command(name="info", description="ดูข้อมูลบอสตัวเดียวละเอียด")
@app_commands.autocomplete(boss=boss_autocomplete)
async def boss_info_slash(interaction: discord.Interaction, boss: str):
    found = BOSSES_MAP.get(boss)
    if not found:
        await interaction.response.send_message(f"❌ ไม่พบบอส: {boss}", ephemeral=True)
        return
    data = timers_data.get(found["id"])
    now = datetime.now(ICT)
    ns = datetime.fromisoformat(data["next_spawn"]) if data and data.get("next_spawn") else now
    left = ns - now
    embed = make_discord_message(found, mode="10m" if left.total_seconds() > 600 else "spawn")
    embed.add_field(name="เวลาที่เหลือ", value=format_time_left(left))
    embed.add_field(name="เกิดรอบหน้า", value=ns.strftime("%d/%m %H:%M ICT"))
    await interaction.response.send_message(embed=embed)

@boss_group.command(name="kill", description="แจ้งฆ่าบอสแล้วรีเซ็ตเวลา")
@app_commands.autocomplete(boss=boss_autocomplete)
async def boss_kill_slash(interaction: discord.Interaction, boss: str):
    global timers_data
    found = BOSSES_MAP.get(boss)
    if not found:
        # ลองหาจากชื่อ
        for b in BOSSES:
            if boss.lower() in b["name_th"].lower() or boss.lower() in b["name_en"].lower():
                found = b
                break
    if not found:
        await interaction.response.send_message(f"❌ ไม่พบบอส: {boss} ลอง /boss list", ephemeral=True)
        return

    now = datetime.now(ICT)
    next_spawn = now + timedelta(minutes=found["respawn_min"])
    timers_data[found["id"]] = {
        "next_spawn": next_spawn.isoformat(),
        "notified_10m": False,
        "notified_spawn": False,
        "last_kill": now.isoformat()
    }
    save_timers(timers_data)

    embed = discord.Embed(
        title=f"☠️ Kill บอส: {found['name_th']}",
        description=f"## {found['name_th']}\n-# {found['name_en']}\nรีเซ็ตเวลาแล้ว เกิดใหม่ใน {found['respawn_min']} นาที\n**รอบหน้า:** {next_spawn.strftime('%H:%M:%S ICT')}",
        color=0xFF0000
    )
    await interaction.response.send_message(content="@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))

bot.tree.add_command(boss_group)

# Prefix commands ยังใช้ได้
@bot.command(name="kill")
async def kill_prefix(ctx, *, boss_name: str):
    global timers_data
    found = None
    for b in BOSSES:
        if boss_name.lower() in b["id"].lower() or boss_name.lower() in b["name_th"].lower() or boss_name.lower() in b["name_en"].lower():
            found = b
            break
    if not found:
        await ctx.send(f"❌ ไม่พบบอส: {boss_name}")
        return
    now = datetime.now(ICT)
    next_spawn = now + timedelta(minutes=found["respawn_min"])
    timers_data[found["id"]] = {
        "next_spawn": next_spawn.isoformat(),
        "notified_10m": False,
        "notified_spawn": False,
        "last_kill": now.isoformat()
    }
    save_timers(timers_data)
    await ctx.send(f"✅ Kill **{found['name_th']} / {found['name_en']}** แล้ว รีเกิดใน {found['respawn_min']} นาที ( {next_spawn.strftime('%H:%M ICT')} ) @everyone", allowed_mentions=discord.AllowedMentions(everyone=True))

@bot.command(name="bosses")
async def bosses_prefix(ctx):
    now = datetime.now(ICT)
    lines = []
    for b in BOSSES:
        data = timers_data.get(b["id"])
        ns = datetime.fromisoformat(data["next_spawn"]) if data and data.get("next_spawn") else now
        left = format_time_left(ns - now)
        lines.append(f"**{b['name_th']}** ({b['name_en']}) - {b['map_th']} | {left}")
    await ctx.send("\n".join(lines)[:2000])

# --- FLASK WEB SERVER ---
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/bosses")
def api_bosses():
    now = datetime.now(ICT)
    result = []
    for b in BOSSES:
        data = timers_data.get(b["id"], {})
        ns_str = data.get("next_spawn")
        if ns_str:
            ns = datetime.fromisoformat(ns_str)
            diff = (ns - now).total_seconds()
        else:
            ns = now
            diff = 0
        result.append({
            **b,
            "next_spawn": ns_str,
            "next_spawn_human": ns.strftime("%d/%m %H:%M:%S") if ns_str else "-",
            "seconds_left": diff,
            "time_left_text": format_time_left(timedelta(seconds=diff)) if diff>0 else "เกิดแล้ว!"
        })
    return jsonify(result)

@app.route("/api/kill/<boss_id>", methods=["POST"])
def api_kill(boss_id):
    global timers_data
    if boss_id not in BOSSES_MAP:
        return jsonify({"error": "boss not found"}), 404
    boss = BOSSES_MAP[boss_id]
    now = datetime.now(ICT)
    next_spawn = now + timedelta(minutes=boss["respawn_min"])
    timers_data[boss_id] = {
        "next_spawn": next_spawn.isoformat(),
        "notified_10m": False,
        "notified_spawn": False,
        "last_kill": now.isoformat()
    }
    save_timers(timers_data)
    return jsonify({"ok": True, "next_spawn": next_spawn.isoformat()})

@app.route("/bosses.json")
def bosses_json():
    return jsonify(BOSSES)

def run_flask():
    # ใช้ waitress แทน Flask dev server (แก้ WARNING)
    try:
        from waitress import serve
        print("🌐 Web server running (PRODUCTION) on http://localhost:5000 - waitress")
        serve(app, host="0.0.0.0", port=5000)
    except ImportError:
        print("⚠️ ไม่พบ waitress ใช้ Flask dev (ติดตั้งด้วย pip install waitress)")
        app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    # เช็คว่ามี token ไหม
    if not DISCORD_TOKEN:
        print("⚠️ ยังไม่มี DISCORD_TOKEN - จะรันแค่เว็บอย่างเดียว")
        print("สร้างไฟล์ .env ใส่:")
        print("DISCORD_TOKEN=ใส่โทเคนบอท")
        print("CHANNEL_ID=ใส่ไอดีแชนแนล")
        print("")
        print("💡 ถ้ามองไม่เห็นไฟล์ .env ให้รัน setup_env.py หรือ สร้าง_ENV.bat")
        print("หรือตั้ง env ใน Windows: set DISCORD_TOKEN=xxx")
        print("")
        run_flask()
    else:
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        time.sleep(1)
        print(f"✅ Boss times: {[b['name_th']+':'+str(b['respawn_min'])+'m' for b in BOSSES]}")
        print("⏰ Timezone: ICT UTC+7 (timezone-aware - แก้ DeprecationWarning แล้ว)")
        try:
            bot.run(DISCORD_TOKEN)
        except discord.errors.LoginFailure:
            print("❌ Token ไม่ถูกต้อง ตรวจสอบ DISCORD_TOKEN ใน .env")
            input("กด Enter เพื่อปิด...")
