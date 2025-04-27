from flask import Flask, render_template_string, request, redirect
import os

app = Flask(__name__)

# Nuova struttura: nome ➔ {"url": ..., "prezzo": ...}
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
                        <th>Nome Ricerca</th>
                        <th>Prezzo Max (€)</th>
                        <th>Azioni</th>
                    </tr>
                </thead>
                <tbody>
                    {% for nome, dati in ricerche.items() %}
                    <tr>
                        <td><a href="{{ dati.url }}" target="_blank" class="link-light text-decoration-underline">{{ nome }}</a></td>
                        <td>{{ dati.prezzo }}</td>
                        <td>
                            <form action="/delete" method="post" style="display:inline;">
                                <input type="hidden" name="nome" value="{{ nome }}">
                                <button type="submit" class="btn btn-sm btn-danger">❌ Rimuovi</button>
                            </form>
                            <form action="/edit" method="get" style="display:inline;">
                                <input type="hidden" name="nome" value="{{ nome }}">
                                <button type="submit" class="btn btn-sm btn-warning">✏️ Modifica</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="col-md-4">
            <h2>➕ Aggiungi Nuova Ricerca</h2>
            <form action="/add" method="post" class="mb-3">
                <div class="mb-3">
                    <label class="form-label">Nome Ricerca</label>
                    <input type="text" name="nome" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Link Vinted</label>
                    <input type="text" name="url" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Prezzo Max (€)</label>
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
    <p class="text-muted">Made by Pendry - 2025</p>
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
    nome = request.form["nome"].strip()
    url = request.form["url"].strip()
    prezzo = float(request.form["prezzo"].strip())
    vinted_searches[nome] = {"url": url, "prezzo": prezzo}
    return redirect("/")

@app.route("/delete", methods=["POST"])
def delete_search():
    nome = request.form["nome"].strip()
    if nome in vinted_searches:
        del vinted_searches[nome]
    return redirect("/")

@app.route("/edit", methods=["GET", "POST"])
def edit_search():
    if request.method == "GET":
        nome = request.args.get("nome")
        dati = vinted_searches.get(nome, {})
        return render_template_string("""
        <html><head><title>Modifica Ricerca</title></head><body class="bg-dark text-light">
        <div class="container">
            <h2 class="mt-4">✏️ Modifica Ricerca</h2>
            <form action="/edit" method="post">
                <input type="hidden" name="old_nome" value="{{ nome }}">
                <div class="mb-3">
                    <label class="form-label">Nuovo Nome</label>
                    <input type="text" name="new_nome" class="form-control" value="{{ nome }}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Link Vinted</label>
                    <input type="text" name="url" class="form-control" value="{{ dati.url }}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Prezzo Max (€)</label>
                    <input type="number" step="0.01" name="prezzo" class="form-control" value="{{ dati.prezzo }}" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">💾 Salva Modifiche</button>
            </form>
            <a href="/" class="btn btn-secondary mt-3">🔙 Torna indietro</a>
        </div>
        </body></html>
        """, nome=nome, dati=dati)
    else:
        old_nome = request.form["old_nome"].strip()
        new_nome = request.form["new_nome"].strip()
        url = request.form["url"].strip()
        prezzo = float(request.form["prezzo"].strip())

        if old_nome in vinted_searches:
            del vinted_searches[old_nome]

        vinted_searches[new_nome] = {"url": url, "prezzo": prezzo}
        return redirect("/")

@app.route("/reset", methods=["POST"])
def reset_last_items():
    last_items.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
