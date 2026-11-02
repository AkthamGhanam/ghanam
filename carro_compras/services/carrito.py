"""Lógica del carrito de compras.

El carrito se guarda como un diccionario {"id_producto": cantidad}. Así puede
vivir en la sesión de Flask (una cookie firmada) en lugar de en la memoria del
servidor. Esto es necesario en Vercel: cada petición puede llegar a una
instancia distinta de la función, por lo que una lista en memoria se perdería
entre peticiones y, además, sería compartida por todos los visitantes.

El precio, el nombre y el stock salen siempre del catálogo del servidor; el
navegador solo envía el id del producto y la cantidad.
"""


class Producto:
    """Producto del catálogo."""

    def __init__(self, id_producto, nombre, precio, stock, categoria, descripcion=""):
        self.id_producto = int(id_producto)
        self.nombre = str(nombre)
        self.precio = float(precio)
        self.stock = int(stock)
        self.categoria = str(categoria)
        self.descripcion = str(descripcion)

    def to_dict(self):
        return {
            "id_producto": self.id_producto,
            "nombre": self.nombre,
            "precio": self.precio,
            "stock": self.stock,
            "categoria": self.categoria,
            "descripcion": self.descripcion,
        }


class ErrorCarrito(Exception):
    """Error de negocio que se devuelve al cliente con un código HTTP."""

    def __init__(self, mensaje, status=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


def _entero(valor, campo):
    # bool es subclase de int: True no debe contar como 1.
    if isinstance(valor, bool):
        raise ErrorCarrito(f"El campo '{campo}' debe ser un número entero.")
    try:
        numero = int(valor)
    except (TypeError, ValueError, OverflowError):
        raise ErrorCarrito(f"El campo '{campo}' debe ser un número entero.") from None
    if isinstance(valor, float) and numero != valor:
        raise ErrorCarrito(f"El campo '{campo}' debe ser un número entero.")
    return numero


class CarritoCompra:
    """Carrito de un visitante.

    `buscar_producto` es una función id -> Producto | None (el catálogo).
    `items` es lo guardado en la sesión: una lista de pares [id, cantidad]
    (una lista, y no un diccionario, para conservar el orden en que se
    añadieron los productos).
    """

    def __init__(self, buscar_producto, items=None):
        self._buscar_producto = buscar_producto
        self.items = {}
        if isinstance(items, dict):
            items = list(items.items())
        if not isinstance(items, list):
            items = []
        # Se limpia lo que venga de la sesión: productos que ya no existen,
        # cantidades inválidas o mayores al stock actual.
        for par in items:
            try:
                id_producto, cantidad = par
                producto = self._buscar_producto(int(id_producto))
                cantidad = int(cantidad)
            except (TypeError, ValueError, OverflowError):
                continue
            if producto is None or cantidad < 1 or producto.stock < 1:
                continue
            self.items[str(producto.id_producto)] = min(cantidad, producto.stock)

    def para_sesion(self):
        return [[int(clave), cantidad] for clave, cantidad in self.items.items()]

    def _producto(self, id_producto):
        producto = self._buscar_producto(_entero(id_producto, "id_producto"))
        if producto is None:
            raise ErrorCarrito("El producto no existe en el catálogo.", 404)
        return producto

    # Ingreso de productos al carrito (suma a la cantidad que ya hubiera).
    def add_items(self, id_producto, cantidad=1):
        producto = self._producto(id_producto)
        cantidad = _entero(cantidad, "cantidad")
        if cantidad < 1:
            raise ErrorCarrito("La cantidad debe ser al menos 1.")
        clave = str(producto.id_producto)
        nueva_cantidad = self.items.get(clave, 0) + cantidad
        if nueva_cantidad > producto.stock:
            raise ErrorCarrito(
                f"Solo hay {producto.stock} unidades de {producto.nombre}.", 409
            )
        self.items[clave] = nueva_cantidad
        return producto

    # Cambio de la cantidad de un producto que ya está en el carrito (0 lo quita).
    def update_item(self, id_producto, cantidad):
        producto = self._producto(id_producto)
        cantidad = _entero(cantidad, "cantidad")
        clave = str(producto.id_producto)
        if clave not in self.items:
            raise ErrorCarrito("El producto no está en el carrito.", 404)
        if cantidad < 0:
            raise ErrorCarrito("La cantidad no puede ser negativa.")
        if cantidad > producto.stock:
            raise ErrorCarrito(
                f"Solo hay {producto.stock} unidades de {producto.nombre}.", 409
            )
        if cantidad == 0:
            del self.items[clave]
        else:
            self.items[clave] = cantidad
        return producto

    # Remoción de un solo producto del carrito.
    def remove_item(self, id_producto):
        producto = self._producto(id_producto)
        clave = str(producto.id_producto)
        if clave not in self.items:
            raise ErrorCarrito("El producto no está en el carrito.", 404)
        del self.items[clave]
        return producto

    # Eliminación de todos los productos del carrito.
    def clear_cart(self):
        self.items.clear()

    # Resumen del carrito listo para enviarse como JSON.
    def show_item(self):
        productos = []
        total = 0.0
        unidades = 0
        for clave, cantidad in self.items.items():
            producto = self._buscar_producto(int(clave))
            subtotal = round(producto.precio * cantidad, 2)
            productos.append({**producto.to_dict(), "cantidad": cantidad, "subtotal": subtotal})
            total += subtotal
            unidades += cantidad
        return {"carrito": productos, "total": round(total, 2), "unidades": unidades}
