from flask import Flask, render_template_string, request, redirect
import os

app = Flask(__name__)

# Variabili globali (le stesse che usiamo nel bot)
vinted_searches = {}
last_items = set()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VintedCracker Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark text-light">

<nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">VintedCracker Admin 🛠️</a>
  </div>
</nav>

<div class="container">
    <div class="row">
        <div class="col-md-8">
            <h2>🔍 Ricerche Monitorate:</h2>
            <table class="table table-dark table-hover table-striped">
                <thead>
                    <tr>
                        <th>Link Ricerca</th>
                        <th>Prezzo Massimo (€)</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% for url, prezzo in ricerche.items() %}
                    <tr>
                        <td style="word-break:break-all;">{{ url }}</td>
                        <td>{{ prezzo }}</td>
                        <td>
                            <form action="/delete" method="post" style="display:inline;">
                                <input type="hidden" name="url" value="{{ url }}">
                                <button type="submit" class="btn btn-sm btn-danger">❌ Rimuovi</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="col-md-4">
            <h2>➕ Aggiungi Ricerca</h2>
            <form action="/add" method="post" class="mb-3">
                <div class="mb-3">
                    <label class="form-label">Link Vinted</label>
                    <input type="text" name="url" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Prezzo Massimo (€)</label>
                    <input type="number" step="0.01" name="prezzo" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-success w-100">✅ Aggiungi</button>
            </form>

            <h2>♻️ Resetta Articoli</h2>
            <form action="/reset" method="post">
                <button type="submit" class="btn btn-warning w-100">♻️ Resetta Lista</button>
            </form>
        </div>
    </div>
</div>

<footer class="text-center mt-4 mb-2">
    <p class="text-muted">Made by the GOAT 🐐 - {{ year }}</p>
</footer>

</body>
</html>
"""

from datetime import datetime

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE, ricerche=vinted_searches, year=datetime.now().year)

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
