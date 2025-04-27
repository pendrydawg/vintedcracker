import os
import asyncio
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import re
import json

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))  # opzionale per DM admin
VINTED_SEARCH_URLS_RAW = os.getenv("VINTED_SEARCH_URL", "")

# ⚠️ INSERISCI QUI I TUOI COOKIE VINTED
ACCESS_TOKEN_WEB = os.getenv("VINTED_ACCESS_TOKEN")
VINTED_SESSION = os.getenv("VINTED_SESSION")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Prepara il dizionario URL -> prezzo massimo
vinted_searches = {}
for entry in VINTED_SEARCH_URLS_RAW.split(","):
    if "=" in entry:
        try:
            url, price = entry.split("=")
            vinted_searches[url.strip()] = float(price.strip())
        except ValueError:
            print(f"Errore nel parsing della riga: {entry}")

last_items = set()
last_reset = datetime.now(timezone.utc)

@bot.event
async def on_ready():
    print(f"✅ Connesso come {bot.user}")
    check_vinted.start()

# /ping
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot operativo ✅")

# /stato
@bot.command()
async def stato(ctx):
    uptime = datetime.now(timezone.utc) - last_reset
    await ctx.send(
        f"✅ Bot operativo\n"
        f"🔍 Monitorando {len(vinted_searches)} ricerche Vinted\n"
        f"🕒 Online da {uptime.seconds//3600} ore e {(uptime.seconds//60)%60} minuti"
    )

# /ultimi
@bot.command()
async def ultimi(ctx):
    if not last_items:
        await ctx.send("⚠️ Nessun articolo recente trovato.")
        return

    response = "🛍️ Ultimi articoli trovati:\n"
    counter = 0
    for link in list(last_items)[-5:]:
        response += f"🔗 {link}\n"
        counter += 1
        if counter >= 5:
            break

    await ctx.send(response)

# /forzareset
@bot.command()
async def forzareset(ctx):
    last_items.clear()
    await ctx.send("♻️ Lista articoli resettata manualmente!")

# /aggiungi
@bot.command()
async def aggiungi(ctx, url: str, prezzo: float):
    vinted_searches[url.strip()] = prezzo
    await ctx.send(f"✅ Aggiunta ricerca:\n🔗 {url}\n💰 Prezzo massimo: {prezzo:.2f}€")

# /comandi
@bot.command(name="comandi")
async def comandi(ctx):
    help_text = (
        "🛠️ **Comandi disponibili:**\n\n"
        "✅ `/ping` ➔ Controlla se il bot è operativo.\n"
        "✅ `/stato` ➔ Mostra quante ricerche sono monitorate e da quanto il bot è online.\n"
        "✅ `/ultimi` ➔ Mostra gli ultimi 5 articoli trovati.\n"
        "✅ `/forzareset` ➔ Resetta manualmente la lista articoli monitorati.\n"
        "✅ `/aggiungi [link] [prezzo]` ➔ Aggiunge una nuova ricerca live.\n"
        "✅ `/test` ➔ Invia un articolo finto di prova.\n"
    )
    await ctx.send(help_text)

# /test - invia articolo finto manualmente
@bot.command()
async def test(ctx):
    channel = bot.get_channel(CHANNEL_ID)
    embed = discord.Embed(
        title="🧪 Finto Articolo Nike Shox",
        description="Prezzo: 49.99€",
        url="https://www.vinted.it/item-finto-nike-shox"
    )
    embed.set_image(url="https://cdn.vinted.net/images/it/auto/finto_nike_shox.jpg")
    await channel.send(embed=embed)
    await ctx.send("✅ Articolo finto inviato nel canale per test!")
    print("🧪 TEST manuale completato con successo.")

# 🔥 Funzione per inviare offerta automatica (-40%)
async def invia_offerta(link, prezzo_originale):
    cookies = {
        'access_token_web': ACCESS_TOKEN_WEB,
        '_vinted_fr_session': VINTED_SESSION,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {cookies['access_token_web']}",
    }

    try:
        match = re.search(r'/(\d+)-', link)
        if not match:
            print(f"⚠️ Errore: impossibile estrarre ID da {link}")
            return
        product_id = match.group(1)
        print(f"🆔 ID prodotto estratto: {product_id}")

        prezzo_offerta = round(prezzo_originale * 0.6, 2)

        payload = {
            "item_id": int(product_id),
            "price": prezzo_offerta,
            "currency": "EUR"
        }

        response = requests.post(
            'https://www.vinted.it/api/v2/offers',
            headers=headers,
            cookies=cookies,
            data=json.dumps(payload)
        )

        if response.status_code == 200:
            print(f"✅ Offerta inviata con successo per {link} a {prezzo_offerta}€")
        else:
            print(f"❌ Errore nell'invio offerta: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"⚠️ Eccezione durante invio offerta: {e}")

# 🔄 Monitoraggio Vinted ogni 2 minuti
@tasks.loop(minutes=2)
async def check_vinted():
    global last_items, last_reset, vinted_searches
    channel = bot.get_channel(CHANNEL_ID)

    if datetime.now(timezone.utc) - last_reset > timedelta(hours=12):
        last_items.clear()
        last_reset = datetime.now(timezone.utc)
        print("♻️ Reset della lista articoli monitorati.")

    headers = {"User-Agent": "Mozilla/5.0"}

    for search_url, max_price in vinted_searches.items():
        try:
            response = requests.get(search_url.strip(), headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")

            items = soup.find_all("div", class_="feed-grid__item")

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
                print(f"📦 Trovato: {title} - {price:.2f}€ -> {link}")
                await invia_offerta(link, price)

        except Exception as e:
            print(f"⚠️ Errore durante il check su {search_url}: {e}")

bot.run(TOKEN)
