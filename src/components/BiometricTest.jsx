import React, { useState } from 'react';

const BiometricTest = ({ socket, onComplete, onCancel }) => {
    const [testState, setTestState] = useState('initial');
    const [logs, setLogs] = useState([]);

    const addLog = (message) => {
        const timestamp = new Date().toLocaleTimeString();
        setLogs(prev => [...prev, `${timestamp}: ${message}`]);
        console.log(`[BIOMETRIC TEST] ${timestamp}: ${message}`);
    };

    const testSocketConnection = () => {
        addLog('=== INICIANDO PRUEBA DE SOCKET ===');
        addLog(`Socket disponible: ${!!socket}`);
        addLog(`Socket conectado: ${socket?.connected}`);
        addLog(`Socket ID: ${socket?.id || 'N/A'}`);
        
        if (socket && socket.connected) {
            addLog('Enviando mensaje de prueba...');
            socket.emit('test_message', { test: 'biometric_test' }, (response) => {
                addLog(`Respuesta del servidor: ${JSON.stringify(response)}`);
            });
        } else {
            addLog('ERROR: Socket no disponible o no conectado');
        }
    };

    const testReactState = () => {
        addLog('=== INICIANDO PRUEBA DE ESTADO REACT ===');
        addLog(`Estado actual: ${testState}`);
        
        try {
            setTestState('updated');
            addLog('Estado actualizado correctamente');
            
            setTimeout(() => {
                addLog(`Estado después de timeout: ${testState}`);
            }, 100);
        } catch (error) {
            addLog(`ERROR al actualizar estado: ${error.message}`);
        }
    };

    const testCallbacks = () => {
        addLog('=== INICIANDO PRUEBA DE CALLBACKS ===');
        addLog(`onComplete disponible: ${!!onComplete}`);
        addLog(`onCancel disponible: ${!!onCancel}`);
        
        if (onComplete) {
            addLog('Ejecutando onComplete...');
            onComplete();
            addLog('onComplete ejecutado');
        }
        
        if (onCancel) {
            addLog('Ejecutando onCancel...');
            onCancel();
            addLog('onCancel ejecutado');
        }
    };

    const testBiometricCommand = () => {
        addLog('=== INICIANDO PRUEBA DE COMANDO BIOMÉTRICO ===');
        
        if (!socket) {
            addLog('ERROR: Socket no disponible');
            return;
        }
        
        if (!socket.connected) {
            addLog('ERROR: Socket no conectado');
            return;
        }
        
        try {
            socket.emit('biometric_command', { command: 'test_command', test: true }, (response) => {
                addLog(`Respuesta de biometric_command: ${JSON.stringify(response)}`);
            });
            addLog('Comando biometric_command enviado');
        } catch (error) {
            addLog(`ERROR al enviar comando: ${error.message}`);
        }
    };

    return (
        <div className="fixed inset-0 z-[9999] bg-black flex flex-col items-center justify-center font-mono select-none overflow-hidden">
            <div className="bg-gray-900 border border-cyan-500 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
                <h2 className="text-xl font-bold text-cyan-400 mb-4">COMPONENTE DE PRUEVA BIOMÉTRICA</h2>
                
                <div className="grid grid-cols-2 gap-4 mb-6">
                    <button 
                        onClick={testSocketConnection}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                    >
                        Probar Socket
                    </button>
                    
                    <button 
                        onClick={testReactState}
                        className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
                    >
                        Probar Estado React
                    </button>
                    
                    <button 
                        onClick={testCallbacks}
                        className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded"
                    >
                        Probar Callbacks
                    </button>
                    
                    <button 
                        onClick={testBiometricCommand}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded"
                    >
                        Probar Comando Biométrico
                    </button>
                </div>
                
                <div className="bg-black border border-gray-700 rounded p-4">
                    <h3 className="text-sm font-bold text-gray-400 mb-2">LOGS:</h3>
                    <div className="text-xs text-green-400 font-mono space-y-1">
                        {logs.length === 0 ? (
                            <div className="text-gray-500">No hay logs aún...</div>
                        ) : (
                            logs.map((log, index) => (
                                <div key={index}>{log}</div>
                            ))
                        )}
                    </div>
                </div>
                
                <div className="flex gap-4 mt-4">
                    <button 
                        onClick={() => {
                            addLog('Botón COMPLETAR presionado');
                            if (onComplete) onComplete();
                        }}
                        className="bg-cyan-600 hover:bg-cyan-700 text-white px-6 py-2 rounded"
                    >
                        COMPLETAR
                    </button>
                    
                    <button 
                        onClick={() => {
                            addLog('Botón CANCELAR presionado');
                            if (onCancel) onCancel();
                        }}
                        className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded"
                    >
                        CANCELAR
                    </button>
                </div>
            </div>
        </div>
    );
};

export default BiometricTest;