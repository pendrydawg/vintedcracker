import os
import asyncio
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import json

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

last_items = set()
last_reset = datetime.now(timezone.utc)

DATA_FILE = "searches.json"

# Funzione per caricare le ricerche dal file
def load_searches():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@bot.event
async def on_ready():
    print(f"Connesso come {bot.user}")
    check_vinted.start()

@tasks.loop(minutes=2)
async def check_vinted():
    global last_items, last_reset
    channel = bot.get_channel(CHANNEL_ID)

    if datetime.now(timezone.utc) - last_reset > timedelta(hours=12):
        last_items.clear()
        last_reset = datetime.now(timezone.utc)
        print("♻️ Reset della lista articoli monitorati.")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    vinted_searches = load_searches()

    for nome, dati in vinted_searches.items():
        search_url = dati["url"]
        max_price = dati["prezzo"]
        try:
            response = requests.get(search_url.strip(), headers=headers)
            if response.status_code != 200:
                print(f"❗ Errore HTTP {response.status_code} su {search_url}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            items = soup.find_all("div", class_="feed-grid__item")

            print(f"🔍 Trovati {len(items)} articoli per {nome}")

            new_items = []
            for item in items:
                link_tag = item.find("a", href=True)
                price_tag = item.find("div", class_="item-box__title")
                img_tag = item.find("img")
                title_tag = item.find("div", class_="item-box__brand-name")

                if link_tag and price_tag and img_tag:
                    link = "https://www.vinted.it" + link_tag['href']
                    price_text = price_tag.text.strip().replace("\u20ac", "").replace(",", ".")
                    image_url = img_tag.get("src")
                    title = title_tag.text.strip() if title_tag else nome

                    try:
                        price = float(price_text.split()[0])
                    except (ValueError, IndexError):
                        print(f"❗ Errore parsing prezzo per {link}")
                        continue

                    print(f"➔ Articolo trovato: {title} | Prezzo: {price:.2f}€")

                    if price <= max_price and link not in last_items:
                        new_items.append((link, price, title, image_url))
                        last_items.add(link)

            for link, price, title, image_url in new_items:
                embed = discord.Embed(title=title, description=f"Prezzo: {price:.2f}€", url=link)
                embed.set_image(url=image_url)
                await channel.send(embed=embed)
                print(f"✅ Inviato articolo: {title} ({price:.2f}€)")

        except Exception as e:
            print(f"❗ Errore durante il check su {search_url}: {e}")

bot.run(TOKEN)
