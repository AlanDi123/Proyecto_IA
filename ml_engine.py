"""
Motor de Aprendizaje Automático - Núcleo de Procesamiento Cognitivo
Desarrollado para Su Majestad

Este módulo implementa el sistema de aprendizaje automático que potencia
las capacidades de procesamiento y generación de respuestas de la IA.
"""

import os
import time
import logging
import threading
import numpy as np
import pickle
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model, Model
from tensorflow.keras.layers import Dense, LSTM, Embedding, Input, Dropout, Bidirectional
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

class MLEngine:
    """Motor de aprendizaje automático y generación de respuestas"""
    
    def __init__(self, model_path, knowledge_base, max_sequence_length=100, embedding_dim=256):
        """Inicializa el motor de ML con la ruta al modelo y base de conocimiento"""
        self.logger = logging.getLogger("MLEngine")
        self.logger.info("Inicializando motor de aprendizaje automático...")
        
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
                self.model = load_model(model_file)
                
                with open(tokenizer_file, 'rb') as f:
                    self.tokenizer = pickle.load(f)
                    self.word_index = self.tokenizer.word_index
                
                self.logger.info(f"Modelo cargado con {len(self.word_index)} palabras en vocabulario")
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
        
        self.logger.info("Motor de ML detenido")
    
    def _save_model(self):
        """Guarda el modelo y tokenizador actuales"""
        try:
            if not os.path.exists(self.model_path):
                os.makedirs(self.model_path)
                
            model_file = os.path.join(self.model_path, "model.h5")
            tokenizer_file = os.path.join(self.model_path, "tokenizer.pkl")
            
            self.logger.info(f"Guardando modelo en {model_file}")
            self.model.save(model_file)
            
            with open(tokenizer_file, 'wb') as f:
                pickle.dump(self.tokenizer, f)
                
            self.logger.info("Modelo y tokenizador guardados correctamente")
        except Exception as e:
            self.logger.error(f"Error al guardar modelo: {str(e)}")
    
    def _build_model(self, vocab_size):
        """Construye la arquitectura del modelo de lenguaje"""
        self.logger.info(f"Construyendo modelo con vocabulario de tamaño {vocab_size}")
        
        # Definir arquitectura de red neuronal
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
        model.summary(print_fn=self.logger.info)
        return model
    
    def train(self, text_data):
        """Entrena el modelo con nuevos datos de texto"""
        if self.is_training:
            self.logger.warning("Ya hay un entrenamiento en curso")
            return False
        
        try:
            self.is_training = True
            self.logger.info(f"Iniciando entrenamiento con {len(text_data)} ejemplos")
            
            # Tokenizar los datos
            if not self.tokenizer.word_index:
                self.tokenizer.fit_on_texts(text_data)
                self.word_index = self.tokenizer.word_index
            
            sequences = self.tokenizer.texts_to_sequences(text_data)
            
            # Crear pares de entrada/salida (predecir palabra siguiente)
            input_sequences = []
            output_sequences = []
            
            for seq in sequences:
                for i in range(1, len(seq)):
                    input_sequences.append(seq[:i])
                    output_sequences.append(seq[i])
            
            # Padding de secuencias
            input_sequences = pad_sequences(input_sequences, maxlen=self.max_sequence_length, padding='pre')
            output_sequences = np.array(output_sequences)
            
            # Construir o actualizar modelo
            vocab_size = len(self.tokenizer.word_index) + 1
            
            if self.model is None:
                self.model = self._build_model(vocab_size)
            
            # Configurar punto de control para guardar el mejor modelo
            checkpoint_path = os.path.join(self.model_path, "checkpoint.h5")
            checkpoint = ModelCheckpoint(
                checkpoint_path,
                monitor='val_accuracy',
                save_best_only=True,
                save_weights_only=False
            )
            
            # Entrenar el modelo
            self.model.fit(
                input_sequences, 
                output_sequences,
                epochs=5,
                batch_size=64,
                validation_split=0.2,
                callbacks=[checkpoint]
            )
            
            # Guardar el modelo final
            self._save_model()
            
            self.logger.info("Entrenamiento completado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error durante el entrenamiento: {str(e)}")
            return False
        finally:
            self.is_training = False
    
    def _background_training_loop(self):
        """Ejecuta entrenamiento periódico en segundo plano"""
        while self.is_running:
            try:
                # Esperar un período antes del próximo ciclo de entrenamiento
                time.sleep(3600)  # 1 hora entre entrenamientos
                
                if not self.is_running:
                    break
                
                # Si no hay entrenamiento activo, obtener nuevos datos y entrenar
                if not self.is_training:
                    self.logger.info("Iniciando ciclo de entrenamiento programado")
                    
                    # Obtener datos de la base de conocimiento
                    training_data = self.knowledge_base.get_training_data()
                    
                    if training_data and len(training_data) > 0:
                        self.train(training_data)
                    else:
                        self.logger.info("No hay suficientes datos para entrenamiento, omitiendo ciclo")
            except Exception as e:
                self.logger.error(f"Error en ciclo de entrenamiento en segundo plano: {str(e)}")
    
    def generate_response(self, input_text, conversation_history):
        """Genera una respuesta basada en el texto de entrada y el contexto de la conversación"""
        with self.response_lock:
            try:
                # Si no hay modelo entrenado, usar respuestas de la base de conocimiento
                if self.model is None or self.tokenizer is None or not self.tokenizer.word_index:
                    self.logger.info("Modelo no disponible, utilizando respuesta predeterminada")
                    return self.knowledge_base.get_predefined_response(input_text)
                
                # Preprocesar la entrada
                input_seq = self.tokenizer.texts_to_sequences([input_text])[0]
                input_seq = pad_sequences([input_seq], maxlen=self.max_sequence_length, padding='pre')
                
                # Extraer contexto de la conversación reciente (últimas 5 interacciones)
                context = []
                for entry in conversation_history[-10:]:
                    if entry["role"] == "user":
                        context.append(f"Usuario: {entry['content']}")
                    else:
                        context.append(f"Asistente: {entry['content']}")
                
                context_text = " ".join(context)
                context_seq = self.tokenizer.texts_to_sequences([context_text])[0][-50:]  # Limitar a 50 tokens
                context_seq = pad_sequences([context_seq], maxlen=50, padding='pre')[0]
                
                # Generar texto token por token
                max_length = 100  # Máxima longitud de respuesta
                response_tokens = []
                
                for _ in range(max_length):
                    # Predecir el siguiente token
                    prediction = self.model.predict(input_seq, verbose=0)
                    predicted_token = np.argmax(prediction[0])
                    
                    # Detener si llegamos a fin de secuencia
                    if predicted_token == 0:
                        break
                        
                    # Añadir token a la respuesta
                    response_tokens.append(predicted_token)
                    
                    # Actualizar secuencia de entrada para la siguiente predicción
                    input_seq = np.append(input_seq[0][1:], predicted_token).reshape(1, self.max_sequence_length)
                
                # Convertir tokens a texto
                response_words = []
                reverse_word_index = {v: k for k, v in self.tokenizer.word_index.items()}
                
                for token in response_tokens:
                    word = reverse_word_index.get(token, "<UNK>")
                    response_words.append(word)
                
                response = " ".join(response_words)
                
                # Si la respuesta generada no es coherente, usar la base de conocimiento
                if len(response.split()) < 3:
                    self.logger.info("Respuesta generada demasiado corta, utilizando base de conocimiento")
                    response = self.knowledge_base.get_predefined_response(input_text)
                
                return response
                
            except Exception as e:
                self.logger.error(f"Error al generar respuesta: {str(e)}")
                return "Lo siento, Su Majestad, estoy teniendo dificultades para procesar su solicitud en este momento."