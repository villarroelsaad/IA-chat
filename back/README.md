# Chat bot de consola (modo API y fallback)

Este repositorio contiene `chat.py`, un script de chat por consola que intenta usar la librería `google.genai` (Gemini) si está disponible y si se configura la variable de entorno `GEMINI_API_KEY`. Si no hay acceso a la API, el script cae en un modo "fallback" local que permite probar y usar el bot sin credenciales.

Requisitos
- Python 3.8+
- (Opcional para la API) `google-genai` y una clave en `.env` llamada `GEMINI_API_KEY`.

Instalación
1. Crear y activar un entorno virtual (opcional pero recomendado).
2. Instalar dependencias listadas en `requirements.txt`:

```powershell
pip install -r requirements.txt
```

Configuración (opcional)
Si quieres usar la API, crea un archivo `.env` en la carpeta con:

```
GEMINI_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-2.5-flash
```

Si no configuras la clave o no instalas la librería de la API, `chat.py` ejecutará un modo local de respaldo que no hace llamadas externas.

Uso
Ejecuta:

```powershell
python chat.py
```

Comandos útiles dentro del chat:
- `help` — muestra esta ayuda
- `exit` o `quit` — salir

Notas
- El modo fallback es intencionadamente simple y sirve para pruebas locales. No replica completamente las capacidades de un modelo grande.
- Actualiza `requirements.txt` si instalas una biblioteca diferente para acceder a la API que planeas usar.

Ejecución con Docker (backend + frontend)

1. Construir y arrancar los servicios con docker-compose:

```powershell
docker-compose up --build
```

2. El backend quedará accesible en http://localhost:8000 y el frontend estático en http://localhost:3000

3. Para probar localmente sin Docker, puedes ejecutar `test_api.py` (asegúrate de que `server.py` esté corriendo):

```powershell
python test_api.py
```

Notas sobre CORS
- Para desarrollo, el backend tiene CORS habilitado de forma abierta. En producción restringe los orígenes permitidos.
