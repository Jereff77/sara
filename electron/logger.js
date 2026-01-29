/**
 * Sistema de logging para el proceso principal de Electron.
 * Captura toda la salida de consola con fecha y hora.
 */

const fs = require('fs');
const path = require('path');

class ElectronLogger {
    constructor(logDir = 'logs', logFilePrefix = 'ada_electron') {
        this.logDir = path.join(__dirname, '..', logDir);
        this.logFilePrefix = logFilePrefix;
        
        // Crear directorio de logs si no existe
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
        
        // Generar nombre de archivo con fecha
        const date = new Date();
        const dateStr = date.toISOString().split('T')[0].replace(/-/g, '');
        this.logFile = path.join(this.logDir, `${logFilePrefix}_${dateStr}.log`);
        
        // Guardar las funciones originales de console
        this.originalConsole = {
            log: console.log,
            error: console.error,
            warn: console.warn,
            info: console.info,
            debug: console.debug
        };
        
        // Inicializar el logger
        this._setupLogging();
    }
    
    _getTimestamp() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const ms = String(now.getMilliseconds()).padStart(3, '0');
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}.${ms}`;
    }
    
    _writeLog(message, level = 'INFO') {
        const timestamp = this._getTimestamp();
        const logLine = `[${timestamp}] [${level}] ${message}\n`;
        
        try {
            fs.appendFileSync(this.logFile, logLine, 'utf-8');
        } catch (error) {
            // Si falla escribir al archivo, al menos imprimir a la consola original
            this.originalConsole.error(`Error writing to log: ${error.message}`);
        }
    }
    
    _setupLogging() {
        // Log inicial
        this._writeLog('='.repeat(80), 'INFO');
        this._writeLog('Logger inicializado. Capturando console.log, console.error, etc.', 'INFO');
        this._writeLog(`Archivo de log: ${this.logFile}`, 'INFO');
        this._writeLog('='.repeat(80), 'INFO');
        
        // Sobrescribir console.log
        console.log = (...args) => {
            const message = args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
            ).join(' ');
            this.originalConsole.log(...args);
            this._writeLog(message, 'STDOUT');
        };
        
        // Sobrescribir console.error
        console.error = (...args) => {
            const message = args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
            ).join(' ');
            this.originalConsole.error(...args);
            this._writeLog(message, 'STDERR');
        };
        
        // Sobrescribir console.warn
        console.warn = (...args) => {
            const message = args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
            ).join(' ');
            this.originalConsole.warn(...args);
            this._writeLog(message, 'WARNING');
        };
        
        // Sobrescribir console.info
        console.info = (...args) => {
            const message = args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
            ).join(' ');
            this.originalConsole.info(...args);
            this._writeLog(message, 'INFO');
        };
        
        // Sobrescribir console.debug
        console.debug = (...args) => {
            const message = args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
            ).join(' ');
            this.originalConsole.debug(...args);
            this._writeLog(message, 'DEBUG');
        };
    }
    
    info(message) {
        this._writeLog(message, 'INFO');
    }
    
    error(message) {
        this._writeLog(message, 'ERROR');
    }
    
    warning(message) {
        this._writeLog(message, 'WARNING');
    }
    
    debug(message) {
        this._writeLog(message, 'DEBUG');
    }
    
    restoreOriginalConsole() {
        console.log = this.originalConsole.log;
        console.error = this.originalConsole.error;
        console.warn = this.originalConsole.warn;
        console.info = this.originalConsole.info;
        console.debug = this.originalConsole.debug;
        this._writeLog('Consola original restaurada.', 'INFO');
    }
}

// Instancia global del logger
let _loggerInstance = null;

function initLogger(logDir = 'logs', logFilePrefix = 'ada_electron') {
    if (_loggerInstance === null) {
        _loggerInstance = new ElectronLogger(logDir, logFilePrefix);
    }
    return _loggerInstance;
}

function getLogger() {
    return _loggerInstance;
}

module.exports = {
    ElectronLogger,
    initLogger,
    getLogger
};
