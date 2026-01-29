/**
 * Script wrapper para capturar toda la salida de consola con logging.
 * Ejecuta el comando de desarrollo y captura toda su salida en archivos de log.
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class ProcessLogger {
    constructor(logDir = 'logs', logFilePrefix = 'ada_dev') {
        this.logDir = path.join(__dirname, logDir);
        this.logFilePrefix = logFilePrefix;
        
        // Crear directorio de logs si no existe
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
        
        // Generar nombre de archivo con fecha
        const date = new Date();
        const dateStr = date.toISOString().split('T')[0].replace(/-/g, '');
        this.logFile = path.join(this.logDir, `${logFilePrefix}_${dateStr}.log`);
        
        // Log inicial
        this._writeLog('='.repeat(80), 'INFO');
        this._writeLog('Iniciando sesión de desarrollo con logging activado', 'INFO');
        this._writeLog(`Archivo de log: ${this.logFile}`, 'INFO');
        this._writeLog('='.repeat(80), 'INFO');
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
            console.error(`Error writing to log: ${error.message}`);
        }
    }
    
    runCommand(command, args = []) {
        this._writeLog(`Ejecutando comando: ${command} ${args.join(' ')}`, 'INFO');
        this._writeLog('='.repeat(80), 'INFO');
        
        const child = spawn(command, args, {
            stdio: 'inherit',
            shell: process.platform === 'win32'
        });
        
        child.on('error', (error) => {
            this._writeLog(`Error ejecutando comando: ${error.message}`, 'ERROR');
            console.error(`Error ejecutando comando: ${error.message}`);
        });
        
        child.on('exit', (code, signal) => {
            const exitMsg = `Proceso terminado con código: ${code}, señal: ${signal}`;
            this._writeLog(exitMsg, 'INFO');
            this._writeLog('='.repeat(80), 'INFO');
            console.log(exitMsg);
        });
        
        return child;
    }
    
    runConcurrently() {
        // Ejecutar el comando original de dev
        this._writeLog('Iniciando entorno de desarrollo...', 'INFO');
        
        // Usar el formato correcto para wait-on (tcp:host:port)
        const child = this.runCommand('npx', ['concurrently', '-k', 'vite', 'wait-on tcp:localhost:5173 && npx electron .']);
        
        return child;
    }
}

// Iniciar el logger y ejecutar el comando
const logger = new ProcessLogger('logs', 'ada_dev');
const childProcess = logger.runConcurrently();

// Manejar la terminación del script
process.on('SIGINT', () => {
    logger._writeLog('Recibido SIGINT, terminando...', 'INFO');
    childProcess.kill();
    process.exit(0);
});

process.on('SIGTERM', () => {
    logger._writeLog('Recibido SIGTERM, terminando...', 'INFO');
    childProcess.kill();
    process.exit(0);
});
