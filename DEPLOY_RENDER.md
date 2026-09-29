# Guía para subir la app a Render (Gratis)

## Paso 1: Crear cuenta en Render
1. Ve a https://render.com
2. Regístrate con GitHub (es más fácil) o email
3. Verifica tu cuenta

## Paso 2: Subir código a GitHub
1. Crea un repositorio en GitHub (puede ser privado)
2. Sube todos los archivos del proyecto:
   - server.py
   - index.html
   - productos.json
   - ventas.json (si existe)
   - movimientos.json (si existe)
   - requirements.txt
   - render.yaml
   - importar_excel.py

## Paso 3: Crear Web Service en Render
1. En Render, haz clic en **"New +"** → **"Web Service"**
2. Conecta tu repositorio de GitHub
3. Configura:
   - **Name**: inventario-ohiggins
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
4. Selecciona plan **Free**
5. Haz clic en **"Create Web Service"**

## Paso 4: Acceder a la app
- Render te dará una URL como: `https://inventario-ohiggins.onrender.com`
- Comparte esa URL con tu equipo

## Notas importantes:
- El servidor se **duerme** después de 15 minutos sin uso (plan gratis)
- Al primer acceso después de inactividad, tarda ~50 segundos en despertar
- Los archivos JSON se guardan en el disco de Render (persisten entre reinicios)
- Para producción con más usuarios, considera migrar a base de datos

## Comandos útiles:
```bash
# Ver logs en Render
Dashboard → Tu servicio → Logs

# Reiniciar manualmente
Dashboard → Tu servicio → Manual Deploy → Deploy latest commit
```
