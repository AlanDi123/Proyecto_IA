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
        self.settings = voice_settings or {}
        self.language = self.settings.get("language", "es")
        self.tld = self.settings.get("tld", "com.mx")  # Dominio de nivel superior para acento latinoamericano
        self.speed = self.settings.get("speed", 1.0)
        self.pitch = self.settings.get("pitch", 1.0)
        
        # Inicializar pygame para reproducción de audio
        self.pygame_available = False
        try:
            # Inicializar pygame de forma segura
            if not pygame.get_init():
                pygame.init()
            
            # Inicializar el módulo de audio específicamente
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            
            self.pygame_available = True
            self.logger.info("Pygame inicializado correctamente")
        except Exception as e:
            self.logger.warning(f"No se pudo inicializar pygame: {str(e)}. Intentando alternativa...")
            try:
                # Reintentar con una configuración de audio diferente
                pygame.mixer.quit()
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=2048)
                self.pygame_available = True
                self.logger.info("Pygame inicializado con configuración alternativa")
            except Exception as ex:
                self.logger.warning(f"No se pudo inicializar audio: {str(ex)}. La síntesis de voz estará disponible pero sin reproducción.")
        
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
        if self.is_speaking and self.pygame_available:
            try:
                pygame.mixer.music.stop()
            except Exception as e:
                self.logger.warning(f"Error al detener reproducción: {str(e)}")
                
        self.is_speaking = False
            
        # Esperar a que el hilo termine
        if hasattr(self, 'voice_thread') and self.voice_thread.is_alive():
            try:
                self.voice_thread.join(timeout=1.0)  # Esperar 1 segundo máximo
            except Exception as e:
                self.logger.warning(f"Error al esperar finalización del hilo: {str(e)}")
            
        # Limpiar archivos temporales
        self._clean_temp_files()
        
        self.logger.info("Servicio de voz detenido")
    
    def speak(self, text):
        """Añade texto a la cola para síntesis de voz"""
        if not text or not self.is_running or not isinstance(text, str):
            return
            
        # Segmentar texto largo en frases para mejor fluidez
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            if sentence.strip():
                self.speech_queue.put(sentence)
                
        self.logger.info(f"Texto añadido a cola de síntesis: {len(sentences)} segmentos")
    
    def _split_into_sentences(self, text):
        """Divide el texto en frases para mejor procesamiento"""
        # Verificar si el texto está vacío o no es una cadena
        if not text or not isinstance(text, str):
            return []
            
        # Dividir por puntos, exclamaciones, interrogaciones
        separators = ['. ', '! ', '? ', '.\n', '!\n', '?\n', '; ']
        sentences = []
        
        # Texto restante a procesar
        remaining_text = text.strip()
        
        # Mientras quede texto por procesar
        while remaining_text:
            found_separator = False
            
            # Buscar el primer separador en el texto
            for sep in separators:
                pos = remaining_text.find(sep)
                if pos >= 0:
                    # Añadir la frase encontrada incluyendo el separador
                    sentence = remaining_text[:pos+1].strip()  # +1 para incluir el punto, signo, etc.
                    if sentence:
                        sentences.append(sentence)
                    
                    # Actualizar el texto restante
                    remaining_text = remaining_text[pos+len(sep)-1:].strip()
                    found_separator = True
                    break
            
            # Si no se encontró ningún separador, añadir todo el texto restante
            if not found_separator:
                if remaining_text:
                    sentences.append(remaining_text)
                remaining_text = ""
        
        # Verificar longitud máxima (gTTS tiene límites)
        max_length = 500
        result = []
        
        for sentence in sentences:
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
                    if self.pygame_available:
                        try:
                            pygame.mixer.music.load(audio_file)
                            pygame.mixer.music.play()
                            
                            # Esperar a que termine la reproducción
                            while pygame.mixer.music.get_busy() and self.is_running:
                                time.sleep(0.1)
                        except Exception as e:
                            self.logger.error(f"Error al reproducir audio con pygame: {str(e)}")
                            # Intentar fallback con pydub
                            try:
                                sound = AudioSegment.from_file(audio_file, format="mp3")
                                play(sound)
                            except Exception as e2:
                                self.logger.error(f"Error al reproducir audio con pydub: {str(e2)}")
                    else:
                        # Si pygame no está disponible, intentar con pydub
                        try:
                            sound = AudioSegment.from_file(audio_file, format="mp3")
                            play(sound)
                        except Exception as e:
                            self.logger.error(f"Error al reproducir audio con pydub: {str(e)}")
                    
                    # Marcar como completado
                    self.is_speaking = False
                    
                    # Eliminar archivo temporal
                    try:
                        if os.path.exists(audio_file):
                            os.remove(audio_file)
                    except Exception as e:
                        self.logger.warning(f"Error al eliminar archivo temporal {audio_file}: {str(e)}")
                    
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
            
            # Verificar que el archivo se haya creado correctamente
            if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                raise Exception("El archivo de audio generado está vacío o no existe")
            
            # Modificar velocidad y tono si es necesario
            if self.speed != 1.0 or self.pitch != 1.0:
                result = self._modify_audio(temp_file, self.speed, self.pitch)
                if not result:
                    self.logger.warning(f"No se pudo modificar la velocidad/tono del audio. Se usará el audio original.")
            
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
                # Implementación segura del cambio de velocidad
                try:
                    sound = sound.speedup(playback_speed=speed)
                except AttributeError:
                    # Fallback para versiones antiguas de pydub
                    if speed > 1.0:  # Acelerar
                        sound = sound._spawn(sound.raw_data, overrides={
                            "frame_rate": int(sound.frame_rate * speed)
                        }).set_frame_rate(sound.frame_rate)
                    elif speed < 1.0:  # Ralentizar
                        sound = sound._spawn(sound.raw_data, overrides={
                            "frame_rate": int(sound.frame_rate / (2.0 - speed))
                        }).set_frame_rate(sound.frame_rate)
            
            # Guardar audio modificado
            sound.export(file_path, format="mp3")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al modificar audio: {str(e)}")
            return False
    
    def _clean_temp_files(self):
        """Limpia archivos temporales de audio"""
        try:
            if not os.path.exists(self.temp_dir):
                return
                
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
    
    def set_voice_settings(self, settings):
        """Actualiza la configuración de voz durante la ejecución"""
        if not settings or not isinstance(settings, dict):
            return False
            
        try:
            # Actualizar configuración
            if "language" in settings:
                self.language = settings["language"]
            
            if "tld" in settings:
                self.tld = settings["tld"]
                
            if "speed" in settings:
                self.speed = float(settings["speed"])
                
            if "pitch" in settings:
                self.pitch = float(settings["pitch"])
                
            self.logger.info(f"Configuración de voz actualizada: idioma={self.language}, región={self.tld}, velocidad={self.speed}, tono={self.pitch}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al actualizar configuración de voz: {str(e)}")
            return False
    
    def is_available(self):
        """Verifica si el servicio de voz está disponible"""
        return self.is_running and (self.pygame_available or True)  # Siempre verdadero si está ejecutándose
    
    def test_voice(self, text="Esta es una prueba de la síntesis de voz"):
        """Realiza una prueba de la síntesis de voz con el texto proporcionado"""
        if not self.is_running:
            self.logger.warning("El servicio de voz no está en ejecución. Iniciándolo...")
            self.start()
            
        self.speak(text)
        return True