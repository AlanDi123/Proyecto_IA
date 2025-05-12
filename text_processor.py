"""
Procesador de Texto - Sistema de Análisis de Lenguaje Natural
Desarrollado para Su Majestad
"""

import os
import logging
import re
import string
import random
import nltk
import json
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

class TextProcessor:
    """Procesador de texto para análisis de lenguaje natural"""
    
    def __init__(self):
        """Inicializa el procesador de texto con NLTK"""
        self.logger = logging.getLogger("TextProcessor")
        self.logger.info("Inicializando procesador de texto...")
        
        # Descargar recursos de NLTK si no existen
        self._download_nltk_resources()
        
        # Inicializar stemmer
        self.stemmer = SnowballStemmer('spanish')
        
        # Cargar stopwords
        self.stop_words = set(stopwords.words('spanish'))
        
        # Carga vocabularios específicos
        self.vocabularies = self._load_vocabularies()
        
        self.logger.info("Vocabularios cargados correctamente")
        self.logger.info("Procesador de texto inicializado correctamente")
    
    def _download_nltk_resources(self):
        """Descarga recursos necesarios de NLTK"""
        resources = [
            ('tokenizers/punkt', 'punkt'),
            ('corpora/stopwords', 'stopwords')
        ]
        
        for resource_path, resource_name in resources:
            try:
                nltk.data.find(resource_path)
            except LookupError:
                self.logger.info(f"Descargando recurso NLTK: {resource_name}")
                nltk.download(resource_name, quiet=True)
    
    def _load_vocabularies(self):
        """Carga vocabularios específicos para análisis de intenciones y emociones"""
        vocabularies = {}
        
        # Definir rutas a archivos de vocabulario
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data", "vocabulary")
        
        # Crear directorio si no existe
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Archivos de vocabulario
        vocab_files = {
            "intent": os.path.join(data_dir, "intent_vocab.json"),
            "emotion": os.path.join(data_dir, "emotion_vocab.json")
        }
        
        # Contenido por defecto para los vocabularios
        default_vocabs = {
            "intent": {
                "greeting": ["hola", "buenos días", "buenas tardes", "buenas noches", "saludos"],
                "farewell": ["adiós", "hasta luego", "nos vemos", "hasta pronto", "chao"],
                "question": ["qué", "cómo", "cuándo", "dónde", "por qué", "cuál", "?"],
                "command": ["haz", "muestra", "dime", "busca", "encuentra", "abre"],
                "confirmation": ["sí", "claro", "por supuesto", "afirmativo", "correcto"],
                "negation": ["no", "nunca", "jamás", "negativo", "incorrecto"],
                "gratitude": ["gracias", "agradecido", "te lo agradezco"],
                "apology": ["perdón", "disculpa", "lo siento"]
            },
            "emotion": {
                "joy": ["feliz", "contento", "alegre", "divertido", "entusiasmado"],
                "sadness": ["triste", "deprimido", "melancólico", "desanimado"],
                "anger": ["enojado", "furioso", "irritado", "molesto"],
                "fear": ["miedo", "temor", "asustado", "preocupado"],
                "surprise": ["sorprendido", "asombrado", "impactado", "inesperado"],
                "neutral": ["neutro", "indiferente", "normal", "estándar"]
            }
        }
        
        # Cargar o crear vocabularios
        for vocab_name, vocab_file in vocab_files.items():
            try:
                if os.path.exists(vocab_file):
                    with open(vocab_file, 'r', encoding='utf-8') as f:
                        vocabularies[vocab_name] = json.load(f)
                else:
                    # Crear archivo con vocabulario por defecto
                    with open(vocab_file, 'w', encoding='utf-8') as f:
                        json.dump(default_vocabs[vocab_name], f, indent=2, ensure_ascii=False)
                    vocabularies[vocab_name] = default_vocabs[vocab_name]
            except Exception as e:
                self.logger.warning(f"Error al cargar vocabulario {vocab_name}: {str(e)}")
                vocabularies[vocab_name] = default_vocabs[vocab_name]
        
        return vocabularies
    
    def process(self, text):
        """
        Procesa un texto y extrae información relevante
        
        Args:
            text (str): Texto a procesar
            
        Returns:
            dict: Diccionario con tokens, entidades, frases clave, etc.
        """
        if not text or not isinstance(text, str):
            return {
                'tokens': [],
                'stems': [],
                'entities': [],
                'key_phrases': [],
                'intent': 'unknown',
                'emotion': 'neutral'
            }
        
        # Tokenizar texto
        try:
            sentences = sent_tokenize(text)
            tokens = []
            
            for sentence in sentences:
                tokens.extend(word_tokenize(sentence.lower()))
        except Exception as e:
            self.logger.error(f"Error al tokenizar texto: {str(e)}")
            tokens = text.lower().split()
        
        # Eliminar puntuación y stopwords
        filtered_tokens = [token for token in tokens 
                          if token not in string.punctuation
                          and token not in self.stop_words
                          and len(token) > 1]
        
        # Obtener stems
        stems = [self.stemmer.stem(token) for token in filtered_tokens]
        
        # Extraer "entidades" básicas (palabras con mayúscula inicial)
        entities = []
        entity_pattern = r'\b[A-Z][a-zA-Z]+\b'
        for match in re.finditer(entity_pattern, text):
            entity_text = match.group()
            entities.append({
                'text': entity_text,
                'type': 'MISC',  # Tipo genérico
                'start': match.start(),
                'end': match.end()
            })
        
        # Extraer frases clave (términos multipalabra relevantes)
        key_phrases = self._extract_key_phrases(text, filtered_tokens)
        
        # Detectar intención
        intent = self._detect_intent(text.lower(), filtered_tokens)
        
        # Detectar emoción
        emotion = self._detect_emotion(text.lower(), filtered_tokens)
        
        return {
            'tokens': filtered_tokens,
            'stems': stems,
            'entities': entities,
            'key_phrases': key_phrases,
            'intent': intent,
            'emotion': emotion
        }
    
    def _extract_key_phrases(self, text, tokens):
        """Extrae frases clave del texto"""
        # Extraer n-gramas (bigramas y trigramas)
        bigrams = self._extract_ngrams(tokens, 2)
        trigrams = self._extract_ngrams(tokens, 3)
        
        # Combinar y priorizar
        key_phrases = bigrams[:5] + trigrams[:3]
        
        # Limitar número total de frases clave
        return key_phrases[:7]
    
    def _extract_ngrams(self, tokens, n):
        """Extrae n-gramas de una lista de tokens"""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i+n])
            ngrams.append(ngram)
        
        # Aplicar una puntuación básica (simple)
        ngram_scores = []
        for ngram in ngrams:
            # Puntuación simplemente basada en longitud promedio de palabras
            words = ngram.split()
            avg_len = sum(len(word) for word in words) / len(words)
            score = avg_len / 3.0  # Normalizar
            
            ngram_scores.append((ngram, score))
        
        # Ordenar por puntuación y devolver solo los n-gramas
        ngram_scores.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in ngram_scores]
    
    def _detect_intent(self, text, tokens):
        """
        Detecta la intención del texto basado en vocabularios y patrones
        
        Returns:
            str: Nombre de la intención detectada
        """
        # Normalizar texto
        text_lower = text.lower()
        
        # Inicializar puntuaciones para cada intención
        intent_scores = {intent: 0 for intent in self.vocabularies['intent']}
        
        # Verificar presencia de términos de cada intención
        for intent, terms in self.vocabularies['intent'].items():
            # Puntuación por términos individuales
            for term in terms:
                if term in text_lower:
                    intent_scores[intent] += 1
                # Puntuación adicional para términos al inicio
                if text_lower.startswith(term):
                    intent_scores[intent] += 0.5
            
            # Puntuación adicional por tokens que coinciden exactamente
            for token in tokens:
                if token in terms:
                    intent_scores[intent] += 0.5
        
        # Añadir reglas específicas para ciertas intenciones
        if '?' in text:
            intent_scores['question'] += 1
        
        # Verificar si comienza con un verbo imperativo (comando)
        if tokens and tokens[0] in self.vocabularies['intent']['command']:
            intent_scores['command'] += 1
        
        # Determinar la intención con mayor puntuación
        max_intent = max(intent_scores.items(), key=lambda x: x[1])
        
        # Si ninguna intención tiene puntuación, devolver 'unknown'
        if max_intent[1] == 0:
            return 'unknown'
            
        return max_intent[0]
    
    def _detect_emotion(self, text, tokens):
        """
        Detecta la emoción dominante en el texto basado en vocabularios
        
        Returns:
            str: Nombre de la emoción detectada
        """
        # Normalizar texto
        text_lower = text.lower()
        
        # Inicializar puntuaciones para cada emoción
        emotion_scores = {emotion: 0 for emotion in self.vocabularies['emotion']}
        
        # Verificar presencia de términos de cada emoción
        for emotion, terms in self.vocabularies['emotion'].items():
            # Puntuación por términos individuales
            for term in terms:
                if term in text_lower:
                    emotion_scores[emotion] += 1
            
            # Puntuación adicional por tokens que coinciden exactamente
            for token in tokens:
                if token in terms:
                    emotion_scores[emotion] += 0.5
        
        # Determinar la emoción con mayor puntuación
        max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        # Si ninguna emoción tiene puntuación o todo es muy bajo, asignar neutral
        if max_emotion[1] <= 0.5:
            return 'neutral'
            
        return max_emotion[0]
    
    def similarity(self, text1, text2):
        """
        Calcula similitud entre dos textos usando coincidencia de tokens
        
        Args:
            text1 (str): Primer texto
            text2 (str): Segundo texto
            
        Returns:
            float: Valor de similitud entre 0 y 1
        """
        if not text1 or not text2:
            return 0.0
            
        # Procesar textos
        proc1 = self.process(text1)
        proc2 = self.process(text2)
        
        # Obtener tokens y stems
        tokens1 = set(proc1['tokens'])
        tokens2 = set(proc2['tokens'])
        
        stems1 = set(proc1['stems'])
        stems2 = set(proc2['stems'])
        
        # Si no hay tokens suficientes, devolver 0
        if len(tokens1) < 2 or len(tokens2) < 2:
            return 0.0
            
        # Similitud Jaccard (media entre tokens y stems)
        token_intersection = tokens1.intersection(tokens2)
        token_union = tokens1.union(tokens2)
        token_sim = len(token_intersection) / len(token_union) if token_union else 0
        
        stem_intersection = stems1.intersection(stems2)
        stem_union = stems1.union(stems2)
        stem_sim = len(stem_intersection) / len(stem_union) if stem_union else 0
        
        # Promedio ponderado (más peso a tokens que a stems)
        return (token_sim * 0.6) + (stem_sim * 0.4)
    
    def summarize(self, text, max_sentences=3):
        """
        Genera un resumen extractivo del texto
        
        Args:
            text (str): Texto a resumir
            max_sentences (int): Número máximo de frases
            
        Returns:
            str: Resumen del texto
        """
        if not text:
            return ""
            
        # Dividir en oraciones
        try:
            sentences = sent_tokenize(text)
        except Exception as e:
            self.logger.error(f"Error al dividir en oraciones: {str(e)}")
            # Fallback a división básica por puntos
            sentences = text.split('.')
            sentences = [s.strip() + '.' for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return text
            
        # Procesar cada oración
        sentence_scores = []
        
        for sentence in sentences:
            # Calcular puntuación basada en longitud y palabras clave
            proc = self.process(sentence)
            
            # Puntuación básica: longitud de tokens relevantes
            score = len(proc['tokens']) * 0.1
            
            # Añadir puntuación por entidades
            score += len(proc['entities']) * 0.5
            
            # Añadir puntuación por frases clave
            score += len(proc['key_phrases']) * 0.3
            
            # Normalizar por longitud (preferimos oraciones medias)
            length = len(sentence)
            if length < 20:
                score *= 0.5
            elif length > 200:
                score *= 0.7
                
            sentence_scores.append((sentence, score))
        
        # Ordenar por puntuación
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Tomar las mejores oraciones
        top_sentences = [s[0] for s in sentence_scores[:max_sentences]]
        
        # Reorganizar según aparición original para mantener coherencia
        original_order = []
        for sentence in sentences:
            if sentence in top_sentences:
                original_order.append(sentence)
                
        return " ".join(original_order)