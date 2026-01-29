# AGENTS.md - Guía de Desarrollo para S.A.R.A V2

## Comandos de Build, Test y Desarrollo

### Frontend (React + Electron)
```bash
npm run dev              # Iniciar servidor de desarrollo (backend auto-iniciado)
npm run dev:log          # Iniciar con logging detallado (directorio logs/)
npm run build            # Build de producción
npm start                # Lanzar aplicación Electron
```

### Backend (Python)
```bash
python backend/server.py  # Ejecutar servidor backend separado (puerto 8000)
```

### Testing (Python)
```bash
pytest                           # Ejecutar todos los tests
pytest tests/                     # Ejecutar tests en directorio tests/
pytest tests/test_authenticator.py  # Ejecutar archivo de test específico
pytest tests/test_authenticator.py::TestAuthenticatorInit::test_authenticator_creation  # Test específico
pytest -v                        # Salida verbose
pytest -x                        # Detener en primer fallo
pytest --tb=short                # Traceback más corto
```

## Guías de Estilo de Código

### Frontend (React/JSX)
**Nomenclatura:** Componentes PascalCase (ej: `ChatModule.jsx`) en `src/components/`

**Orden de Imports:** React hooks → librerías externas → componentes locales

**Estructura:** Componentes funcionales con hooks, destructurar props en firma, usar refs para evitar closure staleness en operaciones async, limpiar efectos en cleanup de useEffect

**Gestión de Estado:** `useState` para estado simple, `useRef` para valores que no deben causar re-renders, sincronizar refs cuando cambia estado

**Estilos:** Clases Tailwind CSS, preferir Tailwind sobre inline, usar backdrop-blur/border para glassmorphism, diseño responsive mobile-first

**Socket.IO:** Emitir eventos con `socket.emit()`, escuchar con `useEffect()` y limpiar listeners en return

### Backend (Python)
**Nomenclatura:** Módulos `lowercase_with_underscores`, clases PascalCase, tests `test_*.py` en `tests/`

**Orden de Imports:** Librería estándar → terceros → imports locales

**Async/Await:** Usar async/await en todo código (FastAPI + Socket.IO), todos handlers Socket.IO async, usar `asyncio.create_task()` para operaciones fire-and-forget

**Estructura de Clases:** Docstrings para clase y métodos, constructor con descripción de parámetros

**Manejo de Errores:** Try/except en eventos socket, emitir errores al frontend, usar prints con prefijos de módulo: `print("[MODULE] Mensaje")`

**Logging:** Inicializar `from logger import init_logger; init_logger(...)` al nivel de módulo, errores críticos emitir al frontend

**Eventos Socket.IO:** Handlers decorados con `@sio.event`, siempre envolver en try/except

### Testing (pytest)
**Nomenclatura:** Archivos `test_*.py`, clases `Test*`, funciones `test_*`

**Estructura:** Docstring de módulo, agrupar tests en clases, usar fixtures para setup/cleanup

**Tests Condicionales:** `pytestmark = pytest.mark.skipif(condition, reason="...")`

## Estructura del Proyecto
```
ada_v2/
├── src/              # Frontend React (App.jsx, components/)
├── backend/          # Backend Python (server.py, agentes)
├── tests/            # Tests Python (test_*.py)
├── electron/         # Proceso principal Electron
├── logs/             # Logs runtime (auto-generados)
├── package.json      # Dependencias Node.js
├── requirements.txt  # Dependencias Python
└── pytest.ini       # Config tests (asyncio_mode=auto)
```

## Configuración
**Frontend:** Vite (puerto 5173), Tailwind CSS, sin ESLint/Prettier

**Backend:** Python 3.11, settings en `backend/settings.json`, pytest con `asyncio_mode=auto`

**Entorno:** API keys en `.env` (ej: `GEMINI_API_KEY=xxx`), usar plantilla `.env.example`

## Patrones Comunes
**Comunicación Bidireccional:** Frontend emite → handler async backend → backend responde vía socket

**Manejo de Dispositivos:** Solicitar permisos antes de cámara/micrófono, persistir selección en localStorage

**Recuperación de Errores:** Siempre envolver eventos socket en try/except, emitir errores al frontend

## Tips de Desarrollo
1. Usar `npm run dev:log` para logs detallados
2. Vite tiene HMR, Electron requiere reinicio
3. Verificar permisos de cámara en System Settings (macOS)
4. Backend asume ejecución desde directorio `ada_v2/`
5. Asegurar backend en puerto 8000 antes de frontend

## Sin Herramientas de Linting/Formatting
Este proyecto no usa ESLint, Prettier, Black u herramientas similares. Siga las convenciones documentadas arriba.
