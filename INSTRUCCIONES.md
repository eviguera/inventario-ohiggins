# Sistema de Inventario - Equipamiento Automotriz O'Higgins

Sistema de gestion de inventario para vidrios automotrices.

## Como usar

### Iniciar el servidor

```bash
python server.py
```

Luego abre en el navegador: **http://localhost:8080**

### Importar desde Excel

1. Ejecuta el script de importacion:
   ```bash
   python importar_excel.py
   ```
   Esto lee todas las hojas de vidrios del archivo `INVENTARIO ULTIMO.xlsx` y las guarda en `productos.json`.

2. También puedes importar directamente desde la interfaz web:
   - Ve a la pestaña "Importar Excel"
   - Arrastra tu archivo .xlsx
   - Selecciona la hoja con datos de vidrios
   - Revisa la vista previa y confirma

### Funcionalidades

- **Buscar Productos**: Busca por marca, modelo, atril, vidrio o cualquier campo
- **Agregar Producto**: Agrega nuevos vidrios al inventario
- **Gestionar Stock**: Usa los botones + y - para entradas y salidas
- **Editar**: Modifica datos de cualquier producto
- **Eliminar**: Quita productos del inventario
- **Movimientos**: Historial de todas las entradas y salidas
- **Alertas**: Avisos cuando el stock esta bajo o agotado
- **Importar Excel**: Carga masiva desde archivos .xlsx

### Estructura de archivos

- `server.py` - Servidor web (Python)
- `index.html` - Interfaz web
- `productos.json` - Base de datos de productos
- `movimientos.json` - Historial de movimientos
- `importar_excel.py` - Script de importacion desde Excel
- `INVENTARIO ULTIMO.xlsx` - Archivo Excel fuente

### Campos del producto

- **MARCA**: Marca del vehiculo (ej: TOYOTA, FORD)
- **modelo**: Modelo del vehiculo (ej: COROLLA, F150)
- **Año**: Año o rango de años (ej: 2020, 2010-2015)
- **Atril**: Ubicacion en el almacen (ej: A1, B2, NARANJA B6)
- **VIDRIO**: Tipo de vidrio (ej: PB=Parabrisas, LUNETA)
- **OBSERVACION**: Notas adicionales
- **Stock**: Cantidad disponible
- **COSTO_COMPRA**: Precio de compra
- **PRECIO_VENTA**: Precio de venta
