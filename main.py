"""
Sistema de Inteligencia Artificial Modular - Controlador Principal
Desarrollado para Su Majestad

Este módulo actúa como orquestador central del sistema de IA, inicializando
y coordinando todos los componentes del sistema.
"""

import os
# Suprimir mensajes de TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=todo, 1=INFO, 2=WARNING, 3=ERROR
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Desactivar operaciones oneDNN
import logging
import sys
import threading
import json
import traceback
import time
from datetime import datetime
from modules.knowledge_harvester import KnowledgeHarvester
from modules.content_moderator import ContentModerator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def fix_qt_display_issue():
    import os
    # Establecer estas variables de entorno puede ayudar en algunos sistemas
    os.environ['QT_QPA_PLATFORM'] = 'xcb'  # Para Linux
    # os.environ['QT_QPA_PLATFORM'] = 'windows'  # Para Windows
    # os.environ['QT_QPA_PLATFORM'] = 'cocoa'  # Para macOS
    
    # Deshabilitar effects de Qt6 que pueden causar problemas
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    os.environ['QT_SCALE_FACTOR'] = '1'

# Verificación de dependencias críticas antes de importar módulos personalizados
def check_dependencies():
    """Verifica que las dependencias críticas estén instaladas"""
    try:
        import tensorflow as tf
        import numpy as np
        import spacy
        import nltk
        import PyQt6
        return True
    except ImportError as e:
        print(f"Error: Falta una dependencia crítica: {str(e)}")
        print("Ejecute 'pip install -r requirements.txt' para instalar todas las dependencias")
        return False

# Verificar dependencias antes de continuar
if not check_dependencies():
    sys.exit(1)

# Importación de módulos personalizados
try:
    from modules.ml_engine import MLEngine
    from modules.text_processor import TextProcessor
    from modules.voice_manager import VoiceManager
    from modules.knowledge_base import KnowledgeBase
    from modules.config_manager import ConfigManager
    from modules.gui import ApplicationGUI
except ImportError as e:
    print(f"Error al importar módulos personalizados: {str(e)}")
    print("Asegúrese de que todos los archivos estén en las ubicaciones correctas")
    sys.exit(1)

def configure_robust_logging():
    """Implementa sistema de logging tolerante a codificaciones Unicode variable"""
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Generar nombre de archivo de log con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f'logs/ai_system_{timestamp}.log'
    
    # Configurar handler de archivo con codificación explícita
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    
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
    
    # Formatear mensajes de log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Aplicar configuración
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Redirigir excepciones no capturadas al log
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # No manejar Ctrl+C
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        # Registrar la excepción en el log
        logger = logging.getLogger('root')
        logger.error("Excepción no capturada:", exc_info=(exc_type, exc_value, exc_traceback))
        
    sys.excepthook = handle_exception

class AISystem:
    """Clase principal del sistema de IA"""
    
    def __init__(self):
        """Inicializa el sistema de IA"""
        self.logger = logging.getLogger("AISystem")
        self.logger.info("Inicializando sistema de IA...")
        
        # Definir rutas de archivos y directorios importantes
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = os.path.join(self.base_dir, "config")
        self.models_dir = os.path.join(self.base_dir, "models")
        self.data_dir = os.path.join(self.base_dir, "data")
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.conversation_dir = os.path.join(self.base_dir, "conversation_history")
        
        # Crear directorios si no existen
        for directory in [self.config_dir, self.models_dir, self.data_dir, 
                         self.logs_dir, self.conversation_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Definir rutas a archivos específicos
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.db_file = os.path.join(self.data_dir, "knowledge.db")
        
        # Crear archivo de configuración básico si no existe
        if not os.path.exists(self.config_file):
            self._create_default_config()
        
        # Estado del sistema
        self.is_running = False
        self.conversation_history = []
        
        # Inicializar componentes
        self._init_components()
        
        self.logger.info("Sistema de IA inicializado correctamente")
    
    def _create_default_config(self):
        """Crea un archivo de configuración por defecto"""
        default_config = {
            "system": {
                "name": "Asistente IA",
                "version": "1.0.0",
                "log_level": "INFO"
            },
            "voice": {
                "enabled": True,
                "language": "es",
                "voice_id": "com.mx",
                "rate": 1.0,
                "volume": 1.0
            },
            "knowledge": {
                "auto_harvesting": True,
                "harvesting_interval": 3600
            },
            "ml": {
                "training_interval": 86400,
                "model_backup_interval": 604800
            },
            "gui": {
                "theme": "dark",
                "font_size": 12,
                "window_width": 1200,
                "window_height": 800
            }
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            self.logger.info(f"Archivo de configuración por defecto creado: {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error al crear configuración por defecto: {str(e)}")
    
    def _init_components(self):
        """Inicializa los componentes del sistema con manejo de errores"""
        # Inicializar gestor de configuración PRIMERO
        try:
            self.config_manager = ConfigManager(self.config_file)
        except Exception as e:
            self.logger.error(f"Error al inicializar gestor de configuración: {str(e)}")
            self.config_manager = None
        
        # Inicializar base de conocimiento
        try:
            self.knowledge_base = KnowledgeBase(self.db_file)
        except Exception as e:
            self.logger.error(f"Error al inicializar base de conocimiento: {str(e)}")
            self.knowledge_base = None
        
        # Inicializar procesador de texto
        try:
            self.text_processor = TextProcessor()
        except Exception as e:
            self.logger.error(f"Error al inicializar procesador de texto: {str(e)}")
            self.text_processor = None
        
        # Inicializar moderador de contenido (sin restricciones)
        try:
            self.content_moderator = ContentModerator()
        except Exception as e:
            self.logger.error(f"Error al inicializar moderador de contenido: {str(e)}")
            self.content_moderator = None
        
        # Inicializar motor ML
        try:
            if self.knowledge_base:
                self.ml_engine = MLEngine(
                    model_path=self.models_dir,
                    knowledge_base=self.knowledge_base,
                    max_sequence_length=100,
                    embedding_dim=256
                )
            else:
                self.logger.error("No se puede inicializar ML Engine: knowledge_base no disponible")
                self.ml_engine = None
        except Exception as e:
            self.logger.error(f"Error al inicializar motor ML: {str(e)}")
            self.ml_engine = None
        
        # Inicializar gestor de voz
        try:
            self.voice_manager = VoiceManager()
            
            # Configurarlo (opcional, si está implementado)
            if hasattr(self.voice_manager, 'set_language') and self.config_manager:
                self.voice_manager.set_language(
                    self.config_manager.get('voice', 'language', default='es')
                )
            if hasattr(self.voice_manager, 'set_voice') and self.config_manager:
                self.voice_manager.set_voice(
                    self.config_manager.get('voice', 'voice_id', default='com.mx')
                )
        except Exception as e:
            self.logger.error(f"Error al inicializar gestor de voz: {str(e)}")
            self.voice_manager = None
        
        # AHORA inicializar el recolector de conocimiento (DESPUÉS de KB y text_processor)
        try:
            if self.knowledge_base and self.text_processor:
                self.knowledge_harvester = KnowledgeHarvester(self.knowledge_base, self.text_processor)
                self.logger.info("Recolector de conocimiento inicializado correctamente")
            else:
                self.logger.error("No se pudo inicializar recolector: falta knowledge_base o text_processor")
                self.knowledge_harvester = None
        except Exception as e:
            self.logger.error(f"Error al inicializar recolector de conocimiento: {str(e)}")
            self.knowledge_harvester = None
    
    def start(self):
        """Inicia todos los servicios de la IA y lanza la interfaz gráfica"""
        if self.is_running:
            self.logger.warning("El sistema ya está en ejecución")
            return
        
        self.logger.info("Iniciando sistema de IA...")
        
        try:
            # Iniciar componentes en hilos separados si están disponibles
            if self.ml_engine:
                self.ml_engine.start()
            else:
                self.logger.warning("ML Engine no disponible, no se iniciará")
                
            if self.voice_manager:
                self.voice_manager.start()
            else:
                self.logger.warning("Voice Manager no disponible, no se iniciará")
            
            # No iniciamos el recolector automáticamente, se hará desde la interfaz
            
            # Marcar como en ejecución
            self.is_running = True
            
            # Iniciar la interfaz gráfica
            self.gui = ApplicationGUI(self)
            return self.gui.run()
        except Exception as e:
            self.logger.error(f"Error al iniciar el sistema: {str(e)}")
            traceback.print_exc()
            self.shutdown()
            return 1
    
    def process_input(self, user_input, use_voice=True):
        """Procesa la entrada del usuario y genera una respuesta"""
        if not user_input or not isinstance(user_input, str):
            return "Estoy esperando su comando, Su Majestad."
        
        try:
            # Guardar entrada en historial
            self.conversation_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Generar respuesta usando el motor ML
            if self.ml_engine:
                response = self.ml_engine.generate_response(user_input, self.conversation_history)
            else:
                response = "Lo siento, Su Majestad, el motor de procesamiento no está disponible en este momento."
            
            # Guardar respuesta en historial
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Generar respuesta de voz si está habilitado
            if use_voice and self.voice_manager:
                self.voice_manager.speak(response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error al procesar entrada: {str(e)}")
            return f"Lo siento, Su Majestad, he tenido un problema al procesar su solicitud. ({str(e)})"
    
    def shutdown(self):
        """Detiene todos los servicios y guarda el estado"""
        if not self.is_running:
            return
        
        self.logger.info("Apagando sistema de IA...")
        
        # Guardar historial de conversación
        try:
            if self.conversation_history:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                history_file = os.path.join(self.conversation_dir, f"conversation_{timestamp}.json")
                
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(self.conversation_history, f, indent=4, ensure_ascii=False)
                
                self.logger.info(f"Historial de conversación guardado en {history_file}")
        except Exception as e:
            self.logger.error(f"Error al guardar historial: {str(e)}")
        
        # Detener componentes en orden inverso
        try:
            if hasattr(self, 'ml_engine') and self.ml_engine:
                self.ml_engine.stop()
        except Exception as e:
            self.logger.error(f"Error al detener motor ML: {str(e)}")
        
        try:
            if hasattr(self, 'voice_manager') and self.voice_manager:
                self.voice_manager.stop()
        except Exception as e:
            self.logger.error(f"Error al detener gestor de voz: {str(e)}")
        
        try:
            if hasattr(self, 'knowledge_harvester') and self.knowledge_harvester and self.knowledge_harvester.is_running:
                self.knowledge_harvester.stop()
        except Exception as e:
            self.logger.error(f"Error al detener recolector de conocimiento: {str(e)}")
        
        self.is_running = False
        self.logger.info("Sistema de IA apagado correctamente")

# Función principal para ejecutar el sistema
def main():
    """Función principal para iniciar el sistema"""
    print("="*80)
    print("                    SISTEMA DE INTELIGENCIA ARTIFICIAL MODULAR")
    print("                    Desarrollado para Su Majestad")
    print("                    Versión 1.0.0")
    print("="*80)
    print("Inicializando componentes...")
    print("  \\ Cargando sistema...")
    
    # Crear e iniciar sistema
    system = AISystem()
    print("Sistema listo!")
    
    # Ejecutar sistema
    result = system.start()
    
    logging.info("Sistema terminado")
    return result

# Punto de entrada
if __name__ == "__main__":
    sys.exit(main())