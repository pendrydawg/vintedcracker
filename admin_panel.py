from flask import Flask, render_template_string, request, redirect
import os

app = Flask(__name__)

# Uso globale di vinted_searches e last_items (stesse variabili del bot)
vinted_searches = {}
last_items = set()

@app.route("/")
def home():
    return render_template_string("""
    <h1>🛠️ Pannello Admin VintedBot</h1>
    <h2>🔍 Ricerche Monitorate:</h2>
    <ul>
    {% for url, prezzo in ricerche.items() %}
        <li>{{ url }} ➔ {{ prezzo }}€
            <form action="/delete" method="post" style="display:inline;">
                <input type="hidden" name="url" value="{{ url }}">
                <button type="submit">❌ Rimuovi</button>
            </form>
        </li>
    {% endfor %}
    </ul>
    <h3>➕ Aggiungi nuova ricerca:</h3>
    <form action="/add" method="post">
        Link Vinted: <input type="text" name="url" size="80" required><br>
        Prezzo Massimo: <input type="number" step="0.01" name="prezzo" required><br>
        <button type="submit">✅ Aggiungi</button>
    </form>
    <br>
    <form action="/reset" method="post">
        <button type="submit">♻️ Resetta lista articoli monitorati</button>
    </form>
    """, ricerche=vinted_searches)

@app.route("/add", methods=["POST"])
def add_search():
    url = request.form["url"].strip()
    prezzo = float(request.form["prezzo"].strip())
    vinted_searches[url] = prezzo
    return redirect("/")

@app.route("/delete", methods=["POST"])
def delete_search():
    url = request.form["url"].strip()
    if url in vinted_searches:
        del vinted_searches[url]
    return redirect("/")

@app.route("/reset", methods=["POST"])
def reset_last_items():
    last_items.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
