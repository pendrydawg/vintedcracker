import os
import asyncio
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))  # opzionale: ID tuo Discord per DM
VINTED_SEARCH_URLS_RAW = os.getenv("VINTED_SEARCH_URL", "")

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

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot operativo ✅")

# 🛰️ Comando /stato
@bot.command()
async def stato(ctx):
    uptime = datetime.now(timezone.utc) - last_reset
    await ctx.send(
        f"✅ Bot operativo\n"
        f"🔍 Monitorando {len(vinted_searches)} ricerche Vinted\n"
        f"🕒 Online da {uptime.seconds//3600} ore e {(uptime.seconds//60)%60} minuti"
    )

# 🛒 Comando /ultimi
@bot.command()
async def ultimi(ctx):
    if not last_items:
        await ctx.send("⚠️ Nessun articolo recente trovato.")
        return

    response = "🛍️ Ultimi articoli trovati:\n"
    counter = 0
    for link in list(last_items)[-5:]:  # ultimi 5 articoli
        response += f"🔗 {link}\n"
        counter += 1
        if counter >= 5:
            break

    await ctx.send(response)

# ♻️ Comando /forza-reset
@bot.command()
async def forzareset(ctx):
    last_items.clear()
    await ctx.send("♻️ Lista articoli resettata manualmente!")

# ➕ Comando /aggiungi url prezzo
@bot.command()
async def aggiungi(ctx, url: str, prezzo: float):
    vinted_searches[url.strip()] = prezzo
    await ctx.send(f"✅ Aggiunta ricerca:\n🔗 {url}\n💰 Prezzo massimo: {prezzo:.2f}€")

# 🆘 Comando /comandi
@bot.command(name="comandi")
async def comandi(ctx):
    help_text = (
        "🛠️ **Comandi disponibili:**\n\n"
        "✅ `/ping` ➔ Controlla se il bot è operativo.\n"
        "✅ `/stato` ➔ Mostra quante ricerche sono monitorate e da quanto il bot è online.\n"
        "✅ `/ultimi` ➔ Mostra gli ultimi 5 articoli trovati.\n"
        "✅ `/forzareset` ➔ Resetta manualmente la lista articoli monitorati.\n"
        "✅ `/aggiungi [link] [prezzo]` ➔ Aggiunge una nuova ricerca da monitorare live.\n\n"
        "**Esempio di `/aggiungi`:**\n"
        "`/aggiungi https://www.vinted.it/catalog?search_text=nike+shox&size_id[]=206&size_id[]=207 50`\n\n"
        "**Note Importanti:**\n"
        "- Il link deve essere corretto di Vinted.\n"
        "- Prezzo massimo solo numero (senza € o testo).\n"
        "- Separa il link e il prezzo con uno spazio.\n"
    )
    await ctx.send(help_text)

@tasks.loop(minutes=2)
async def check_vinted():
    global last_items, last_reset, vinted_searches
    channel = bot.get_channel(CHANNEL_ID)

    if datetime.now(timezone.utc) - last_reset > timedelta(hours=12):
        last_items.clear()
        last_reset = datetime.now(timezone.utc)
        print("♻️ Reset della lista articoli monitorati.")

    headers = {"User-Agent": "Mozilla/5.0"}

    # 🧪 TEST: Invia un articolo finto
    if os.getenv("TEST_MODE", "false").lower() == "true":
        channel = bot.get_channel(CHANNEL_ID)
        embed = discord.Embed(
            title="Finto Articolo Nike Shox",
            description="Prezzo: 49.99€",
            url="https://www.vinted.it/item-finto-nike-shox"
        )
        embed.set_image(url="https://cdn.vinted.net/images/it/auto/finto_nike_shox.jpg")
        await channel.send(embed=embed)
        print("🧪 Test articolo finto inviato.")
        return

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

                if ADMIN_USER_ID:
                    user = await bot.fetch_user(ADMIN_USER_ID)
                    if user:
                        await user.send(f"📢 Nuovo articolo trovato: [{title}]({link}) a {price:.2f}€")

        except Exception as e:
            print(f"⚠️ Errore durante il check su {search_url}: {e}")

bot.run(TOKEN)
