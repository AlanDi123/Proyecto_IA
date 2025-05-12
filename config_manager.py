"""
Gestor de Configuración - Sistema de Administración de Parámetros
Desarrollado para Su Majestad

Este módulo implementa la gestión de configuración del sistema,
permitiendo cargar, guardar y administrar parámetros de operación.
"""

import os
import json
import logging
import time
from datetime import datetime

class ConfigManager:
    """Gestor de configuración para carga y persistencia de parámetros del sistema"""
    
    def __init__(self, config_file_path):
        """Inicializa el gestor de configuración con la ruta al archivo de configuración"""
        self.logger = logging.getLogger("ConfigManager")
        self.logger.info("Inicializando gestor de configuración...")
        
        self.config_file = config_file_path
        self.config_data = {}
        self.default_config = {}
        
        # Definir configuración predeterminada
        self._set_default_config()
        
        # Cargar configuración
        self._load_config()
        
        self.logger.info("Gestor de configuración inicializado correctamente")
    
    def _set_default_config(self):
        """Define la configuración predeterminada del sistema"""
        # Rutas de directorios
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.default_config = {
            # Rutas del sistema
            "knowledge_base_path": os.path.join(base_dir, "data", "knowledge"),
            "ml_model_path": os.path.join(base_dir, "models"),
            "logs_path": os.path.join(base_dir, "logs"),
            "resources_path": os.path.join(base_dir, "resources"),
            
            # Configuración de modelo de lenguaje
            "language_model": {
                "language": "es",
                "model": "es_core_news_md",
                "use_gpu": False,
                "max_sequence_length": 100,
                "embedding_dimension": 256
            },
            
            # Configuración de voz
            "voice_settings": {
                "enabled": True,
                "language": "es",
                "tld": "com.mx",  # Dominio para acento latinoamericano
                "speed": 1.0,
                "pitch": 1.0,
                "volume": 1.0
            },
            
            # Configuración de interfaz
            "ui_settings": {
                "theme": "dark",
                "font_size": 10,
                "window_width": 1024,
                "window_height": 768,
                "show_welcome": True
            },
            
            # Configuración de aprendizaje automático
            "ml_settings": {
                "continuous_learning": True,
                "training_interval": 3600,  # Segundos entre ciclos de entrenamiento
                "batch_size": 64,
                "epochs": 5,
                "learning_rate": 0.001,
                "validation_split": 0.2,
                "save_checkpoints": True
            },
            
            # Configuración del sistema
            "system_settings": {
                "auto_start": False,
                "save_conversations": True,
                "max_conversation_history": 100,
                "auto_update": True,
                "debug_mode": False,
                "startup_script": None
            },
            
            # Información de versión
            "version": {
                "major": 1,
                "minor": 0,
                "patch": 0,
                "build_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    
    def _load_config(self):
        """Carga la configuración desde el archivo o crea una nueva"""
        try:
            # Verificar si existe el directorio de configuración
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # Verificar si existe el archivo de configuración
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    try:
                        self.config_data = json.load(f)
                    except json.JSONDecodeError:
                        self.logger.error(f"Error en el formato del archivo de configuración. Usando valores predeterminados.")
                        self.config_data = self.default_config.copy()
                        self._save_config()
                        return
                    
                # Validar configuración cargada y completar con valores predeterminados si faltan
                self._validate_config()
                
                self.logger.info(f"Configuración cargada desde {self.config_file}")
            else:
                # Crear archivo de configuración con valores predeterminados
                self.config_data = self.default_config.copy()
                self._save_config()
                
                self.logger.info(f"Creado nuevo archivo de configuración en {self.config_file}")
        
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {str(e)}")
            # Usar configuración predeterminada en caso de error
            self.config_data = self.default_config.copy()
    
    def _validate_config(self):
        """Valida la configuración y completa valores faltantes"""
        # Verificar cada sección y parámetro
        for section, params in self.default_config.items():
            if section not in self.config_data:
                self.config_data[section] = params
                continue
            
            if isinstance(params, dict):
                # Recursivamente verificar parámetros anidados
                self._check_nested_params(section, params, self.config_data[section])
    
    def _check_nested_params(self, section_path, default_params, config_params):
        """Verifica y completa parámetros anidados faltantes"""
        for key, default_value in default_params.items():
            if key not in config_params:
                config_params[key] = default_value
                self.logger.info(f"Añadido parámetro faltante: {section_path}.{key}")
            elif isinstance(default_value, dict) and isinstance(config_params[key], dict):
                # Recursivamente verificar parámetros anidados
                self._check_nested_params(f"{section_path}.{key}", default_value, config_params[key])
    
    def _save_config(self):
        """Guarda la configuración actual en el archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Configuración guardada en {self.config_file}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {str(e)}")
            return False
    
    def get(self, key, default=None):
        """Obtiene un valor de configuración por su clave"""
        try:
            # Soporte para acceso a parámetros anidados con notación de punto
            if '.' in key:
                keys = key.split('.')
                value = self.config_data
                
                for k in keys:
                    if k in value:
                        value = value[k]
                    else:
                        return default
                
                return value
            
            # Acceso directo para claves de primer nivel
            return self.config_data.get(key, default)
            
        except Exception as e:
            self.logger.error(f"Error al obtener parámetro '{key}': {str(e)}")
            return default
    
    def set(self, key, value):
        """Establece un valor de configuración por su clave"""
        try:
            # Soporte para acceso a parámetros anidados con notación de punto
            if '.' in key:
                keys = key.split('.')
                config = self.config_data
                
                # Navegar hasta el parámetro anidado
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                
                # Establecer el valor
                config[keys[-1]] = value
            else:
                # Establecer directamente para claves de primer nivel
                self.config_data[key] = value
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al establecer parámetro '{key}': {str(e)}")
            return False
    
    def save(self):
        """Guarda la configuración actual"""
        return self._save_config()
    
    def reset(self, key=None):
        """Restablece la configuración a valores predeterminados"""
        try:
            if key is None:
                # Restablecer toda la configuración
                self.config_data = self.default_config.copy()
                return self._save_config()
            
            # Restablecer un parámetro específico
            if '.' in key:
                keys = key.split('.')
                default_value = self.default_config
                
                # Navegar hasta el valor predeterminado
                for k in keys:
                    if k in default_value:
                        default_value = default_value[k]
                    else:
                        return False
                
                # Establecer el valor predeterminado
                return self.set(key, default_value)
            
            # Restablecer parámetro de primer nivel
            if key in self.default_config:
                self.config_data[key] = self.default_config[key]
                return self._save_config()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error al restablecer configuración: {str(e)}")
            return False
    
    def get_all(self):
        """Obtiene toda la configuración como un diccionario"""
        return self.config_data.copy()
    
    def backup(self):
        """Crea una copia de seguridad de la configuración actual"""
        try:
            # Generar nombre para la copia de seguridad
            backup_dir = os.path.join(os.path.dirname(self.config_file), "backups")
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"config_backup_{timestamp}.json")
            
            # Crear copia de seguridad
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Creada copia de seguridad en {backup_file}")
            return backup_file
            
        except Exception as e:
            self.logger.error(f"Error al crear copia de seguridad: {str(e)}")
            return None
    
    def restore(self, backup_file):
        """Restaura la configuración desde una copia de seguridad"""
        try:
            if not os.path.exists(backup_file):
                self.logger.error(f"Archivo de copia de seguridad no encontrado: {backup_file}")
                return False
            
            # Cargar configuración desde copia de seguridad
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_config = json.load(f)
            
            # Validar configuración restaurada
            original_config = self.config_data.copy()
            self.config_data = backup_config
            
            # Validar y completar con valores predeterminados si es necesario
            self._validate_config()
            
            # Guardar configuración restaurada
            result = self._save_config()
            
            if not result:
                # Restaurar configuración original en caso de error
                self.config_data = original_config
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error al restaurar configuración: {str(e)}")
            return False
    
    def export_config(self, export_file):
        """Exporta la configuración a un archivo externo"""
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Configuración exportada a {export_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al exportar configuración: {str(e)}")
            return False
    
    def import_config(self, import_file):
        """Importa configuración desde un archivo externo"""
        try:
            if not os.path.exists(import_file):
                self.logger.error(f"Archivo de importación no encontrado: {import_file}")
                return False
            
            # Crear copia de seguridad antes de importar
            self.backup()
            
            # Cargar configuración a importar
            with open(import_file, 'r', encoding='utf-8') as f:
                import_config = json.load(f)
            
            # Validar configuración importada
            original_config = self.config_data.copy()
            self.config_data = import_config
            
            # Validar y completar con valores predeterminados si es necesario
            self._validate_config()
            
            # Guardar configuración importada
            result = self._save_config()
            
            if not result:
                # Restaurar configuración original en caso de error
                self.config_data = original_config
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error al importar configuración: {str(e)}")
            return False