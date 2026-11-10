from flask import Flask, request, redirect, render_template_string, Response, send_file
import qrcode
import qrcode.image.svg
import io
import json

app = Flask(__name__)

DB_FILE = 'routes.json'

def load_routes():
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "aw66025": "https://awtools.pl/manuals/aw66025.pdf"
        }

def save_routes(routes):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(routes, f, indent=4, ensure_ascii=False)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generator Kodów QR - AW-TOOLS</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 30px auto; padding: 0 20px; background: #f8f9fa; color: #333; }
        .header-bar { display: flex; align-items: center; justify-content: space-between; background: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 25px; }
        .header-bar img { height: 50px; width: auto; object-fit: contain; }
        .header-title { text-align: right; }
        .header-title h1 { margin: 0; font-size: 20px; color: #1a1a1a; }
        .header-title p { margin: 3px 0 0 0; font-size: 12px; color: #666; }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 25px; }
        label { font-weight: 600; display: block; margin-top: 15px; margin-bottom: 5px; }
        input, select, textarea, button { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
        input:focus, select:focus, textarea:focus { border-color: #e31e24; outline: none; }
        button { background: #e31e24; color: white; border: none; font-weight: bold; margin-top: 20px; cursor: pointer; transition: background 0.2s; border-radius: 6px; }
        button:hover { background: #c1171c; }
        .qr-result { text-align: center; margin-top: 25px; padding-top: 25px; border-top: 2px dashed #eee; }
        .qr-result svg { max-width: 220px; height: auto; border: 1px solid #ddd; padding: 10px; background: white; }
        .btn-download { display: inline-block; padding: 10px 18px; margin: 8px 4px; border-radius: 6px; font-weight: bold; text-decoration: none; color: white; font-size: 14px; }
        .btn-svg { background: #28a745; }
        .btn-svg:hover { background: #218838; }
        .btn-png { background: #17a2b8; }
        .btn-png:hover { background: #138496; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #fafafa; font-size: 13px; text-transform: uppercase; color: #666; }
        code { background: #eef; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
        .field-group { margin-bottom: 15px; }
    </style>
    <script>
        function toggleInputFields() {
            var qrType = document.getElementById("type").value;
            var urlGroup = document.getElementById("url-group");
            var textGroup = document.getElementById("text-group");
            
            if (qrType === "text") {
                urlGroup.style.display = "none";
                textGroup.style.display = "block";
                document.getElementById("url").required = false;
                document.getElementById("text_content").required = true;
            } else {
                urlGroup.style.display = "block";
                textGroup.style.display = "none";
                document.getElementById("url").required = true;
                document.getElementById("text_content").required = false;
            }
        }
        window.onload = toggleInputFields;
    </script>
</head>
<body>
    <div class="header-bar">
        <img src="/static/logo.jpg" alt="AW-NARZĘDZIA Logo" onerror="this.onerror=null; this.src='https://awtools.pl/wp-content/uploads/2021/04/logo-awtools.png';">
        <div class="header-title">
            <h1>Generator Kodów QR</h1>
            <p>AW-TOOLS Compliance & Packaging</p>
        </div>
    </div>

    <div class="card">
        <p style="color: #666; margin-top: 0;">Twórz bezpłatne kody QR na opakowania (URL, instrukcje PDF, specyfikacje tekstowe).</p>
        
        <form method="POST" action="/generate">
            <div class="field-group">
                <label for="type">Typ kodu QR:</label>
                <select name="type" id="type" onchange="toggleInputFields()">
                    <option value="dynamic">Dynamiczny URL (Zalecany na pudełka - zmiana PDF bez re-druku)</option>
                    <option value="static">Statyczny URL (Stały link do strony/PDF)</option>
                    <option value="text">Zwykły Tekst (Specyfikacja, numer partii, opis)</option>
                </select>
            </div>

            <div class="field-group" id="url-group">
                <label for="url">Docelowy adres URL (np. link do pliku PDF):</label>
                <input type="url" name="url" id="url" placeholder="https://awtools.pl/manuals/aw66025.pdf">
            </div>

            <div class="field-group" id="text-group" style="display: none;">
                <label for="text_content">Dowolny tekst do zakodowania w QR:</label>
                <textarea name="text_content" id="text_content" rows="4" placeholder="Wpisz specyfikację, numer serii, instrukcję skróconą itp..."></textarea>
            </div>

            <div class="field-group" id="alias-group">
                <label for="alias">Nazwa pliku / Kod artykułu (np. <code>aw66025</code>):</label>
                <input type="text" name="alias" id="alias" placeholder="np. aw66025 lub zostaw puste">
            </div>

            <button type="submit">Generuj Kod QR</button>
        </form>

        {% if qr_svg %}
        <div class="qr-result">
            <h3>Wygenerowany kod QR</h3>
            <div>{{ qr_svg | safe }}</div>
            
            <div style="margin-top: 20px;">
                <a href="/download/svg?data={{ encoded_data | urlencode }}&filename={{ alias_name }}" class="btn-download btn-svg">Pobierz Wektorowy SVG (do druku)</a>
                <a href="/download/png?data={{ encoded_data | urlencode }}&filename={{ alias_name }}" class="btn-download btn-png">Pobierz Podgląd PNG</a>
            </div>

            <p style="margin-top: 15px;">
                <strong>Treść zakodowana w QR:</strong><br>
                <code style="word-break: break-all;">{{ encoded_data }}</code>
            </p>
        </div>
        {% endif %}
    </div>

    <div class="card">
        <h2>Aktywne Przekierowania Dynamiczne</h2>
        {% if routes %}
        <table>
            <thead>
                <tr>
                    <th>Adres QR (z druku)</th>
                    <th>Docelowy PDF / URL</th>
                    <th>Pobierz QR</th>
                </tr>
            </thead>
            <tbody>
                {% for code, target in routes.items() %}
                <tr>
                    <td><code>/qr/{{ code }}</code></td>
                    <td style="max-width: 250px; word-break: break-all;">{{ target }}</td>
                    <td>
                        <a href="/download/svg?data={{ request.host_url.rstrip('/') }}/qr/{{ code }}&filename={{ code }}" style="color: #28a745; font-weight: bold; margin-right: 8px;">SVG</a>
                        <a href="/download/png?data={{ request.host_url.rstrip('/') }}/qr/{{ code }}&filename={{ code }}" style="color: #17a2b8; font-weight: bold;">PNG</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    routes = load_routes()
    return render_template_string(HTML_TEMPLATE, routes=routes)

@app.route('/generate', methods=['POST'])
def generate():
    routes = load_routes()
    qr_type = request.form.get('type')
    alias = request.form.get('alias', '').strip()

    if qr_type == 'text':
        encoded_data = request.form.get('text_content', '').strip()
        alias_name = alias if alias else "qr_text"
    elif qr_type == 'static':
        encoded_data = request.form.get('url', '').strip()
        alias_name = alias if alias else "qr_static"
    else:  # dynamic
        target_url = request.form.get('url', '').strip()
        short_code = alias if alias else f"prod-{len(routes) + 1}"
        routes[short_code] = target_url
        save_routes(routes)
        
        host_url = request.host_url.rstrip('/')
        encoded_data = f"{host_url}/qr/{short_code}"
        alias_name = short_code

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(encoded_data)
    qr.make(fit=True)
    img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    stream = io.BytesIO()
    img.save(stream)
    svg_code = stream.getvalue().decode('utf-8')

    return render_template_string(
        HTML_TEMPLATE, 
        qr_svg=svg_code, 
        encoded_data=encoded_data, 
        alias_name=alias_name,
        routes=routes
    )

@app.route('/download/svg')
def download_svg():
    data = request.args.get('data')
    filename = request.args.get('filename', 'qr_code')
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    
    stream = io.BytesIO()
    img.save(stream)
    stream.seek(0)
    
    return Response(
        stream.getvalue(),
        mimetype="image/svg+xml",
        headers={"Content-disposition": f"attachment; filename=QR_{filename}.svg"}
    )

@app.route('/download/png')
def download_png():
    data = request.args.get('data')
    filename = request.args.get('filename', 'qr_code')
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    stream = io.BytesIO()
    img.save(stream, format="PNG")
    stream.seek(0)
    
    return send_file(
        stream,
        mimetype="image/png",
        as_attachment=True,
        download_name=f"QR_{filename}.png"
    )

@app.route('/qr/<short_code>')
def redirect_short_code(short_code):
    routes = load_routes()
    target = routes.get(short_code)
    if target:
        return redirect(target, code=302)
    return "<h3>Błąd 404: Kod QR nie istnieje.</h3>", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
