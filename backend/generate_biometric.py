import cv2
import os
import json
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import urllib.request
from datetime import datetime
import base64
import threading
import time

# Colores para el texto (mantenidos para compatibilidad)
COLOR_TEXT = (255, 255, 255)
COLOR_ACCENT = (0, 255, 255)
COLOR_SUCCESS = (0, 255, 0)
COLOR_WARNING = (0, 165, 255)
COLOR_ERROR = (0, 0, 255)

class BiometricGenerator:
    """Genera un perfil biométrico completo con múltiples imágenes desde diferentes ángulos.
    
    Esta versión usa OpenCV para mostrar la interfaz de captura.
    """
    
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")
    PROFILES_DIR = os.path.join(os.path.dirname(__file__), "profiles")
    
    def __init__(self):
        self.landmarker = None
        self._ensure_model()
        self._init_landmarker()
        self._ensure_profiles_dir()
    
    def _ensure_model(self):
        """Descarga el modelo de MediaPipe si no existe."""
        if not os.path.exists(self.MODEL_PATH):
            print(f"[BIOMETRIC] Descargando modelo de Face Landmarker...")
            try:
                urllib.request.urlretrieve(self.MODEL_URL, self.MODEL_PATH)
                print(f"[BIOMETRIC] [OK] Modelo descargado a {self.MODEL_PATH}")
            except Exception as e:
                print(f"[BIOMETRIC] [ERROR] Falló la descarga del modelo: {e}")
                raise
    
    def _init_landmarker(self):
        """Inicializa el detector de landmarks faciales."""
        if not os.path.exists(self.MODEL_PATH):
            print("[BIOMETRIC] [ERROR] Modelo no encontrado. No se puede inicializar.")
            return
        
        try:
            base_options = mp_python.BaseOptions(model_asset_path=self.MODEL_PATH)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=1
            )
            self.landmarker = vision.FaceLandmarker.create_from_options(options)
            print("[BIOMETRIC] [OK] Face Landmarker inicializado.")
        except Exception as e:
            print(f"[BIOMETRIC] [ERROR] Falló la inicialización: {e}")
            raise
    
    def _ensure_profiles_dir(self):
        """Crea el directorio de perfiles si no existe."""
        if not os.path.exists(self.PROFILES_DIR):
            os.makedirs(self.PROFILES_DIR)
            print(f"[BIOMETRIC] [OK] Directorio de perfiles creado: {self.PROFILES_DIR}")
    
    def _extract_landmarks(self, image_rgb):
        """Extrae los landmarks faciales de una imagen RGB."""
        if self.landmarker is None:
            return None
        
        try:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            result = self.landmarker.detect(mp_image)
            
            if result.face_landmarks and len(result.face_landmarks) > 0:
                landmarks = result.face_landmarks[0]
                # Convertir a array numpy de coordenadas (x, y, z)
                coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
                return coords.flatten()
            return None
        except Exception as e:
            print(f"[BIOMETRIC] [ERROR] Extracción de landmarks falló: {e}")
            return None
    
    def _draw_text_centered(self, frame, text, y, font_scale=0.7, color=COLOR_TEXT, thickness=2):
        """Dibuja texto centrado en el frame."""
        h, w = frame.shape[:2]
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        x = (w - text_width) // 2
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
        return text_height
    
    def _draw_text_wrapped(self, frame, text, start_y, max_width, font_scale=0.6, color=COLOR_TEXT, thickness=2):
        """Dibuja texto con ajuste de línea automático."""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            (text_width, _), _ = cv2.getTextSize(test_line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            if text_width < max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())
        
        y = start_y
        for line in lines:
            self._draw_text_centered(frame, line, y, font_scale, color, thickness)
            y += 30  # Espacio entre líneas
        
        return len(lines) * 30
    
    def _draw_header(self, frame, title):
        """Dibuja un encabezado en la parte superior."""
        h, w = frame.shape[:2]
        
        # Fondo del encabezado
        cv2.rectangle(frame, (0, 0), (w, 80), (0, 0, 0), -1)
        cv2.rectangle(frame, (0, 0), (w, 80), COLOR_ACCENT, 2)
        
        # Título
        self._draw_text_centered(frame, title, 30, 1.0, COLOR_ACCENT, 3)
        
        # Subtítulo
        self._draw_text_centered(frame, "GENERADOR DE PERFIL BIOMÉTRICO", 60, 0.5, COLOR_TEXT, 1)
    
    def _draw_footer(self, frame, controls):
        """Dibuja un pie de página con controles."""
        h, w = frame.shape[:2]
        
        # Fondo del pie de página
        footer_height = 100
        cv2.rectangle(frame, (0, h - footer_height), (w, h), (0, 0, 0), -1)
        cv2.rectangle(frame, (0, h - footer_height), (w, h), COLOR_ACCENT, 2)
        
        # Controles
        y = h - footer_height + 30
        for control in controls:
            self._draw_text_centered(frame, control, y, 0.5, COLOR_TEXT, 1)
            y += 25
    
    def _draw_progress(self, frame, current, total, text=""):
        """Dibuja una barra de progreso."""
        h, w = frame.shape[:2]
        
        # Posición de la barra
        bar_x = 50
        bar_y = h - 150
        bar_width = w - 100
        bar_height = 20
        
        # Fondo de la barra
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        
        # Progreso
        progress_width = int((current / total) * bar_width)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), COLOR_ACCENT, -1)
        
        # Texto de progreso
        progress_text = f"{current}/{total} - {text}"
        self._draw_text_centered(frame, progress_text, bar_y - 10, 0.6, COLOR_ACCENT, 2)
    
    def _get_user_name(self):
        """Solicita el nombre del usuario a través de la cámara."""
        print("\n" + "="*60)
        print("  IDENTIFICACIÓN DEL USUARIO")
        print("="*60)
        name = input("Ingresa tu nombre (o presiona Enter para usar timestamp): ").strip()
        if not name:
            name = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return name
    
    def _capture_single_photo(self, cap, angle_name, instructions, current_angle, total_angles):
        """
        Captura una foto con instrucciones específicas mostradas en pantalla.
        
        Args:
            cap: Objeto VideoCapture de OpenCV
            angle_name: Nombre del ángulo (ej: "frontal", "izquierda", "derecha")
            instructions: Instrucciones para el usuario
            current_angle: Número del ángulo actual
            total_angles: Total de ángulos a capturar
        
        Returns:
            tuple: (frame, landmarks) o (None, None) si falla
        """
        captured_frame = None
        captured_landmarks = None
        show_confirmation = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Crear frame de display
            display_frame = frame.copy()
            
            # Dibujar encabezado
            self._draw_header(display_frame, f"ÁNGULO {current_angle}/{total_angles}: {angle_name.upper()}")
            
            # Dibujar guía de rostro
            h, w = frame.shape[:2]
            center_x, center_y = w // 2, h // 2
            face_radius = min(w, h) // 3
            
            # Círculo guía
            cv2.circle(display_frame, (center_x, center_y), face_radius, COLOR_ACCENT, 2)
            cv2.circle(display_frame, (center_x, center_y), 5, COLOR_ACCENT, -1)
            
            # Líneas de guía
            cv2.line(display_frame, (center_x - face_radius, center_y), (center_x + face_radius, center_y), COLOR_ACCENT, 1)
            cv2.line(display_frame, (center_x, center_y - face_radius), (center_x, center_y + face_radius), COLOR_ACCENT, 1)
            
            # Instrucciones principales
            if captured_frame is None:
                self._draw_text_wrapped(display_frame, instructions, 120, w - 100, 0.7, COLOR_ACCENT, 2)
            else:
                self._draw_text_centered(display_frame, "¡FOTO CAPTURADA!", 130, 1.2, COLOR_SUCCESS, 3)
                self._draw_text_centered(display_frame, "Revisa la imagen", 170, 0.6, COLOR_SUCCESS, 2)
            
            # Barra de progreso
            self._draw_progress(display_frame, current_angle - 1, total_angles, angle_name.upper())
            
            # Controles
            if captured_frame is None:
                controls = [
                    "Presiona 'S' o ESPACIO para capturar",
                    "Presiona 'Q' o ESC para cancelar"
                ]
            else:
                controls = [
                    "Presiona 'S' para continuar",
                    "Presiona 'R' para retomar la foto",
                    "Presiona 'Q' o ESC para cancelar"
                ]
            self._draw_footer(display_frame, controls)
            
            # Confirmación de cancelación
            if show_confirmation:
                overlay = display_frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
                self._draw_text_centered(overlay, "¿CANCELAR TODO EL PROCESO?", h // 2 - 50, 1.2, COLOR_WARNING, 3)
                self._draw_text_centered(overlay, "Presiona 'Q' nuevamente para confirmar", h // 2 + 10, 0.8, COLOR_WARNING, 2)
                self._draw_text_centered(overlay, "Presiona cualquier otra tecla para continuar", h // 2 + 60, 0.6, COLOR_TEXT, 1)
                cv2.imshow('Generador Biométrico', overlay)
                key = cv2.waitKey(0) & 0xFF
                if key == ord('q'):
                    return None, None
                else:
                    show_confirmation = False
                    continue
            
            cv2.imshow('Generador Biométrico', display_frame)
            key = cv2.waitKey(1) & 0xFF
            
            # Capturar
            if key == ord('s') or key == 32:  # 's' o ESPACIO
                if captured_frame is None:
                    # Extraer landmarks para verificar que hay un rostro
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    landmarks = self._extract_landmarks(rgb_frame)
                    
                    if landmarks is not None:
                        captured_frame = frame.copy()
                        captured_landmarks = landmarks
                    else:
                        # Mostrar error temporal
                        error_frame = display_frame.copy()
                        cv2.rectangle(error_frame, (0, h - 150), (w, h - 50), (0, 0, 0), -1)
                        self._draw_text_centered(error_frame, "ERROR: No se detectó rostro", h - 120, 0.8, COLOR_ERROR, 2)
                        self._draw_text_centered(error_frame, "Asegúrate de que tu rostro sea visible", h - 90, 0.6, COLOR_ERROR, 1)
                        cv2.imshow('Generador Biométrico', error_frame)
                        cv2.waitKey(2000)
                else:
                    # Continuar al siguiente ángulo
                    break
            
            # Retomar
            elif key == ord('r') and captured_frame is not None:
                captured_frame = None
                captured_landmarks = None
            
            # Cancelar todo
            elif key == ord('q') or key == 27:  # 'q' o ESC
                if captured_frame is not None:
                    show_confirmation = True
                else:
                    return None, None
        
        return captured_frame, captured_landmarks
    
    def capture_profile(self, camera_index=0):
        """
        Captura un perfil completo con múltiples fotos desde diferentes ángulos.
        
        Args:
            camera_index: Índice de la cámara a usar (0, 1, etc.)
        
        Returns:
            dict con información del perfil generado
        """
        # Abrir cámara
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            cap = cv2.VideoCapture(1)
            if not cap.isOpened():
                print("[ERROR] No se pudo abrir ninguna cámara.")
                return None
        
        # Mostrar pantalla de bienvenida
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            display_frame = frame.copy()
            h, w = frame.shape[:2]
            
            # Fondo oscuro
            overlay = display_frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
            
            # Título
            self._draw_text_centered(overlay, "GENERADOR DE PERFIL BIOMÉTRICO", h // 3, 1.5, COLOR_ACCENT, 4)
            
            # Instrucciones
            instructions = [
                "Este proceso capturará 3 fotos de tu rostro",
                "desde diferentes ángulos para mejorar",
                "la precisión del reconocimiento facial."
            ]
            y = h // 2 - 20
            for instruction in instructions:
                self._draw_text_centered(overlay, instruction, y, 0.8, COLOR_TEXT, 2)
                y += 40
            
            # Requisitos
            self._draw_text_centered(overlay, "ASEGÚRATE DE:", h // 2 + 100, 0.8, COLOR_WARNING, 2)
            self._draw_text_centered(overlay, "✓ Buena iluminación", h // 2 + 150, 0.6, COLOR_SUCCESS, 1)
            self._draw_text_centered(overlay, "✓ Rostro completo visible", h // 2 + 190, 0.6, COLOR_SUCCESS, 1)
            self._draw_text_centered(overlay, "✓ Seguir las instrucciones", h // 2 + 230, 0.6, COLOR_SUCCESS, 1)
            
            # Footer
            self._draw_footer(overlay, ["Presiona 'S' o ESPACIO para comenzar", "Presiona 'Q' o ESC para salir"])
            
            cv2.imshow('Generador Biométrico', overlay)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('s') or key == 32:
                break
            elif key == ord('q') or key == 27:
                cap.release()
                cv2.destroyAllWindows()
                return None
        
        # Obtener nombre del usuario
        user_name = self._get_user_name()
        
        # Verificar si existe el perfil
        profile_dir = os.path.join(self.PROFILES_DIR, user_name)
        if os.path.exists(profile_dir):
            # Mostrar advertencia en pantalla
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                display_frame = frame.copy()
                h, w = frame.shape[:2]
                
                overlay = display_frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
                
                self._draw_text_centered(overlay, "¡ADVERTENCIA!", h // 3, 1.5, COLOR_WARNING, 4)
                self._draw_text_centered(overlay, f"Ya existe un perfil para '{user_name}'", h // 2 - 30, 0.9, COLOR_TEXT, 2)
                self._draw_text_centered(overlay, "Se sobrescribirán las fotos existentes", h // 2 + 20, 0.7, COLOR_TEXT, 1)
                
                self._draw_footer(overlay, ["Presiona 'S' para sobrescribir", "Presiona 'Q' para cancelar"])
                
                cv2.imshow('Generador Biométrico', overlay)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('s'):
                    break
                elif key == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    return None
        else:
            os.makedirs(profile_dir)
        
        # Definir ángulos de captura
        angles = [
            {
                "name": "frontal",
                "filename": "frontal.jpg",
                "instructions": "Mira directamente a la cámara, con el rostro centrado"
            },
            {
                "name": "izquierda",
                "filename": "izquierda.jpg",
                "instructions": "Gira tu rostro ligeramente hacia la izquierda (45° aprox)"
            },
            {
                "name": "derecha",
                "filename": "derecha.jpg",
                "instructions": "Gira tu rostro ligeramente hacia la derecha (45° aprox)"
            }
        ]
        
        # Capturar fotos para cada ángulo
        photos = []
        all_landmarks = []
        
        for i, angle in enumerate(angles, 1):
            frame, landmarks = self._capture_single_photo(
                cap,
                angle["name"],
                angle["instructions"],
                i,
                len(angles)
            )
            
            if frame is None:
                cap.release()
                cv2.destroyAllWindows()
                return None
            
            # Guardar foto
            photo_path = os.path.join(profile_dir, angle["filename"])
            cv2.imwrite(photo_path, frame)
            
            photos.append({
                "angle": angle["name"],
                "filename": angle["filename"],
                "path": photo_path,
                "landmarks": landmarks.tolist() if landmarks is not None else None,
                "landmark_count": len(landmarks) if landmarks is not None else 0
            })
            
            if landmarks is not None:
                all_landmarks.append(landmarks)
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Calcular landmarks promedio
        if all_landmarks:
            avg_landmarks = np.mean(all_landmarks, axis=0)
        else:
            avg_landmarks = None
        
        # Crear archivo de perfil JSON
        profile_data = {
            "name": user_name,
            "created_at": datetime.now().isoformat(),
            "model": "mediapipe_face_landmarker_v1",
            "photos": photos,
            "average_landmarks": avg_landmarks.tolist() if avg_landmarks is not None else None,
            "total_landmarks": len(avg_landmarks) if avg_landmarks is not None else 0,
            "photo_count": len(photos)
        }
        
        profile_json_path = os.path.join(profile_dir, "profile.json")
        with open(profile_json_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        # Crear reference.jpg para compatibilidad con el sistema existente
        frontal_photo = None
        for photo in photos:
            if photo["angle"] == "frontal":
                frontal_photo = photo
                break
        if frontal_photo:
            reference_path = os.path.join(os.path.dirname(__file__), "reference.jpg")
            cv2.imwrite(reference_path, cv2.imread(frontal_photo["path"]))
        
        # Mostrar pantalla de éxito
        success_cap = cv2.VideoCapture(camera_index)
        while True:
            ret, frame = success_cap.read()
            if not ret:
                break
            
            display_frame = frame.copy()
            h, w = frame.shape[:2]
            
            overlay = display_frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
            
            self._draw_text_centered(overlay, "¡PERFIL GENERADO EXITOSAMENTE!", h // 3, 1.2, COLOR_SUCCESS, 4)
            self._draw_text_centered(overlay, f"Usuario: {user_name}", h // 2 - 40, 0.9, COLOR_TEXT, 2)
            
            # Estadísticas
            self._draw_text_centered(overlay, f"Fotos: {len(photos)}", h // 2 + 30, 0.7, COLOR_ACCENT, 2)
            self._draw_text_centered(overlay, f"Landmarks: {len(avg_landmarks) if avg_landmarks is not None else 0}", h // 2 + 70, 0.7, COLOR_ACCENT, 2)
            
            self._draw_footer(overlay, ["Presiona cualquier tecla para salir"])
            
            cv2.imshow('Generador Biométrico', overlay)
            if cv2.waitKey(1) & 0xFF != 255:
                break
        
        success_cap.release()
        cv2.destroyAllWindows()
        
        print(f"\n[OK] Perfil guardado en: {profile_dir}")
        
        return {
            "user_name": user_name,
            "profile_dir": profile_dir,
            "profile_json": profile_json_path,
            "photos": photos,
            "reference_path": reference_path if frontal_photo else None
        }


class BiometricGeneratorSocket:
    """Genera un perfil biométrico completo sin UI de OpenCV, usando callbacks/sockets.
    
    Esta versión está diseñada para ser usada con Socket.io para comunicación
    con el componente React BiometricCapture.jsx.
    """
    
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")
    PROFILES_DIR = os.path.join(os.path.dirname(__file__), "profiles")
    
    # Estados de captura
    STATE_IDLE = "idle"
    STATE_WELCOME = "welcome"
    STATE_CAPTURING = "capturing"
    STATE_CONFIRMATION = "confirmation"
    STATE_SUCCESS = "success"
    STATE_ERROR = "error"
    
    def __init__(self, on_frame_callback=None, on_face_detected_callback=None, on_status_callback=None):
        """
        Inicializa el generador biométrico con callbacks.
        
        Args:
            on_frame_callback: Callback(frame_b64) para enviar frames de video
            on_face_detected_callback: Callback(detected) para enviar estado de detección
            on_status_callback: Callback(status_data) para enviar estado del proceso
        """
        self.landmarker = None
        self.cap = None
        self.is_running = False
        self.current_state = self.STATE_IDLE
        self.user_name = None
        self.profile_dir = None
        self.current_angle_index = 0
        self.captured_photos = []
        self.captured_landmarks = []
        
        # Callbacks
        self.on_frame_callback = on_frame_callback
        self.on_face_detected_callback = on_face_detected_callback
        self.on_status_callback = on_status_callback
        
        # Thread para captura de video
        self.capture_thread = None
        self.frame_lock = threading.Lock()
        
        # Inicializar modelo y directorios
        self._ensure_model()
        self._init_landmarker()
        self._ensure_profiles_dir()
        
        # Definir ángulos de captura
        self.angles = [
            {
                "name": "frontal",
                "filename": "frontal.jpg",
                "instructions": "Mira directamente a la cámara, con el rostro centrado"
            },
            {
                "name": "izquierda",
                "filename": "izquierda.jpg",
                "instructions": "Gira tu rostro ligeramente hacia la izquierda (45° aprox)"
            },
            {
                "name": "derecha",
                "filename": "derecha.jpg",
                "instructions": "Gira tu rostro ligeramente hacia la derecha (45° aprox)"
            }
        ]
    
    def _ensure_model(self):
        """Descarga el modelo de MediaPipe si no existe."""
        if not os.path.exists(self.MODEL_PATH):
            print(f"[BIOMETRIC SOCKET] Descargando modelo de Face Landmarker...")
            try:
                urllib.request.urlretrieve(self.MODEL_URL, self.MODEL_PATH)
                print(f"[BIOMETRIC SOCKET] [OK] Modelo descargado a {self.MODEL_PATH}")
            except Exception as e:
                print(f"[BIOMETRIC SOCKET] [ERROR] Falló la descarga del modelo: {e}")
                raise
    
    def _init_landmarker(self):
        """Inicializa el detector de landmarks faciales."""
        if not os.path.exists(self.MODEL_PATH):
            print("[BIOMETRIC SOCKET] [ERROR] Modelo no encontrado. No se puede inicializar.")
            return
        
        try:
            base_options = mp_python.BaseOptions(model_asset_path=self.MODEL_PATH)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
                num_faces=1
            )
            self.landmarker = vision.FaceLandmarker.create_from_options(options)
            print("[BIOMETRIC SOCKET] [OK] Face Landmarker inicializado.")
        except Exception as e:
            print(f"[BIOMETRIC SOCKET] [ERROR] Falló la inicialización: {e}")
            raise
    
    def _ensure_profiles_dir(self):
        """Crea el directorio de perfiles si no existe."""
        if not os.path.exists(self.PROFILES_DIR):
            os.makedirs(self.PROFILES_DIR)
            print(f"[BIOMETRIC SOCKET] [OK] Directorio de perfiles creado: {self.PROFILES_DIR}")
    
    def _extract_landmarks(self, image_rgb):
        """Extrae los landmarks faciales de una imagen RGB."""
        if self.landmarker is None:
            return None
        
        try:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            result = self.landmarker.detect(mp_image)
            
            if result.face_landmarks and len(result.face_landmarks) > 0:
                landmarks = result.face_landmarks[0]
                # Convertir a array numpy de coordenadas (x, y, z)
                coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
                return coords.flatten()
            return None
        except Exception as e:
            print(f"[BIOMETRIC SOCKET] [ERROR] Extracción de landmarks falló: {e}")
            return None
    
    def _frame_to_base64(self, frame, quality=75):
        """Convierte un frame OpenCV a base64."""
        try:
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            return frame_b64
        except Exception as e:
            print(f"[BIOMETRIC SOCKET] [ERROR] Error al convertir frame a base64: {e}")
            return None
    
    def _emit_frame(self, frame):
        """Emite un frame vía callback."""
        if self.on_frame_callback:
            frame_b64 = self._frame_to_base64(frame)
            if frame_b64:
                self.on_frame_callback(frame_b64)
    
    def _emit_face_detected(self, detected):
        """Emite el estado de detección de rostro vía callback."""
        if self.on_face_detected_callback:
            self.on_face_detected_callback(detected)
    
    def _emit_status(self, status_data):
        """Emite el estado del proceso vía callback."""
        if self.on_status_callback:
            self.on_status_callback(status_data)
    
    def _capture_loop(self):
        """Loop de captura de video en un thread separado."""
        print("[BIOMETRIC SOCKET DEBUG] Iniciando loop de captura...")
        print(f"[BIOMETRIC SOCKET DEBUG] is_running: {self.is_running}")
        print(f"[BIOMETRIC SOCKET DEBUG] cap: {self.cap}")
        print(f"[BIOMETRIC SOCKET DEBUG] cap.isOpened(): {self.cap.isOpened() if self.cap else 'N/A'}")
        
        frame_count = 0
        while self.is_running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print("[BIOMETRIC SOCKET DEBUG] No se pudo leer frame de la cámara")
                    break
                
                # Log cada 30 frames para no saturar
                frame_count += 1
                if frame_count % 30 == 0:
                    print(f"[BIOMETRIC SOCKET DEBUG] Frame #{frame_count} capturado exitosamente")
                
                # Detectar rostro
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                landmarks = self._extract_landmarks(rgb_frame)
                face_detected = landmarks is not None
                
                # Emitir frame y estado de detección
                self._emit_frame(frame)
                self._emit_face_detected(face_detected)
                
                # Pequeña pausa para no saturar
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"[BIOMETRIC SOCKET DEBUG] Error en loop de captura: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print("[BIOMETRIC SOCKET DEBUG] Loop de captura terminado")
    
    def start_capture(self, camera_index=0):
        """
        Inicia la captura de video.
        
        Args:
            camera_index: Índice de la cámara a usar (0, 1, etc.)
        
        Returns:
            bool: True si se inició correctamente, False en caso contrario
        """
        print(f"[BIOMETRIC SOCKET DEBUG] start_capture llamado con camera_index={camera_index}")
        print(f"[BIOMETRIC SOCKET DEBUG] self.is_running actual: {self.is_running}")
        
        if self.is_running:
            print("[BIOMETRIC SOCKET DEBUG] La captura ya está en ejecución")
            return False
        
        try:
            # Intentar abrir cámara
            print(f"[BIOMETRIC SOCKET DEBUG] Intentando abrir cámara {camera_index}...")
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                print(f"[BIOMETRIC SOCKET DEBUG] No se pudo abrir cámara {camera_index}, intentando cámara 1...")
                self.cap = cv2.VideoCapture(1)
                if not self.cap.isOpened():
                    print("[BIOMETRIC SOCKET DEBUG] ERROR: No se pudo abrir ninguna cámara")
                    return False
            
            print(f"[BIOMETRIC SOCKET DEBUG] Cámara abierta exitosamente")
            
            # Configurar resolución
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            print(f"[BIOMETRIC SOCKET DEBUG] Resolución configurada a 640x480")
            
            self.is_running = True
            self.current_state = self.STATE_WELCOME
            print(f"[BIOMETRIC SOCKET DEBUG] is_running establecido a True, state={self.current_state}")
            
            # Iniciar thread de captura
            print(f"[BIOMETRIC SOCKET DEBUG] Iniciando thread de captura...")
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            print(f"[BIOMETRIC SOCKET DEBUG] Thread iniciado")
            
            # Emitir estado de bienvenida
            print(f"[BIOMETRIC SOCKET DEBUG] Emitiendo estado de bienvenida...")
            self._emit_status({
                "state": self.STATE_WELCOME,
                "message": "Bienvenido al generador de perfil biométrico"
            })
            
            print("[BIOMETRIC SOCKET DEBUG] Captura iniciada correctamente, retornando True")
            return True
            
        except Exception as e:
            print(f"[BIOMETRIC SOCKET DEBUG] ERROR al iniciar captura: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_capture(self):
        """Detiene la captura de video."""
        if not self.is_running:
            return
        
        print("[BIOMETRIC SOCKET] Deteniendo captura...")
        self.is_running = False
        
        # Esperar que termine el thread
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        
        # Liberar cámara
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.current_state = self.STATE_IDLE
        print("[BIOMETRIC SOCKET] Captura detenida")
    
    def set_user_name(self, name):
        """
        Establece el nombre del usuario.
        
        Args:
            name: Nombre del usuario
        """
        if not name:
            name = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.user_name = name
        self.profile_dir = os.path.join(self.PROFILES_DIR, name)
        
        # Crear directorio si no existe
        if not os.path.exists(self.profile_dir):
            os.makedirs(self.profile_dir)
        
        print(f"[BIOMETRIC SOCKET] Usuario establecido: {name}")
    
    def start_capturing_photos(self):
        """
        Inicia el proceso de captura de fotos.
        
        Returns:
            bool: True si se inició correctamente, False en caso contrario
        """
        if not self.is_running or not self.user_name:
            print("[BIOMETRIC SOCKET] No se puede iniciar captura de fotos: captura no iniciada o sin usuario")
            return False
        
        self.current_state = self.STATE_CAPTURING
        self.current_angle_index = 0
        self.captured_photos = []
        self.captured_landmarks = []
        
        # Emitir estado de inicio de captura
        self._emit_status({
            "state": self.STATE_CAPTURING,
            "current_angle": self.angles[0]["name"],
            "total_angles": len(self.angles),
            "current_angle_index": 0,
            "instructions": self.angles[0]["instructions"]
        })
        
        print("[BIOMETRIC SOCKET] Iniciando captura de fotos")
        return True
    
    def capture_photo(self):
        """
        Captura una foto del ángulo actual.
        
        Returns:
            dict: Información de la foto capturada o None si falló
        """
        if not self.is_running or self.current_state != self.STATE_CAPTURING:
            print("[BIOMETRIC SOCKET] No se puede capturar foto: estado incorrecto")
            return None
        
        if self.current_angle_index >= len(self.angles):
            print("[BIOMETRIC SOCKET] No se puede capturar foto: no hay más ángulos")
            return None
        
        try:
            # Capturar frame actual
            ret, frame = self.cap.read()
            if not ret:
                print("[BIOMETRIC SOCKET] No se pudo capturar frame")
                return None
            
            # Detectar rostro y extraer landmarks
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks = self._extract_landmarks(rgb_frame)
            
            if landmarks is None:
                print("[BIOMETRIC SOCKET] No se detectó rostro en la foto")
                return None
            
            # Guardar foto
            angle = self.angles[self.current_angle_index]
            photo_path = os.path.join(self.profile_dir, angle["filename"])
            cv2.imwrite(photo_path, frame)
            
            photo_info = {
                "angle": angle["name"],
                "filename": angle["filename"],
                "path": photo_path,
                "landmarks": landmarks.tolist(),
                "landmark_count": len(landmarks)
            }
            
            self.captured_photos.append(photo_info)
            self.captured_landmarks.append(landmarks)
            
            print(f"[BIOMETRIC SOCKET] Foto capturada: {angle['name']}")
            
            # Avanzar al siguiente ángulo
            self.current_angle_index += 1
            
            # Verificar si hay más ángulos
            if self.current_angle_index < len(self.angles):
                # Emitir estado para el siguiente ángulo
                next_angle = self.angles[self.current_angle_index]
                self._emit_status({
                    "state": self.STATE_CAPTURING,
                    "current_angle": next_angle["name"],
                    "total_angles": len(self.angles),
                    "current_angle_index": self.current_angle_index,
                    "instructions": next_angle["instructions"]
                })
            else:
                # Todos los ángulos capturados, ir a confirmación
                self.current_state = self.STATE_CONFIRMATION
                self._emit_status({
                    "state": self.STATE_CONFIRMATION,
                    "photos_count": len(self.captured_photos),
                    "message": "Todas las fotos han sido capturadas"
                })
            
            return photo_info
            
        except Exception as e:
            print(f"[BIOMETRIC SOCKET] Error al capturar foto: {e}")
            return None
    
    def complete_profile(self):
        """
        Completa el proceso de generación de perfil.
        
        Returns:
            dict: Información del perfil generado o None si falló
        """
        if not self.user_name or not self.captured_photos:
            print("[BIOMETRIC SOCKET] No se puede completar perfil: no hay datos suficientes")
            return None
        
        try:
            # Calcular landmarks promedio
            if self.captured_landmarks:
                avg_landmarks = np.mean(self.captured_landmarks, axis=0)
            else:
                avg_landmarks = None
            
            # Crear archivo de perfil JSON
            profile_data = {
                "name": self.user_name,
                "created_at": datetime.now().isoformat(),
                "model": "mediapipe_face_landmarker_v1",
                "photos": self.captured_photos,
                "average_landmarks": avg_landmarks.tolist() if avg_landmarks is not None else None,
                "total_landmarks": len(avg_landmarks) if avg_landmarks is not None else 0,
                "photo_count": len(self.captured_photos)
            }
            
            profile_json_path = os.path.join(self.profile_dir, "profile.json")
            with open(profile_json_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            # Crear reference.jpg para compatibilidad con el sistema existente
            frontal_photo = None
            for photo in self.captured_photos:
                if photo["angle"] == "frontal":
                    frontal_photo = photo
                    break
            
            reference_path = None
            if frontal_photo:
                reference_path = os.path.join(os.path.dirname(__file__), "reference.jpg")
                cv2.imwrite(reference_path, cv2.imread(frontal_photo["path"]))
            
            # Emitir estado de éxito
            self.current_state = self.STATE_SUCCESS
            self._emit_status({
                "state": self.STATE_SUCCESS,
                "user_name": self.user_name,
                "profile_dir": self.profile_dir,
                "photos_count": len(self.captured_photos),
                "landmarks_count": len(avg_landmarks) if avg_landmarks is not None else 0,
                "message": "Perfil generado exitosamente"
            })
            
            print(f"[BIOMETRIC SOCKET] Perfil completado: {self.user_name}")
            
            return {
                "user_name": self.user_name,
                "profile_dir": self.profile_dir,
                "profile_json": profile_json_path,
                "photos": self.captured_photos,
                "reference_path": reference_path
            }
            
        except Exception as e:
            print(f"[BIOMETRIC SOCKET] Error al completar perfil: {e}")
            self.current_state = self.STATE_ERROR
            self._emit_status({
                "state": self.STATE_ERROR,
                "message": f"Error al completar perfil: {str(e)}"
            })
            return None
    
    def cancel_capture(self):
        """Cancela el proceso de captura."""
        print("[BIOMETRIC SOCKET] Cancelando captura...")
        self.current_state = self.STATE_IDLE
        self.user_name = None
        self.profile_dir = None
        self.current_angle_index = 0
        self.captured_photos = []
        self.captured_landmarks = []
        
        self._emit_status({
            "state": self.STATE_IDLE,
            "message": "Captura cancelada"
        })
    
    def get_current_state(self):
        """Obtiene el estado actual del proceso."""
        return {
            "state": self.current_state,
            "user_name": self.user_name,
            "current_angle": self.angles[self.current_angle_index]["name"] if self.current_angle_index < len(self.angles) else None,
            "current_angle_index": self.current_angle_index,
            "total_angles": len(self.angles),
            "photos_captured": len(self.captured_photos)
        }


def main():
    """Función principal para ejecutar el generador de perfiles."""
    try:
        generator = BiometricGenerator()
        
        # Intentar con cámara 0, luego 1 si falla
        result = generator.capture_profile(camera_index=0)
        
        if result is None:
            print("\nIntentando con cámara alternativa...")
            result = generator.capture_profile(camera_index=1)
        
        if result:
            print("\n✓ ¡Listo! Ahora puedes iniciar la aplicación y usar autenticación facial.")
            print(f"  Tu perfil está guardado en: {result['profile_dir']}")
        else:
            print("\n✗ No se pudo generar el perfil biométrico.")
            print("  Verifica que tu cámara esté conectada y funcionando.")
    
    except Exception as e:
        print(f"\n[ERROR CRÍTICO] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
