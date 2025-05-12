"""
Base de Conocimiento - Repositorio Central de Información
Desarrollado para Su Majestad

Este módulo implementa la base de conocimiento que almacena, gestiona
y proporciona acceso a la información utilizada por el sistema de IA.
"""

import os
import json
import logging
import random
import re
import sqlite3
import time
from datetime import datetime
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class KnowledgeBase:
    """Gestor de la base de conocimiento del sistema"""
    
    def __init__(self, knowledge_path):
        """Inicializa la base de conocimiento"""
        self.logger = logging.getLogger("KnowledgeBase")
        self.logger.info("Inicializando base de conocimiento...")
        
        self.knowledge_path = knowledge_path
        
        # Crear directorios si no existen
        if not os.path.exists(knowledge_path):
            os.makedirs(knowledge_path)
            
        # Inicializar base de datos SQLite
        self.db_path = os.path.join(knowledge_path, "knowledge.db")
        self._initialize_database()
        
        # Inicializar vectorizador para búsqueda semántica
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents='unicode',
            ngram_range=(1, 2),
            max_df=0.85,
            min_df=2,
            max_features=10000
        )
        
        # Cargar respuestas predefinidas
        self.predefined_responses = self._load_predefined_responses()
        
        # Caché para vectorizaciones frecuentes
        self.vector_cache = {}
        
        self.logger.info("Base de conocimiento inicializada correctamente")
    
    def _initialize_database(self):
        """Crea o verifica la estructura de la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla para hechos/conceptos
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT,
                importance REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
            ''')
            
            # Tabla para conversaciones
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                system_response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                feedback INTEGER DEFAULT 0
            )
            ''')
            
            # Tabla para características lingüísticas del usuario
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_linguistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_type TEXT NOT NULL,
                feature_value TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Tabla para vectores semánticos
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS semantic_vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER,
                content_type TEXT NOT NULL,
                vector BLOB NOT NULL,
                FOREIGN KEY (content_id) REFERENCES facts(id) ON DELETE CASCADE
            )
            ''')
            
            # Índices para mejorar rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Base de datos inicializada correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar base de datos: {str(e)}")
    
    def _load_predefined_responses(self):
        """Carga respuestas predefinidas desde archivo JSON"""
        responses_file = os.path.join(self.knowledge_path, "predefined_responses.json")
        
        # Crear archivo de respuestas predefinidas si no existe
        if not os.path.exists(responses_file):
            default_responses = {
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
                json.dump(default_responses, f, ensure_ascii=False, indent=2)
            
            return default_responses
        
        # Cargar respuestas existentes
        try:
            with open(responses_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error al cargar respuestas predefinidas: {str(e)}")
            return {}
    
    def get_predefined_response(self, input_text):
        """Obtiene una respuesta predefinida basada en la entrada del usuario"""
        input_lower = input_text.lower()
        
        # Detectar saludos
        greeting_patterns = ["hola", "buenos días", "buenas tardes", "buenas noches", "saludos"]
        for pattern in greeting_patterns:
            if pattern in input_lower:
                if "greeting" in self.predefined_responses:
                    return random.choice(self.predefined_responses["greeting"])
        
        # Detectar despedidas
        farewell_patterns = ["adiós", "hasta luego", "chao", "nos vemos", "hasta pronto"]
        for pattern in farewell_patterns:
            if pattern in input_lower:
                if "farewell" in self.predefined_responses:
                    return random.choice(self.predefined_responses["farewell"])
        
        # Buscar respuesta basada en similitud semántica
        response = self._get_semantic_response(input_text)
        if response:
            return response
        
        # Si no hay coincidencia, devolver respuesta para desconocido
        if "unknown" in self.predefined_responses:
            return random.choice(self.predefined_responses["unknown"])
        
        return "No comprendo completamente su solicitud, Su Majestad. ¿Podría proporcionarme más detalles?"
    
    def _get_semantic_response(self, input_text):
        """Busca una respuesta basada en similitud semántica con conversaciones anteriores"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener últimas conversaciones
            cursor.execute('''
            SELECT user_input, system_response FROM conversations
            ORDER BY timestamp DESC LIMIT 100
            ''')
            
            conversations = cursor.fetchall()
            conn.close()
            
            if not conversations:
                return None
            
            # Preparar textos para vectorización
            user_inputs = [conv[0] for conv in conversations]
            
            # Vectorizar entrada actual y conversaciones previas
            if len(user_inputs) >= 5:  # Necesitamos suficientes ejemplos para vectorización efectiva
                try:
                    # Vectorizar
                    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
                    tfidf_matrix = vectorizer.fit_transform(user_inputs + [input_text])
                    
                    # Calcular similitud coseno
                    cosine_similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
                    
                    # Encontrar la conversación más similar
                    max_similarity_idx = np.argmax(cosine_similarities)
                    max_similarity = cosine_similarities[max_similarity_idx]
                    
                    # Si hay similitud suficiente, devolver la respuesta correspondiente
                    if max_similarity > 0.6:
                        return conversations[max_similarity_idx][1]
                except Exception as e:
                    self.logger.warning(f"Error en la vectorización durante búsqueda semántica: {str(e)}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda semántica: {str(e)}")
            return None
    
    def add_fact(self, content, category=None, importance=1.0):
        """Añade un nuevo hecho/concepto a la base de conocimiento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insertar nuevo hecho
            cursor.execute('''
            INSERT INTO facts (content, category, importance, created_at)
            VALUES (?, ?, ?, datetime('now'))
            ''', (content, category, importance))
            
            fact_id = cursor.lastrowid
            
            # Actualizar vectores semánticos
            self._update_semantic_vector(conn, fact_id, content, 'fact')
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Nuevo hecho añadido: ID {fact_id}, categoría {category}")
            return fact_id
            
        except Exception as e:
            self.logger.error(f"Error al añadir hecho: {str(e)}")
            return None
    
    def add_conversation(self, user_input, system_response, feedback=0):
        """Registra una conversación en la base de conocimiento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insertar conversación
            cursor.execute('''
            INSERT INTO conversations (user_input, system_response, timestamp, feedback)
            VALUES (?, ?, datetime('now'), ?)
            ''', (user_input, system_response, feedback))
            
            conversation_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Analizar características lingüísticas del usuario
            self._analyze_user_linguistics(user_input)
            
            return conversation_id
            
        except Exception as e:
            self.logger.error(f"Error al registrar conversación: {str(e)}")
            return None
    
    def _analyze_user_linguistics(self, text):
        """Analiza las características lingüísticas del texto del usuario"""
        try:
            # Analizar expresiones comunes
            common_phrases = re.findall(r'\b(\w+\s+\w+\s+\w+)\b', text.lower())
            
            # Analizar palabras frecuentes
            words = re.findall(r'\b(\w+)\b', text.lower())
            
            # Registrar en base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Registrar frases comunes
            for phrase in common_phrases:
                cursor.execute('''
                SELECT id, frequency FROM user_linguistics 
                WHERE feature_type = 'phrase' AND feature_value = ?
                ''', (phrase,))
                
                result = cursor.fetchone()
                
                if result:
                    cursor.execute('''
                    UPDATE user_linguistics 
                    SET frequency = ?, last_observed = datetime('now')
                    WHERE id = ?
                    ''', (result[1] + 1, result[0]))
                else:
                    cursor.execute('''
                    INSERT INTO user_linguistics (feature_type, feature_value, frequency, last_observed)
                    VALUES ('phrase', ?, 1, datetime('now'))
                    ''', (phrase,))
            
            # Registrar palabras frecuentes (solo las relevantes)
            stop_words = {"el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "a", "ante", "bajo", "con", 
                         "de", "desde", "en", "entre", "hacia", "hasta", "para", "por", "según", "sin", "sobre", "tras"}
            
            for word in words:
                if len(word) > 3 and word not in stop_words:
                    cursor.execute('''
                    SELECT id, frequency FROM user_linguistics 
                    WHERE feature_type = 'word' AND feature_value = ?
                    ''', (word,))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        cursor.execute('''
                        UPDATE user_linguistics 
                        SET frequency = ?, last_observed = datetime('now')
                        WHERE id = ?
                        ''', (result[1] + 1, result[0]))
                    else:
                        cursor.execute('''
                        INSERT INTO user_linguistics (feature_type, feature_value, frequency, last_observed)
                        VALUES ('word', ?, 1, datetime('now'))
                        ''', (word,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error al analizar lingüística: {str(e)}")
    
    def _update_semantic_vector(self, conn, content_id, content, content_type):
        """Actualiza vectores semánticos para búsqueda eficiente"""
        try:
            cursor = conn.cursor()
            
            # Verificar si tenemos suficientes datos para vectorización
            cursor.execute('SELECT COUNT(*) FROM facts')
            fact_count = cursor.fetchone()[0]
            
            if fact_count < 5:  # Necesitamos más datos para vectorización efectiva
                return
            
            # Obtener todos los contenidos para re-entrenar vectorizador
            cursor.execute('SELECT id, content FROM facts')
            facts = cursor.fetchall()
            
            fact_ids = [fact[0] for fact in facts]
            fact_contents = [fact[1] for fact in facts]
            
            # Entrenar vectorizador
            vectors = self.vectorizer.fit_transform(fact_contents)
            
            # Limpiar vectores anteriores
            cursor.execute('DELETE FROM semantic_vectors WHERE content_type = ?', (content_type,))
            
            # Guardar vectores
            for i in range(len(fact_ids)):
                vector_blob = vectors[i].toarray().tobytes()
                
                cursor.execute('''
                INSERT INTO semantic_vectors (content_id, content_type, vector)
                VALUES (?, ?, ?)
                ''', (fact_ids[i], content_type, vector_blob))
            
        except Exception as e:
            self.logger.error(f"Error al actualizar vectores semánticos: {str(e)}")
    
    def get_training_data(self):
        """Obtiene datos para entrenamiento del modelo de ML"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener hechos y conversaciones
            cursor.execute('SELECT content FROM facts')
            facts = [row[0] for row in cursor.fetchall()]
            
            cursor.execute('SELECT user_input, system_response FROM conversations')
            conversations = cursor.fetchall()
            
            conn.close()
            
            # Combinar datos para entrenamiento
            training_data = facts.copy()
            
            for user_input, system_response in conversations:
                training_data.append(user_input)
                training_data.append(system_response)
            
            return training_data
            
        except Exception as e:
            self.logger.error(f"Error al obtener datos de entrenamiento: {str(e)}")
            return []
    
    def get_facts_by_category(self, category):
        """Obtiene hechos/conceptos por categoría"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, content, importance FROM facts
            WHERE category = ?
            ORDER BY importance DESC
            ''', (category,))
            
            facts = cursor.fetchall()
            conn.close()
            
            # Actualizar estadísticas de acceso
            if facts:
                self._update_access_stats([fact[0] for fact in facts])
            
            return [{"id": fact[0], "content": fact[1], "importance": fact[2]} for fact in facts]
            
        except Exception as e:
            self.logger.error(f"Error al obtener hechos por categoría: {str(e)}")
            return []
    
    def search_facts(self, query, limit=10):
        """Busca hechos/conceptos por similitud con la consulta"""
        try:
            # Obtener todos los hechos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, content, category, importance FROM facts')
            facts = cursor.fetchall()
            
            if not facts:
                conn.close()
                return []
            
            # Preparar datos para vectorización
            fact_ids = [fact[0] for fact in facts]
            fact_contents = [fact[1] for fact in facts]
            
            # Vectorizar hechos y consulta
            tfidf_matrix = self.vectorizer.fit_transform(fact_contents + [query])
            
            # Calcular similitud
            cosine_similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
            
            # Combinar con importancia para ranking final
            rankings = []
            for i, (fact_id, _, _, importance) in enumerate(facts):
                similarity = cosine_similarities[i]
                # Fórmula de ranking: 70% similitud + 30% importancia
                combined_score = (0.7 * similarity) + (0.3 * float(importance))
                rankings.append((fact_id, combined_score))
            
            # Ordenar por ranking y obtener los mejores resultados
            rankings.sort(key=lambda x: x[1], reverse=True)
            top_fact_ids = [fact_id for fact_id, _ in rankings[:limit]]
            
            # Obtener información completa de los mejores resultados
            results = []
            for fact_id in top_fact_ids:
                for fact in facts:
                    if fact[0] == fact_id:
                        results.append({
                            "id": fact[0],
                            "content": fact[1],
                            "category": fact[2],
                            "importance": fact[3]
                        })
                        break
            
            conn.close()
            
            # Actualizar estadísticas de acceso
            if results:
                self._update_access_stats([r["id"] for r in results])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error al buscar hechos: {str(e)}")
            return []
    
    def _update_access_stats(self, fact_ids):
        """Actualiza estadísticas de acceso para hechos consultados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for fact_id in fact_ids:
                cursor.execute('''
                UPDATE facts 
                SET last_accessed = datetime('now'), 
                    access_count = access_count + 1
                WHERE id = ?
                ''', (fact_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error al actualizar estadísticas de acceso: {str(e)}")