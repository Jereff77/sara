import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Camera, User, CheckCircle, XCircle, ArrowRight, ArrowLeft, RotateCcw, X } from 'lucide-react';

const BiometricCapture = ({ socket, onComplete, onCancel }) => {
    console.log('[BIOMETRIC DEBUG] BiometricCapture renderizado - Props:', {
        socket: !!socket,
        socketConnected: socket?.connected,
        onComplete: !!onComplete,
        onCancel: !!onCancel
    });
    
    // Estados principales
    const [step, setStep] = useState('welcome');
    const [frameSrc, setFrameSrc] = useState(null);
    const [faceDetected, setFaceDetected] = useState(false);
    const [capturedImage, setCapturedImage] = useState(null);
    const [progress, setProgress] = useState(0);
    const [isCapturing, setIsCapturing] = useState(false);
    
    // Log cuando cambian los estados principales
    console.log('[BIOMETRIC DEBUG] Estado actual:', { step, isCapturing, faceDetected, progress });

    // Refs para evitar closures obsoletos
    const stepRef = useRef(step);
    const faceDetectedRef = useRef(faceDetected);
    const capturedImageRef = useRef(capturedImage);
    const progressRef = useRef(progress);
    const isCapturingRef = useRef(isCapturing);

    // Actualizar refs cuando cambian los estados
    useEffect(() => {
        stepRef.current = step;
        faceDetectedRef.current = faceDetected;
        capturedImageRef.current = capturedImage;
        progressRef.current = progress;
        isCapturingRef.current = isCapturing;
    }, [step, faceDetected, capturedImage, progress, isCapturing]);

    // Manejo de eventos de Socket.io
    useEffect(() => {
        console.log('[BIOMETRIC DEBUG] useEffect socket llamado - INICIO');
        console.log('[BIOMETRIC DEBUG] Socket disponible:', !!socket);
        console.log('[BIOMETRIC DEBUG] Socket conectado:', socket?.connected);
        console.log('[BIOMETRIC DEBUG] Socket ID:', socket?.id);
        
        if (!socket) {
            console.log('[BIOMETRIC DEBUG] Socket es null, saliendo del useEffect');
            return;
        }
        
        console.log('[BIOMETRIC DEBUG] Configurando listeners de socket...');

        const handleBiometricFrame = (data) => {
            console.log('[BIOMETRIC DEBUG] biometric_frame recibido');
            setFrameSrc(`data:image/jpeg;base64,${data.image}`);
        };

        const handleFaceDetected = (data) => {
            console.log('[BIOMETRIC DEBUG] face_detected recibido:', data);
            setFaceDetected(data.detected);
        };

        const handleBiometricStatus = (data) => {
            console.log('[BIOMETRIC DEBUG] biometric_status recibido:', data);
        };

        socket.on('biometric_frame', handleBiometricFrame);
        socket.on('face_detected', handleFaceDetected);
        socket.on('biometric_status', handleBiometricStatus);

        return () => {
            console.log('[BIOMETRIC DEBUG] Limpiando listeners de socket - INICIO');
            socket.off('biometric_frame', handleBiometricFrame);
            socket.off('face_detected', handleFaceDetected);
            socket.off('biometric_status', handleBiometricStatus);
            console.log('[BIOMETRIC DEBUG] Listeners limpiados correctamente');
        };
    }, [socket]);

    // Enviar comandos al backend
    const sendCommand = (command, data = {}) => {
        console.log('[BIOMETRIC DEBUG] sendCommand llamado - INICIO:', { command, data, socketConnected: socket?.connected });
        
        if (!socket) {
            console.error('[BIOMETRIC DEBUG] ERROR: Socket es null o undefined');
            return;
        }
        
        if (!socket.connected) {
            console.error('[BIOMETRIC DEBUG] ERROR: Socket no está conectado. Socket.connected:', socket.connected);
            console.error('[BIOMETRIC DEBUG] Socket ID:', socket.id);
            console.error('[BIOMETRIC DEBUG] Socket status:', socket.readyState);
            return;
        }
        
        try {
            console.log('[BIOMETRIC DEBUG] Enviando comando al backend:', command, data);
            socket.emit('biometric_command', { command, ...data }, (response) => {
                console.log('[BIOMETRIC DEBUG] Respuesta del backend:', response);
            });
            console.log('[BIOMETRIC DEBUG] Comando emitido correctamente');
        } catch (error) {
            console.error('[BIOMETRIC DEBUG] Error al emitir comando:', error);
        }
    };

    // Iniciar captura
    const startCapture = () => {
        console.log('[BIOMETRIC DEBUG] startCapture llamado - INICIO');
        console.log('[BIOMETRIC DEBUG] Estado actual:', { step, isCapturing, socketConnected: socket?.connected });
        
        try {
            console.log('[BIOMETRIC DEBUG] Actualizando step a capture_frontal...');
            setStep('capture_frontal');
            console.log('[BIOMETRIC DEBUG] Step actualizado correctamente');
            
            console.log('[BIOMETRIC DEBUG] Actualizando isCapturing a true...');
            setIsCapturing(true);
            console.log('[BIOMETRIC DEBUG] isCapturing actualizado correctamente');
            
            console.log('[BIOMETRIC DEBUG] Enviando comando start_capture...');
            sendCommand('start_capture', { angle: 'frontal' });
            console.log('[BIOMETRIC DEBUG] Comando enviado correctamente');
        } catch (error) {
            console.error('[BIOMETRIC DEBUG] Error en startCapture():', error);
        }
    };

    // Capturar foto actual
    const capturePhoto = () => {
        if (frameSrc) {
            setCapturedImage(frameSrc);
            setStep('confirm');
            setIsCapturing(false);
            sendCommand('capture_photo', { 
                angle: stepRef.current.replace('capture_', ''),
                image: frameSrc 
            });
        }
    };

    // Confirmar foto y continuar
    const confirmPhoto = () => {
        const newProgress = progressRef.current + 1;
        setProgress(newProgress);

        if (newProgress >= 3) {
            // Completar todas las capturas
            setStep('success');
            sendCommand('complete_capture');
            setTimeout(() => {
                if (onComplete) onComplete();
            }, 2000);
        } else {
            // Continuar al siguiente ángulo
            const nextStep = newProgress === 1 ? 'capture_izquierda' : 'capture_derecha';
            setStep(nextStep);
            setIsCapturing(true);
            setCapturedImage(null);
            const angle = nextStep.replace('capture_', '');
            sendCommand('start_capture', { angle });
        }
    };

    // Retomar foto
    const retakePhoto = () => {
        setCapturedImage(null);
        setStep(stepRef.current);
        setIsCapturing(true);
        const angle = stepRef.current.replace('capture_', '');
        sendCommand('start_capture', { angle });
    };

    // Cancelar captura
    const handleCancel = () => {
        console.log('[BIOMETRIC DEBUG] handleCancel llamado - INICIO');
        console.log('[BIOMETRIC DEBUG] Estado actual:', { step, isCapturing, socketConnected: socket?.connected });
        
        try {
            console.log('[BIOMETRIC DEBUG] Enviando comando cancel_capture...');
            sendCommand('cancel_capture');
            console.log('[BIOMETRIC DEBUG] Comando cancel_capture enviado correctamente');
            
            if (onCancel) {
                console.log('[BIOMETRIC DEBUG] Ejecutando callback onCancel');
                onCancel();
                console.log('[BIOMETRIC DEBUG] Callback onCancel ejecutado correctamente');
            } else {
                console.log('[BIOMETRIC DEBUG] WARNING: onCancel es null o undefined');
            }
        } catch (error) {
            console.error('[BIOMETRIC DEBUG] Error en handleCancel():', error);
        }
    };

    // Obtener información del paso actual
    const getStepInfo = () => {
        switch (step) {
            case 'welcome':
                return {
                    title: 'GENERADOR DE PERFIL BIOMÉTRICO',
                    subtitle: 'Captura tu rostro desde 3 ángulos',
                    instructions: [
                        'Este proceso capturará 3 fotos de tu rostro',
                        'desde diferentes ángulos para mejorar',
                        'la precisión del reconocimiento facial.'
                    ],
                    requirements: [
                        'Buena iluminación',
                        'Rostro completo visible',
                        'Seguir las instrucciones'
                    ]
                };
            case 'capture_frontal':
                return {
                    title: 'ÁNGULO 1/3: FRONTAL',
                    subtitle: 'Mira directamente a la cámara',
                    instructions: 'Centra tu rostro en el círculo guía'
                };
            case 'capture_izquierda':
                return {
                    title: 'ÁNGULO 2/3: IZQUIERDA',
                    subtitle: 'Gira hacia la izquierda',
                    instructions: 'Gira tu rostro ligeramente hacia la izquierda (45° aprox)'
                };
            case 'capture_derecha':
                return {
                    title: 'ÁNGULO 3/3: DERECHA',
                    subtitle: 'Gira hacia la derecha',
                    instructions: 'Gira tu rostro ligeramente hacia la derecha (45° aprox)'
                };
            case 'confirm':
                return {
                    title: 'CONFIRMAR CAPTURA',
                    subtitle: 'Revisa la imagen capturada'
                };
            case 'success':
                return {
                    title: '¡PERFIL GENERADO!',
                    subtitle: 'Captura completada exitosamente'
                };
            default:
                return {};
        }
    };

    const stepInfo = getStepInfo();

    // Componente de barra de progreso
    const ProgressBar = ({ current, total }) => (
        <div className="w-full max-w-md">
            <div className="flex justify-between text-cyan-300 text-sm mb-2 font-mono">
                <span>PROGRESO</span>
                <span>{current}/{total}</span>
            </div>
            <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(current / total) * 100}%` }}
                    transition={{ duration: 0.5 }}
                    className="h-full bg-gradient-to-r from-cyan-500 to-cyan-300 shadow-[0_0_10px_rgba(34,211,238,0.5)]"
                />
            </div>
        </div>
    );

    // Componente de guía de rostro
    const FaceGuide = () => (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <motion.div
                animate={{
                    scale: faceDetected ? [1, 1.05, 1] : 1,
                    borderColor: faceDetected ? 'rgba(34, 197, 94, 0.8)' : 'rgba(34, 211, 238, 0.5)'
                }}
                transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                }}
                className="w-48 h-48 rounded-full border-2 relative"
            >
                {/* Líneas de guía */}
                <div className="absolute top-1/2 left-0 w-full h-px bg-current opacity-30" />
                <div className="absolute left-1/2 top-0 h-full w-px bg-current opacity-30" />
                
                {/* Indicador de detección */}
                {faceDetected && (
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute -top-2 -right-2"
                    >
                        <CheckCircle size={24} className="text-green-500 drop-shadow-[0_0_10px_rgba(34,197,94,0.8)]" />
                    </motion.div>
                )}
            </motion.div>
        </div>
    );

    // Componente de botón estilizado
    const StyledButton = ({ onClick, children, variant = 'primary', icon: Icon }) => (
        <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onClick}
            className={`
                flex items-center gap-2 px-6 py-3 rounded-lg font-mono text-sm tracking-wider
                transition-all duration-300 border-2
                ${variant === 'primary' 
                    ? 'bg-cyan-500/20 border-cyan-500 text-cyan-300 hover:bg-cyan-500/30 hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]' 
                    : variant === 'secondary'
                    ? 'bg-gray-800/50 border-gray-600 text-gray-300 hover:bg-gray-700/50'
                    : 'bg-red-500/20 border-red-500 text-red-300 hover:bg-red-500/30 hover:shadow-[0_0_20px_rgba(239,68,68,0.4)]'
                }
            `}
        >
            {Icon && <Icon size={18} />}
            {children}
        </motion.button>
    );

    return (
        <div className="fixed inset-0 z-[9999] bg-black flex flex-col items-center justify-center font-mono select-none overflow-hidden">
            {/* Background Grid */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-cyan-900/20 via-black to-black pointer-events-none" />
            
            {/* Grid Pattern */}
            <div className="absolute inset-0 opacity-10 pointer-events-none">
                <div className="absolute inset-0" style={{
                    backgroundImage: `
                        linear-gradient(rgba(34, 211, 238, 0.1) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(34, 211, 238, 0.1) 1px, transparent 1px)
                    `,
                    backgroundSize: '50px 50px'
                }} />
            </div>

            <AnimatePresence mode="wait">
                {/* Pantalla de Bienvenida */}
                {step === 'welcome' && (
                    <motion.div
                        key="welcome"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.5 }}
                        className="relative flex flex-col items-center gap-8 p-10 border border-cyan-500/30 rounded-lg bg-black/80 backdrop-blur-xl shadow-[0_0_50px_rgba(34,211,238,0.2)] max-w-2xl mx-4"
                    >
                        <div className="text-center">
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                                className="flex items-center justify-center gap-4 mb-4"
                            >
                                <Camera size={48} className="text-cyan-400" />
                            </motion.div>
                            <h1 className="text-3xl font-bold tracking-[0.3em] uppercase text-cyan-400 drop-shadow-[0_0_10px_rgba(34,211,238,0.8)]">
                                {stepInfo.title}
                            </h1>
                            <p className="text-cyan-200/70 mt-2 text-lg">{stepInfo.subtitle}</p>
                        </div>

                        <div className="w-full border-t border-cyan-500/20 pt-6">
                            <p className="text-cyan-300 text-center mb-4 tracking-wider">INSTRUCCIONES</p>
                            <div className="space-y-3 text-gray-300">
                                {stepInfo.instructions.map((instruction, i) => (
                                    <motion.p
                                        key={i}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: 0.3 + i * 0.1 }}
                                        className="text-center"
                                    >
                                        {instruction}
                                    </motion.p>
                                ))}
                            </div>
                        </div>

                        <div className="w-full border-t border-cyan-500/20 pt-6">
                            <p className="text-cyan-300 text-center mb-4 tracking-wider">ASEGÚRATE DE:</p>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {stepInfo.requirements.map((req, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.5 + i * 0.1 }}
                                        className="flex items-center gap-2 text-green-400 text-sm"
                                    >
                                        <CheckCircle size={16} />
                                        {req}
                                    </motion.div>
                                ))}
                            </div>
                        </div>

                        <div className="flex gap-4 mt-4">
                            <StyledButton
                                onClick={() => {
                                    console.log('[BIOMETRIC DEBUG] Botón COMENZAR presionado - INICIO');
                                    console.log('[BIOMETRIC DEBUG] Estado actual:', { step, isCapturing, socketConnected: socket?.connected });
                                    try {
                                        startCapture();
                                        console.log('[BIOMETRIC DEBUG] startCapture() ejecutado correctamente');
                                    } catch (error) {
                                        console.error('[BIOMETRIC DEBUG] Error en startCapture():', error);
                                    }
                                }}
                                icon={Camera}
                            >
                                COMENZAR
                            </StyledButton>
                            <StyledButton
                                onClick={() => {
                                    console.log('[BIOMETRIC DEBUG] Botón CANCELAR presionado - INICIO');
                                    console.log('[BIOMETRIC DEBUG] Estado actual:', { step, isCapturing, socketConnected: socket?.connected });
                                    try {
                                        handleCancel();
                                        console.log('[BIOMETRIC DEBUG] handleCancel() ejecutado correctamente');
                                    } catch (error) {
                                        console.error('[BIOMETRIC DEBUG] Error en handleCancel():', error);
                                    }
                                }}
                                variant="danger"
                                icon={X}
                            >
                                CANCELAR
                            </StyledButton>
                        </div>
                    </motion.div>
                )}

                {/* Pantallas de Captura */}
                {(step.startsWith('capture_') || step === 'confirm') && (
                    <motion.div
                        key="capture"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 1.05 }}
                        transition={{ duration: 0.5 }}
                        className="relative flex flex-col items-center gap-6 p-8 border border-cyan-500/30 rounded-lg bg-black/80 backdrop-blur-xl shadow-[0_0_50px_rgba(34,211,238,0.2)] max-w-3xl mx-4"
                    >
                        {/* Header */}
                        <div className="text-center">
                            <h2 className="text-2xl font-bold tracking-[0.2em] uppercase text-cyan-400 drop-shadow-[0_0_10px_rgba(34,211,238,0.8)]">
                                {stepInfo.title}
                            </h2>
                            <p className="text-cyan-200/70 mt-2">{stepInfo.subtitle}</p>
                        </div>

                        {/* Barra de Progreso */}
                        <ProgressBar current={progress} total={3} />

                        {/* Contenedor de Video/Foto */}
                        <div className="relative w-80 h-80 border-2 border-cyan-500/50 rounded-lg overflow-hidden bg-gray-900 shadow-inner">
                            {step === 'confirm' && capturedImage ? (
                                // Vista previa de la foto capturada
                                <img
                                    src={capturedImage}
                                    alt="Captured"
                                    className="w-full h-full object-cover transform scale-x-[-1]"
                                />
                            ) : frameSrc ? (
                                // Streaming de video
                                <>
                                    <img
                                        src={frameSrc}
                                        alt="Camera Feed"
                                        className="w-full h-full object-cover transform scale-x-[-1]"
                                    />
                                    <FaceGuide />
                                    
                                    {/* Indicador de detección */}
                                    <div className="absolute bottom-4 left-4 right-4 flex items-center justify-center gap-2">
                                        {faceDetected ? (
                                            <motion.div
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                className="flex items-center gap-2 text-green-400 text-sm bg-black/70 px-3 py-1 rounded-full"
                                            >
                                                <CheckCircle size={16} />
                                                <span>ROSTRO DETECTADO</span>
                                            </motion.div>
                                        ) : (
                                            <motion.div
                                                animate={{ opacity: [0.5, 1, 0.5] }}
                                                transition={{ duration: 1.5, repeat: Infinity }}
                                                className="flex items-center gap-2 text-yellow-400 text-sm bg-black/70 px-3 py-1 rounded-full"
                                            >
                                                <User size={16} />
                                                <span>Buscando rostro...</span>
                                            </motion.div>
                                        )}
                                    </div>
                                </>
                            ) : (
                                // Estado de carga
                                <div className="w-full h-full flex items-center justify-center">
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                                    >
                                        <Camera size={64} className="text-cyan-800 animate-pulse" />
                                    </motion.div>
                                </div>
                            )}
                        </div>

                        {/* Instrucciones */}
                        {step !== 'confirm' && (
                            <p className="text-cyan-300 text-center text-sm tracking-wider">
                                {stepInfo.instructions}
                            </p>
                        )}

                        {/* Botones de acción */}
                        <div className="flex gap-4">
                            {step === 'confirm' ? (
                                <>
                                    <StyledButton onClick={retakePhoto} variant="secondary" icon={RotateCcw}>
                                        RETOMAR
                                    </StyledButton>
                                    <StyledButton onClick={confirmPhoto} icon={CheckCircle}>
                                        CONFIRMAR
                                    </StyledButton>
                                </>
                            ) : (
                                <>
                                    <StyledButton 
                                        onClick={capturePhoto} 
                                        disabled={!faceDetected}
                                        icon={Camera}
                                    >
                                        CAPTURAR
                                    </StyledButton>
                                    <StyledButton onClick={handleCancel} variant="danger" icon={X}>
                                        CANCELAR
                                    </StyledButton>
                                </>
                            )}
                        </div>
                    </motion.div>
                )}

                {/* Pantalla de Éxito */}
                {step === 'success' && (
                    <motion.div
                        key="success"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 1.1 }}
                        transition={{ duration: 0.5 }}
                        className="relative flex flex-col items-center gap-8 p-10 border border-green-500/30 rounded-lg bg-black/80 backdrop-blur-xl shadow-[0_0_50px_rgba(34,197,94,0.2)] max-w-md mx-4"
                    >
                        <motion.div
                            initial={{ scale: 0, rotate: -180 }}
                            animate={{ scale: 1, rotate: 0 }}
                            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                            className="relative"
                        >
                            <motion.div
                                animate={{ scale: [1, 1.2, 1] }}
                                transition={{ duration: 1, repeat: Infinity }}
                            >
                                <CheckCircle size={96} className="text-green-500 drop-shadow-[0_0_30px_rgba(34,197,94,0.8)]" />
                            </motion.div>
                        </motion.div>

                        <div className="text-center">
                            <h2 className="text-3xl font-bold tracking-[0.2em] uppercase text-green-400 drop-shadow-[0_0_10px_rgba(34,197,94,0.8)]">
                                {stepInfo.title}
                            </h2>
                            <p className="text-green-200/70 mt-4 text-lg">
                                Tu perfil biométrico ha sido generado exitosamente.
                            </p>
                        </div>

                        <div className="w-full border-t border-green-500/20 pt-6">
                            <div className="grid grid-cols-2 gap-4 text-center">
                                <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/30">
                                    <p className="text-green-400 text-2xl font-bold">3</p>
                                    <p className="text-green-300/70 text-sm">Fotos capturadas</p>
                                </div>
                                <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/30">
                                    <p className="text-green-400 text-2xl font-bold">100%</p>
                                    <p className="text-green-300/70 text-sm">Completado</p>
                                </div>
                            </div>
                        </div>

                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="text-green-300 text-sm animate-pulse"
                        >
                            Redirigiendo...
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default BiometricCapture;
