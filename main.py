"""
Sistema de Inteligencia Artificial Modular - Controlador Principal
Desarrollado para Su Majestad

Este módulo actúa como orquestador central del sistema de IA, inicializando
y coordinando todos los componentes del sistema.
"""

import os
import logging
import sys
import threading
import json
from datetime import datetime

# Importación de módulos personalizados
from modules.ml_engine import MLEngine
from modules.text_processor import TextProcessor
from modules.voice_manager import VoiceManager
from modules.knowledge_base import KnowledgeBase
from modules.config_manager import ConfigManager
from modules.gui import ApplicationGUI



def configure_robust_logging():
    """Implementa sistema de logging tolerante a codificaciones Unicode variable"""
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configurar handler de archivo con codificación explícita
    file_handler = logging.FileHandler('logs/ai_system.log', encoding='utf-8')
    
    # Configurar handler de consola con gestión de errores de codificación
    class EncodingCompatibleStreamHandler(logging.StreamHandler):
        def emit(self, record):
            try:
                msg = self.format(record)
                stream = self.stream
                stream.write(msg + self.terminator)
                self.flush()
            except UnicodeEncodeError:
                # Fallback a codificación ASCII con reemplazo de caracteres no ASCII
                stream.write(msg.encode('ascii', 'replace').decode('ascii') + self.terminator)
                self.flush()
    
    console_handler = EncodingCompatibleStreamHandler(sys.stdout)
    
    # Aplicar configuración
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[file_handler, console_handler]
    )

class AISystem:
    """Sistema de IA principal que coordina todos los componentes"""
    
    def __init__(self):
        """Inicializa el sistema y carga la configuración"""
        self.logger = logging.getLogger("AISystem")
        self.logger.info("Inicializando sistema de IA...")
        
        # Aseguramos que existan las carpetas necesarias
        self._ensure_directories()
        
        # Inicializamos el administrador de configuración
        self.config = ConfigManager("config/settings.json")
        
        # Inicializamos los componentes principales
        self.knowledge_base = KnowledgeBase(self.config.get("knowledge_base_path"))
        self.ml_engine = MLEngine(self.config.get("ml_model_path"), self.knowledge_base)
        self.text_processor = TextProcessor(self.config.get("language_model"))
        self.voice_manager = VoiceManager(self.config.get("voice_settings"))
        
        # Estado del sistema
        self.is_running = False
        self.conversation_history = []
        
        self.logger.info("Sistema de IA inicializado correctamente")
    
    def _ensure_directories(self):
        """Crea las carpetas necesarias si no existen"""
        directories = ["logs", "data", "models", "config", "resources", "conversation_history"]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logging.info(f"Directorio {directory} creado")
    
    def start(self):
        """Inicia todos los servicios de la IA y lanza la interfaz gráfica"""
        if self.is_running:
            self.logger.warning("El sistema ya está en ejecución")
            return
            
        self.logger.info("Iniciando sistema de IA...")
        
        # Iniciar componentes en hilos separados
        self.ml_engine.start()
        self.voice_manager.start()
        
        # Marcar como en ejecución
        self.is_running = True
        
        # Iniciar la interfaz gráfica (esto bloqueará hasta que se cierre la ventana)
        self.gui = ApplicationGUI(self)
        self.gui.run()
    
    def process_input(self, user_input, use_voice=True):
        """Procesa la entrada del usuario y genera una respuesta"""
        if not user_input.strip():
            return "Estoy esperando su comando, Su Majestad."
        
        # Registrar la entrada del usuario
        self.logger.info(f"Procesando entrada: {user_input}")
        self.conversation_history.append({"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()})
        
        # Procesar el texto usando NLP
        processed_input = self.text_processor.process(user_input)
        
        # Obtener respuesta del motor de ML
        response = self.ml_engine.generate_response(processed_input, self.conversation_history)
        
        # Registrar la respuesta
        self.logger.info(f"Respuesta generada: {response}")
        self.conversation_history.append({"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()})
        
        # Generar respuesta de voz si está habilitado
        if use_voice:
            threading.Thread(target=self.voice_manager.speak, args=(response,)).start()
        
        # Guardar historial de conversación periódicamente
        if len(self.conversation_history) % 10 == 0:
            self._save_conversation_history()
            
        return response
    
    def _save_conversation_history(self):
        """Guarda el historial de conversación en un archivo JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_history/conversation_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Historial de conversación guardado en {filename}")
    
    def shutdown(self):
        """Detiene todos los servicios y guarda el estado"""
        if not self.is_running:
            return
            
        self.logger.info("Apagando sistema de IA...")
        
        # Guardar historial de conversación
        self._save_conversation_history()
        
        # Detener componentes
        self.ml_engine.stop()
        self.voice_manager.stop()
        
        # Marcar como detenido
        self.is_running = False
        self.logger.info("Sistema de IA apagado correctamente")

if __name__ == "__main__":
    """Punto de entrada principal al sistema"""
    try:
        # Configurar sistema de logging robusto
        configure_robust_logging()
        
        # Inicializar sistema de IA
        ai_system = AISystem()
        
        # Iniciar interfaz (no devuelve hasta cerrar la ventana)
        exit_code = ai_system.start()
        
        # Salir con código de estado
        sys.exit(exit_code)
    except Exception as e:
        logging.error(f"Error fatal en el sistema: {str(e)}", exc_info=True)
    finally:
        logging.info("Sistema terminado")
