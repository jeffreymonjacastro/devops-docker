from flask import Flask, jsonify, render_template_string, request
import os
from psycopg_pool import ConnectionPool


def db_connect():
    url = (
        f"host={os.environ.get('DB_HOST')} "
        f"dbname={os.environ.get('DB_DATABASE')} "
        f"user={os.environ.get('DB_USER')} "
        f"password={os.environ.get('DB_PASSWORD')}"
    )
    pool = ConnectionPool(url)
    pool.wait()
    return pool


pool = db_connect()

app = Flask(__name__)


@app.route("/")
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask Docker App</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
            h1 { color: #2196F3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Flask + PostgreSQL</h1>
            <p>Stack Flask + PostgreSQL corriendo con Docker Compose.</p>
            <ul>
                <li><a href="/api/health">Estado de la API</a></li>
                <li><a href="/items">Listar items</a></li>
            </ul>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "version": os.environ.get("APP_VERSION")})


def save_item(priority, task):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO item (priority, task) VALUES (%s, %s)", (priority, task)
            )
            conn.commit()


def get_items():
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT item_id, priority, task FROM item")
            return [{"id": r[0], "priority": r[1], "task": r[2]} for r in cur]


@app.route("/items", methods=["GET", "POST"])
def items():
    if request.method == "POST":
        body = request.get_json()
        save_item(body["priority"], body["task"])
        return {"message": "item saved!"}, 201
    return get_items(), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
