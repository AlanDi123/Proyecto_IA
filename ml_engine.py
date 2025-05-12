"""
Motor de Aprendizaje Automático - Núcleo de Procesamiento Cognitivo
Desarrollado para Su Majestad

Este módulo implementa el sistema de aprendizaje automático que potencia
las capacidades de procesamiento y generación de respuestas de la IA.
"""

import os
import re
import time
import logging
import threading
import numpy as np
import pickle
from datetime import datetime
import tensorflow as tf
from tensorflow import Sequential, load_model, Model
from tensorflow import Dense, LSTM, Embedding, Input, Dropout, Bidirectional
from tensorflow import Adam
from tensorflow import ModelCheckpoint, EarlyStopping
from tensorflow import Tokenizer
from tensorflow import pad_sequences

class MLEngine:
    """Motor de aprendizaje automático y generación de respuestas"""
    
    def __init__(self, model_path, knowledge_base, max_sequence_length=100, embedding_dim=256):
        """Inicializa el motor de ML con la ruta al modelo y base de conocimiento"""
        self.logger = logging.getLogger("MLEngine")
        self.logger.info("Inicializando motor de aprendizaje automático...")
        
        # Crear directorio de modelos si no existe
        if not os.path.exists(model_path):
            try:
                os.makedirs(model_path)
                self.logger.info(f"Directorio de modelos creado: {model_path}")
            except Exception as e:
                self.logger.warning(f"No se pudo crear directorio de modelos: {str(e)}")
        
        self.model_path = model_path
        self.knowledge_base = knowledge_base
        self.max_sequence_length = max_sequence_length
        self.embedding_dim = embedding_dim
        
        # Estado del motor
        self.is_running = False
        self.is_training = False
        self.tokenizer = None
        self.model = None
        self.word_index = None
        
        # Configurar TensorFlow para que sea menos verbose
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=all, 1=INFO, 2=WARNING, 3=ERROR
        tf.get_logger().setLevel('ERROR')
        
        # Configurar para usar GPU si está disponible pero sin mensajes de error
        try:
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                self.logger.info(f"GPU disponible: {gpus}")
                # Configurar para usar la memoria de forma dinámica
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                    self.logger.info(f"GPU {gpu} configurada para crecimiento dinámico de memoria")
        except Exception as e:
            self.logger.warning(f"Error al configurar GPU: {str(e)}")
        
        # Semáforo para generación de respuestas
        self.response_lock = threading.Semaphore(1)
        
        # Memoria a corto plazo para contexto
        self.short_term_memory = []
        
        # Carga el modelo y tokenizador si existen
        self._load_resources()
    
    def _load_resources(self):
        """Carga el modelo, tokenizador y otros recursos necesarios"""
        try:
            # Verificar si existe modelo previo
            model_file = os.path.join(self.model_path, "model.h5")
            tokenizer_file = os.path.join(self.model_path, "tokenizer.pkl")
            
            if os.path.exists(model_file) and os.path.exists(tokenizer_file):
                self.logger.info("Cargando modelo y tokenizador existentes...")
                
                try:
                    # Cargar el modelo con manejo de excepciones
                    self.model = load_model(model_file)
                    self.logger.info("Modelo cargado correctamente")
                except Exception as e:
                    self.logger.error(f"Error al cargar modelo: {str(e)}")
                    self.model = None
                
                try:
                    # Cargar tokenizador
                    with open(tokenizer_file, 'rb') as f:
                        self.tokenizer = pickle.load(f)
                        if hasattr(self.tokenizer, 'word_index'):
                            self.word_index = self.tokenizer.word_index
                            self.logger.info(f"Tokenizador cargado con {len(self.word_index)} palabras en vocabulario")
                        else:
                            self.logger.warning("El tokenizador no tiene word_index")
                            self.tokenizer = Tokenizer(oov_token="<UNK>")
                except Exception as e:
                    self.logger.error(f"Error al cargar tokenizador: {str(e)}")
                    self.tokenizer = Tokenizer(oov_token="<UNK>")
            else:
                self.logger.info("No se encontró modelo existente, se creará uno nuevo durante el entrenamiento")
                self.tokenizer = Tokenizer(oov_token="<UNK>")
        except Exception as e:
            self.logger.error(f"Error al cargar recursos: {str(e)}")
            self.tokenizer = Tokenizer(oov_token="<UNK>")
    
    def start(self):
        """Inicia el motor de ML en un hilo separado"""
        if self.is_running:
            return
            
        self.is_running = True
        self.logger.info("Motor de ML iniciado")
        
        # Inicia un hilo para entrenamiento continuo en segundo plano
        self.training_thread = threading.Thread(target=self._background_training_loop)
        self.training_thread.daemon = True
        self.training_thread.start()
    
    def stop(self):
        """Detiene el motor de ML y guarda el estado actual"""
        if not self.is_running:
            return
            
        self.logger.info("Deteniendo motor de ML...")
        self.is_running = False
        
        # Si hay un modelo activo, lo guardamos
        if self.model and self.tokenizer:
            self._save_model()
        
        # Esperar a que termine el hilo de entrenamiento
        if hasattr(self, 'training_thread') and self.training_thread.is_alive():
            try:
                self.training_thread.join(timeout=2.0)  # Esperar máximo 2 segundos
            except Exception as e:
                self.logger.warning(f"Error al esperar finalización del hilo: {str(e)}")
        
        self.logger.info("Motor de ML detenido")
    
    def _save_model(self):
        """Guarda el modelo y tokenizador actuales"""
        try:
            if not os.path.exists(self.model_path):
                os.makedirs(self.model_path)
                
            model_file = os.path.join(self.model_path, "model.h5")
            tokenizer_file = os.path.join(self.model_path, "tokenizer.pkl")
            
            # Guardar el modelo con manejo de excepciones
            try:
                self.logger.info(f"Guardando modelo en {model_file}")
                self.model.save(model_file)
                self.logger.info("Modelo guardado correctamente")
            except Exception as e:
                self.logger.error(f"Error al guardar modelo: {str(e)}")
            
            # Guardar tokenizador
            try:
                with open(tokenizer_file, 'wb') as f:
                    pickle.dump(self.tokenizer, f)
                self.logger.info("Tokenizador guardado correctamente")
            except Exception as e:
                self.logger.error(f"Error al guardar tokenizador: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error al guardar modelo: {str(e)}")
    
    def _build_model(self, vocab_size):
        """Construye la arquitectura del modelo de lenguaje"""
        self.logger.info(f"Construyendo modelo con vocabulario de tamaño {vocab_size}")
        
        try:
            # Definir arquitectura de red neuronal con manejo de excepciones
            model = Sequential([
                Embedding(vocab_size, self.embedding_dim, mask_zero=True),
                Bidirectional(LSTM(256, return_sequences=True)),
                Dropout(0.3),
                Bidirectional(LSTM(128)),
                Dropout(0.3),
                Dense(256, activation='relu'),
                Dropout(0.3),
                Dense(vocab_size, activation='softmax')
            ])
            
            # Compilar modelo
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )
            
            self.logger.info("Modelo construido correctamente")
            # Usar lista de comprensión segura para el print_fn
            model.summary(print_fn=lambda x: self.logger.info(x) if x else None)
            return model
            
        except Exception as e:
            self.logger.error(f"Error al construir modelo: {str(e)}")
            
            # Construcción de modelo alternativo más simple en caso de error
            self.logger.info("Intentando construir modelo alternativo...")
            try:
                model = Sequential([
                    Embedding(vocab_size, 128, mask_zero=True),
                    LSTM(128),
                    Dropout(0.2),
                    Dense(256, activation='relu'),
                    Dropout(0.2),
                    Dense(vocab_size, activation='softmax')
                ])
                
                model.compile(
                    optimizer=Adam(learning_rate=0.001),
                    loss='sparse_categorical_crossentropy',
                    metrics=['accuracy']
                )
                
                self.logger.info("Modelo alternativo construido correctamente")
                return model
                
            except Exception as e2:
                self.logger.error(f"Error al construir modelo alternativo: {str(e2)}")
                return None
    
    def train(self, text_data):
        """Entrena el modelo con nuevos datos de texto"""
        if self.is_training:
            self.logger.warning("Ya hay un entrenamiento en curso")
            return False
        
        if not text_data or len(text_data) < 10:
            self.logger.warning("Datos de entrenamiento insuficientes")
            return False
        
        try:
            self.is_training = True
            self.logger.info(f"Iniciando entrenamiento con {len(text_data)} ejemplos")
            
            # Tokenizar los datos
            if not self.tokenizer.word_index or len(self.tokenizer.word_index) < 100:
                self.tokenizer.fit_on_texts(text_data)
                self.word_index = self.tokenizer.word_index
            
            # Convertir texto a secuencias
            sequences = self.tokenizer.texts_to_sequences(text_data)
            
            # Verificar que las secuencias tengan contenido
            sequences = [seq for seq in sequences if len(seq) > 0]
            
            if not sequences:
                self.logger.warning("No se generaron secuencias válidas para entrenamiento")
                self.is_training = False
                return False
            
            # Crear pares de entrada/salida (predecir palabra siguiente)
            input_sequences = []
            output_sequences = []
            
            for seq in sequences:
                for i in range(1, len(seq)):
                    input_sequences.append(seq[:i])
                    output_sequences.append(seq[i])
            
            # Verificar que se hayan generado suficientes pares para entrenamiento
            if len(input_sequences) < 10 or len(output_sequences) < 10:
                self.logger.warning("No se generaron suficientes pares entrada/salida para entrenamiento")
                self.is_training = False
                return False
            
            # Padding de secuencias
            input_sequences = pad_sequences(input_sequences, maxlen=self.max_sequence_length, padding='pre')
            output_sequences = np.array(output_sequences)
            
            # Construir o actualizar modelo
            vocab_size = len(self.tokenizer.word_index) + 1
            
            if self.model is None:
                self.model = self._build_model(vocab_size)
                
                if self.model is None:
                    self.logger.error("No se pudo construir el modelo")
                    self.is_training = False
                    return False
            
            # Configurar callbacks para entrenamiento
            callbacks = []
            
            # Punto de control para guardar el mejor modelo
            checkpoint_path = os.path.join(self.model_path, "checkpoint.h5")
            checkpoint = ModelCheckpoint(
                checkpoint_path,
                monitor='val_accuracy',
                save_best_only=True,
                save_weights_only=False
            )
            callbacks.append(checkpoint)
            
            # Early stopping para evitar sobreajuste
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=3,
                restore_best_weights=True
            )
            callbacks.append(early_stopping)
            
            # Entrenar el modelo con manejo de errores
            try:
                self.model.fit(
                    input_sequences, 
                    output_sequences,
                    epochs=5,
                    batch_size=64,
                    validation_split=0.2,
                    callbacks=callbacks,
                    verbose=1
                )
                
                # Guardar el modelo final
                self._save_model()
                
                self.logger.info("Entrenamiento completado exitosamente")
                return True
                
            except Exception as e:
                self.logger.error(f"Error durante el entrenamiento del modelo: {str(e)}")
                
                # Intentar continuar con el modelo actual si existe
                if os.path.exists(checkpoint_path):
                    self.logger.info("Cargando el último modelo guardado correctamente...")
                    try:
                        self.model = load_model(checkpoint_path)
                        self.logger.info("Modelo recuperado del último checkpoint")
                        return True
                    except Exception as e2:
                        self.logger.error(f"Error al cargar modelo desde checkpoint: {str(e2)}")
                
                return False
            
        except Exception as e:
            self.logger.error(f"Error durante el entrenamiento: {str(e)}")
            return False
        finally:
            self.is_training = False
    
    def _background_training_loop(self):
        """Ejecuta entrenamiento periódico en segundo plano"""
        # Esperar inicialmente para dar tiempo a la carga del sistema
        time.sleep(60)  # 1 minuto de espera inicial
        
        while self.is_running:
            try:
                # Esperar un período antes del próximo ciclo de entrenamiento
                for _ in range(36):  # 3600 segundos / 100 = 36 iteraciones de 100 segundos
                    if not self.is_running:
                        break
                    time.sleep(100)  # Verificar cada ~1.5 minutos si debe detenerse
                
                if not self.is_running:
                    break
                
                # Si no hay entrenamiento activo, obtener nuevos datos y entrenar
                if not self.is_training:
                    self.logger.info("Iniciando ciclo de entrenamiento programado")
                    
                    # Obtener datos de la base de conocimiento
                    try:
                        training_data = self.knowledge_base.get_training_data()
                        
                        if training_data and len(training_data) > 10:
                            self.train(training_data)
                        else:
                            self.logger.info("No hay suficientes datos para entrenamiento, omitiendo ciclo")
                    except Exception as e:
                        self.logger.error(f"Error al obtener datos de entrenamiento: {str(e)}")
            except Exception as e:
                self.logger.error(f"Error en ciclo de entrenamiento en segundo plano: {str(e)}")
                time.sleep(300)  # Esperar 5 minutos en caso de error
    
    def generate_response(self, input_text, conversation_history=None):
        """Genera una respuesta basada en el texto de entrada y el contexto de la conversación"""
        if conversation_history is None:
            conversation_history = []
                
        # Normalizar el input_text a string
        if isinstance(input_text, dict) and 'original' in input_text:
            original_text = input_text['original'].lower()
            input_text_for_kb = input_text['original']
        else:
            original_text = str(input_text).lower()
            input_text_for_kb = str(input_text)
        
        # Detectar saludos básicos
        if original_text in ["hola", "saludos", "buenos días", "buenas tardes", "buenas noches"]:
            return f"Saludos, Su Majestad. ¿En qué puedo servirle hoy?"
        
        # Buscar respuesta en la base de conocimiento
        try:
            # Buscar hechos relevantes
            facts = self.knowledge_base.search_facts(input_text_for_kb, limit=3)
            
            if facts:
                # Construir respuesta basada en hechos encontrados
                response = "Su Majestad, basado en mi conocimiento: "
                
                # Añadir hechos
                for i, fact in enumerate(facts):
                    if i > 0:
                        response += " Además, "
                    response += fact['content']
                
                # Añadir fuente
                if len(facts) > 0 and 'category' in facts[0] and facts[0]['category']:
                    response += f" Esta información está relacionada con {facts[0]['category']}."
                
                return response
        except Exception as e:
            self.logger.warning(f"Error al buscar en la base de conocimiento: {str(e)}")
        
        with self.response_lock:
            try:
                # Si no hay modelo entrenado, usar respuestas de la base de conocimiento
                if self.model is None or self.tokenizer is None or not self.tokenizer.word_index:
                    self.logger.info("Modelo no disponible, utilizando respuesta predeterminada")
                    try:
                        return self.knowledge_base.get_predefined_response(input_text_for_kb)
                    except Exception as e:
                        self.logger.error(f"Error al obtener respuesta predeterminada: {str(e)}")
                        return "A sus órdenes, Su Majestad. ¿Cómo puedo servirle hoy?"
                
                # Preprocesar la entrada
                try:
                    input_seq = self.tokenizer.texts_to_sequences([input_text_for_kb])[0]
                    
                    # Si la secuencia está vacía, usar respuesta predeterminada
                    if not input_seq:
                        self.logger.warning("No se pudo tokenizar la entrada, utilizando respuesta predeterminada")
                        return self.knowledge_base.get_predefined_response(input_text_for_kb)
                        
                    input_seq = pad_sequences([input_seq], maxlen=self.max_sequence_length, padding='pre')
                except Exception as e:
                    self.logger.error(f"Error al preprocesar entrada: {str(e)}")
                    return self.knowledge_base.get_predefined_response(input_text_for_kb)
                
                # Extraer contexto de la conversación reciente (últimas 10 interacciones)
                context = []
                for entry in conversation_history[-10:]:
                    if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                        if entry["role"] == "user":
                            context.append(f"Usuario: {entry['content']}")
                        else:
                            context.append(f"Asistente: {entry['content']}")
                    elif isinstance(entry, str):
                        context.append(entry)
                
                context_text = " ".join(context)
                
                # Procesar contexto si existe
                try:
                    if context_text:
                        context_seq = self.tokenizer.texts_to_sequences([context_text])[0][-50:]  # Limitar a 50 tokens
                        context_seq = pad_sequences([context_seq], maxlen=50, padding='pre')[0]
                    else:
                        context_seq = []
                except Exception as e:
                    self.logger.warning(f"Error al procesar contexto: {str(e)}")
                    context_seq = []
                
                # Generar texto token por token
                max_length = 100  # Máxima longitud de respuesta
                response_tokens = []
                
                try:
                    for _ in range(max_length):
                        # Predecir el siguiente token
                        prediction = self.model.predict(input_seq, verbose=0)
                        
                        # Añadir aleatoriedad a la predicción (temperatura)
                        temperature = 0.7
                        prediction = np.log(prediction[0]) / temperature
                        exp_prediction = np.exp(prediction)
                        prediction = exp_prediction / np.sum(exp_prediction)
                        
                        # Muestreo probabilístico
                        probabilities = np.random.multinomial(1, prediction, 1)[0]
                        predicted_token = np.argmax(probabilities)
                        
                        # Detener si llegamos a fin de secuencia
                        if predicted_token == 0:
                            break
                            
                        # Añadir token a la respuesta
                        response_tokens.append(predicted_token)
                        
                        # Actualizar secuencia de entrada para la siguiente predicción
                        input_seq = np.append(input_seq[0][1:], predicted_token).reshape(1, self.max_sequence_length)
                except Exception as e:
                    self.logger.error(f"Error al generar predicciones: {str(e)}")
                    return self.knowledge_base.get_predefined_response(input_text_for_kb)
                
                # Convertir tokens a texto
                response_words = []
                try:
                    reverse_word_index = {v: k for k, v in self.tokenizer.word_index.items()}
                    
                    for token in response_tokens:
                        if token in reverse_word_index:
                            word = reverse_word_index[token]
                            response_words.append(word)
                        else:
                            response_words.append("<UNK>")
                    
                    response = " ".join(response_words)
                except Exception as e:
                    self.logger.error(f"Error al convertir tokens a texto: {str(e)}")
                    response = ""
                
                # Si la respuesta generada no es coherente, usar la base de conocimiento
                if len(response.split()) < 3 or not response:
                    self.logger.info("Respuesta generada demasiado corta o vacía, utilizando base de conocimiento")
                    return self.knowledge_base.get_predefined_response(input_text_for_kb)
                
                # Mejorar formato de la respuesta (primera letra mayúscula, signos de puntuación, etc.)
                response = self._format_response(response)
                
                return response
                    
            except Exception as e:
                self.logger.error(f"Error al generar respuesta: {str(e)}")
                return "Lo siento, Su Majestad, estoy teniendo dificultades para procesar su solicitud en este momento."
    def _format_response(self, text):
        """Mejora el formato del texto generado"""
        if not text:
            return text
            
        # Capitalizar primera letra
        formatted = text[0].upper() + text[1:]
        
        # Asegurar que termine con un signo de puntuación
        if not formatted[-1] in ['.', '!', '?']:
            formatted += '.'
            
        # Corregir espacios antes de signos de puntuación
        formatted = re.sub(r'\s+([.,;:!?])', r'\1', formatted)
        
        # Corregir espacios duplicados
        formatted = re.sub(r'\s+', ' ', formatted)
            
        return formatted.strip()