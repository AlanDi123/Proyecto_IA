# modules/content_moderator.py

import logging

class ContentModerator:
    """Sistema de moderación de contenido para el Sistema de IA - Sin restricciones"""
    
    def __init__(self):
        self.logger = logging.getLogger("ContentModerator")
        self.logger.info("Inicializando moderador de contenido...")
        self.logger.info("Moderador de contenido inicializado correctamente")
    
    def check_content(self, text):
        """Verifica si el contenido es apropiado - siempre retorna True"""
        return True, ""
    
    def sanitize_content(self, text):
        """No realiza sanitización - retorna el texto tal cual"""
        return text