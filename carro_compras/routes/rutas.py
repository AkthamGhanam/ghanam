# Rutas del catálogo y del carrito de compras.
from flask import Blueprint, jsonify, request, session

from carro_compras.services.carrito import CarritoCompra, ErrorCarrito
from carro_compras.services.catalogo import (
    CATEGORIAS,
    buscar_por_nombre,
    listar_productos,
    obtener_producto,
)

# Uso de Blueprints para armar la modularidad.
carrito_compras = Blueprint("compras", __name__)
catalogo = Blueprint("catalogo", __name__)

# Clave de la sesión (cookie firmada) donde vive el carrito de cada visitante.
CLAVE_SESION = "carrito"


def _cargar_carrito():
    return CarritoCompra(obtener_producto, session.get(CLAVE_SESION))


def _guardar_carrito(carrito):
    session.permanent = True
    session[CLAVE_SESION] = carrito.para_sesion()


def _respuesta(carrito, mensaje=None, status=200):
    datos = carrito.show_item()
    if mensaje:
        datos["mensaje"] = mensaje
    return jsonify(datos), status


def _datos_json():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ErrorCarrito("Envía los datos en formato JSON.")
    return datos


def _id_producto(datos):
    """Acepta 'id_producto' o, por compatibilidad, el 'nombre' del producto."""
    if datos.get("id_producto") is not None:
        return datos["id_producto"]
    if datos.get("nombre"):
        producto = buscar_por_nombre(datos["nombre"])
        if producto is None:
            raise ErrorCarrito("El producto no existe en el catálogo.", 404)
        return producto.id_producto
    raise ErrorCarrito("Falta el campo 'id_producto'.")


@carrito_compras.errorhandler(ErrorCarrito)
def _error_carrito(error):
    return jsonify({"error": error.mensaje}), error.status


# ---------------------------------------------------------------- Catálogo

@catalogo.get("/catalogo")
def obtener_catalogo():
    categoria = request.args.get("categoria") or None
    if categoria and categoria not in CATEGORIAS:
        return jsonify({"error": "Categoría no válida."}), 400
    productos = listar_productos(categoria, request.args.get("q"))
    return jsonify({
        # Lista (y no diccionario) para conservar el orden de las categorías.
        "categorias": [{"clave": clave, "nombre": nombre} for clave, nombre in CATEGORIAS.items()],
        "productos": [producto.to_dict() for producto in productos],
    })


# ----------------------------------------------------------------- Carrito

# Muestra de los productos del carrito.
@carrito_compras.get("/show")
def obtener_carrito():
    carrito = _cargar_carrito()
    # Se vuelve a guardar por si la limpieza quitó productos inválidos.
    _guardar_carrito(carrito)
    return _respuesta(carrito)


# Ingreso de productos al carrito. Body: {"id_producto": 1, "cantidad": 1}
@carrito_compras.post("/income")
def subir_productos():
    datos = _datos_json()
    carrito = _cargar_carrito()
    producto = carrito.add_items(_id_producto(datos), datos.get("cantidad", 1))
    _guardar_carrito(carrito)
    return _respuesta(carrito, f"{producto.nombre} añadido al carrito.")


# Cambio de cantidad. Body: {"id_producto": 1, "cantidad": 3} (0 lo elimina)
@carrito_compras.put("/update")
def actualizar_producto():
    datos = _datos_json()
    if "cantidad" not in datos:
        raise ErrorCarrito("Falta el campo 'cantidad'.")
    carrito = _cargar_carrito()
    producto = carrito.update_item(_id_producto(datos), datos["cantidad"])
    _guardar_carrito(carrito)
    return _respuesta(carrito, f"Cantidad de {producto.nombre} actualizada.")


# Eliminación de un producto. Body: {"id_producto": 1}
@carrito_compras.put("/clear_item")
def eliminar_producto_carrito():
    datos = _datos_json()
    carrito = _cargar_carrito()
    producto = carrito.remove_item(_id_producto(datos))
    _guardar_carrito(carrito)
    return _respuesta(carrito, f"{producto.nombre} eliminado del carrito.")


# Eliminación de todos los productos del carrito.
@carrito_compras.delete("/clear")
def eliminar_todo_el_carrito():
    carrito = _cargar_carrito()
    carrito.clear_cart()
    _guardar_carrito(carrito)
    return _respuesta(carrito, "Carrito vacío.")
