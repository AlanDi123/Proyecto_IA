"""
Paquete de Módulos del Sistema de Inteligencia Artificial
Desarrollado para Su Majestad

Este paquete contiene todos los módulos necesarios para el funcionamiento
del sistema de inteligencia artificial con capacidades de aprendizaje automático.
"""

from .ml_engine import MLEngine
from .text_processor import TextProcessor
from .voice_manager import VoiceManager
from .knowledge_base import KnowledgeBase
from .config_manager import ConfigManager
from .gui import ApplicationGUI

__all__ = [
    'MLEngine',
    'TextProcessor',
    'VoiceManager',
    'KnowledgeBase',
    'ConfigManager',
    'ApplicationGUI'
]

__version__ = '1.0.0'