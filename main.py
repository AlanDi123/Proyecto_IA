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

# Configurar variables de entorno para PyQt
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['QT_SCALE_FACTOR'] = '1'

import logging
import sys
import json
import traceback
import time
from datetime import datetime
import importlib.util
import pkg_resources

# Configurar logging
def configure_logging():
    """Configura el sistema de registro (logging)"""
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configurar formato y nivel de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/ai_system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

# Verificación de dependencias críticas
def check_dependencies():
    """Verifica que las dependencias críticas estén instaladas"""
    required_packages = {
        'tensorflow': '2.10.0',
        'numpy': '1.22.0',
        'PyQt6': '6.2.0',
        'nltk': '3.7',
        'gtts': '2.2.4',
        'pygame': '2.1.2'
    }
    
    missing_packages = []
    
    for package, min_version in required_packages.items():
        try:
            # Verificar si el paquete está instalado
            spec = importlib.util.find_spec(package)
            if spec is None:
                missing_packages.append(f"{package} (>={min_version})")
                continue
            
            # Verificar la versión instalada
            try:
                installed_version = pkg_resources.get_distribution(package).version
                if pkg_resources.parse_version(installed_version) < pkg_resources.parse_version(min_version):
                    missing_packages.append(f"{package} (>={min_version}, found {installed_version})")
            except:
                # Si no podemos verificar la versión, continuamos
                pass
                
        except ModuleNotFoundError:
            missing_packages.append(f"{package} (>={min_version})")
    
    if missing_packages:
        logging.error("Faltan dependencias requeridas:")
        for package in missing_packages:
            logging.error(f"  - {package}")
        logging.error("Ejecute 'pip install -r requirements.txt' para instalar todas las dependencias")
        return False
    
    return True

# Configurar logging antes que nada
configure_logging()

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
    from modules.knowledge_harvester import KnowledgeHarvester 
    from modules.content_moderator import ContentModerator
except ImportError as e:
    logging.error(f"Error al importar módulos personalizados: {str(e)}")
    logging.error("Asegúrese de que todos los archivos estén en las ubicaciones correctas")
    sys.exit(1)

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
            "voice_settings": {
                "enabled": True,
                "language": "es",
                "tld": "com.mx",
                "speed": 1.0,
                "volume": 1.0
            },
            "knowledge": {
                "auto_harvesting": True,
                "harvesting_interval": 3600
            },
            "ml_settings": {
                "continuous_learning": true,
                "training_interval": 86400,
                "batch_size": 64,
                "epochs": 5,
                "learning_rate": 0.001,
                "validation_split": 0.2,
                "model_backup_interval": 604800
            },
            "ui_settings": {
                "theme": "dark",
                "font_size": 10,
                "window_width": 1024,
                "window_height": 768,
                "show_welcome": true
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
        # Inicializar componentes en orden de dependencia
        self.components = {}
        
        # 1. Config Manager (primero, ya que otros componentes lo necesitan)
        try:
            self.config_manager = ConfigManager(self.config_file)
            self.components['config_manager'] = self.config_manager
        except Exception as e:
            self.logger.error(f"Error al inicializar gestor de configuración: {str(e)}")
            self.config_manager = None
        
        # 2. Knowledge Base
        try:
            self.knowledge_base = KnowledgeBase(self.db_file)
            self.components['knowledge_base'] = self.knowledge_base
        except Exception as e:
            self.logger.error(f"Error al inicializar base de conocimiento: {str(e)}")
            self.knowledge_base = None
        
        # 3. Text Processor
        try:
            self.text_processor = TextProcessor()
            self.components['text_processor'] = self.text_processor
        except Exception as e:
            self.logger.error(f"Error al inicializar procesador de texto: {str(e)}")
            self.text_processor = None
        
        # 4. Voice Manager
        try:
            self.voice_manager = VoiceManager()
            
            # Configurar según settings si está disponible
            if self.config_manager:
                lang = self.config_manager.get('voice_settings', 'language', 'es')
                tld = self.config_manager.get('voice_settings', 'tld', 'com.mx')
                
                if hasattr(self.voice_manager, 'set_language'):
                    self.voice_manager.set_language(lang)
                
                if hasattr(self.voice_manager, 'set_voice'):
                    self.voice_manager.set_voice(tld)
                    self.components['voice_manager'] = self.voice_manager
        except Exception as e:
            self.logger.error(f"Error al inicializar gestor de voz: {str(e)}")
            self.voice_manager = None
        
        # 5. Content Moderator
        try:
            self.content_moderator = ContentModerator()
            self.components['content_moderator'] = self.content_moderator
        except Exception as e:
            self.logger.error(f"Error al inicializar moderador de contenido: {str(e)}")
            self.content_moderator = None
        
        # 6. ML Engine (depende de knowledge_base)
        try:
            if self.knowledge_base:
                # Configurar opciones desde el archivo de configuración
                max_seq_length = 100
                embedding_dim = 256
                
                if self.config_manager:
                    max_seq_length = self.config_manager.get('language_model', 'max_sequence_length', 100)
                    embedding_dim = self.config_manager.get('language_model', 'embedding_dimension', 256)
                
                self.ml_engine = MLEngine(
                    model_path=self.models_dir,
                    knowledge_base=self.knowledge_base,
                    max_sequence_length=max_seq_length,
                    embedding_dim=embedding_dim
                )
                self.components['ml_engine'] = self.ml_engine
            else:
                self.logger.error("No se puede inicializar ML Engine: knowledge_base no disponible")
                self.ml_engine = None
        except Exception as e:
            self.logger.error(f"Error al inicializar motor ML: {str(e)}")
            self.ml_engine = None
        
        # 7. Knowledge Harvester (depende de knowledge_base y text_processor)
        try:
            if self.knowledge_base and self.text_processor:
                self.knowledge_harvester = KnowledgeHarvester(self.knowledge_base, self.text_processor)
                self.components['knowledge_harvester'] = self.knowledge_harvester
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
            return 0
        
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
            try:
                self.gui = ApplicationGUI(self)
                return self.gui.run()
            except Exception as e:
                self.logger.error(f"Error al iniciar la interfaz gráfica: {str(e)}")
                self.shutdown()
                return 1
                
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
                # Usar respuesta predefinida si no está disponible el motor ML
                if self.knowledge_base:
                    response = self.knowledge_base.get_predefined_response(user_input)
                else:
                    response = "Lo siento, Su Majestad, el motor de procesamiento no está disponible en este momento."
            
            # Guardar respuesta en historial
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Generar respuesta de voz si está habilitado
            if use_voice and self.voice_manager and self.voice_manager.is_running:
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
        
        # Detener componentes en orden inverso a la inicialización
        components_to_stop = ['knowledge_harvester', 'ml_engine', 'voice_manager']
        
        for component_name in components_to_stop:
            if component_name in self.components:
                component = self.components[component_name]
                try:
                    if hasattr(component, 'stop'):
                        component.stop()
                        self.logger.info(f"Componente {component_name} detenido correctamente")
                except Exception as e:
                    self.logger.error(f"Error al detener {component_name}: {str(e)}")
        
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