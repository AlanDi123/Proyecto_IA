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
    """Sistema de IA principal que coordina todos los componentes"""
    
    def __init__(self):
        """Inicializa el sistema y carga la configuración"""
        self.logger = logging.getLogger("AISystem")
        self.logger.info("Inicializando sistema de IA...")
        
        # Establecer el estado del sistema como no iniciado
        self.is_running = False
        
        # Aseguramos que existan las carpetas necesarias
        self._ensure_directories()
        
        try:
            # Inicializamos el administrador de configuración
            self.config = ConfigManager("config/settings.json")
            
            # Inicializamos los componentes principales con manejo de errores
            self._init_components()
            
            # Estado del sistema
            self.conversation_history = []
            
            self.logger.info("Sistema de IA inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar el sistema: {str(e)}")
            traceback.print_exc()
            raise
    
    def _ensure_directories(self):
        """Crea las carpetas necesarias si no existen"""
        directories = ["logs", "data", "models", "config", "resources", "conversation_history"]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"Directorio {directory} creado")
    
    def _init_components(self):
        """Inicializa los componentes del sistema con manejo de errores"""
        # Inicializar componentes con gestión de errores
        try:
            self.knowledge_base = KnowledgeBase(self.config.get("knowledge_base_path"))
        except Exception as e:
            self.logger.error(f"Error al inicializar base de conocimiento: {str(e)}")
            # Crear un valor por defecto para que el sistema pueda continuar
            self.knowledge_base = KnowledgeBase("data/knowledge")
        
        try:
            self.ml_engine = MLEngine(self.config.get("ml_model_path"), self.knowledge_base)
        except Exception as e:
            self.logger.error(f"Error al inicializar motor de ML: {str(e)}")
            # Crear un valor por defecto para que el sistema pueda continuar
            self.ml_engine = MLEngine("models", self.knowledge_base)
        
        try:
            self.text_processor = TextProcessor(self.config.get("language_model"))
        except Exception as e:
            self.logger.error(f"Error al inicializar procesador de texto: {str(e)}")
            # Crear un valor por defecto para que el sistema pueda continuar
            self.text_processor = TextProcessor({"language": "es", "model": "es_core_news_sm"})
        
        try:
            self.voice_manager = VoiceManager(self.config.get("voice_settings"))
        except Exception as e:
            self.logger.error(f"Error al inicializar gestor de voz: {str(e)}")
            # Crear un valor por defecto para que el sistema pueda continuar
            self.voice_manager = VoiceManager({"enabled": True, "language": "es", "tld": "com.mx"})
    
    def start(self):
        """Inicia todos los servicios de la IA y lanza la interfaz gráfica"""
        if self.is_running:
            self.logger.warning("El sistema ya está en ejecución")
            return
            
        self.logger.info("Iniciando sistema de IA...")
        
        try:
            # Iniciar componentes en hilos separados
            self.ml_engine.start()
            self.voice_manager.start()
            
            # Marcar como en ejecución
            self.is_running = True
            
            # Iniciar la interfaz gráfica (sin usar worker thread)
            self.gui = ApplicationGUI(self)
            return self.gui.run()  # Llamar directamente al método run de ApplicationGUI
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
            # Registrar la entrada del usuario
            self.logger.info(f"Procesando entrada: {user_input}")
            self.conversation_history.append({"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()})
            
            # Procesar el texto usando NLP
            try:
                processed_input = self.text_processor.process(user_input)
            except Exception as e:
                self.logger.error(f"Error al procesar texto: {str(e)}")
                processed_input = {"original": user_input, "processed": user_input}
            
            # Obtener respuesta del motor de ML
            try:
                response = self.ml_engine.generate_response(processed_input, self.conversation_history)
            except Exception as e:
                self.logger.error(f"Error al generar respuesta: {str(e)}")
                response = "Lo siento, Su Majestad, estoy teniendo dificultades para procesar su solicitud en este momento."
            
            # Registrar la respuesta
            self.logger.info(f"Respuesta generada: {response}")
            self.conversation_history.append({"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()})
            
            # Generar respuesta de voz si está habilitado
            if use_voice and response:
                try:
                    threading.Thread(target=self.voice_manager.speak, args=(response,)).start()
                except Exception as e:
                    self.logger.error(f"Error al iniciar síntesis de voz: {str(e)}")
            
            # Guardar historial de conversación periódicamente
            if len(self.conversation_history) % 10 == 0:
                self._save_conversation_history()
                
            return response
        except Exception as e:
            self.logger.error(f"Error al procesar entrada: {str(e)}")
            traceback.print_exc()
            return "Lo siento, Su Majestad, ha ocurrido un error al procesar su solicitud."
    
    def _save_conversation_history(self):
        """Guarda el historial de conversación en un archivo JSON"""
        try:
            if not os.path.exists("conversation_history"):
                os.makedirs("conversation_history")
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_history/conversation_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Historial de conversación guardado en {filename}")
        except Exception as e:
            self.logger.error(f"Error al guardar historial de conversación: {str(e)}")
    
    def shutdown(self):
        """Detiene todos los servicios y guarda el estado"""
        if not self.is_running:
            return
            
        self.logger.info("Apagando sistema de IA...")
        
        # Guardar historial de conversación
        self._save_conversation_history()
        
        # Detener componentes
        try:
            if hasattr(self, 'ml_engine'):
                self.ml_engine.stop()
        except Exception as e:
            self.logger.error(f"Error al detener motor ML: {str(e)}")
        
        try:
            if hasattr(self, 'voice_manager'):
                self.voice_manager.stop()
        except Exception as e:
            self.logger.error(f"Error al detener gestor de voz: {str(e)}")
        
        # Marcar como detenido
        self.is_running = False
        self.logger.info("Sistema de IA apagado correctamente")

def splash_screen():
    """Muestra una pantalla de bienvenida en la consola"""
    print("\n" + "="*80)
    print(" "*20 + "SISTEMA DE INTELIGENCIA ARTIFICIAL MODULAR")
    print(" "*20 + "Desarrollado para Su Majestad")
    print(" "*20 + "Versión 1.0.0")
    print("="*80 + "\n")
    print("Inicializando componentes...")
    
    # Pequeño spinner de carga
    for _ in range(5):
        for c in "|/-\\":
            sys.stdout.write(f"\r  {c} Cargando sistema...")
            sys.stdout.flush()
            time.sleep(0.1)
    
    print("\n\nSistema listo!\n")

if __name__ == "__main__":
    """Punto de entrada principal al sistema"""
    try:
        # Mostrar pantalla de inicio
        splash_screen()
        
        # Configurar sistema de logging robusto
        configure_robust_logging()
        
        # Inicializar sistema de IA
        ai_system = AISystem()
        
        # Iniciar interfaz (no devuelve hasta cerrar la ventana)
        exit_code = ai_system.start()
        
        # Salir con código de estado
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logging.info("Sistema interrumpido por el usuario")
        try:
            if 'ai_system' in locals():
                ai_system.shutdown()
        except:
            pass
    except Exception as e:
        logging.error(f"Error fatal en el sistema: {str(e)}", exc_info=True)
        traceback.print_exc()
    finally:
        logging.info("Sistema terminado")