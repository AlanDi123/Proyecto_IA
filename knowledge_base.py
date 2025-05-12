"""
Base de Conocimiento - Sistema de Almacenamiento y Recuperación
Desarrollado para Su Majestad
"""

import os
import sqlite3
import logging
import uuid
import json
import re
from datetime import datetime

class KnowledgeBase:
    """Base de conocimiento para almacenar y recuperar información"""
    
    def __init__(self, db_file):
        """Inicializa la base de conocimiento con la ruta a la base de datos"""
        self.logger = logging.getLogger("KnowledgeBase")
        self.logger.info("Inicializando base de conocimiento...")
        
        self.db_file = db_file
        
        # Crear directorio si no existe
        db_dir = os.path.dirname(db_file)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Inicializar base de datos
        self._init_database()
        
        # Cargar respuestas predefinidas
        self.predefined_responses = self._load_predefined_responses()
        
        self.logger.info("Base de conocimiento inicializada correctamente")
    
    def _init_database(self):
        """Inicializa la estructura de la base de datos"""
        try:
            # Conectar a la base de datos (la crea si no existe)
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Crear tabla de hechos si no existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facts (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    category TEXT,
                    importance REAL DEFAULT 0.5,
                    timestamp TEXT
                )
            ''')
            
            # Crear tabla de etiquetas si no existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    fact_id TEXT,
                    tag TEXT,
                    FOREIGN KEY (fact_id) REFERENCES facts(id)
                )
            ''')
            
            # Crear índices para búsqueda rápida
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)')
            
            # Crear tabla de fuentes si no existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    fact_id TEXT,
                    source_type TEXT,
                    url TEXT,
                    title TEXT,
                    author TEXT,
                    publication_date TEXT,
                    FOREIGN KEY (fact_id) REFERENCES facts(id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Base de datos inicializada correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al inicializar base de datos: {str(e)}")
            return False
    
    def _load_predefined_responses(self):
        """Carga respuestas predefinidas desde archivo JSON"""
        responses = {
            "greeting": "Saludos, Su Majestad. ¿En qué puedo servirle hoy?",
            "farewell": "Ha sido un honor servirle, Su Majestad. Aquí estaré cuando me necesite.",
            "unknown": "Lamento no entender completamente su petición, Su Majestad. ¿Podría reformularla?",
            "thinking": "Procesando su solicitud, Su Majestad...",
            "error": "Lo siento, Su Majestad, estoy teniendo dificultades para procesar su solicitud en este momento."
        }
        
        # Intentar cargar desde archivo si existe
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            responses_file = os.path.join(base_dir, "data", "predefined_responses.json")
            
            if os.path.exists(responses_file):
                with open(responses_file, 'r', encoding='utf-8') as f:
                    loaded_responses = json.load(f)
                    
                    # Si el archivo tiene un formato diferente (array de opciones)
                    for key, value in loaded_responses.items():
                        if isinstance(value, list) and value:
                            responses[key] = value[0]  # Usar primera opción
                        else:
                            responses[key] = value
                            
            else:
                # Si no existe, crearlo con respuestas por defecto
                os.makedirs(os.path.dirname(responses_file), exist_ok=True)
                
                # Versión extendida para guardar
                extended_responses = {
                    "greeting": [
                        "Saludos, Su Majestad. ¿En qué puedo servirle hoy?",
                        "A sus órdenes, Mi Rey. ¿Cómo puedo asistirle?",
                        "Es un honor atenderle, Su Majestad. Estoy a su disposición."
                    ],
                    "farewell": [
                        "Ha sido un honor servirle, Su Majestad. Estaré aquí cuando me necesite.",
                        "Que tenga un excelente día, Mi Rey. Quedo a su disposición.",
                        "Me retiro a su orden, Su Majestad. Regresaré cuando lo solicite."
                    ],
                    "unknown": [
                        "Lamento no comprender completamente su solicitud, Su Majestad. ¿Podría reformularla?",
                        "Mi Rey, me temo que necesito más información para procesar adecuadamente su petición.",
                        "Su Majestad, permítame solicitar una aclaración para poder servirle mejor."
                    ],
                    "acknowledgment": [
                        "Entendido, Su Majestad.",
                        "A sus órdenes, Mi Rey.",
                        "Comprendido perfectamente, Su Alteza."
                    ]
                }
                
                with open(responses_file, 'w', encoding='utf-8') as f:
                    json.dump(extended_responses, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Error al cargar respuestas predefinidas: {str(e)}")
        
        return responses
    
    def add_fact(self, content, category=None, importance=0.5, tags=None, source=None):
        """
        Añade un nuevo hecho a la base de conocimiento
        
        Args:
            content (str): Contenido del hecho
            category (str, optional): Categoría del hecho
            importance (float, optional): Importancia del hecho (0-1)
            tags (list, optional): Lista de etiquetas
            source (dict, optional): Información sobre la fuente
            
        Returns:
            str: ID del hecho añadido o None si hay error
        """
        if not content or not isinstance(content, str):
            return None
        
        try:
            # Generar ID único
            fact_id = str(uuid.uuid4())
            
            # Preparar datos
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insertar en base de datos
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO facts (id, content, category, importance, timestamp) VALUES (?, ?, ?, ?, ?)',
                (fact_id, content, category, importance, timestamp)
            )
            
            # Insertar etiquetas si existen
            if tags and isinstance(tags, list):
                for tag in tags:
                    cursor.execute(
                        'INSERT INTO tags (fact_id, tag) VALUES (?, ?)',
                        (fact_id, tag)
                    )
            
            # Insertar información de fuente si existe
            if source and isinstance(source, dict):
                source_id = str(uuid.uuid4())
                
                cursor.execute(
                    '''INSERT INTO sources 
                       (id, fact_id, source_type, url, title, author, publication_date) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        source_id,
                        fact_id,
                        source.get('type', 'unknown'),
                        source.get('url', ''),
                        source.get('title', ''),
                        source.get('author', ''),
                        source.get('date', '')
                    )
                )
            
            conn.commit()
            conn.close()
            
            return fact_id
            
        except Exception as e:
            self.logger.error(f"Error al añadir hecho: {str(e)}")
            return None
    
    def search_facts(self, query, category=None, limit=10):
        """
        Busca hechos en la base de conocimiento
        
        Args:
            query (str): Texto a buscar
            category (str, optional): Filtrar por categoría
            limit (int, optional): Límite de resultados
            
        Returns:
            list: Lista de hechos encontrados
        """
        results = []
        
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row  # Para acceder a resultados por nombre
            cursor = conn.cursor()
            
            # Construir consulta SQL
            sql = 'SELECT f.*, s.url, s.title FROM facts f LEFT JOIN sources s ON f.id = s.fact_id WHERE 1=1'
            params = []
            
            # Añadir filtro de texto
            if query:
                sql += ' AND (f.content LIKE ? OR f.category LIKE ?)'
                params.extend([f'%{query}%', f'%{query}%'])
            
            # Añadir filtro de categoría
            if category:
                sql += ' AND f.category = ?'
                params.append(category)
            
            # Ordenar por importancia y limitar resultados
            sql += ' ORDER BY f.importance DESC LIMIT ?'
            params.append(limit)
            
            # Ejecutar consulta
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Convertir a lista de diccionarios
            for row in rows:
                fact = {
                    'id': row['id'],
                    'content': row['content'],
                    'category': row['category'],
                    'importance': row['importance'],
                    'timestamp': row['timestamp']
                }
                
                # Añadir fuente si existe
                if row['url'] or row['title']:
                    fact['source'] = {
                        'url': row['url'],
                        'title': row['title']
                    }
                    
                # Obtener etiquetas
                cursor.execute('SELECT tag FROM tags WHERE fact_id = ?', (row['id'],))
                tags = cursor.fetchall()
                
                if tags:
                    fact['tags'] = [tag[0] for tag in tags]
                
                results.append(fact)
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error al buscar hechos: {str(e)}")
        
        return results
    
    def get_predefined_response(self, input_text):
        """
        Obtiene una respuesta predefinida basada en el texto de entrada
        
        Args:
            input_text (str): Texto de entrada del usuario
            
        Returns:
            str: Respuesta predefinida
        """
        if not input_text or not isinstance(input_text, str):
            return self.predefined_responses.get("unknown", "No entiendo su solicitud, Su Majestad.")
        
        input_lower = input_text.lower()
        
        # Detectar saludos
        if any(greeting in input_lower for greeting in ["hola", "saludos", "buenos días", "buenas tardes", "buenas noches"]):
            return self.predefined_responses.get("greeting", "Saludos, Su Majestad.")
        
        # Detectar despedidas
        if any(farewell in input_lower for farewell in ["adiós", "hasta luego", "nos vemos", "chao"]):
            return self.predefined_responses.get("farewell", "Hasta pronto, Su Majestad.")
        
        # Buscar hechos relacionados
        facts = self.search_facts(input_text, limit=3)
        
        if facts:
            # Construir respuesta basada en hechos encontrados
            response = "Su Majestad, según mi conocimiento: "
            
            # Añadir hechos
            for i, fact in enumerate(facts):
                if i > 0:
                    response += " Además, "
                response += fact['content']
            
            # Añadir fuente si hay categoría
            if len(facts) > 0 and facts[0].get('category'):
                response += f" Esta información está relacionada con {facts[0]['category']}."
            
            return response
        
        # Respuesta por defecto
        return self.predefined_responses.get("unknown", "No tengo información sobre eso, Su Majestad.")

    def get_training_data(self, limit=1000):
        """
        Obtiene datos para entrenar el modelo de lenguaje
        
        Args:
            limit (int): Número máximo de hechos a retornar
            
        Returns:
            list: Lista de textos para entrenamiento
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Obtener todos los hechos
            cursor.execute(
                'SELECT content FROM facts ORDER BY importance DESC, timestamp DESC LIMIT ?',
                (limit,)
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            # Extraer contenido
            training_data = [row[0] for row in rows if row[0]]
            
            # Añadir respuestas predefinidas para mejorar el modelo
            for key, response in self.predefined_responses.items():
                if isinstance(response, list):
                    training_data.extend(response)
                else:
                    training_data.append(response)
            
            return training_data
            
        except Exception as e:
            self.logger.error(f"Error al obtener datos de entrenamiento: {str(e)}")
            return []