"""Punto de entrada de la tienda GHANAM (Flask).

Vercel detecta este archivo automáticamente y usa la variable `app`.
En local: `python app.py` y abre http://127.0.0.1:5000
"""

import os
from datetime import timedelta

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException, InternalServerError

from carro_compras.routes.rutas import carrito_compras, catalogo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Solo para desarrollo. En Vercel define la variable de entorno SECRET_KEY.
CLAVE_DESARROLLO = "ghanam-solo-para-desarrollo"


def create_app(config=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        # En Vercel la carpeta public/ la sirve directamente su CDN; esto es
        # para que los mismos archivos funcionen al ejecutar en local.
        static_folder=os.path.join(BASE_DIR, "public"),
        static_url_path="",
    )
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", CLAVE_DESARROLLO),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # Vercel define VERCEL=1: ahí todo va por HTTPS.
        SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")),
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    )
    if config:
        app.config.update(config)

    if os.environ.get("VERCEL") and app.config["SECRET_KEY"] == CLAVE_DESARROLLO:
        app.logger.warning(
            "SECRET_KEY no está configurada en Vercel: usa una clave propia "
            "en Settings > Environment Variables."
        )

    app.json.ensure_ascii = False  # Respuestas JSON con tildes y ñ legibles.
    app.json.sort_keys = False  # Conserva el orden de los campos.

    # La API va bajo /api: en Vercel, los errores (404, 500) de rutas fuera de
    # /api se reemplazan por su página de error HTML, y el carrito necesita
    # que sus errores lleguen como JSON.
    app.register_blueprint(catalogo, url_prefix="/api")
    app.register_blueprint(carrito_compras, url_prefix="/api/cart")

    @app.get("/")
    def inicio():
        return render_template("index.html")

    # Errores de la API siempre en JSON (rutas o métodos que no existen, fallos).
    @app.errorhandler(HTTPException)
    def error_http(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": error.description}), error.code
        return error

    @app.errorhandler(Exception)
    def error_interno(error):
        app.logger.exception("Error no controlado")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Error interno del servidor."}), 500
        return InternalServerError()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
