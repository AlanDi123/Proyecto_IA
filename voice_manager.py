"""
Gestor de Respuesta por Voz - Sistema de Sintetización Vocal
Desarrollado para Su Majestad

Este módulo implementa las capacidades de respuesta por voz del sistema
utilizando tecnologías de síntesis de voz gratuitas para español latinoamericano.
"""

import os
import logging
import threading
import time
import tempfile
import queue
import pygame
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play

class VoiceManager:
    """Gestor de síntesis y reproducción de voz"""
    
    def __init__(self, voice_settings):
        """Inicializa el gestor de voz con la configuración especificada"""
        self.logger = logging.getLogger("VoiceManager")
        self.logger.info("Inicializando gestor de voz...")
        
        # Configuración de voz
        self.settings = voice_settings
        self.language = voice_settings.get("language", "es")
        self.tld = voice_settings.get("tld", "com.mx")  # Dominio de nivel superior para acento latinoamericano
        self.speed = voice_settings.get("speed", 1.0)
        self.pitch = voice_settings.get("pitch", 1.0)
        
        # Inicializar pygame para reproducción de audio
        try:
            pygame.mixer.init()
            self.pygame_available = True
            self.logger.info("Pygame inicializado correctamente")
        except Exception as e:
            self.logger.warning(f"No se pudo inicializar pygame: {str(e)}. La síntesis de voz estará deshabilitada.")
            self.pygame_available = False
        
        # Cola de mensajes para síntesis
        self.speech_queue = queue.Queue()
        
        # Estado del servicio
        self.is_running = False
        self.is_speaking = False
        self.current_audio_file = None
        
        # Directorio para archivos temporales
        self.temp_dir = os.path.join(tempfile.gettempdir(), "ai_voice")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            
        self.logger.info(f"Gestor de voz configurado para idioma {self.language} (region: {self.tld})")
    
    def start(self):
        """Inicia el servicio de voz en un hilo separado"""
        if self.is_running:
            return
            
        self.is_running = True
        self.logger.info("Iniciando servicio de voz...")
        
        # Iniciar hilo para procesamiento de cola de síntesis
        self.voice_thread = threading.Thread(target=self._process_speech_queue)
        self.voice_thread.daemon = True
        self.voice_thread.start()
        
        self.logger.info("Servicio de voz iniciado correctamente")
    
    def stop(self):
        """Detiene el servicio de voz"""
        if not self.is_running:
            return
            
        self.logger.info("Deteniendo servicio de voz...")
        self.is_running = False
        
        # Detener reproducción actual
        if self.is_speaking:
            pygame.mixer.music.stop()
            self.is_speaking = False
            
        # Limpiar archivos temporales
        self._clean_temp_files()
        
        self.logger.info("Servicio de voz detenido")
    
    def speak(self, text):
        """Añade texto a la cola para síntesis de voz"""
        if not text or not self.is_running:
            return
            
        # Segmentar texto largo en frases para mejor fluidez
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            if sentence.strip():
                self.speech_queue.put(sentence)
                
        self.logger.info(f"Texto añadido a cola de síntesis: {len(sentences)} segmentos")
    
    def _split_into_sentences(self, text):
        """Divide el texto en frases para mejor procesamiento"""
        # Separar por puntos, exclamaciones, interrogaciones
        raw_sentences = []
        for sep in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
            fragments = []
            for fragment in text.split(sep):
                if fragment:
                    fragments.append(fragment)
            if fragments:
                raw_sentences.extend([f"{s}{sep[0]}" for s in fragments[:-1]])
                raw_sentences.append(fragments[-1])
                break
        
        # Si no se pudo dividir, usar el texto completo
        if not raw_sentences:
            raw_sentences = [text]
        
        # Verificar longitud máxima (gTTS tiene límites)
        max_length = 500
        result = []
        
        for sentence in raw_sentences:
            if len(sentence) <= max_length:
                result.append(sentence)
            else:
                # Dividir frases muy largas por comas
                comma_fragments = sentence.split(", ")
                current_fragment = ""
                
                for fragment in comma_fragments:
                    if len(current_fragment) + len(fragment) + 2 <= max_length:
                        if current_fragment:
                            current_fragment += ", " + fragment
                        else:
                            current_fragment = fragment
                    else:
                        if current_fragment:
                            result.append(current_fragment)
                        current_fragment = fragment
                
                if current_fragment:
                    result.append(current_fragment)
        
        return result
    
    def _process_speech_queue(self):
        """Procesa la cola de mensajes para síntesis y reproducción"""
        while self.is_running:
            try:
                # Obtener siguiente mensaje de la cola (con timeout para poder verificar is_running)
                try:
                    text = self.speech_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                if not text or not self.is_running:
                    continue
                
                # Generar archivo de audio
                audio_file = self._synthesize_speech(text)
                
                if audio_file and os.path.exists(audio_file):
                    # Registrar archivo actual
                    self.current_audio_file = audio_file
                    self.is_speaking = True
                    
                    # Reproducir audio
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    
                    # Esperar a que termine la reproducción
                    while pygame.mixer.music.get_busy() and self.is_running:
                        time.sleep(0.1)
                    
                    # Marcar como completado
                    self.is_speaking = False
                    
                    # Eliminar archivo temporal
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                    
                # Marcar como procesado en la cola
                self.speech_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error en procesamiento de cola de voz: {str(e)}")
                time.sleep(1)  # Evitar bucle rápido en caso de error
    
    def _synthesize_speech(self, text):
        """Sintetiza voz a partir del texto"""
        try:
            # Crear nombre de archivo temporal
            timestamp = int(time.time() * 1000)
            temp_file = os.path.join(self.temp_dir, f"speech_{timestamp}.mp3")
            
            # Generar audio con gTTS
            self.logger.info(f"Sintetizando voz: '{text[:50]}...' ({len(text)} caracteres)")
            tts = gTTS(text=text, lang=self.language, tld=self.tld, slow=False)
            tts.save(temp_file)
            
            # Modificar velocidad y tono si es necesario
            if self.speed != 1.0 or self.pitch != 1.0:
                self._modify_audio(temp_file, self.speed, self.pitch)
            
            return temp_file
            
        except Exception as e:
            self.logger.error(f"Error en síntesis de voz: {str(e)}")
            return None
    
    def _modify_audio(self, file_path, speed=1.0, pitch=1.0):
        """Modifica la velocidad y tono del audio"""
        try:
            # Cargar audio
            sound = AudioSegment.from_file(file_path, format="mp3")
            
            # Aplicar cambios
            if speed != 1.0:
                sound = sound.speedup(playback_speed=speed)
            
            # Para el pitch necesitaríamos bibliotecas adicionales como librosa
            # Esta es una implementación básica que podría mejorarse
            
            # Guardar audio modificado
            sound.export(file_path, format="mp3")
        except Exception as e:
            self.logger.error(f"Error al modificar audio: {str(e)}")
    
    def _clean_temp_files(self):
        """Limpia archivos temporales de audio"""
        try:
            for file in os.listdir(self.temp_dir):
                if file.startswith("speech_") and file.endswith(".mp3"):
                    file_path = os.path.join(self.temp_dir, file)
                    try:
                        # Verificar si el archivo no está en uso actualmente
                        if self.current_audio_file != file_path:
                            os.remove(file_path)
                    except Exception as e:
                        self.logger.warning(f"No se pudo eliminar archivo temporal {file_path}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error al limpiar archivos temporales: {str(e)}")