# modules/voice_manager.py
"""
Gestor de Voz - Sistema de Síntesis de Voz
Desarrollado para Su Majestad
"""

import os
import logging
import threading
import tempfile
import time
from datetime import datetime
import pygame

class VoiceManager:
    """Gestor de síntesis de voz"""
    
    def __init__(self):
        """Inicializa el gestor de voz"""
        self.logger = logging.getLogger("VoiceManager")
        self.logger.info("Inicializando gestor de voz...")
        
        # Estado del sistema
        self.is_running = False
        self.speaking = False
        self.audio_queue = []
        self.voice_lock = threading.Lock()
        
        # Inicializar pygame para reproducción de audio
        try:
            pygame.init()
            pygame.mixer.init()
            self.logger.info("Pygame inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar pygame: {str(e)}")
        
        # Configuración por defecto
        self.language = 'es'
        self.voice_id = 'com.mx'
        
        self.logger.info(f"Gestor de voz configurado para idioma {self.language} (region: {self.voice_id})")
    
    def set_language(self, language):
        """Establece el idioma de la voz"""
        self.language = language
        self.logger.info(f"Idioma cambiado a: {language}")
    
    def set_voice(self, voice_id):
        """Establece el ID de voz específico"""
        self.voice_id = voice_id
        self.logger.info(f"Voz cambiada a: {voice_id}")
    
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
        
        # Esperar a que termine el hilo
        if hasattr(self, 'voice_thread') and self.voice_thread.is_alive():
            try:
                self.voice_thread.join(timeout=2.0)
            except:
                pass
        
        # Detener pygame
        try:
            pygame.mixer.quit()
        except:
            pass
        
        self.logger.info("Servicio de voz detenido")
    
    def speak(self, text):
        """
        Sintetiza voz para el texto proporcionado
        
        Esta versión simplificada no genera audio real,
        pero simula el comportamiento
        """
        if not text or not self.is_running:
            return False
        
        try:
            with self.voice_lock:
                self.audio_queue.append(text)
            return True
        except Exception as e:
            self.logger.error(f"Error al añadir texto a la cola: {str(e)}")
            return False
    
    def _voice_worker(self):
        """Hilo trabajador para procesar la cola de audio"""
        while self.is_running:
            try:
                # Verificar si hay texto en la cola
                text_to_speak = None
                with self.voice_lock:
                    if self.audio_queue:
                        text_to_speak = self.audio_queue.pop(0)
                
                if text_to_speak:
                    self.speaking = True
                    self.logger.info(f"Simulando voz: {text_to_speak[:50]}...")
                    
                    # Simulamos la duración de habla basada en la longitud del texto
                    speak_time = min(len(text_to_speak) * 0.05, 10)  # 50ms por carácter, máximo 10 segundos
                    time.sleep(speak_time)
                    
                    self.speaking = False
                else:
                    # Si no hay nada que reproducir, esperar un momento
                    time.sleep(0.1)
                    
            except Exception as e:
                self.logger.error(f"Error en hilo de voz: {str(e)}")
                time.sleep(1)