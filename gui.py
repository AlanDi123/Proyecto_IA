"""
Interfaz Gráfica - Sistema de Visualización y Control
Desarrollado para Su Majestad

Este módulo implementa una interfaz gráfica moderna para el sistema de IA
utilizando PyQt6 para crear una experiencia visual superior a Tkinter.
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                           QLabel, QSplitter, QFrame, QTabWidget, QScrollArea,
                           QSlider, QCheckBox, QComboBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QTextCursor, QColor, QPalette, QSyntaxHighlighter, QTextCharFormat, QPixmap

class CustomHighlighter(QSyntaxHighlighter):
    """Resaltador de sintaxis personalizado para el historial de chat"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Formatos para diferentes tipos de texto
        self.user_format = QTextCharFormat()
        self.user_format.setForeground(QColor("#2979FF"))
        self.user_format.setFontWeight(QFont.Weight.Bold)
        
        self.assistant_format = QTextCharFormat()
        self.assistant_format.setForeground(QColor("#00BFA5"))
        self.assistant_format.setFontWeight(QFont.Weight.Bold)
        
        self.timestamp_format = QTextCharFormat()
        self.timestamp_format.setForeground(QColor("#9E9E9E"))
        self.timestamp_format.setFontItalic(True)
    
    def highlightBlock(self, text):
        """Aplica formato de resaltado al texto"""
        # Resaltar líneas que comienzan con "Usuario:"
        if text.startswith("Usuario:"):
            self.setFormat(0, len("Usuario:"), self.user_format)
        
        # Resaltar líneas que comienzan con "Asistente:"
        elif text.startswith("Asistente:"):
            self.setFormat(0, len("Asistente:"), self.assistant_format)
        
        # Resaltar marcas de tiempo entre corchetes
        timestamp_pattern = r'\[\d{2}:\d{2}:\d{2}\]'
        start = text.find('[')
        if start >= 0 and ']' in text[start:]:
            end = text.find(']', start) + 1
            self.setFormat(start, end - start, self.timestamp_format)

class WorkerThread(QThread):
    """Hilo de trabajo para tareas en segundo plano"""
    update_signal = pyqtSignal(str)
    
    def __init__(self, target_function, *args, **kwargs):
        super().__init__()
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs
        self.result = None
    
    def run(self):
        """Ejecuta la función objetivo en un hilo separado"""
        try:
            self.result = self.target_function(*self.args, **self.kwargs)
            self.update_signal.emit(self.result)
        except Exception as e:
            self.update_signal.emit(f"Error: {str(e)}")

class ApplicationGUI(QMainWindow):
    def __init__(self, ai_system):
        """Inicializa la interfaz gráfica asegurando QApplication vivo."""
        # ————————> PRIMERO: CREAR/QCARGAR QApplication <———————
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        # Guardamos la instancia para que no sea recolectada
        self._qt_app = app

        # ————————> SEGUNDO: LLAMAR AL CONSTRUCTOR DEL QMainWindow <———————
        super().__init__()

        # Ahora sí continuamos con el resto de la inicialización
        self._setup_styles()

        
        self.logger = logging.getLogger("GUI")
        self.logger.info("Inicializando interfaz gráfica...")
        
        self.ai_system = ai_system
        self.enable_voice = True
        
        # Configuración de la ventana principal
        self.setWindowTitle("Sistema de Inteligencia Artificial - Panel de Control")
        self.setMinimumSize(1024, 768)
        
        # Crear directorio de recursos si no existe
        self.resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
        if not os.path.exists(self.resources_dir):
            os.makedirs(self.resources_dir)
        
        # Configurar estilos y apariencia
        self._setup_styles()
        
        # Configurar interfaz
        self._create_ui()
        
        # Configurar temporizadores y eventos
        self._setup_timers()
        
        self.logger.info("Interfaz gráfica inicializada correctamente")
    
    def _setup_styles(self):
        """Configura estilos y colores de la aplicación"""
        # Usar paleta de colores oscura
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        # Definir paleta personalizada
        palette = QPalette()
        
        # Colores de fondo
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        
        # Colores de texto
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        
        # Colores de selección
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        
        # Colores desactivados
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        
        app.setPalette(palette)
        
        # Definir fuentes
        self.default_font = QFont("Segoe UI", 10)
        self.monospace_font = QFont("Consolas", 10)
        app.setFont(self.default_font)
    
    def _create_ui(self):
        """Crea los elementos de la interfaz de usuario"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Divisor principal (Chat a la izquierda, Paneles a la derecha)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Panel de chat (izquierda)
        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(10)
        
        # Panel derecho (pestañas)
        right_panel = QTabWidget()
        
        # Agregar paneles al divisor principal
        main_splitter.addWidget(chat_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([700, 300])  # Distribución inicial de tamaño
        
        # Crear componentes del panel de chat
        self._create_chat_panel(chat_layout)
        
        # Crear paneles de pestañas
        self._create_settings_panel(right_panel)
        self._create_knowledge_panel(right_panel)
        self._create_voice_panel(right_panel)
        self._create_training_panel(right_panel)
        
        # Barra de estado
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Sistema listo")
        
        # Centrar ventana en pantalla
        screen_geometry = QApplication.primaryScreen().geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y)
    
    def _create_chat_panel(self, parent_layout):
        """Crea el panel de chat"""
        # Título del panel
        chat_title = QLabel("Conversación con Asistente IA")
        chat_title.setFont(QFont(self.default_font.family(), 14, QFont.Weight.Bold))
        chat_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        parent_layout.addWidget(chat_title)
        
        # Área de historial de chat
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(self.default_font)
        self.chat_history.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        parent_layout.addWidget(self.chat_history)
        
        # Aplicar resaltador personalizado al historial de chat
        self.highlighter = CustomHighlighter(self.chat_history.document())
        
        # Panel de entrada
        input_panel = QWidget()
        input_layout = QHBoxLayout(input_panel)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)
        
        # Campo de entrada
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Escriba su mensaje aquí...")
        self.input_field.setMaximumHeight(80)
        self.input_field.setFont(self.default_font)
        input_layout.addWidget(self.input_field)
        
        # Botones de acción
        button_panel = QWidget()
        button_layout = QVBoxLayout(button_panel)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        
        # Botón de envío
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self._on_send_message)
        button_layout.addWidget(self.send_button)
        
        # Botón de voz
        self.voice_toggle = QPushButton("Voz: ON")
        self.voice_toggle.setCheckable(True)
        self.voice_toggle.setChecked(True)
        self.voice_toggle.clicked.connect(self._toggle_voice)
        button_layout.addWidget(self.voice_toggle)
        
        # Botón de limpiar
        clear_button = QPushButton("Limpiar")
        clear_button.clicked.connect(self._clear_chat)
        button_layout.addWidget(clear_button)
        
        input_layout.addWidget(button_panel)
        input_layout.setStretch(0, 4)
        input_layout.setStretch(1, 1)
        
        parent_layout.addWidget(input_panel)
        
        # Conectar eventos adicionales
        self.input_field.textChanged.connect(self._on_input_changed)
        # Permitir enviar con Ctrl+Enter
        self.input_field.installEventFilter(self)
    
    def _create_settings_panel(self, tab_widget):
        """Crea el panel de configuración general"""
        settings_panel = QWidget()
        settings_layout = QVBoxLayout(settings_panel)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(15)
        
        # Título del panel
        title = QLabel("Configuración del Sistema")
        title.setFont(QFont(self.default_font.family(), 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(title)
        
        # Crear secciones de configuración
        self._create_theme_settings(settings_layout)
        self._create_model_settings(settings_layout)
        self._create_system_settings(settings_layout)
        
        # Espacio flexible
        settings_layout.addStretch()
        
        # Botones de acción
        buttons_panel = QWidget()
        buttons_layout = QHBoxLayout(buttons_panel)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        
        # Botón para guardar configuración
        save_button = QPushButton("Guardar Configuración")
        save_button.clicked.connect(self._save_settings)
        buttons_layout.addWidget(save_button)
        
        # Botón para restaurar valores predeterminados
        reset_button = QPushButton("Restaurar Valores Predeterminados")
        reset_button.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(reset_button)
        
        settings_layout.addWidget(buttons_panel)
        
        # Añadir a pestañas
        tab_widget.addTab(settings_panel, "Configuración")
    
    def _create_theme_settings(self, parent_layout):
        """Crea la sección de configuración de tema"""
        group_box = QFrame()
        group_box.setFrameShape(QFrame.Shape.StyledPanel)
        group_box.setFrameShadow(QFrame.Shadow.Raised)
        
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título de sección
        section_title = QLabel("Apariencia")
        section_title.setFont(QFont(self.default_font.family(), 11, QFont.Weight.Bold))
        layout.addWidget(section_title)
        
        # Selector de tema
        theme_layout = QHBoxLayout()
        theme_layout.setContentsMargins(0, 0, 0, 0)
        
        theme_label = QLabel("Tema:")
        theme_label.setFixedWidth(120)
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Oscuro", "Claro", "Sistema"])
        theme_layout.addWidget(self.theme_combo)
        
        layout.addLayout(theme_layout)
        
        # Selector de tamaño de fuente
        font_layout = QHBoxLayout()
        font_layout.setContentsMargins(0, 0, 0, 0)
        
        font_label = QLabel("Tamaño de fuente:")
        font_label.setFixedWidth(120)
        font_layout.addWidget(font_label)
        
        self.font_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_slider.setMinimum(8)
        self.font_slider.setMaximum(16)
        self.font_slider.setValue(10)
        self.font_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.font_slider.setTickInterval(1)
        self.font_slider.valueChanged.connect(self._update_font_size)
        
        self.font_size_label = QLabel("10 pt")
        self.font_size_label.setFixedWidth(40)
        self.font_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        font_layout.addWidget(self.font_slider)
        font_layout.addWidget(self.font_size_label)
        
        layout.addLayout(font_layout)
        
        parent_layout.addWidget(group_box)
    
    def _create_model_settings(self, parent_layout):
        """Crea la sección de configuración del modelo"""
        group_box = QFrame()
        group_box.setFrameShape(QFrame.Shape.StyledPanel)
        group_box.setFrameShadow(QFrame.Shadow.Raised)
        
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título de sección
        section_title = QLabel("Modelo de IA")
        section_title.setFont(QFont(self.default_font.family(), 11, QFont.Weight.Bold))
        layout.addWidget(section_title)
        
        # Configuración de creatividad
        creativity_layout = QHBoxLayout()
        creativity_layout.setContentsMargins(0, 0, 0, 0)
        
        creativity_label = QLabel("Creatividad:")
        creativity_label.setFixedWidth(120)
        creativity_layout.addWidget(creativity_label)
        
        self.creativity_slider = QSlider(Qt.Orientation.Horizontal)
        self.creativity_slider.setMinimum(0)
        self.creativity_slider.setMaximum(100)
        self.creativity_slider.setValue(70)
        self.creativity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.creativity_slider.setTickInterval(10)
        
        self.creativity_value = QLabel("70%")
        self.creativity_value.setFixedWidth(40)
        self.creativity_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.creativity_slider.valueChanged.connect(lambda v: self.creativity_value.setText(f"{v}%"))
        
        creativity_layout.addWidget(self.creativity_slider)
        creativity_layout.addWidget(self.creativity_value)
        
        layout.addLayout(creativity_layout)
        
        # Configuración de longitud de respuesta
        length_layout = QHBoxLayout()
        length_layout.setContentsMargins(0, 0, 0, 0)
        
        length_label = QLabel("Longitud de respuesta:")
        length_label.setFixedWidth(120)
        length_layout.addWidget(length_label)
        
        self.length_combo = QComboBox()
        self.length_combo.addItems(["Corta", "Media", "Larga", "Muy larga"])
        self.length_combo.setCurrentIndex(1)  # Media por defecto
        length_layout.addWidget(self.length_combo)
        
        layout.addLayout(length_layout)
        
        # Casilla de aprendizaje continuo
        learning_layout = QHBoxLayout()
        learning_layout.setContentsMargins(0, 0, 0, 0)
        
        self.continuous_learning = QCheckBox("Habilitar aprendizaje continuo")
        self.continuous_learning.setChecked(True)
        learning_layout.addWidget(self.continuous_learning)
        
        layout.addLayout(learning_layout)
        
        parent_layout.addWidget(group_box)
    
    def _create_system_settings(self, parent_layout):
        """Crea la sección de configuración del sistema"""
        group_box = QFrame()
        group_box.setFrameShape(QFrame.Shape.StyledPanel)
        group_box.setFrameShadow(QFrame.Shadow.Raised)
        
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título de sección
        section_title = QLabel("Sistema")
        section_title.setFont(QFont(self.default_font.family(), 11, QFont.Weight.Bold))
        layout.addWidget(section_title)
        
        # Opciones de inicio
        startup_check = QCheckBox("Iniciar automáticamente con el sistema")
        startup_check.setChecked(False)
        layout.addWidget(startup_check)
        
        # Opciones de guardado
        save_check = QCheckBox("Guardar historial de conversaciones")
        save_check.setChecked(True)
        layout.addWidget(save_check)
        
        # Opciones de actualizaciones
        update_check = QCheckBox("Buscar actualizaciones automáticamente")
        update_check.setChecked(True)
        layout.addWidget(update_check)
        
        # Ruta de datos
        data_layout = QHBoxLayout()
        data_layout.setContentsMargins(0, 0, 0, 0)
        
        data_label = QLabel("Directorio de datos:")
        data_layout.addWidget(data_label)
        
        data_path = QLineEdit()
        data_path.setText("./data")
        data_path.setReadOnly(True)
        data_layout.addWidget(data_path)
        
        browse_button = QPushButton("...")
        browse_button.setMaximumWidth(30)
        browse_button.clicked.connect(lambda: self._browse_directory(data_path))
        data_layout.addWidget(browse_button)
        
        layout.addLayout(data_layout)
        
        parent_layout.addWidget(group_box)
    
    def _create_knowledge_panel(self, tab_widget):
        """Crea el panel de gestión de conocimiento"""
        knowledge_panel = QWidget()
        knowledge_layout = QVBoxLayout(knowledge_panel)
        knowledge_layout.setContentsMargins(10, 10, 10, 10)
        knowledge_layout.setSpacing(15)
        
        # Título del panel
        title = QLabel("Base de Conocimiento")
        title.setFont(QFont(self.default_font.family(), 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        knowledge_layout.addWidget(title)
        
        # Panel de pestañas para diferentes tipos de conocimiento
        knowledge_tabs = QTabWidget()
        knowledge_layout.addWidget(knowledge_tabs)
        
        # Pestaña de hechos/conceptos
        facts_tab = QWidget()
        facts_layout = QVBoxLayout(facts_tab)
        facts_layout.setContentsMargins(10, 10, 10, 10)
        facts_layout.setSpacing(10)
        
        # Editor de hechos
        facts_layout.addWidget(QLabel("Añadir nuevo concepto o hecho:"))
        
        fact_input = QTextEdit()
        fact_input.setPlaceholderText("Escriba la información que desea añadir...")
        fact_input.setMaximumHeight(100)
        facts_layout.addWidget(fact_input)
        
        # Categoría
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Categoría:"))
        
        category_combo = QComboBox()
        category_combo.setEditable(True)
        category_combo.addItems(["General", "Ciencia", "Historia", "Tecnología", "Arte", "Personalizado"])
        category_layout.addWidget(category_combo)
        
        facts_layout.addLayout(category_layout)
        
        # Importancia
        importance_layout = QHBoxLayout()
        importance_layout.addWidget(QLabel("Importancia:"))
        
        importance_slider = QSlider(Qt.Orientation.Horizontal)
        importance_slider.setMinimum(1)
        importance_slider.setMaximum(10)
        importance_slider.setValue(5)
        importance_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        importance_slider.setTickInterval(1)
        
        importance_value = QLabel("5")
        importance_value.setFixedWidth(20)
        importance_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        importance_slider.valueChanged.connect(lambda v: importance_value.setText(str(v)))
        
        importance_layout.addWidget(importance_slider)
        importance_layout.addWidget(importance_value)
        
        facts_layout.addLayout(importance_layout)
        
        # Botón de añadir
        add_fact_button = QPushButton("Añadir a la Base de Conocimiento")
        facts_layout.addWidget(add_fact_button)
        
        # Explorador de hechos
        facts_layout.addWidget(QLabel("Explorar base de conocimiento:"))
        
        search_layout = QHBoxLayout()
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Buscar en base de conocimiento...")
        search_layout.addWidget(search_input)
        
        search_button = QPushButton("Buscar")
        search_layout.addWidget(search_button)
        
        facts_layout.addLayout(search_layout)
        
        # Resultados de búsqueda
        search_results = QTextEdit()
        search_results.setReadOnly(True)
        search_results.setPlaceholderText("Los resultados de búsqueda aparecerán aquí...")
        facts_layout.addWidget(search_results)
        
        knowledge_tabs.addTab(facts_tab, "Hechos y Conceptos")
        
        # Pestaña de importación de datos
        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)
        import_layout.setContentsMargins(10, 10, 10, 10)
        import_layout.setSpacing(10)
        
        import_layout.addWidget(QLabel("Importar conocimiento desde archivos:"))
        
        # Sección de importación de texto
        import_layout.addWidget(QLabel("Archivos de texto (.txt, .pdf, .docx):"))
        
        import_text_layout = QHBoxLayout()
        
        text_path = QLineEdit()
        text_path.setPlaceholderText("Seleccione archivo de texto...")
        text_path.setReadOnly(True)
        import_text_layout.addWidget(text_path)
        
        text_browse = QPushButton("Examinar")
        import_text_layout.addWidget(text_browse)
        
        import_layout.addLayout(import_text_layout)
        
        # Sección de importación CSV
        import_layout.addWidget(QLabel("Datos estructurados (.csv, .xlsx):"))
        
        import_csv_layout = QHBoxLayout()
        
        csv_path = QLineEdit()
        csv_path.setPlaceholderText("Seleccione archivo de datos...")
        csv_path.setReadOnly(True)
        import_csv_layout.addWidget(csv_path)
        
        csv_browse = QPushButton("Examinar")
        import_csv_layout.addWidget(csv_browse)
        
        import_layout.addLayout(import_csv_layout)
        
        # Opciones de importación
        import_options_layout = QHBoxLayout()
        
        replace_check = QCheckBox("Reemplazar datos existentes")
        import_options_layout.addWidget(replace_check)
        
        categorize_check = QCheckBox("Categorizar automáticamente")
        categorize_check.setChecked(True)
        import_options_layout.addWidget(categorize_check)
        
        import_layout.addLayout(import_options_layout)
        
        # Botón de importación
        import_button = QPushButton("Importar Datos")
        import_layout.addWidget(import_button)
        
        # Progreso de importación
        import_progress = QLabel("Listo para importar")
        import_layout.addWidget(import_progress)
        
        import_layout.addStretch()
        
        knowledge_tabs.addTab(import_tab, "Importar Datos")
        
        # Añadir a pestañas principales
        tab_widget.addTab(knowledge_panel, "Conocimiento")
    
    def _create_voice_panel(self, tab_widget):
        """Crea el panel de configuración de voz"""
        voice_panel = QWidget()
        voice_layout = QVBoxLayout(voice_panel)
        voice_layout.setContentsMargins(10, 10, 10, 10)
        voice_layout.setSpacing(15)
        
        # Título del panel
        title = QLabel("Configuración de Voz")
        title.setFont(QFont(self.default_font.family(), 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        voice_layout.addWidget(title)
        
        # Panel de selección de voz
        voice_frame = QFrame()
        voice_frame.setFrameShape(QFrame.Shape.StyledPanel)
        voice_frame.setFrameShadow(QFrame.Shadow.Raised)
        
        voice_settings_layout = QVBoxLayout(voice_frame)
        voice_settings_layout.setContentsMargins(10, 10, 10, 10)
        voice_settings_layout.setSpacing(10)
        
        # Seleccionar idioma/acento
        dialect_layout = QHBoxLayout()
        dialect_layout.setContentsMargins(0, 0, 0, 0)
        
        dialect_label = QLabel("Acento español:")
        dialect_label.setFixedWidth(120)
        dialect_layout.addWidget(dialect_label)
        
        dialect_combo = QComboBox()
        dialect_combo.addItems([
            "Latinoamericano (México)", 
            "Latinoamericano (Argentina)", 
            "Latinoamericano (Colombia)", 
            "Español (España)"
        ])
        dialect_layout.addWidget(dialect_combo)
        
        voice_settings_layout.addLayout(dialect_layout)
        
        # Control de velocidad
        speed_layout = QHBoxLayout()
        speed_layout.setContentsMargins(0, 0, 0, 0)
        
        speed_label = QLabel("Velocidad:")
        speed_label.setFixedWidth(120)
        speed_layout.addWidget(speed_label)
        
        speed_slider = QSlider(Qt.Orientation.Horizontal)
        speed_slider.setMinimum(50)
        speed_slider.setMaximum(150)
        speed_slider.setValue(100)
        speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        speed_slider.setTickInterval(10)
        
        speed_value = QLabel("100%")
        speed_value.setFixedWidth(40)
        speed_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        speed_slider.valueChanged.connect(lambda v: speed_value.setText(f"{v}%"))
        
        speed_layout.addWidget(speed_slider)
        speed_layout.addWidget(speed_value)
        
        voice_settings_layout.addLayout(speed_layout)
        
        # Control de tono
        pitch_layout = QHBoxLayout()
        pitch_layout.setContentsMargins(0, 0, 0, 0)
        
        pitch_label = QLabel("Tono:")
        pitch_label.setFixedWidth(120)
        pitch_layout.addWidget(pitch_label)
        
        pitch_slider = QSlider(Qt.Orientation.Horizontal)
        pitch_slider.setMinimum(50)
        pitch_slider.setMaximum(150)
        pitch_slider.setValue(100)
        pitch_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        pitch_slider.setTickInterval(10)
        
        pitch_value = QLabel("100%")
        pitch_value.setFixedWidth(40)
        pitch_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pitch_slider.valueChanged.connect(lambda v: pitch_value.setText(f"{v}%"))
        
        pitch_layout.addWidget(pitch_slider)
        pitch_layout.addWidget(pitch_value)
        
        voice_settings_layout.addLayout(pitch_layout)
        
        # Opciones de activación
        activation_check = QCheckBox("Activar voz automáticamente al iniciar")
        activation_check.setChecked(True)
        voice_settings_layout.addWidget(activation_check)
        
        voice_layout.addWidget(voice_frame)
        
        # Sección de prueba de voz
        test_frame = QFrame()
        test_frame.setFrameShape(QFrame.Shape.StyledPanel)
        test_frame.setFrameShadow(QFrame.Shadow.Raised)
        
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(10, 10, 10, 10)
        test_layout.setSpacing(10)
        
        test_layout.addWidget(QLabel("Probar configuración de voz:"))
        
        test_input = QTextEdit()
        test_input.setPlaceholderText("Escriba texto para probar la voz...")
        test_input.setMaximumHeight(80)
        test_layout.addWidget(test_input)
        
        test_button = QPushButton("Reproducir Prueba")
        test_layout.addWidget(test_button)
        
        voice_layout.addWidget(test_frame)
        
        # Espacio flexible
        voice_layout.addStretch()
        
        # Botones de acción
        buttons_panel = QWidget()
        buttons_layout = QHBoxLayout(buttons_panel)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        
        save_button = QPushButton("Guardar Configuración")
        buttons_layout.addWidget(save_button)
        
        restore_button = QPushButton("Restaurar Valores Predeterminados")
        buttons_layout.addWidget(restore_button)
        
        voice_layout.addWidget(buttons_panel)
        
        # Añadir a pestañas principales
        tab_widget.addTab(voice_panel, "Voz")
    
    def _create_training_panel(self, tab_widget):
        """Crea el panel de entrenamiento del modelo"""
        training_panel = QWidget()
        training_layout = QVBoxLayout(training_panel)
        training_layout.setContentsMargins(10, 10, 10, 10)
        training_layout.setSpacing(15)
        
        # Título del panel
        title = QLabel("Entrenamiento del Modelo")
        title.setFont(QFont(self.default_font.family(), 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        training_layout.addWidget(title)
        
        # Información del modelo
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setFrameShadow(QFrame.Shadow.Raised)
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(10)
        
        info_layout.addWidget(QLabel("Información del modelo:"))
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setPlaceholderText("La información del modelo se cargará al iniciar...")
        info_text.setMaximumHeight(100)
        info_layout.addWidget(info_text)
        
        training_layout.addWidget(info_frame)
        
        # Opciones de entrenamiento
        options_frame = QFrame()
        options_frame.setFrameShape(QFrame.Shape.StyledPanel)
        options_frame.setFrameShadow(QFrame.Shadow.Raised)
        
        options_layout = QVBoxLayout(options_frame)
        options_layout.setContentsMargins(10, 10, 10, 10)
        options_layout.setSpacing(10)
        
        options_layout.addWidget(QLabel("Opciones de entrenamiento:"))
        
        # Parámetros de entrenamiento
        params_layout = QHBoxLayout()
        
        epochs_layout = QVBoxLayout()
        epochs_layout.addWidget(QLabel("Épocas:"))
        
        epochs_input = QComboBox()
        epochs_input.addItems(["1", "3", "5", "10", "20"])
        epochs_input.setCurrentIndex(2)  # 5 por defecto
        epochs_layout.addWidget(epochs_input)
        
        params_layout.addLayout(epochs_layout)
        
        batch_layout = QVBoxLayout()
        batch_layout.addWidget(QLabel("Batch size:"))
        
        batch_input = QComboBox()
        batch_input.addItems(["16", "32", "64", "128"])
        batch_input.setCurrentIndex(2)  # 64 por defecto
        batch_layout.addWidget(batch_input)
        
        params_layout.addLayout(batch_layout)
        
        learning_layout = QVBoxLayout()
        learning_layout.addWidget(QLabel("Learning rate:"))
        
        learning_input = QComboBox()
        learning_input.addItems(["0.0001", "0.001", "0.01", "0.1"])
        learning_input.setCurrentIndex(1)  # 0.001 por defecto
        learning_layout.addWidget(learning_input)
        
        params_layout.addLayout(learning_layout)
        
        options_layout.addLayout(params_layout)
        
        # Opciones avanzadas
        advanced_layout = QHBoxLayout()
        
        validation_check = QCheckBox("Usar validación cruzada")
        validation_check.setChecked(True)
        advanced_layout.addWidget(validation_check)
        
        checkpoint_check = QCheckBox("Guardar checkpoints")
        checkpoint_check.setChecked(True)
        advanced_layout.addWidget(checkpoint_check)
        
        early_check = QCheckBox("Early stopping")
        early_check.setChecked(True)
        advanced_layout.addWidget(early_check)
        
        options_layout.addLayout(advanced_layout)
        
        training_layout.addWidget(options_frame)
        
        # Botones de acción
        buttons_frame = QFrame()
        buttons_frame.setFrameShape(QFrame.Shape.StyledPanel)
        buttons_frame.setFrameShadow(QFrame.Shadow.Raised)
        
        buttons_layout = QVBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(10, 10, 10, 10)
        buttons_layout.setSpacing(10)
        
        train_button = QPushButton("Iniciar Entrenamiento")
        buttons_layout.addWidget(train_button)
        
        # Progreso de entrenamiento
        progress_label = QLabel("Estado: Listo para entrenar")
        buttons_layout.addWidget(progress_label)
        
        training_layout.addWidget(buttons_frame)
        
        # Espacio flexible
        training_layout.addStretch()
        
        # Añadir a pestañas principales
        tab_widget.addTab(training_panel, "Entrenamiento")
    
    def _setup_timers(self):
        """Configura temporizadores y eventos periódicos"""
        # Timer para actualizar estado
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # Actualizar cada 5 segundos
    
    def _update_status(self):
        """Actualiza información de estado periódicamente"""
        # Actualizar información en barra de estado
        current_time = datetime.now().strftime("%H:%M:%S")
        self.status_bar.showMessage(f"Sistema en ejecución | Última actualización: {current_time}")
    
    def _update_font_size(self, size):
        """Actualiza el tamaño de fuente en la interfaz"""
        self.font_size_label.setText(f"{size} pt")
        
        # Actualizar fuentes
        new_default_font = QFont(self.default_font.family(), size)
        new_monospace_font = QFont(self.monospace_font.family(), size)
        
        # Aplicar a elementos específicos
        self.chat_history.setFont(new_default_font)
        self.input_field.setFont(new_default_font)
    
    def _on_input_changed(self):
        """Gestiona cambios en el campo de entrada"""
        # Ajustar altura del campo de entrada según contenido
        document_height = self.input_field.document().size().height()
        max_height = 80
        
        if document_height < max_height:
            self.input_field.setMaximumHeight(int(document_height + 10))
        else:
            self.input_field.setMaximumHeight(max_height)
    
    def _on_send_message(self):
        """Procesa el envío de un mensaje"""
        # Obtener texto del campo de entrada
        user_input = self.input_field.toPlainText().strip()
        
        if not user_input:
            return
        
        # Deshabilitar botón de envío durante el procesamiento
        self.send_button.setEnabled(False)
        
        # Añadir mensaje del usuario al historial
        current_time = datetime.now().strftime("%H:%M:%S")
        self.chat_history.append(f"Usuario: {user_input} [{current_time}]")
        
        # Limpiar campo de entrada
        self.input_field.clear()
        
        # Procesar mensaje en hilo separado
        self.worker = WorkerThread(self.ai_system.process_input, user_input, self.enable_voice)
        self.worker.update_signal.connect(self._on_response_ready)
        self.worker.start()
    
    def _on_response_ready(self, response):
        """Maneja la recepción de una respuesta del sistema de IA"""
        # Añadir respuesta al historial
        current_time = datetime.now().strftime("%H:%M:%S")
        self.chat_history.append(f"Asistente: {response} [{current_time}]")
        
        # Desplazar al final del historial
        self.chat_history.moveCursor(QTextCursor.MoveOperation.End)
        
        # Habilitar nuevamente el botón de envío
        self.send_button.setEnabled(True)
    
    def _toggle_voice(self):
        """Activa/desactiva la respuesta por voz"""
        self.enable_voice = self.voice_toggle.isChecked()
        
        if self.enable_voice:
            self.voice_toggle.setText("Voz: ON")
        else:
            self.voice_toggle.setText("Voz: OFF")
    
    def _clear_chat(self):
        """Limpia el historial de chat"""
        reply = QMessageBox.question(
            self, 
            "Limpiar Conversación", 
            "¿Está seguro de que desea limpiar el historial de conversación?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.chat_history.clear()
    
    def _save_settings(self):
        """Guarda la configuración actual"""
        QMessageBox.information(
            self,
            "Guardar Configuración",
            "Configuración guardada correctamente."
        )
    
    def _reset_settings(self):
        """Restaura la configuración a valores predeterminados"""
        reply = QMessageBox.question(
            self, 
            "Restaurar Configuración", 
            "¿Está seguro de que desea restaurar la configuración a valores predeterminados?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Restaurar valores predeterminados
            self.theme_combo.setCurrentIndex(0)  # Oscuro
            self.font_slider.setValue(10)
            self.creativity_slider.setValue(70)
            self.length_combo.setCurrentIndex(1)  # Media
            self.continuous_learning.setChecked(True)
            
            QMessageBox.information(
                self,
                "Restaurar Configuración",
                "Configuración restaurada a valores predeterminados."
            )
    
    def _browse_directory(self, target_field):
        """Abre diálogo para seleccionar directorio"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Directorio",
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if directory:
            target_field.setText(directory)
    
    def closeEvent(self, event):
        """Gestiona el cierre de la ventana"""
        reply = QMessageBox.question(
            self, 
            "Confirmar Salida", 
            "¿Está seguro de que desea salir?\nSe guardarán todos los datos y se detendrá el sistema.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Detener sistema de IA
            self.ai_system.shutdown()
            event.accept()
        else:
            event.ignore()
    
    def eventFilter(self, source, event):
        """Filtra eventos para componentes específicos"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        
        # Detectar Ctrl+Enter en campo de entrada para enviar mensaje
        if (source is self.input_field and event.type() == QEvent.Type.KeyPress):
            key_event = event
            
            # Verificar si es Ctrl+Enter
            if (key_event.key() == Qt.Key.Key_Return or key_event.key() == Qt.Key.Key_Enter) and key_event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self._on_send_message()
                return True
        
        return super().eventFilter(source, event)
    
    def run(self):
        """Muestra la ventana principal y ejecuta el bucle de eventos"""
        # Asegurar que QApplication existe antes de mostrar cualquier widget
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Ahora es seguro mostrar la ventana
        self.show()
        
        # Retornar código de salida de la aplicación
        return app.exec()