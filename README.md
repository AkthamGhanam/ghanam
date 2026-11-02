# GHANAM

Tienda online de **Maison GHANAM**: página de inicio, catálogo con filtros y búsqueda, y carrito de compras. El frontend es HTML + Tailwind + JavaScript, y el backend es una API en **Flask** que se despliega en **Vercel**.

## Estructura

```
├── app.py                      # Punto de entrada Flask (Vercel lo detecta solo)
├── carro_compras/
│   ├── routes/rutas.py         # Rutas de la API (catálogo y carrito)
│   └── services/
│       ├── carrito.py          # Lógica del carrito (Producto, CarritoCompra)
│       └── catalogo.py         # Catálogo de productos (EDITAR AQUÍ)
├── templates/index.html        # Página principal
├── public/                     # Archivos estáticos (Vercel los sirve desde su CDN)
│   ├── style/styles.css
│   ├── js/script.js            # Buscador a pantalla completa (móvil)
│   ├── js/tienda.js            # Catálogo, búsqueda y carrito
│   └── resource/GHANAM.png
├── tests/test_app.py           # Pruebas de la API
├── requirements.txt
└── vercel.json                 # Fuerza el framework Flask en Vercel
```

## Ejecutar en local

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abre http://127.0.0.1:5000

> El entorno virtual (`.venv/`) **no** se sube al repositorio; cada persona lo crea en su máquina con los comandos de arriba.

## Pruebas

```bash
python -m unittest
```

## API

Todas las rutas responden JSON. El carrito de cada visitante se guarda en una cookie de sesión firmada, así que cada persona tiene su propio carrito y este sobrevive a recargas (7 días).

| Método | Ruta | Body (JSON) | Descripción |
|---|---|---|---|
| GET | `/api/catalogo` | — | Productos y categorías. Filtros opcionales: `?categoria=calidos` y `?q=texto` |
| GET | `/api/cart/show` | — | Contenido del carrito, total y unidades |
| POST | `/api/cart/income` | `{"id_producto": 1, "cantidad": 1}` | Añade un producto (suma si ya estaba) |
| PUT | `/api/cart/update` | `{"id_producto": 1, "cantidad": 3}` | Cambia la cantidad (`0` lo quita) |
| PUT | `/api/cart/clear_item` | `{"id_producto": 1}` | Quita un producto |
| DELETE | `/api/cart/clear` | — | Vacía el carrito |

El precio, el nombre y el stock **siempre salen del catálogo del servidor**; el navegador solo envía el id y la cantidad. Los errores llegan como `{"error": "mensaje"}` con su código HTTP (400 datos inválidos, 404 no existe, 409 sin stock suficiente).

## Catálogo

Los productos de `carro_compras/services/catalogo.py` son **de ejemplo**. Cambia nombres, descripciones, precios (en pesos colombianos) y stock por los reales. Las categorías válidas son `calidos`, `frios`, `relojes` y `premium`.

## Desplegar en Vercel

1. Entra a https://vercel.com/new e importa el repositorio `AkthamGhanam/ghanam`.
2. Deja la configuración por defecto: `vercel.json` ya indica que es una app **Flask**, sin comando de build ni carpeta de salida.
3. En **Settings → Environment Variables** crea `SECRET_KEY` con un valor largo y aleatorio. Puedes generarlo con:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Sin esta variable la tienda funciona, pero con una clave de desarrollo que no es segura.
4. Pulsa **Deploy**. Cada `git push` a `main` vuelve a desplegar producción, y cada rama o PR obtiene su propia URL de prueba.

### GitHub Pages

Este repositorio estaba publicado con GitHub Pages, que solo sirve archivos estáticos y **no puede ejecutar Flask** (el carrito no funcionaría ahí). Una vez que la tienda esté en Vercel, desactiva Pages en **Settings → Pages** del repositorio.
