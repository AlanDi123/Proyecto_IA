# modules/text_processor.py - Versión simplificada basada en NLTK

import logging
import re
import string
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import random

class TextProcessor:
    """Procesador de texto simplificado que usa solo NLTK"""
    
    def __init__(self):
        """Inicializa el procesador de texto"""
        self.logger = logging.getLogger("TextProcessor")
        self.logger.info("Inicializando procesador de texto...")
        
        # Descargar recursos de NLTK si no existen
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            self.logger.info("Descargando recurso NLTK: punkt")
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            self.logger.info("Descargando recurso NLTK: stopwords")
            nltk.download('stopwords', quiet=True)
        
        # Inicializar stemmer
        self.stemmer = SnowballStemmer('spanish')
        
        # Cargar stopwords
        self.stop_words = set(stopwords.words('spanish'))
        
        self.logger.info("Procesador de texto inicializado correctamente")
    
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
                'key_phrases': []
            }
        
        # Tokenizar texto
        tokens = word_tokenize(text.lower())
        
        # Eliminar puntuación y stopwords
        tokens = [token for token in tokens 
                 if token not in string.punctuation
                 and token not in self.stop_words
                 and len(token) > 1]
        
        # Obtener stems
        stems = [self.stemmer.stem(token) for token in tokens]
        
        # Extraer "entidades" básicas (palabras con mayúscula inicial)
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        entities = [{'text': word, 'type': 'MISC'} for word in words]
        
        # Extraer frases clave (simplemente n-gramas)
        key_phrases = self._extract_ngrams(tokens, 2) + self._extract_ngrams(tokens, 3)
        
        return {
            'tokens': tokens,
            'stems': stems,
            'entities': entities,
            'key_phrases': key_phrases
        }
    
    def _extract_ngrams(self, tokens, n):
        """Extrae n-gramas de una lista de tokens"""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i+n])
            ngrams.append(ngram)
        
        # Limitar y aleatorizar
        random.shuffle(ngrams)
        return ngrams[:min(5, len(ngrams))]
    
    def similarity(self, text1, text2):
        """
        Calcula similitud básica entre dos textos
        
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
        
        # Obtener tokens
        tokens1 = set(proc1['tokens'])
        tokens2 = set(proc2['tokens'])
        
        # Similitud Jaccard básica
        if not tokens1 or not tokens2:
            return 0.0
            
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union)
    
    def summarize(self, text, max_sentences=3):
        """
        Genera un resumen básico del texto
        
        Args:
            text (str): Texto a resumir
            max_sentences (int): Número máximo de frases
            
        Returns:
            str: Resumen del texto
        """
        if not text:
            return ""
            
        # Dividir en oraciones
        sentences = sent_tokenize(text)
        
        if len(sentences) <= max_sentences:
            return text
            
        # Procesar cada oración
        sentence_scores = []
        
        for sentence in sentences:
            # Calcular puntuación basada en longitud y palabras clave
            proc = self.process(sentence)
            
            # Puntuación basada en número de tokens no stopwords
            score = len(proc['tokens'])
            
            # Añadir puntuación extra por entidades
            score += len(proc['entities']) * 2
            
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
        
        # Reorganizar según aparición original
        original_order = []
        for sentence in sentences:
            if sentence in top_sentences:
                original_order.append(sentence)
                
        return " ".join(original_order)