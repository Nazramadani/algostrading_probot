from flask import Flask, render_template_string
from threading import Thread
from shared_state import bot_data

app = Flask(__name__)

# Ky është kodi HTML për pamjen e Dashboard-it
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ProBot Live Monitor</title>
    <!-- Kjo bën që faqja të bëjë Refresh vetë çdo 5 sekonda -->
    <meta http-equiv="refresh" content="5">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #ffffff; padding: 20px; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 10px; max-width: 400px; margin: auto; border-left: 5px solid #00ff88; }
        .row { padding: 10px 0; border-bottom: 1px solid #333; display: flex; justify-content: space-between; }
        .row:last-child { border-bottom: none; }
        .val { color: #00ff88; font-weight: bold; }
        h2 { text-align: center; color: #00ff88; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📊 AlgoBot Dashboard</h2>
        <div class="row"><span>Statusi:</span> <span class="val">{{ data.status }}</span></div>
        <div class="row"><span>Koha e Skanimit:</span> <span class="val">{{ data.last_scan_time }}</span></div>
        <div class="row"><span>Çifti:</span> <span class="val">{{ data.current_pair }}</span></div>
        <div class="row"><span>Struktura:</span> <span class="val">{{ data.market_structure }}</span></div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    # Kjo dërgon të dhënat live nga bot_data direkt te faqja HTML
    return render_template_string(HTML_TEMPLATE, data=bot_data)

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
