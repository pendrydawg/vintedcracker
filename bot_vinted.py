import os
import asyncio
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta, timezone

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

last_items = set()
last_reset = datetime.now(timezone.utc)

@bot.event
async def on_ready():
    print(f"✅ Bot connesso come {bot.user}")
    check_vinted.start()

@tasks.loop(minutes=2)
async def check_vinted():
    global last_items, last_reset
    channel = bot.get_channel(CHANNEL_ID)

    if datetime.now(timezone.utc) - last_reset > timedelta(hours=12):
        last_items.clear()
        last_reset = datetime.now(timezone.utc)
        print("♻️ Reset lista articoli monitorati.")

    # Carica le ricerche dal file JSON
    try:
        with open("searches.json", "r") as f:
            searches = json.load(f)
        print(f"✅ searches.json caricato, {len(searches)} ricerche trovate.")
    except Exception as e:
        print(f"❌ Errore caricando searches.json: {e}")
        return

    headers = {"User-Agent": "Mozilla/5.0"}

    for search in searches:
        search_url = search["url"]
        max_price = float(search["price"])
        print(f"🔍 Controllando URL: {search_url} (max {max_price}€)")

        try:
            response = requests.get(search_url.strip(), headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("div", class_="feed-grid__item")
            print(f"🔎 Trovati {len(items)} articoli sulla pagina.")

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
                    title = title_tag.text.strip() if title_tag else "Articolo Vinted"

                    try:
                        price = float(price_text.split()[0])
                    except (ValueError, IndexError):
                        continue

                    if price <= max_price and link not in last_items:
                        new_items.append((link, price, title, image_url))
                        last_items.add(link)

            for link, price, title, image_url in new_items:
                embed = discord.Embed(title=title, description=f"Prezzo: {price:.2f}€", url=link)
                embed.set_image(url=image_url)
                await channel.send(embed=embed)
                print(f"✅ Inviato su Discord: {title} - {price:.2f}€")

        except Exception as e:
            print(f"❌ Errore durante il check su {search_url}: {e}")

bot.run(TOKEN)
