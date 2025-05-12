"""
Recolector de Conocimiento - Sistema de Adquisición Continua
Desarrollado para Su Majestad
"""

import os
import time
import logging
import threading
import random
import re
import html.parser
import urllib.request
import urllib.parse
import urllib.error
from urllib.parse import quote_plus, urlparse
from nltk.tokenize import sent_tokenize
import queue
import json
import socket

# Configuración de timeout para conexiones
socket.setdefaulttimeout(15)  # 15 segundos

class HTMLExtractor(html.parser.HTMLParser):
    """Extractor de texto HTML usando el parser nativo de Python"""
    
    def __init__(self):
        super().__init__()
        self.reset()
        self.text_parts = []
        self.in_paragraph = False
        self.in_script = False
        self.in_style = False
        self.in_header = False
        self.in_footer = False
        self.in_nav = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.in_paragraph = True
        elif tag in ['script', 'style', 'header', 'footer', 'nav']:
            setattr(self, f'in_{tag}', True)
            
    def handle_endtag(self, tag):
        if tag == 'p':
            self.in_paragraph = False
            self.text_parts.append(' ')  # Separar párrafos con espacios
        elif tag in ['script', 'style', 'header', 'footer', 'nav']:
            setattr(self, f'in_{tag}', False)
            
    def handle_data(self, data):
        if (not self.in_script and not self.in_style and 
            not self.in_header and not self.in_footer and 
            not self.in_nav):
            # Si estamos en un párrafo o en texto relevante
            text = data.strip()
            if text:
                self.text_parts.append(text)
                
    def get_text(self):
        return ' '.join(self.text_parts)

class KnowledgeHarvester:
    """Recolector de conocimiento desde fuentes en línea"""
    
    def __init__(self, knowledge_base, text_processor):
        """Inicializa el recolector de conocimiento"""
        self.logger = logging.getLogger("KnowledgeHarvester")
        self.logger.info("Inicializando recolector de conocimiento...")
        
        self.knowledge_base = knowledge_base
        self.text_processor = text_processor
        
        # Cola de temas para investigar
        self.topic_queue = queue.Queue()
        
        # Estado del recolector
        self.is_running = False
        self.pause_between_requests = 10  # segundos entre solicitudes para evitar bloqueos
        
        # Temas iniciales para explorar (generales para comenzar)
        self.seed_topics = [
            "inteligencia artificial aplicaciones",
            "procesamiento lenguaje natural avances",
            "historia de la computación",
            "algoritmos de aprendizaje automático",
            "filosofía del conocimiento",
            "ciencia de datos conceptos básicos",
            "desarrollo de software principios",
            "interfaz humano-computadora",
            "síntesis de voz tecnologías",
            "tendencias tecnológicas actuales"
        ]
        
        # Limitar el número máximo de hechos a almacenar para evitar sobrecarga
        self.max_facts_per_topic = 20
        
        # Headers para parecer un navegador normal
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
        }
        
        self.logger.info("Recolector de conocimiento inicializado correctamente")
    
    def start(self):
        """Inicia el recolector de conocimiento en segundo plano"""
        if self.is_running:
            return True
            
        self.is_running = True
        self.logger.info("Iniciando recolector de conocimiento...")
        
        # Añadir temas iniciales a la cola
        for topic in self.seed_topics:
            self.topic_queue.put(topic)
        
        # Iniciar hilo para recolección continua
        self.harvester_thread = threading.Thread(target=self._continuous_harvesting)
        self.harvester_thread.daemon = True
        self.harvester_thread.start()
        
        self.logger.info("Recolector de conocimiento iniciado en segundo plano")
        return True
    
    def stop(self):
        """Detiene el recolector de conocimiento"""
        if not self.is_running:
            return True
            
        self.logger.info("Deteniendo recolector de conocimiento...")
        self.is_running = False
        
        # Esperar a que termine el hilo
        if hasattr(self, 'harvester_thread') and self.harvester_thread.is_alive():
            try:
                self.harvester_thread.join(timeout=5.0)  # Esperar máximo 5 segundos
            except Exception as e:
                self.logger.warning(f"Error al esperar finalización del hilo: {str(e)}")
        
        self.logger.info("Recolector de conocimiento detenido")
        return True
    
    def add_topic(self, topic):
        """Añade un nuevo tema a la cola de investigación sin restricciones"""
        if not topic or not isinstance(topic, str):
            return False, "El tema debe ser un texto válido"
        
        self.topic_queue.put(topic)
        self.logger.info(f"Tema añadido a la cola: {topic}")
        return True, f"Tema '{topic}' añadido correctamente a la cola de investigación"
    
    def get_status(self):
        """Devuelve el estado actual del recolector"""
        status = "En ejecución" if self.is_running else "Detenido"
        queue_size = self.topic_queue.qsize()
        return {
            "status": status,
            "queue_size": queue_size,
            "is_running": self.is_running
        }
    
    def _continuous_harvesting(self):
        """Proceso continuo de recolección de conocimiento"""
        topics_explored = set()  # Para evitar repetir temas
        
        while self.is_running:
            try:
                # Obtener siguiente tema de la cola (con timeout para poder verificar is_running)
                try:
                    topic = self.topic_queue.get(timeout=1.0)
                except queue.Empty:
                    # Si la cola está vacía, generar un tema aleatorio basado en el conocimiento actual
                    self._generate_new_topics()
                    continue
                
                # Evitar repetir temas
                if topic in topics_explored:
                    self.topic_queue.task_done()
                    continue
                
                topics_explored.add(topic)
                
                # Realizar búsqueda para el tema
                self.logger.info(f"Investigando tema: {topic}")
                articles = self._search_for_information(topic)
                
                # Procesar artículos encontrados
                facts_added = 0
                for article in articles:
                    # Verificar si tenemos suficientes hechos para este tema
                    if facts_added >= self.max_facts_per_topic:
                        break
                        
                    # Extraer contenido y añadir a la base de conocimiento
                    content = self._extract_content(article['url'])
                    if not content:
                        continue
                    
                    # Procesar y segmentar contenido
                    facts = self._extract_facts(content, topic)
                    importance = 0.7  # Importancia media para hechos de internet
                    
                    # Añadir hechos a la base de conocimiento
                    for fact in facts[:self.max_facts_per_topic - facts_added]:
                        fact_id = self.knowledge_base.add_fact(fact, category=topic, importance=importance)
                        if fact_id:
                            facts_added += 1
                            
                            # Extraer posibles subtemas para investigar más tarde
                            if random.random() < 0.3:  # 30% de probabilidad
                                subtopic = self._extract_subtopic(fact)
                                if subtopic and subtopic not in topics_explored:
                                    self.topic_queue.put(subtopic)
                
                self.logger.info(f"Añadidos {facts_added} hechos sobre: {topic}")
                
                # Marcar como procesado en la cola
                self.topic_queue.task_done()
                
                # Pausa para evitar solicitudes muy frecuentes
                time.sleep(self.pause_between_requests)
                
            except Exception as e:
                self.logger.error(f"Error en recolección de conocimiento: {str(e)}")
                time.sleep(30)  # Pausa más larga en caso de error
    
    def _search_for_information(self, query):
        """Realiza una búsqueda y devuelve los resultados usando urllib en lugar de requests"""
        try:
            # Codificar consulta para URL
            encoded_query = quote_plus(query)
            
            # Usar URL de búsqueda más simple
            search_url = f"https://www.bing.com/search?q={encoded_query}&setlang=es"
            
            # Crear solicitud con urllib
            request = urllib.request.Request(
                search_url,
                headers=self.headers
            )
            
            # Realizar solicitud
            try:
                with urllib.request.urlopen(request) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
            except urllib.error.URLError as e:
                self.logger.warning(f"Error al realizar solicitud: {str(e)}")
                # Retornar resultado simulado
                return [{
                    'title': f'Información sobre {query}',
                    'url': f'https://es.wikipedia.org/wiki/{query.replace(" ", "_")}'
                }]
            
            # Extraer enlaces usando regex
            url_pattern = r'<a href="(https?://[^"]+)"[^>]*>[^<]+</a>'
            matches = re.findall(url_pattern, html_content)
            
            # Filtrar y limpiar resultados
            results = []
            for url in matches:
                # Ignorar URLs de buscadores y sitios irrelevantes
                if not any(x in url for x in ['bing.com/search', 'google.com/search', 'accounts.', 'policies.', 'preferences']):
                    # Extraer título (simplificado)
                    title_match = re.search(r'<a href="' + re.escape(url) + r'"[^>]*>([^<]+)</a>', html_content)
                    title = title_match.group(1) if title_match else "Sin título"
                    
                    results.append({
                        'title': title,
                        'url': url
                    })
                    
                    # Limitar a 5 resultados
                    if len(results) >= 5:
                        break
            
            # Si no hay resultados, añadir un resultado simulado
            if not results:
                results.append({
                    'title': f'Información sobre {query}',
                    'url': f'https://es.wikipedia.org/wiki/{query.replace(" ", "_")}'
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error al buscar información: {str(e)}")
            # Retornar un resultado simulado en caso de error
            return [{
                'title': f'Información sobre {query}',
                'url': f'https://es.wikipedia.org/wiki/{query.replace(" ", "_")}'
            }]
    
    def _extract_content(self, url):
        """Extrae contenido de una página web usando urllib en lugar de requests"""
        try:
            # Crear solicitud
            request = urllib.request.Request(url, headers=self.headers)
            
            # Realizar solicitud
            try:
                with urllib.request.urlopen(request) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
            except urllib.error.URLError as e:
                self.logger.warning(f"Error al acceder a URL {url}: {str(e)}")
                return ""
            
            # Usar el parser HTML nativo de Python
            parser = HTMLExtractor()
            parser.feed(html_content)
            content = parser.get_text()
            
            # Limpiar espacios múltiples
            content = re.sub(r'\s+', ' ', content).strip()
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error al extraer contenido: {str(e)}")
            return ""
    
    def _extract_facts(self, content, topic):
        """Extrae hechos relevantes del contenido"""
        try:
            # Dividir en oraciones
            sentences = sent_tokenize(content)
            
            # Filtrar oraciones muy cortas o muy largas
            filtered_sentences = [s for s in sentences if 20 < len(s) < 300]
            
            # Si hay pocas oraciones, usar todas
            if len(filtered_sentences) < 10:
                return filtered_sentences
            
            # Usar procesador de texto para determinar relevancia
            facts = []
            
            for sentence in filtered_sentences:
                # Evitar oraciones con demasiados enlaces o simbolos
                if sentence.count('http') > 0 or sentence.count('%') > 3:
                    continue
                    
                # Analizar relevancia al tema
                processed = self.text_processor.process(sentence)
                
                # Añadir si contiene entidades o frases clave
                if processed['entities'] or processed['key_phrases']:
                    facts.append(sentence)
                    continue
                
                # Calcular similitud con el tema
                similarity = self.text_processor.similarity(topic, sentence)
                if similarity > 0.2:  # Umbral de similitud
                    facts.append(sentence)
            
            # Limitar número de hechos y aleatorizar para variedad
            random.shuffle(facts)
            return facts[:30]  # Tomar máximo 30 hechos
            
        except Exception as e:
            self.logger.error(f"Error al extraer hechos: {str(e)}")
            return []
    
    def _extract_subtopic(self, fact):
        """Extrae posibles subtemas para explorar a partir de un hecho"""
        try:
            # Procesar el texto para extraer entidades y frases clave
            processed = self.text_processor.process(fact)
            
            # Candidatos para subtemas
            candidates = []
            
            # Añadir entidades
            for entity in processed['entities']:
                candidates.append(entity['text'])
            
            # Añadir frases clave
            candidates.extend(processed['key_phrases'])
            
            # Si no hay candidatos, devolver nada
            if not candidates:
                return None
                
            # Seleccionar un candidato aleatorio
            subtopic = random.choice(candidates)
            
            # Limitar longitud
            if len(subtopic) > 50:
                subtopic = subtopic[:50]
                
            return subtopic
            
        except Exception as e:
            self.logger.error(f"Error al extraer subtema: {str(e)}")
            return None
    
    def _generate_new_topics(self):
        """Genera nuevos temas basados en la base de conocimiento"""
        try:
            # Obtener categorías existentes
            facts = self.knowledge_base.search_facts("", limit=100)
            
            categories = set()
            for fact in facts:
                if fact.get('category'):
                    categories.add(fact['category'])
            
            # Si no hay categorías, utilizar semillas
            if not categories:
                for topic in random.sample(self.seed_topics, min(3, len(self.seed_topics))):
                    self.topic_queue.put(topic)
                return
            
            # Seleccionar categorías aleatorias para ampliar
            selected_categories = random.sample(list(categories), min(3, len(categories)))
            
            for category in selected_categories:
                # Buscar variaciones
                variations = [
                    f"{category} avances recientes",
                    f"{category} historia",
                    f"{category} aplicaciones",
                    f"{category} futuro",
                    f"problemas en {category}"
                ]
                
                # Añadir una variación aleatoria
                self.topic_queue.put(random.choice(variations))
                
        except Exception as e:
            self.logger.error(f"Error al generar nuevos temas: {str(e)}")
            # Fallback a temas iniciales
            for topic in random.sample(self.seed_topics, 3):
                self.topic_queue.put(topic)