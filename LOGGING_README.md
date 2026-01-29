# Sistema de Logging de SARA

Este proyecto incluye un sistema completo de logging que captura toda la salida de consola con fecha y hora para facilitar el debugging y seguimiento de errores.

## 📁 Archivos de Log

Los logs se almacenan en el directorio `logs/` con el siguiente formato de nombre:

- `sara_backend_YYYYMMDD.log` - Logs del backend de Python
- `sara_electron_YYYYMMDD.log` - Logs del proceso principal de Electron
- `sara_dev_YYYYMMDD.log` - Logs del script de desarrollo

## 🚀 Uso

### Iniciar el entorno de desarrollo con logging

```bash
npm run dev:log
```

Este comando:
1. Inicia Vite (frontend)
2. Inicia Electron (aplicación de escritorio)
3. Inicia el backend de Python automáticamente
4. Captura toda la salida de consola en archivos de log con timestamps

### Iniciar sin logging (modo normal)

```bash
npm run dev
```

## 📝 Formato de los Logs

Cada entrada de log tiene el siguiente formato:

```
[YYYY-MM-DD HH:MM:SS.mmm] [NIVEL] Mensaje
```

Donde:
- `YYYY-MM-DD HH:MM:SS.mmm` es la fecha y hora con milisegundos
- `NIVEL` puede ser: `STDOUT`, `STDERR`, `INFO`, `WARNING`, `ERROR`, `DEBUG`

## 🔍 Ejemplo de Log

```
[2025-12-27 19:30:45.123] [STDOUT] Starting Audio Loop...
[2025-12-27 19:30:45.456] [INFO] AudioLoop initialized successfully.
[2025-12-27 19:30:45.789] [ERROR] Failed to connect to printer: Connection timeout
[2025-12-27 19:30:46.012] [WARNING] Retrying connection in 5 seconds...
```

## 🛠️ Componentes del Sistema de Logging

### 1. Backend Python (`backend/logger.py`)

El logger de Python intercepta `sys.stdout` y `sys.stderr` para capturar toda la salida del backend.

**Inicialización automática:** El logger se inicializa automáticamente al inicio de [`backend/server.py`](backend/server.py).

**Uso programático:**
```python
from logger import get_logger

logger = get_logger()
logger.info("Mensaje de información")
logger.error("Mensaje de error")
logger.warning("Mensaje de advertencia")
logger.debug("Mensaje de debug")
```

### 2. Electron Main Process (`electron/logger.js`)

El logger de Electron intercepta `console.log`, `console.error`, `console.warn`, `console.info` y `console.debug`.

**Inicialización automática:** El logger se inicializa automáticamente al inicio de [`electron/main.js`](electron/main.js).

**Uso programático:**
```javascript
const { getLogger } = require('./logger');

const logger = getLogger();
logger.info('Mensaje de información');
logger.error('Mensaje de error');
logger.warning('Mensaje de advertencia');
logger.debug('Mensaje de debug');
```

### 3. Script Wrapper (`start-with-logging.js`)

Script que envuelve la ejecución del entorno de desarrollo y captura toda la salida de los procesos hijos.

## 📂 Estructura de Archivos

```
ada_v2/
├── logs/                          # Directorio de logs (creado automáticamente)
│   ├── ada_backend_20251227.log   # Logs del backend
│   ├── ada_electron_20251227.log  # Logs de Electron
│   └── ada_dev_20251227.log       # Logs del script de desarrollo
├── backend/
│   ├── server.py                  # Inicializa el logger de Python
│   └── logger.py                  # Sistema de logging de Python
├── electron/
│   ├── main.js                    # Inicializa el logger de Electron
│   └── logger.js                  # Sistema de logging de Electron
├── start-with-logging.js          # Script wrapper para desarrollo
├── package.json                   # Scripts npm
└── LOGGING_README.md              # Este archivo
```

## 🔧 Configuración

### Cambiar el directorio de logs

**Python (`backend/server.py`):**
```python
from logger import init_logger
init_logger(log_dir="../mi_directorio_logs", log_file_prefix="mi_backend")
```

**Electron (`electron/main.js`):**
```javascript
const { initLogger } = require('./logger');
initLogger('mi_directorio_logs', 'mi_electron');
```

**Script Wrapper (`start-with-logging.js`):**
```javascript
const logger = new ProcessLogger('mi_directorio_logs', 'mi_dev');
```

## 📊 Niveles de Log

| Nivel | Descripción |
|-------|-------------|
| `STDOUT` | Salida estándar del proceso |
| `STDERR` | Salida de error del proceso |
| `INFO` | Información general |
| `WARNING` | Advertencias |
| `ERROR` | Errores |
| `DEBUG` | Información de depuración |

## 🔄 Rotación de Logs

Los logs se rotan diariamente. Cada día se crea un nuevo archivo de log con la fecha correspondiente en el nombre. Los archivos de logs antiguos no se eliminan automáticamente, por lo que debes gestionarlos manualmente según tus necesidades.

## 🧹 Limpieza de Logs

Para eliminar logs antiguos:

**Windows (PowerShell):**
```powershell
# Eliminar logs de hace más de 7 días
Get-ChildItem logs\*.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item
```

**Linux/Mac:**
```bash
# Eliminar logs de hace más de 7 días
find logs/ -name "*.log" -mtime +7 -delete
```

## 🐛 Debugging con Logs

Cuando encuentres un error:

1. Abre el archivo de log correspondiente en el directorio `logs/`
2. Busca el timestamp aproximado del error
3. Revisa los mensajes de `ERROR` y `STDERR` alrededor de ese timestamp
4. Los mensajes de `DEBUG` pueden proporcionar contexto adicional

## ⚠️ Notas Importantes

- El directorio `logs/` está excluido del control de versiones en [`.gitignore`](.gitignore)
- Los logs se crean automáticamente cuando se inicia la aplicación
- El sistema de logging no afecta el rendimiento de la aplicación
- Los timestamps están en la zona horaria local del sistema

## 📞 Soporte

Si encuentras problemas con el sistema de logging, revisa los archivos de log para obtener información detallada sobre cualquier error que pueda ocurrir.
