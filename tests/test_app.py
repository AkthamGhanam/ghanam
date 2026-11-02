"""Pruebas de la API. Ejecutar desde la raíz: python -m unittest"""

import unittest

from app import create_app


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "pruebas"})
        self.client = self.app.test_client()

    def agregar(self, id_producto, cantidad=1, client=None):
        client = client or self.client
        return client.post("/api/cart/income", json={"id_producto": id_producto, "cantidad": cantidad})


class CatalogoTest(BaseTest):
    def test_lista_todos_los_productos_y_categorias_en_orden(self):
        datos = self.client.get("/api/catalogo").get_json()
        self.assertEqual(len(datos["productos"]), 8)
        self.assertEqual(
            [c["clave"] for c in datos["categorias"]],
            ["calidos", "frios", "relojes", "premium"],
        )

    def test_filtra_por_categoria(self):
        datos = self.client.get("/api/catalogo?categoria=relojes").get_json()
        self.assertTrue(datos["productos"])
        self.assertTrue(all(p["categoria"] == "relojes" for p in datos["productos"]))

    def test_categoria_invalida(self):
        self.assertEqual(self.client.get("/api/catalogo?categoria=xyz").status_code, 400)

    def test_busqueda_ignora_tildes(self):
        datos = self.client.get("/api/catalogo?q=frio").get_json()
        self.assertEqual({p["id_producto"] for p in datos["productos"]}, {3, 4})


class CarritoTest(BaseTest):
    def test_carrito_inicia_vacio(self):
        datos = self.client.get("/api/cart/show").get_json()
        self.assertEqual(datos, {"carrito": [], "total": 0, "unidades": 0})

    def test_agregar_usa_precio_del_servidor(self):
        # Aunque el cliente envíe otro precio, se usa el del catálogo.
        r = self.client.post("/api/cart/income", json={"id_producto": 1, "cantidad": 2, "precio": 1})
        self.assertEqual(r.status_code, 200)
        datos = r.get_json()
        self.assertEqual(datos["unidades"], 2)
        self.assertEqual(datos["total"], 378000)
        self.assertIn("mensaje", datos)

    def test_agregar_acumula_y_conserva_orden(self):
        self.agregar(5)
        self.agregar(3)
        self.agregar(5)
        datos = self.client.get("/api/cart/show").get_json()
        self.assertEqual([p["id_producto"] for p in datos["carrito"]], [5, 3])
        self.assertEqual(datos["carrito"][0]["cantidad"], 2)
        self.assertEqual(datos["carrito"][0]["subtotal"], 2500000)

    def test_no_supera_el_stock(self):
        self.agregar(7, 3)
        r = self.agregar(7, 1)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.client.get("/api/cart/show").get_json()["unidades"], 3)

    def test_cantidades_invalidas(self):
        for cantidad in (0, -1, "abc", 1.5, True, None):
            with self.subTest(cantidad=cantidad):
                self.assertEqual(self.agregar(1, cantidad).status_code, 400)

    def test_producto_inexistente(self):
        self.assertEqual(self.agregar(999).status_code, 404)

    def test_errores_de_la_api_en_json(self):
        r = self.client.get("/api/no-existe")
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.get_json())
        r = self.client.post("/api/cart/show")  # Solo admite GET
        self.assertEqual(r.status_code, 405)
        self.assertIn("error", r.get_json())

    def test_datos_que_no_son_json(self):
        r = self.client.post("/api/cart/income", data="hola")
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/cart/income", json={})
        self.assertEqual(r.status_code, 400)

    def test_actualizar_cantidad(self):
        self.agregar(2)
        r = self.client.put("/api/cart/update", json={"id_producto": 2, "cantidad": 4})
        self.assertEqual(r.get_json()["unidades"], 4)
        r = self.client.put("/api/cart/update", json={"id_producto": 2, "cantidad": 99})
        self.assertEqual(r.status_code, 409)
        r = self.client.put("/api/cart/update", json={"id_producto": 2, "cantidad": 0})
        self.assertEqual(r.get_json()["carrito"], [])
        r = self.client.put("/api/cart/update", json={"id_producto": 2, "cantidad": 1})
        self.assertEqual(r.status_code, 404)

    def test_eliminar_producto_por_id_y_por_nombre(self):
        self.agregar(1)
        self.agregar(3)
        r = self.client.put("/api/cart/clear_item", json={"id_producto": 1})
        self.assertEqual(r.status_code, 200)
        r = self.client.put("/api/cart/clear_item", json={"nombre": "Frío N.º 1"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["carrito"], [])

    def test_eliminar_producto_que_no_esta(self):
        r = self.client.put("/api/cart/clear_item", json={"id_producto": 1})
        self.assertEqual(r.status_code, 404)

    def test_vaciar_carrito(self):
        self.agregar(1)
        self.agregar(4)
        r = self.client.delete("/api/cart/clear")
        self.assertEqual(r.get_json()["unidades"], 0)

    def test_cada_visitante_tiene_su_carrito(self):
        otro = self.app.test_client()
        self.agregar(1, 2)
        self.assertEqual(otro.get("/api/cart/show").get_json()["unidades"], 0)
        self.assertEqual(self.client.get("/api/cart/show").get_json()["unidades"], 2)

    def test_limpia_datos_invalidos_de_la_sesion(self):
        with self.client.session_transaction() as sesion:
            sesion["carrito"] = [[1, 2], [999, 1], ["x", 1], [7, 50], [3, -2], "basura"]
        datos = self.client.get("/api/cart/show").get_json()
        self.assertEqual([(p["id_producto"], p["cantidad"]) for p in datos["carrito"]], [(1, 2), (7, 3)])


class PaginasTest(BaseTest):
    def test_pagina_de_inicio(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"GHANAM", r.data)

    def test_archivos_estaticos(self):
        for ruta in ("/style/styles.css", "/js/script.js", "/js/tienda.js", "/resource/GHANAM.png"):
            with self.subTest(ruta=ruta):
                r = self.client.get(ruta)
                self.assertEqual(r.status_code, 200)
                r.close()


if __name__ == "__main__":
    unittest.main()
