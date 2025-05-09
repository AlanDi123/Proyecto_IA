# Sistema de Inteligencia Artificial Modular

Sistema personalizado de inteligencia artificial con interfaz gráfica, procesamiento de texto, síntesis de voz y capacidades de aprendizaje automático.

## Características Principales

- 🧠 **Motor de Aprendizaje Automático**: Modelo de lenguaje basado en redes neuronales con capacidad de aprendizaje continuo.
- 💬 **Interfaz Conversacional**: Procesamiento de lenguaje natural para mantener conversaciones contextuales.
- 🔊 **Síntesis de Voz**: Respuesta por voz en español latinoamericano con control de velocidad y tono.
- 🖥️ **Interfaz Gráfica Moderna**: Panel de control intuitivo basado en PyQt6, superior a Tkinter.
- 📚 **Base de Conocimiento**: Sistema de almacenamiento y gestión de información con capacidades semánticas.
- ⚙️ **Arquitectura Modular**: Diseño orientado a componentes para facilitar la extensibilidad y mantenimiento.

## Estructura del Proyecto

```
sistema-ia/
├── main.py                     # Punto de entrada principal
├── requirements.txt            # Dependencias del proyecto
├── README.md                   # Documentación
├── config/                     # Configuración del sistema
│   └── settings.json           # Archivo de configuración principal
├── modules/                    # Módulos del sistema
│   ├── __init__.py             # Inicializador del paquete de módulos
│   ├── ml_engine.py            # Motor de aprendizaje automático
│   ├── text_processor.py       # Procesador de texto y NLP
│   ├── voice_manager.py        # Gestor de síntesis de voz
│   ├── knowledge_base.py       # Base de conocimiento
│   ├── config_manager.py       # Gestor de configuración
│   └── gui.py                  # Interfaz gráfica de usuario
├── data/                       # Datos del sistema
│   ├── knowledge/              # Base de conocimiento
│   ├── nltk_data/              # Datos de NLTK
│   └── vocabulary/             # Vocabularios para NLP
├── models/                     # Modelos de aprendizaje automático
├── logs/                       # Registros del sistema
└── resources/                  # Recursos adicionales
```

## Requisitos

- Python 3.9 o superior
- Dependencias listadas en requirements.txt

## Instalación

1. Clone el repositorio:
   ```
   git clone https://github.com/usuario/sistema-ia.git
   cd sistema-ia
   ```

2. Cree un entorno virtual e instale las dependencias:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Descargue los modelos de lenguaje necesarios:
   ```
   python -m spacy download es_core_news_md
   python -m nltk.downloader punkt stopwords
   ```

4. Ejecute el sistema:
   ```
   python main.py
   ```

## Configuración

El sistema se configura a través del archivo `config/settings.json`. Las principales opciones incluyen:

- **Modelo de lenguaje**: Configuración del modelo NLP y parámetros de procesamiento
- **Síntesis de voz**: Acento, velocidad y otras opciones de voz
- **Interfaz gráfica**: Tema, tamaño y comportamiento de la interfaz
- **Aprendizaje automático**: Frecuencia de entrenamiento y parámetros del modelo

## Extensión y Personalización

El sistema está diseñado para ser extensible. Puede agregar nuevas capacidades mediante:

1. Creación de nuevos módulos en la carpeta `modules/`
2. Modificación de la base de conocimiento para incluir información específica
3. Ajuste de parámetros del modelo de aprendizaje automático
4. Personalización de la interfaz gráfica

## Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT.

## Reconocimientos

- TensorFlow - Framework de aprendizaje automático
- spaCy - Biblioteca de procesamiento de lenguaje natural
- PyQt6 - Framework de interfaz gráfica
- gTTS - Biblioteca de síntesis de voz de Google