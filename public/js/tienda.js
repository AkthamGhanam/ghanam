// Tienda GHANAM: catálogo, búsqueda y carrito conectados a la API de Flask.
// La API vive en el mismo dominio (Vercel o `python app.py`), por eso las
// rutas son relativas y el carrito viaja en la cookie de sesión.
(() => {
    'use strict';

    const API = {
        catalogo: '/api/catalogo',
        ver: '/api/cart/show',
        agregar: '/api/cart/income',
        actualizar: '/api/cart/update',
        quitar: '/api/cart/clear_item',
        vaciar: '/api/cart/clear',
    };
    const CORREO_PEDIDOS = 'exito@ghanam.com';
    const formatoPrecio = new Intl.NumberFormat('es-CO', {
        style: 'currency', currency: 'COP', maximumFractionDigits: 0,
    });

    const estado = {
        productos: [],
        categorias: [],
        filtro: 'todos',
        busqueda: '',
        carrito: { carrito: [], total: 0, unidades: 0 },
        ocupado: false,
    };

    const $ = (id) => document.getElementById(id);
    const el = {
        productos: $('productos'),
        filtros: $('filtros'),
        resumen: $('coleccion-resumen'),
        coleccion: $('coleccion'),
        busquedaPc: $('desktop-search-input'),
        busquedaMovil: $('mobile-search-input'),
        botonCarrito: $('cart-button'),
        contador: $('cart-count'),
        panel: $('cart-drawer'),
        fondo: $('cart-backdrop'),
        cerrar: $('cart-close'),
        items: $('cart-items'),
        total: $('cart-total'),
        pedir: $('cart-checkout'),
        vaciar: $('cart-clear'),
        aviso: $('toast'),
    };

    // ------------------------------------------------------------ Utilidades

    async function api(ruta, metodo = 'GET', cuerpo) {
        const opciones = { method: metodo, credentials: 'same-origin', headers: {} };
        if (cuerpo !== undefined) {
            opciones.headers['Content-Type'] = 'application/json';
            opciones.body = JSON.stringify(cuerpo);
        }
        let respuesta;
        try {
            respuesta = await fetch(ruta, opciones);
        } catch {
            throw new Error('No hay conexión con el servidor.');
        }
        let datos = {};
        try { datos = await respuesta.json(); } catch { /* respuesta sin JSON */ }
        if (!respuesta.ok) {
            throw new Error(datos.error || `Error ${respuesta.status} del servidor.`);
        }
        return datos;
    }

    function crear(etiqueta, clase, texto) {
        const nodo = document.createElement(etiqueta);
        if (clase) nodo.className = clase;
        if (texto !== undefined) nodo.textContent = texto;
        return nodo;
    }

    function normalizar(texto) {
        return String(texto).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').trim();
    }

    let temporizadorAviso;
    function avisar(mensaje, esError = false) {
        el.aviso.textContent = mensaje;
        el.aviso.classList.toggle('is-error', esError);
        el.aviso.hidden = false;
        requestAnimationFrame(() => el.aviso.classList.add('is-visible'));
        clearTimeout(temporizadorAviso);
        temporizadorAviso = setTimeout(() => {
            el.aviso.classList.remove('is-visible');
            setTimeout(() => { el.aviso.hidden = true; }, 300);
        }, 2600);
    }

    function nombreCategoria(clave) {
        const categoria = estado.categorias.find((c) => c.clave === clave);
        return categoria ? categoria.nombre : clave;
    }

    function cantidadEnCarrito(idProducto) {
        const item = estado.carrito.carrito.find((p) => p.id_producto === idProducto);
        return item ? item.cantidad : 0;
    }

    // -------------------------------------------------------------- Catálogo

    function productosVisibles() {
        const termino = normalizar(estado.busqueda);
        return estado.productos.filter((p) => {
            if (estado.filtro !== 'todos' && p.categoria !== estado.filtro) return false;
            if (!termino) return true;
            return normalizar(`${p.nombre} ${p.descripcion} ${nombreCategoria(p.categoria)}`).includes(termino);
        });
    }

    function pintarFiltros() {
        el.filtros.replaceChildren();
        const opciones = [{ clave: 'todos', nombre: 'Todos' }, ...estado.categorias];
        for (const opcion of opciones) {
            const boton = crear('button', 'filtro-chip', opcion.nombre);
            boton.type = 'button';
            boton.dataset.filtro = opcion.clave;
            const activo = opcion.clave === estado.filtro;
            boton.classList.toggle('is-active', activo);
            boton.setAttribute('aria-pressed', String(activo));
            el.filtros.append(boton);
        }
    }

    function tarjetaProducto(producto) {
        const tarjeta = crear('article', 'producto-card');
        tarjeta.dataset.categoria = producto.categoria;

        const visual = crear('div', `producto-visual visual-${producto.categoria}`);
        const logo = crear('img', 'producto-logo');
        logo.src = '/resource/GHANAM.png';
        logo.alt = '';
        visual.append(logo, crear('span', 'producto-tag', nombreCategoria(producto.categoria)));

        const cuerpo = crear('div', 'producto-cuerpo');
        cuerpo.append(
            crear('h3', 'producto-nombre', producto.nombre),
            crear('p', 'producto-descripcion', producto.descripcion),
        );

        const pie = crear('div', 'producto-pie');
        const precio = crear('div', 'producto-precio-wrap');
        precio.append(crear('span', 'producto-precio', formatoPrecio.format(producto.precio)));

        const enCarrito = cantidadEnCarrito(producto.id_producto);
        const disponibles = producto.stock - enCarrito;
        let textoStock = `${producto.stock} disponibles`;
        if (producto.stock <= 0) textoStock = 'Agotado';
        else if (enCarrito > 0) textoStock = `${enCarrito} en tu carrito`;
        precio.append(crear('span', 'producto-stock', textoStock));

        const boton = crear('button', 'producto-agregar', disponibles > 0 ? 'Añadir' : 'Sin stock');
        boton.type = 'button';
        boton.dataset.agregar = String(producto.id_producto);
        boton.disabled = disponibles <= 0;
        boton.setAttribute('aria-label', `Añadir ${producto.nombre} al carrito`);

        pie.append(precio, boton);
        cuerpo.append(pie);
        tarjeta.append(visual, cuerpo);
        return tarjeta;
    }

    function pintarProductos() {
        const visibles = productosVisibles();
        el.productos.replaceChildren();
        if (visibles.length === 0) {
            const vacio = crear('div', 'productos-estado');
            vacio.append(crear('p', '', 'No encontramos piezas con esa búsqueda.'));
            const limpiar = crear('button', 'filtro-chip', 'Ver toda la colección');
            limpiar.type = 'button';
            limpiar.dataset.filtro = 'todos';
            vacio.append(limpiar);
            el.productos.append(vacio);
        } else {
            el.productos.append(...visibles.map(tarjetaProducto));
        }

        let resumen = `${visibles.length} ${visibles.length === 1 ? 'pieza' : 'piezas'}`;
        if (estado.filtro !== 'todos') resumen += ` · ${nombreCategoria(estado.filtro)}`;
        if (estado.busqueda.trim()) resumen += ` · “${estado.busqueda.trim()}”`;
        el.resumen.textContent = resumen;
    }

    function irAColeccion() {
        el.coleccion.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function aplicarFiltro(filtro, { limpiarBusqueda = true, desplazar = true } = {}) {
        estado.filtro = filtro;
        if (limpiarBusqueda) fijarBusqueda('');
        pintarFiltros();
        pintarProductos();
        if (desplazar) irAColeccion();
    }

    function fijarBusqueda(texto) {
        estado.busqueda = texto;
        if (el.busquedaPc && el.busquedaPc.value !== texto) el.busquedaPc.value = texto;
        if (el.busquedaMovil && el.busquedaMovil.value !== texto) el.busquedaMovil.value = texto;
    }

    function buscar(texto, { desplazar = false } = {}) {
        fijarBusqueda(texto);
        if (texto.trim()) {
            estado.filtro = 'todos';
            pintarFiltros();
        }
        pintarProductos();
        if (desplazar) irAColeccion();
    }

    async function cargarCatalogo() {
        try {
            const datos = await api(API.catalogo);
            estado.productos = datos.productos;
            estado.categorias = datos.categorias;
            pintarFiltros();
            pintarProductos();
        } catch (error) {
            el.productos.replaceChildren(crear('p', 'productos-estado', `No se pudo cargar la colección. ${error.message}`));
        }
    }

    // --------------------------------------------------------------- Carrito

    function abrirCarrito() {
        el.fondo.hidden = false;
        requestAnimationFrame(() => {
            el.panel.classList.add('is-open');
            el.fondo.classList.add('is-visible');
        });
        el.panel.setAttribute('aria-hidden', 'false');
        el.botonCarrito.setAttribute('aria-expanded', 'true');
        document.body.classList.add('no-scroll', 'cart-open');
        el.cerrar.focus();
    }

    function cerrarCarrito() {
        el.panel.classList.remove('is-open');
        el.fondo.classList.remove('is-visible');
        el.panel.setAttribute('aria-hidden', 'true');
        el.botonCarrito.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('no-scroll', 'cart-open');
        setTimeout(() => { el.fondo.hidden = true; }, 300);
    }

    function carritoAbierto() {
        return el.panel.classList.contains('is-open');
    }

    function filaCarrito(item) {
        const fila = crear('div', 'cart-item');

        const info = crear('div', 'cart-item-info');
        info.append(
            crear('span', 'cart-item-categoria', nombreCategoria(item.categoria)),
            crear('span', 'cart-item-nombre', item.nombre),
            crear('span', 'cart-item-precio', `${formatoPrecio.format(item.precio)} c/u`),
        );

        const controles = crear('div', 'cart-item-controles');
        const menos = crear('button', 'cart-qty-btn', '−');
        menos.type = 'button';
        menos.dataset.cantidad = String(item.cantidad - 1);
        menos.dataset.producto = String(item.id_producto);
        menos.setAttribute('aria-label', `Quitar una unidad de ${item.nombre}`);

        const cantidad = crear('span', 'cart-qty', String(item.cantidad));

        const mas = crear('button', 'cart-qty-btn', '+');
        mas.type = 'button';
        mas.dataset.cantidad = String(item.cantidad + 1);
        mas.dataset.producto = String(item.id_producto);
        mas.disabled = item.cantidad >= item.stock;
        mas.setAttribute('aria-label', `Añadir una unidad de ${item.nombre}`);

        controles.append(menos, cantidad, mas);

        const lateral = crear('div', 'cart-item-lateral');
        const quitar = crear('button', 'cart-item-quitar', 'Quitar');
        quitar.type = 'button';
        quitar.dataset.quitar = String(item.id_producto);
        quitar.setAttribute('aria-label', `Quitar ${item.nombre} del carrito`);
        lateral.append(crear('span', 'cart-item-subtotal', formatoPrecio.format(item.subtotal)), quitar);

        fila.append(info, controles, lateral);
        return fila;
    }

    function pintarCarrito() {
        const { carrito, total, unidades } = estado.carrito;

        el.contador.textContent = String(unidades);
        el.contador.hidden = unidades === 0;
        el.botonCarrito.setAttribute('aria-label', `Abrir carrito (${unidades} ${unidades === 1 ? 'producto' : 'productos'})`);

        el.items.replaceChildren();
        if (carrito.length === 0) {
            const vacio = crear('div', 'cart-vacio');
            vacio.append(
                crear('p', 'cart-vacio-titulo', 'Tu carrito está vacío'),
                crear('p', 'cart-vacio-texto', 'Explora la colección y añade las piezas que te acompañarán.'),
            );
            const explorar = crear('button', 'cart-explorar', 'Explorar colección');
            explorar.type = 'button';
            explorar.dataset.categoria = 'todos';
            vacio.append(explorar);
            el.items.append(vacio);
        } else {
            el.items.append(...carrito.map(filaCarrito));
        }

        el.total.textContent = formatoPrecio.format(total);
        el.pedir.disabled = carrito.length === 0;
        el.vaciar.disabled = carrito.length === 0;

        // Los botones "Añadir" dependen de lo que ya está en el carrito.
        if (estado.productos.length) pintarProductos();
    }

    async function operarCarrito(ruta, metodo, cuerpo) {
        if (estado.ocupado) return null;
        estado.ocupado = true;
        document.body.classList.add('cart-busy');
        try {
            const datos = await api(ruta, metodo, cuerpo);
            estado.carrito = datos;
            pintarCarrito();
            return datos;
        } catch (error) {
            avisar(error.message, true);
            // Se resincroniza por si el carrito cambió en otra pestaña.
            try { estado.carrito = await api(API.ver); pintarCarrito(); } catch { /* sin conexión */ }
            return null;
        } finally {
            estado.ocupado = false;
            document.body.classList.remove('cart-busy');
        }
    }

    async function cargarCarrito() {
        try {
            estado.carrito = await api(API.ver);
            pintarCarrito();
        } catch (error) {
            avisar(`No se pudo cargar el carrito. ${error.message}`, true);
        }
    }

    function solicitarPedido() {
        const { carrito, total } = estado.carrito;
        if (carrito.length === 0) return;
        const lineas = carrito.map(
            (p) => `• ${p.cantidad} x ${p.nombre} — ${formatoPrecio.format(p.subtotal)}`,
        );
        const cuerpo = [
            'Hola, GHANAM. Quiero hacer este pedido:',
            '',
            ...lineas,
            '',
            `Total: ${formatoPrecio.format(total)}`,
            '',
            'Nombre:',
            'Teléfono:',
            'Ciudad y dirección de entrega:',
        ].join('\n');
        const asunto = 'Pedido desde la tienda GHANAM';
        window.location.href = `mailto:${CORREO_PEDIDOS}?subject=${encodeURIComponent(asunto)}&body=${encodeURIComponent(cuerpo)}`;
    }

    // --------------------------------------------------------------- Eventos

    document.addEventListener('click', async (evento) => {
        const objetivo = evento.target.closest('button, a');
        if (!objetivo) return;
        const { dataset } = objetivo;

        if (dataset.agregar) {
            const datos = await operarCarrito(API.agregar, 'POST', { id_producto: Number(dataset.agregar), cantidad: 1 });
            if (datos) avisar(datos.mensaje || 'Producto añadido al carrito.');
            return;
        }
        if (dataset.quitar) {
            await operarCarrito(API.quitar, 'PUT', { id_producto: Number(dataset.quitar) });
            return;
        }
        if (dataset.producto && dataset.cantidad !== undefined) {
            await operarCarrito(API.actualizar, 'PUT', {
                id_producto: Number(dataset.producto),
                cantidad: Number(dataset.cantidad),
            });
            return;
        }
        if (dataset.filtro) {
            aplicarFiltro(dataset.filtro, { desplazar: false });
            return;
        }
        if (dataset.categoria) {
            evento.preventDefault();
            if (carritoAbierto()) cerrarCarrito();
            cerrarBuscadorMovil();
            aplicarFiltro(dataset.categoria);
            return;
        }
        if (dataset.busqueda) {
            cerrarBuscadorMovil();
            buscar(dataset.busqueda, { desplazar: true });
        }
    });

    el.botonCarrito.addEventListener('click', () => (carritoAbierto() ? cerrarCarrito() : abrirCarrito()));
    el.cerrar.addEventListener('click', cerrarCarrito);
    el.fondo.addEventListener('click', cerrarCarrito);
    el.pedir.addEventListener('click', solicitarPedido);
    el.vaciar.addEventListener('click', async () => {
        if (!window.confirm('¿Vaciar todo el carrito?')) return;
        const datos = await operarCarrito(API.vaciar, 'DELETE');
        if (datos) avisar('Carrito vacío.');
    });

    document.addEventListener('keydown', (evento) => {
        if (evento.key === 'Escape' && carritoAbierto()) cerrarCarrito();
    });

    function cerrarBuscadorMovil() {
        const overlay = $('search-overlay');
        if (overlay && overlay.classList.contains('active') && typeof window.toggleSearch === 'function') {
            window.toggleSearch();
        }
    }

    if (el.busquedaPc) {
        el.busquedaPc.addEventListener('input', () => buscar(el.busquedaPc.value));
        el.busquedaPc.addEventListener('keydown', (evento) => {
            if (evento.key === 'Enter') buscar(el.busquedaPc.value, { desplazar: true });
        });
    }
    if (el.busquedaMovil) {
        el.busquedaMovil.addEventListener('keydown', (evento) => {
            if (evento.key === 'Enter') {
                evento.preventDefault();
                el.busquedaMovil.blur();
                cerrarBuscadorMovil();
                buscar(el.busquedaMovil.value, { desplazar: true });
            }
        });
    }

    const anio = $('anio-actual');
    if (anio) anio.textContent = String(new Date().getFullYear());

    // Inicio: catálogo y carrito en paralelo.
    cargarCatalogo();
    cargarCarrito();
})();
