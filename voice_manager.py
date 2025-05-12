"""
Gestor de Voz - Sistema de Síntesis de Voz
Desarrollado para Su Majestad
"""

import os
import logging
import threading
import tempfile
import time
import queue
from datetime import datetime
from gtts import gTTS
import pygame

class VoiceManager:
    """Gestor de síntesis de voz utilizando gTTS y pygame"""
    
    def __init__(self):
        """Inicializa el gestor de voz"""
        self.logger = logging.getLogger("VoiceManager")
        self.logger.info("Inicializando gestor de voz...")
        
        # Estado del sistema
        self.is_running = False
        self.speaking = False
        self.audio_queue = queue.Queue()
        self.voice_lock = threading.Lock()
        self.temp_dir = tempfile.mkdtemp(prefix="voice_")
        
        # Inicializar pygame para reproducción de audio
        try:
            pygame.mixer.init()
            self.logger.info("Pygame mixer inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar pygame mixer: {str(e)}")
        
        # Configuración por defecto
        self.language = 'es'
        self.voice_id = 'com.mx'
        self.rate = 1.0
        self.volume = 1.0
        
        self.logger.info(f"Gestor de voz configurado para idioma {self.language} (region: {self.voice_id})")
    
    def set_language(self, language):
        """Establece el idioma de la voz"""
        self.language = language
        self.logger.info(f"Idioma cambiado a: {language}")
    
    def set_voice(self, voice_id):
        """Establece el ID de voz específico (TLD para gTTS)"""
        self.voice_id = voice_id
        self.logger.info(f"Voz cambiada a: {voice_id}")
    
    def set_rate(self, rate):
        """Establece la velocidad de la voz (factor multiplicador)"""
        self.rate = max(0.5, min(2.0, rate))  # Limitar entre 0.5 y 2.0
        self.logger.info(f"Velocidad cambiada a: {self.rate}")
    
    def set_volume(self, volume):
        """Establece el volumen de la voz (0.0 a 1.0)"""
        self.volume = max(0.0, min(1.0, volume))  # Limitar entre 0.0 y 1.0
        pygame.mixer.music.set_volume(self.volume)
        self.logger.info(f"Volumen cambiado a: {self.volume}")
    
    def start(self):
        """Inicia el servicio de voz en un hilo separado"""
        if self.is_running:
            return
            
        self.is_running = True
        self.logger.info("Iniciando servicio de voz...")
        
        # Iniciar hilo para reproducción continua
        self.voice_thread = threading.Thread(target=self._voice_worker)
        self.voice_thread.daemon = True
        self.voice_thread.start()
        
        self.logger.info("Servicio de voz iniciado correctamente")
    
    def stop(self):
        """Detiene el servicio de voz"""
        if not self.is_running:
            return
            
        self.logger.info("Deteniendo servicio de voz...")
        self.is_running = False
        
        # Vaciar la cola de audio
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break
        
        # Detener reproducción de audio actual
        try:
            pygame.mixer.music.stop()
        except:
            pass
        
        # Esperar a que termine el hilo
        if hasattr(self, 'voice_thread') and self.voice_thread.is_alive():
            try:
                self.voice_thread.join(timeout=2.0)
            except:
                pass
        
        self.logger.info("Servicio de voz detenido")
    
    def speak(self, text):
        """
        Sintetiza voz para el texto proporcionado
        
        Args:
            text (str): Texto a sintetizar
            
        Returns:
            bool: True si se pudo encolar el texto, False en caso contrario
        """
        if not text or not self.is_running:
            return False
        
        try:
            # Preprocesar texto (segmentar si es demasiado largo)
            segments = self._preprocess_text(text)
            
            # Agregar a la cola
            with self.voice_lock:
                for segment in segments:
                    self.audio_queue.put(segment)
                
            self.logger.info(f"Texto añadido a cola de síntesis: {len(segments)} segmentos")
            return True
        except Exception as e:
            self.logger.error(f"Error al añadir texto a la cola: {str(e)}")
            return False
    
    def _preprocess_text(self, text):
        """
        Preprocesa el texto para síntesis de voz
        
        Args:
            text (str): Texto a procesar
            
        Returns:
            list: Lista de segmentos de texto preparados para síntesis
        """
        # Limitar longitud máxima para evitar problemas con gTTS
        max_segment_length = 500
        
        # Si el texto es corto, devolverlo directamente
        if len(text) <= max_segment_length:
            return [text]
        
        # Dividir texto en segmentos más pequeños
        segments = []
        current_pos = 0
        
        while current_pos < len(text):
            # Tomar un trozo de texto
            segment_end = min(current_pos + max_segment_length, len(text))
            
            # Asegurarse de no cortar en medio de una palabra
            if segment_end < len(text):
                # Buscar el último espacio en el segmento
                last_space = text.rfind(' ', current_pos, segment_end)
                if last_space != -1:
                    segment_end = last_space + 1
            
            # Extraer segmento
            segment = text[current_pos:segment_end].strip()
            if segment:  # Evitar segmentos vacíos
                segments.append(segment)
            
            current_pos = segment_end
        
        return segments
    
    def _voice_worker(self):
        """Hilo trabajador para procesar la cola de audio"""
        while self.is_running:
            try:
                # Verificar si hay texto en la cola
                try:
                    text_to_speak = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                if text_to_speak:
                    self.speaking = True
                    self.logger.info(f"Sintetizando voz: '{text_to_speak[:50]}...' ({len(text_to_speak)} caracteres)")
                    
                    # Crear archivo temporal para el audio
                    temp_file = os.path.join(self.temp_dir, f"voice_{int(time.time())}.mp3")
                    
                    try:
                        # Generar audio con gTTS
                        tts = gTTS(text=text_to_speak, lang=self.language, tld=self.voice_id, slow=False)
                        tts.save(temp_file)
                        
                        # Reproducir audio
                        pygame.mixer.music.load(temp_file)
                        pygame.mixer.music.set_volume(self.volume)
                        pygame.mixer.music.play()
                        
                        # Esperar a que termine la reproducción
                        while pygame.mixer.music.get_busy() and self.is_running:
                            time.sleep(0.1)
                        
                        # Eliminar archivo temporal
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    except Exception as e:
                        self.logger.error(f"Error al sintetizar voz: {str(e)}")
                    
                    self.speaking = False
                    self.audio_queue.task_done()
                    
            except Exception as e:
                self.logger.error(f"Error en hilo de voz: {str(e)}")
                time.sleep(1)