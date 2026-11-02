"""Catálogo de productos de GHANAM.

IMPORTANTE: estos productos son de EJEMPLO para que la tienda funcione de
punta a punta. Reemplaza nombres, descripciones, precios (en pesos
colombianos) y stock por los reales. Las categorías deben ser una de las
claves de CATEGORIAS.
"""

import unicodedata

from carro_compras.services.carrito import Producto

CATEGORIAS = {
    "calidos": "Cálidos",
    "frios": "Fríos",
    "relojes": "Relojes",
    "premium": "Premium",
}

PRODUCTOS = [
    Producto(1, "Cálido N.º 1", 189000, 12, "calidos",
             "Tonos ámbar y dorados para quienes llegan con presencia."),
    Producto(2, "Cálido N.º 2", 219000, 8, "calidos",
             "Una pieza intensa y envolvente, pensada para la noche."),
    Producto(3, "Frío N.º 1", 179000, 15, "frios",
             "Líneas limpias y tonos plata. Minimalismo sin esfuerzo."),
    Producto(4, "Frío N.º 2", 199000, 10, "frios",
             "Fresco y preciso, para el día a día de alto nivel."),
    Producto(5, "Reloj Automático Zafiro", 1250000, 5, "relojes",
             "Cristal de zafiro curvado, movimiento automático y 100 m de resistencia."),
    Producto(6, "Reloj Minimalista Acero", 890000, 6, "relojes",
             "Caja de acero y esfera limpia. La elegancia de lo esencial."),
    Producto(7, "Colección Oro", 2400000, 3, "premium",
             "Edición limitada con acabados en oro. Exclusiva de la Sala Premium."),
    Producto(8, "Edición Nuevo Éxito", 1650000, 4, "premium",
             "La pieza en tendencia de la temporada, numerada a mano."),
]

_POR_ID = {producto.id_producto: producto for producto in PRODUCTOS}


def _normalizar(texto):
    """Minúsculas y sin tildes, para que 'frios' encuentre 'Fríos'."""
    texto = unicodedata.normalize("NFD", str(texto).lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def obtener_producto(id_producto):
    return _POR_ID.get(id_producto)


def buscar_por_nombre(nombre):
    buscado = _normalizar(nombre).strip()
    for producto in PRODUCTOS:
        if _normalizar(producto.nombre) == buscado:
            return producto
    return None


def listar_productos(categoria=None, busqueda=None):
    productos = PRODUCTOS
    if categoria:
        productos = [p for p in productos if p.categoria == categoria]
    if busqueda:
        termino = _normalizar(busqueda).strip()
        productos = [
            p for p in productos
            if termino in _normalizar(f"{p.nombre} {p.descripcion} {CATEGORIAS[p.categoria]}")
        ]
    return productos
