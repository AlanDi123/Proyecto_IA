"""
Gestor de Configuración - Sistema de Gestión de Ajustes
Desarrollado para Su Majestad
"""

import os
import json
import logging

class ConfigManager:
    """Gestor de configuración del sistema"""
    
    def __init__(self, config_file):
        """Inicializa el gestor de configuración"""
        self.logger = logging.getLogger("ConfigManager")
        self.logger.info("Inicializando gestor de configuración...")
        
        self.config_file = config_file
        self.config = {}
        
        # Cargar configuración
        self.load()
        
        self.logger.info("Gestor de configuración inicializado correctamente")
    
    def load(self):
        """Carga la configuración desde el archivo"""
        try:
            # Verificar si el archivo existe
            if not os.path.exists(self.config_file):
                self.logger.warning(f"Archivo de configuración no encontrado: {self.config_file}")
                self._create_default_config()
                return
            
            # Cargar configuración
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                
            self.logger.info(f"Configuración cargada desde {self.config_file}")
            
        except json.JSONDecodeError:
            self.logger.error(f"Error al parsear archivo de configuración: {self.config_file}")
            self._create_default_config()
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {str(e)}")
            self._create_default_config()
    
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
        
        self.config = default_config
        
        try:
            # Crear directorio si no existe
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            # Guardar configuración
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
                
            self.logger.info(f"Configuración por defecto creada: {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error al crear configuración por defecto: {str(e)}")
    
    def save(self):
        """Guarda la configuración actual en el archivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
                
            self.logger.info(f"Configuración guardada en {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {str(e)}")
            return False
    
    def get(self, section, key, default=None):
        """
        Obtiene un valor de configuración
        
        Args:
            section (str): Sección de configuración
            key (str): Clave de configuración
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración o valor por defecto
        """
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def set(self, section, key, value):
        """
        Establece un valor de configuración
        
        Args:
            section (str): Sección de configuración
            key (str): Clave de configuración
            value: Valor a establecer
            
        Returns:
            bool: True si se estableció correctamente
        """
        try:
            # Crear sección si no existe
            if section not in self.config:
                self.config[section] = {}
                
            # Establecer valor
            self.config[section][key] = value
            
            # Guardar configuración
            return self.save()
        except Exception as e:
            self.logger.error(f"Error al establecer configuración: {str(e)}")
            return False