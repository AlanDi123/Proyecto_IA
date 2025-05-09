"""
Procesador de Texto - Sistema de Análisis Lingüístico
Desarrollado para Su Majestad

Este módulo implementa las capacidades de procesamiento de lenguaje natural
para analizar, comprender y generar respuestas a las entradas de texto.
"""

import os
import re
import logging
import json
import string
import numpy as np
from collections import Counter, defaultdict
import spacy
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TextProcessor:
    """Procesador de lenguaje natural para análisis y comprensión de texto"""
    
    def __init__(self, language_model):
        """Inicializa el procesador de texto con el modelo de lenguaje especificado"""
        self.logger = logging.getLogger("TextProcessor")
        self.logger.info("Inicializando procesador de texto...")
        
        self.language_model = language_model
        
        # Cargar recursos de NLP
        self._load_nlp_resources()
        
        # Patrones de expresiones regulares comunes
        self.patterns = {
            'url': re.compile(r'https?://\S+|www\.\S+'),
            'email': re.compile(r'\S+@\S+\.\S+'),
            'emoji': re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE),
            'hashtag': re.compile(r'#\w+'),
            'mention': re.compile(r'@\w+'),
            'numbers': re.compile(r'\d+'),
            'special_chars': re.compile(r'[^\w\s]')
        }
        
        # Categorías de intenciones
        self.intent_categories = [
            'greeting', 'farewell', 'question', 'statement', 
            'command', 'confirmation', 'negation', 'gratitude',
            'apology', 'opinion', 'request', 'clarification'
        ]
        
        # Características emocionales
        self.emotion_categories = [
            'joy', 'sadness', 'anger', 'fear', 
            'surprise', 'disgust', 'neutral'
        ]
        
        # Cargar vocabulario de intenciones y emociones
        self._load_vocabulary()
        
        # Vectorizador para análisis semántico
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents='unicode',
            ngram_range=(1, 2),
            max_df=0.85,
            min_df=2,
            max_features=5000
        )
        
        self.logger.info("Procesador de texto inicializado correctamente")
    
    def _load_nlp_resources(self):
        """Carga recursos necesarios para procesamiento de lenguaje natural"""
        try:
            # Configuración y descarga de recursos de NLTK
            nltk_data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "nltk_data")
            if not os.path.exists(nltk_data_path):
                os.makedirs(nltk_data_path)
            
            nltk.data.path.append(nltk_data_path)
            
            # Descargar recursos de NLTK si no existen
            for resource in ['punkt', 'stopwords']:
                try:
                    nltk.data.find(f'tokenizers/{resource}')
                except LookupError:
                    self.logger.info(f"Descargando recurso NLTK: {resource}")
                    nltk.download(resource, download_dir=nltk_data_path, quiet=True)
            
            # Inicializar stemmer para español
            self.stemmer = SnowballStemmer('spanish')
            
            # Cargar lista de stopwords
            self.stop_words = set(stopwords.words('spanish'))
            
            # Cargar modelo spaCy para español
            try:
                self.nlp = spacy.load("es_core_news_md")
                self.logger.info("Modelo spaCy cargado correctamente")
            except OSError:
                self.logger.warning("Modelo spaCy no encontrado, utilizando modelo alternativo")
                # Fallback a un modelo más pequeño o integrado
                try:
                    self.nlp = spacy.load("es_core_news_sm")
                except OSError:
                    self.logger.warning("Ningún modelo spaCy disponible, se reducirá la funcionalidad")
                    self.nlp = None
        
        except Exception as e:
            self.logger.error(f"Error al cargar recursos NLP: {str(e)}")
            # Configuración básica en caso de error
            self.stemmer = None
            self.stop_words = set()
            self.nlp = None
    
    def _load_vocabulary(self):
        """Carga vocabularios para detección de intenciones y emociones"""
        try:
            # Rutas de archivos de vocabulario
            vocab_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "vocabulary")
            
            if not os.path.exists(vocab_dir):
                os.makedirs(vocab_dir)
                
            intent_file = os.path.join(vocab_dir, "intent_vocab.json")
            emotion_file = os.path.join(vocab_dir, "emotion_vocab.json")
            
            # Vocabulario de intenciones predeterminado
            default_intent_vocab = {
                'greeting': ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos', 'hey'],
                'farewell': ['adiós', 'hasta luego', 'nos vemos', 'hasta pronto', 'chao'],
                'question': ['qué', 'cómo', 'cuándo', 'dónde', 'por qué', 'cuál', '?'],
                'command': ['haz', 'muestra', 'dime', 'busca', 'encuentra', 'abre', 'ejecuta'],
                'confirmation': ['sí', 'claro', 'por supuesto', 'afirmativo', 'correcto', 'exacto'],
                'negation': ['no', 'nunca', 'jamás', 'negativo', 'incorrecto'],
                'gratitude': ['gracias', 'agradecido', 'te lo agradezco'],
                'apology': ['perdón', 'disculpa', 'lo siento'],
                'opinion': ['creo', 'pienso', 'considero', 'opino', 'me parece'],
                'request': ['podrías', 'puedes', 'te pido', 'quisiera', 'me gustaría'],
                'clarification': ['explica', 'aclara', 'no entiendo', 'confundido']
            }
            
            # Vocabulario de emociones predeterminado
            default_emotion_vocab = {
                'joy': ['feliz', 'contento', 'alegre', 'divertido', 'entusiasmado', 'encantado'],
                'sadness': ['triste', 'deprimido', 'melancólico', 'desanimado', 'abatido'],
                'anger': ['enojado', 'furioso', 'irritado', 'molesto', 'indignado'],
                'fear': ['miedo', 'temor', 'asustado', 'preocupado', 'nervioso'],
                'surprise': ['sorprendido', 'asombrado', 'impactado', 'increíble', 'inesperado'],
                'disgust': ['asco', 'repugnancia', 'desagrado', 'repulsión'],
                'neutral': ['neutro', 'indiferente', 'normal', 'estándar']
            }
            
            # Guardar vocabularios predeterminados si no existen
            if not os.path.exists(intent_file):
                with open(intent_file, 'w', encoding='utf-8') as f:
                    json.dump(default_intent_vocab, f, ensure_ascii=False, indent=2)
                self.intent_vocab = default_intent_vocab
            else:
                with open(intent_file, 'r', encoding='utf-8') as f:
                    self.intent_vocab = json.load(f)
            
            if not os.path.exists(emotion_file):
                with open(emotion_file, 'w', encoding='utf-8') as f:
                    json.dump(default_emotion_vocab, f, ensure_ascii=False, indent=2)
                self.emotion_vocab = default_emotion_vocab
            else:
                with open(emotion_file, 'r', encoding='utf-8') as f:
                    self.emotion_vocab = json.load(f)
                    
            self.logger.info("Vocabularios cargados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al cargar vocabularios: {str(e)}")
            # Usar vocabularios predeterminados en caso de error
            self.intent_vocab = default_intent_vocab
            self.emotion_vocab = default_emotion_vocab
    
    def process(self, text):
        """Procesa el texto de entrada y retorna información estructurada"""
        if not text or not text.strip():
            return {
                'original': '',
                'processed': '',
                'tokens': [],
                'sentences': [],
                'intent': 'unknown',
                'emotion': 'neutral',
                'entities': [],
                'key_phrases': []
            }
        
        try:
            # Normalizar texto
            processed_text = self._normalize_text(text)
            
            # Tokenización
            tokens = self._tokenize(processed_text)
            sentences = sent_tokenize(processed_text)
            
            # Análisis de intención y emoción
            intent = self._detect_intent(processed_text, tokens)
            emotion = self._detect_emotion(processed_text, tokens)
            
            # Extracción de entidades
            entities = self._extract_entities(text)
            
            # Extracción de frases clave
            key_phrases = self._extract_key_phrases(processed_text)
            
            result = {
                'original': text,
                'processed': processed_text,
                'tokens': tokens,
                'sentences': sentences,
                'intent': intent,
                'emotion': emotion,
                'entities': entities,
                'key_phrases': key_phrases
            }
            
            self.logger.info(f"Texto procesado: intención={intent}, emoción={emotion}, entidades={len(entities)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error al procesar texto: {str(e)}")
            # Retornar resultado básico en caso de error
            return {
                'original': text,
                'processed': text,
                'tokens': [],
                'sentences': [],
                'intent': 'unknown',
                'emotion': 'neutral',
                'entities': [],
                'key_phrases': []
            }
    
    def _normalize_text(self, text):
        """Normaliza el texto: elimina URLs, limpia espacios, etc."""
        # Convertir a minúsculas
        text = text.lower()
        
        # Eliminar URLs y correos
        text = self.patterns['url'].sub(' ', text)
        text = self.patterns['email'].sub(' ', text)
        
        # Remover hashtags y menciones
        text = self.patterns['hashtag'].sub(' ', text)
        text = self.patterns['mention'].sub(' ', text)
        
        # Eliminar emojis
        text = self.patterns['emoji'].sub(' ', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _tokenize(self, text):
        """Tokeniza el texto en palabras y elimina stopwords"""
        tokens = word_tokenize(text)
        
        # Filtrar stopwords
        tokens = [t for t in tokens if t not in self.stop_words and t not in string.punctuation]
        
        # Aplicar stemming si está disponible
        if self.stemmer:
            tokens = [self.stemmer.stem(t) for t in tokens]
        
        return tokens
    
    def _detect_intent(self, text, tokens):
        """Detecta la intención principal del texto"""
        # Conteo de palabras clave de intención
        intent_scores = {intent: 0 for intent in self.intent_categories}
        
        # Calcular puntuación para cada intención basada en palabras clave
        for intent, keywords in self.intent_vocab.items():
            for token in tokens:
                if token in keywords:
                    intent_scores[intent] += 1
        
        # Análisis de estructura gramatical
        # Preguntas
        if '?' in text or any(q in text for q in ['qué', 'cómo', 'cuándo', 'dónde', 'por qué', 'quién']):
            intent_scores['question'] += 3
        
        # Comandos (imperativos)
        command_verbs = ['haz', 'muestra', 'dime', 'busca', 'encuentra', 'abre', 'ejecuta']
        if any(v in tokens for v in command_verbs) and len(tokens) > 1:
            intent_scores['command'] += 2
        
        # Determinar intención dominante
        dominant_intent = max(intent_scores.items(), key=lambda x: x[1])
        
        # Si no hay una intención clara, analizar con spaCy si está disponible
        if dominant_intent[1] == 0 and self.nlp:
            doc = self.nlp(text)
            
            # Analizar verbos y estructura sintáctica
            verbs = [token.lemma_ for token in doc if token.pos_ == 'VERB']
            
            if verbs and verbs[0] in ['preguntar', 'saber', 'conocer']:
                return 'question'
            elif verbs and verbs[0] in ['hacer', 'mostrar', 'decir', 'buscar']:
                return 'command'
            elif any(token.text in ['gracias', 'agradecido'] for token in doc):
                return 'gratitude'
            else:
                return 'statement'
        
        # Si no hay puntuación o es igual para varias intenciones, usar 'statement' por defecto
        if dominant_intent[1] == 0:
            return 'statement'
        
        return dominant_intent[0]
    
    def _detect_emotion(self, text, tokens):
        """Detecta la emoción predominante en el texto"""
        # Conteo de palabras clave de emoción
        emotion_scores = {emotion: 0 for emotion in self.emotion_categories}
        
        # Calcular puntuación para cada emoción basada en palabras clave
        for emotion, keywords in self.emotion_vocab.items():
            for token in tokens:
                if token in keywords:
                    emotion_scores[emotion] += 1
        
        # Determinar emoción dominante
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        # Si no hay una emoción clara, usar 'neutral' por defecto
        if dominant_emotion[1] == 0:
            return 'neutral'
        
        return dominant_emotion[0]
    
    def _extract_entities(self, text):
        """Extrae entidades nombradas del texto"""
        entities = []
        
        # Usar spaCy para extracción de entidades si está disponible
        if self.nlp:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'type': ent.label_
                })
        # Fallback simple basado en patrones
        else:
            # Detectar fechas
            date_pattern = re.compile(r'\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2} de [a-z]+ de \d{2,4}')
            for match in date_pattern.finditer(text):
                entities.append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'type': 'DATE'
                })
            
            # Detectar cantidades
            number_pattern = re.compile(r'\d+(?:[.,]\d+)?')
            for match in number_pattern.finditer(text):
                entities.append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'type': 'QUANTITY'
                })
        
        return entities
    
    def _extract_key_phrases(self, text):
        """Extrae frases clave del texto basado en importancia"""
        key_phrases = []
        
        # Usar spaCy para análisis sintáctico si está disponible
        if self.nlp:
            doc = self.nlp(text)
            
            # Extraer sintagmas nominales (noun phrases)
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) > 1:  # Frases con más de una palabra
                    key_phrases.append(chunk.text)
            
            # Extraer verbos con sus objetos
            for token in doc:
                if token.pos_ == 'VERB' and token.dep_ == 'ROOT':
                    phrase = token.text
                    for child in token.children:
                        if child.dep_ in ['dobj', 'iobj']:
                            phrase = f"{phrase} {child.text}"
                    
                    if len(phrase.split()) > 1:
                        key_phrases.append(phrase)
        
        # Fallback simple basado en n-gramas
        else:
            # Crear n-gramas
            words = word_tokenize(text)
            bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
            trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
            
            # Filtrar n-gramas que contengan solo stopwords
            key_phrases = [ngram for ngram in bigrams + trigrams 
                           if not all(word in self.stop_words for word in ngram.split())]
        
        # Eliminar duplicados y limitar a un máximo de 5 frases
        key_phrases = list(set(key_phrases))[:5]
        
        return key_phrases
    
    def similarity(self, text1, text2):
        """Calcula la similitud semántica entre dos textos"""
        try:
            # Normalizar textos
            text1_norm = self._normalize_text(text1)
            text2_norm = self._normalize_text(text2)
            
            # Si los textos son idénticos, similitud máxima
            if text1_norm == text2_norm:
                return 1.0
            
            # Calcular similitud con spaCy si está disponible
            if self.nlp:
                doc1 = self.nlp(text1_norm)
                doc2 = self.nlp(text2_norm)
                return doc1.similarity(doc2)
            
            # Fallback a TF-IDF con similitud coseno
            tfidf_matrix = self.vectorizer.fit_transform([text1_norm, text2_norm])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(cosine_sim)
            
        except Exception as e:
            self.logger.error(f"Error al calcular similitud: {str(e)}")
            # Similitud mínima en caso de error
            return 0.0
    
    def extract_context(self, user_input, conversation_history):
        """Extrae información contextual de la conversación"""
        context = {
            'references': {},  # Referencias pronominales
            'topics': set(),   # Temas de la conversación
            'entities': [],    # Entidades mencionadas
            'state': {}        # Estado de la conversación
        }
        
        try:
            # Extraer temas de las últimas entradas de la conversación
            recent_exchanges = []
            for entry in conversation_history[-5:]:
                if 'content' in entry:
                    recent_exchanges.append(entry['content'])
            
            all_text = ' '.join(recent_exchanges + [user_input])
            
            # Usar spaCy para análisis contextual si está disponible
            if self.nlp:
                doc = self.nlp(all_text)
                
                # Extraer entidades
                for ent in doc.ents:
                    context['entities'].append({
                        'text': ent.text,
                        'type': ent.label_
                    })
                    context['topics'].add(ent.text.lower())
                
                # Identificar posibles referencias pronominales
                pronoun_refs = {}
                
                for sent in doc.sents:
                    for token in sent:
                        if token.pos_ == 'PRON':
                            # Buscar el antecedente más cercano
                            for ancestor in token.ancestors:
                                if ancestor.pos_ in ['NOUN', 'PROPN']:
                                    pronoun_refs[token.text] = ancestor.text
                                    break
                
                context['references'] = pronoun_refs
                
                # Detectar temas adicionales basados en sustantivos frecuentes
                nouns = [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN']]
                noun_freq = Counter(nouns)
                
                # Añadir los sustantivos más frecuentes como temas
                for noun, freq in noun_freq.most_common(5):
                    if freq > 1:  # Mencionado más de una vez
                        context['topics'].add(noun.lower())
            
            # Convertir set a lista para serialización
            context['topics'] = list(context['topics'])
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error al extraer contexto: {str(e)}")
            # Contexto básico en caso de error
            return {
                'references': {},
                'topics': [],
                'entities': [],
                'state': {}
            }
    
    def generate_response_template(self, processed_input):
        """Genera una plantilla de respuesta basada en el análisis del texto"""
        try:
            intent = processed_input.get('intent', 'unknown')
            emotion = processed_input.get('emotion', 'neutral')
            
            templates = {
                'greeting': [
                    "Saludos, Su Majestad. {topic}",
                    "A sus órdenes, Mi Rey. {topic}",
                    "Es un honor atenderle, Su Majestad. {topic}"
                ],
                'farewell': [
                    "Ha sido un honor servirle, Su Majestad. {topic}",
                    "Como ordene, Mi Rey. {topic}",
                    "Quedo a su disposición para cuando me necesite nuevamente, Su Majestad. {topic}"
                ],
                'question': [
                    "En respuesta a su consulta, Su Majestad: {topic}",
                    "La respuesta a su pregunta es, Mi Rey: {topic}",
                    "Permitame informarle, Su Majestad: {topic}"
                ],
                'command': [
                    "De inmediato, Su Majestad. {topic}",
                    "Ejecutando su orden, Mi Rey. {topic}",
                    "Como usted ordene, Su Majestad. {topic}"
                ],
                'statement': [
                    "En efecto, Su Majestad. {topic}",
                    "Así es, Mi Rey. {topic}",
                    "Comprendo su punto, Su Majestad. {topic}"
                ],
                'unknown': [
                    "Entendido, Su Majestad. {topic}",
                    "A sus órdenes, Mi Rey. {topic}",
                    "Como usted indique, Su Majestad. {topic}"
                ]
            }
            
            # Seleccionar plantilla según intención
            if intent in templates:
                selected_template = np.random.choice(templates[intent])
            else:
                selected_template = np.random.choice(templates['unknown'])
            
            # Incluir placeholder para la respuesta específica
            template = selected_template.format(topic="{response_content}")
            
            return template
            
        except Exception as e:
            self.logger.error(f"Error al generar plantilla: {str(e)}")
            # Plantilla genérica en caso de error
            return "Su Majestad, {response_content}"