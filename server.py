"""
Servidor para Sistema de Inventario - Equipamiento Automotriz O'Higgins
Gestion de vidrios automotrices con control de stock, flujos y alertas
"""
import http.server
import json
import os
import urllib.parse
from datetime import datetime

PRODUCTOS_FILE = 'productos.json'
MOVIMIENTOS_FILE = 'movimientos.json'
VENTAS_FILE = 'ventas.json'
PORT = int(os.environ.get('PORT', 8080))
STOCK_MINIMO_DEFAULT = 1  # Alerta cuando stock <= este value


def cargar_json(filename, default=None):
    if default is None:
        default = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default
    return default


def guardar_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cargar_productos():
    return cargar_json(PRODUCTOS_FILE, [])


def guardar_productos(data):
    guardar_json(PRODUCTOS_FILE, data)


def cargar_movimientos():
    return cargar_json(MOVIMIENTOS_FILE, [])


def guardar_movimientos(data):
    guardar_json(MOVIMIENTOS_FILE, data)


def cargar_ventas():
    return cargar_json(VENTAS_FILE, [])


def guardar_ventas(data):
    guardar_json(VENTAS_FILE, data)


def registrar_movimiento(producto_id, tipo, cantidad, motivo=''):
    """Registra un movimiento de entrada o salida"""
    movimientos = cargar_movimientos()
    movimiento = {
        'id': len(movimientos) + 1,
        'producto_id': producto_id,
        'tipo': tipo,  # 'entrada' o 'salida'
        'cantidad': cantidad,
        'motivo': motivo,
        'fecha': datetime.now().isoformat(),
    }
    movimientos.append(movimiento)
    guardar_movimientos(movimientos)
    return movimiento


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/productos':
            self.send_json(cargar_productos())
        elif path == '/api/movimientos':
            self.send_json(cargar_movimientos())
        elif path == '/api/alertas':
            productos = cargar_productos()
            alertas = [p for p in productos if p.get('Stock', 0) <= STOCK_MINIMO_DEFAULT]
            self.send_json(alertas)
        elif path == '/api/stats':
            productos = cargar_productos()
            total = len(productos)
            con_stock = sum(1 for p in productos if p.get('Stock', 0) > 0)
            sin_stock = total - con_stock
            unidades = sum(p.get('Stock', 0) for p in productos)
            valor_costo = sum(p.get('COSTO_COMPRA', 0) * p.get('Stock', 0) for p in productos)
            valor_venta = sum(p.get('PRECIO_VENTA', 0) * p.get('Stock', 0) for p in productos)
            self.send_json({
                'total': total,
                'con_stock': con_stock,
                'sin_stock': sin_stock,
                'unidades': unidades,
                'valor_costo': valor_costo,
                'valor_venta': valor_venta,
            })
        elif path == '/api/ventas':
            ventas = cargar_ventas()
            self.send_json(ventas)
        elif path == '/api/ventas/hoy':
            hoy = datetime.now().strftime('%Y-%m-%d')
            ventas = cargar_ventas()
            ventas_hoy = [v for v in ventas if v.get('fecha', '').startswith(hoy)]
            total_dia = sum(v.get('total', 0) for v in ventas_hoy)
            self.send_json({
                'ventas': ventas_hoy,
                'total_dia': total_dia,
                'cantidad_ventas': len(ventas_hoy)
            })
        elif path == '/api/ventas/reporte':
            # Reporte por fecha
            fecha = urllib.parse.parse_qs(parsed.query).get('fecha', [None])[0]
            ventas = cargar_ventas()
            if fecha:
                ventas = [v for v in ventas if v.get('fecha', '').startswith(fecha)]
            total = sum(v.get('total', 0) for v in ventas)
            self.send_json({
                'ventas': ventas,
                'total': total,
                'cantidad': len(ventas)
            })
        else:
            return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error_json(400, 'JSON invalido')
            return

        if path == '/api/productos':
            # Agregar nuevo producto
            productos = cargar_productos()
            data['id'] = len(productos) + 1
            data.setdefault('Stock', 0)
            data.setdefault('COSTO_COMPRA', 0)
            data.setdefault('PRECIO_VENTA', 0)
            productos.append(data)
            guardar_productos(productos)
            self.send_json({'ok': True, 'id': data['id'], 'total': len(productos)})

        elif path == '/api/productos/<id>':
            pass  # Manejado en PUT

        elif path == '/api/movimiento':
            # Registrar movimiento de stock
            producto_id = data.get('producto_id')
            tipo = data.get('tipo')  # 'entrada' o 'salida'
            cantidad = int(data.get('cantidad', 0))
            motivo = data.get('motivo', '')

            if not producto_id or tipo not in ('entrada', 'salida') or cantidad <= 0:
                self.send_error_json(400, 'Datos invalidos')
                return

            productos = cargar_productos()
            producto = next((p for p in productos if p.get('id') == producto_id), None)
            if not producto:
                self.send_error_json(404, 'Producto no encontrado')
                return

            if tipo == 'salida' and producto['Stock'] < cantidad:
                self.send_error_json(400, f"Stock insuficiente. Disponible: {producto['Stock']}")
                return

            # Actualizar stock
            if tipo == 'entrada':
                producto['Stock'] += cantidad
            else:
                producto['Stock'] -= cantidad

            guardar_productos(productos)
            movimiento = registrar_movimiento(producto_id, tipo, cantidad, motivo)
            self.send_json({
                'ok': True,
                'nuevo_stock': producto['Stock'],
                'movimiento': movimiento
            })

        elif path == '/api/importar':
            # Importar lista de productos desde Excel
            nuevos = data.get('productos', [])
            if not nuevos:
                self.send_error_json(400, 'No se recibieron productos')
                return

            productos = cargar_productos()
            # Eliminar duplicados por marca+modelo+atril+vidrio
            existentes = {(p.get('MARCA', ''), p.get('modelo', ''), 
                          p.get('Atril', ''), p.get('VIDRIO', '')) for p in productos}
            
            agregados = 0
            for p in nuevos:
                key = (p.get('MARCA', ''), p.get('modelo', ''),
                       p.get('Atril', ''), p.get('VIDRIO', ''))
                if key not in existentes:
                    p['id'] = len(productos) + 1
                    productos.append(p)
                    existentes.add(key)
                    agregados += 1

            guardar_productos(productos)
            self.send_json({'ok': True, 'agregados': agregados, 'total': len(productos)})

        elif path == '/api/ventas':
            # Registrar nueva venta
            productos_venta = data.get('productos', [])
            medio_pago = data.get('medio_pago', 'efectivo')
            cliente = data.get('cliente', '')
            observaciones = data.get('observaciones', '')

            if not productos_venta:
                self.send_error_json(400, 'No se recibieron productos')
                return

            productos = cargar_productos()
            ventas = cargar_ventas()

            # Validar stock y calcular total
            total_venta = 0
            productos_actualizados = []
            
            for item in productos_venta:
                producto_id = item.get('producto_id')
                cantidad = int(item.get('cantidad', 0))
                precio_unitario = float(item.get('precio_unitario', 0))
                
                if cantidad <= 0:
                    self.send_error_json(400, 'Cantidad invalida')
                    return
                
                producto = next((p for p in productos if p.get('id') == producto_id), None)
                if not producto:
                    self.send_error_json(404, f'Producto {producto_id} no encontrado')
                    return
                
                if producto['Stock'] < cantidad:
                    self.send_error_json(400, f"Stock insuficiente para {producto['MARCA']} {producto['modelo']}. Disponible: {producto['Stock']}")
                    return
                
                # Descontar stock
                producto['Stock'] -= cantidad
                total_venta += precio_unitario * cantidad
                
                # Registrar movimiento
                registrar_movimiento(producto_id, 'salida', cantidad, f'Venta #{len(ventas) + 1}')
                
                productos_actualizados.append({
                    'producto_id': producto_id,
                    'MARCA': producto['MARCA'],
                    'modelo': producto['modelo'],
                    'VIDRIO': producto['VIDRIO'],
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'subtotal': precio_unitario * cantidad
                })

            # Guardar venta
            venta = {
                'id': len(ventas) + 1,
                'fecha': datetime.now().isoformat(),
                'productos': productos_actualizados,
                'total': total_venta,
                'medio_pago': medio_pago,
                'cliente': cliente,
                'observaciones': observaciones
            }
            
            ventas.append(venta)
            guardar_ventas(ventas)
            guardar_productos(productos)
            
            self.send_json({
                'ok': True,
                'venta': venta,
                'total_ventas': len(ventas)
            })

        else:
            self.send_error_json(404, 'Endpoint no encontrado')

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error_json(400, 'JSON invalido')
            return

        # /api/productos/<id>
        if path.startswith('/api/productos/'):
            try:
                producto_id = int(path.split('/')[-1])
            except ValueError:
                self.send_error_json(400, 'ID invalido')
                return

            productos = cargar_productos()
            producto = next((p for p in productos if p.get('id') == producto_id), None)
            if not producto:
                self.send_error_json(404, 'Producto no encontrado')
                return

            # Actualizar campos
            for key in ['MARCA', 'modelo', 'Año', 'Atril', 'VIDRIO', 'OBSERVACION', 
                       'Stock', 'COSTO_COMPRA', 'PRECIO_VENTA']:
                if key in data:
                    producto[key] = data[key]

            guardar_productos(productos)
            self.send_json({'ok': True, 'producto': producto})
        else:
            self.send_error_json(404, 'Endpoint no encontrado')

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # /api/productos/<id>
        if path.startswith('/api/productos/'):
            try:
                producto_id = int(path.split('/')[-1])
            except ValueError:
                self.send_error_json(400, 'ID invalido')
                return

            productos = cargar_productos()
            productos = [p for p in productos if p.get('id') != producto_id]
            guardar_productos(productos)
            self.send_json({'ok': True, 'total': len(productos)})
        else:
            self.send_error_json(404, 'Endpoint no encontrado')

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def send_error_json(self, status, message):
        self.send_json({'error': message}, status)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f'Servidor corriendo en http://localhost:{PORT}')
    print('Presiona Ctrl+C para detener')
    http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
