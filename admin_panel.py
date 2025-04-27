from flask import Flask, render_template, request, redirect
import os
import json

app = Flask(__name__)

DB_FILE = "searches.json"

# Assicurati che il file esista
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump([], f)

@app.route("/", methods=["GET", "POST"])
def index():
    try:
        if request.method == "POST":
            url = request.form.get("url", "").strip()
            name = request.form.get("name", "").strip()
            price = request.form.get("price", "").strip()

            if not url or not name or not price:
                return "Tutti i campi sono obbligatori.", 400

            with open(DB_FILE, "r+") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []

                data.append({"url": url, "name": name, "price": float(price)})
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=4)

            return redirect("/")

        with open(DB_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
        return render_template("index.html", searches=data)

    except Exception as e:
        return f"Internal Error: {str(e)}", 500

@app.route("/delete/<int:index>")
def delete(index):
    try:
        with open(DB_FILE, "r+") as f:
            data = json.load(f)
            if 0 <= index < len(data):
                data.pop(index)
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=4)
        return redirect("/")
    except Exception as e:
        return f"Internal Error: {str(e)}", 500

@app.route("/edit/<int:index>", methods=["GET", "POST"])
def edit(index):
    try:
        with open(DB_FILE, "r+") as f:
            data = json.load(f)
            if request.method == "POST":
                data[index]["url"] = request.form["url"]
                data[index]["name"] = request.form["name"]
                data[index]["price"] = float(request.form["price"])
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=4)
                return redirect("/")
            item = data[index]
        return render_template("edit.html", item=item, index=index)
    except Exception as e:
        return f"Internal Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
