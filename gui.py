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
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QTabWidget, QFrame, QSlider,
    QMessageBox, QSplitter, QScrollArea, QGroupBox
)
from PyQt6.QtGui import QFont, QTextCursor, QCursor, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                           QLabel, QSplitter, QFrame, QTabWidget, QScrollArea,
                           QSlider, QCheckBox, QComboBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QTextCursor, QColor, QPalette, QSyntaxHighlighter, QTextCharFormat, QPixmap
from datetime import datetime
from PyQt6.QtGui import QTextCursor



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
        """Ejecuta la función objetivo y emite el resultado"""
        try:
            result = self.target_function(*self.args, **self.kwargs)
            self.result = result  # Almacenar el resultado como atributo
            self.update_signal.emit(str(result) if result is not None else "")
        except Exception as e:
            self.logger.error(f"Error en Worker Thread: {str(e)}")
            self.update_signal.emit("")


class ContentModerator:
    """Sistema de moderación de contenido para el Sistema de IA"""
    
    def __init__(self):
        self.logger = logging.getLogger("ContentModerator")
        self.logger.info("Inicializando moderador de contenido...")
        
        # Lista vacía - sin restricciones
        self.prohibited_terms = []
        self.prohibited_patterns = []
        
        self.logger.info("Moderador de contenido inicializado correctamente")
    
    def check_content(self, text):
        """
        Verifica si el contenido es apropiado - siempre retorna True
        """
        return True, ""
    
    def sanitize_content(self, text):
        """
        No realiza sanitización - retorna el texto tal cual
        """
        return text



class ApplicationGUI(QMainWindow):
    def __init__(self, ai_system):
        """Inicializa la interfaz gráfica asegurando QApplication vivo."""
        # ————————> PRIMERO: CREAR/CARGAR QApplication <———————
        app = QApplication.instance()
        if app is None:
            import sys
            app = QApplication(sys.argv)
        # Guardamos la instancia para que no sea recolectada
        self._qt_app = app

        # ————————> SEGUNDO: LLAMAR AL CONSTRUCTOR DEL QMainWindow <———————
        super().__init__()
        
        
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
        # Usar paleta de colores moderna
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        # Definir paleta personalizada para tema oscuro
        palette = QPalette()
        
        # Colores primarios - Azul oscuro con detalles en turquesa
        primary_color = QColor(24, 24, 37)        # Azul muy oscuro
        secondary_color = QColor(0, 180, 170)     # Turquesa
        text_color = QColor(230, 230, 230)        # Blanco suave
        dark_bg = QColor(18, 18, 30)              # Fondo más oscuro
        panel_bg = QColor(35, 35, 50)             # Panels ligeramente más claros
        highlight_color = QColor(0, 150, 136)     # Turquesa ligeramente más oscuro
        
        # Colores de fondo
        palette.setColor(QPalette.ColorRole.Window, primary_color)
        palette.setColor(QPalette.ColorRole.WindowText, text_color)
        palette.setColor(QPalette.ColorRole.Base, dark_bg)
        palette.setColor(QPalette.ColorRole.AlternateBase, panel_bg)
        
        # Colores de texto
        palette.setColor(QPalette.ColorRole.Text, text_color)
        palette.setColor(QPalette.ColorRole.Button, panel_bg)
        palette.setColor(QPalette.ColorRole.ButtonText, text_color)
        
        # Colores de selección
        palette.setColor(QPalette.ColorRole.Highlight, highlight_color)
        palette.setColor(QPalette.ColorRole.HighlightedText, text_color)
        
        # Colores desactivados - corregido para PyQt6
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        
        app.setPalette(palette)
        
        # Definir fuentes
        self.default_font = QFont("Segoe UI", 10)
        self.monospace_font = QFont("Consolas", 10)
        app.setFont(self.default_font)
        
        # Establecer hoja de estilo adicional (CSS para Qt)
        app.setStyleSheet("""
            QMainWindow {
                border: none;
            }
            QTextEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #212134;
            }
            QPushButton {
                background-color: #00B4A6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00968A;
            }
            QPushButton:pressed {
                background-color: #007C72;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #212134;
            }
            QTabBar::tab {
                background-color: #2E2E45;
                color: #CCC;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #00B4A6;
                color: white;
            }
            QTabBar::tab:!selected:hover {
                background-color: #3F3F5F;
            }
            QFrame {
                border-radius: 4px;
            }
        """)
    
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
        self.status_bar.setStyleSheet("color: #00B4A6;")
        
        # Centrar ventana en pantalla
        screen_geometry = QApplication.primaryScreen().geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y)
    
    def _create_chat_panel(self, parent_layout):
        """Crea el panel de chat con burbujas de mensajes"""
        # Título del panel
        chat_title = QLabel("Conversación con Asistente IA")
        chat_title.setFont(QFont(self.default_font.family(), 14, QFont.Weight.Bold))
        chat_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_title.setStyleSheet("color: #00B4A6; margin-bottom: 10px;")
        parent_layout.addWidget(chat_title)
        
        # Área de historial de chat estilizada
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(self.default_font)
        self.chat_history.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a2a;
                border: 1px solid #333;
                border-radius: 6px;
            }
        """)
        
        # Documento para formateo CSS de mensajes
        self.chat_history.document().setDefaultStyleSheet("""
            .user-message {
                background-color: #2D4263;
                border-radius: 10px;
                padding: 8px 12px;
                margin: 4px 20px 4px 50px;
                color: #ECDBBA;
            }
            .assistant-message {
                background-color: #00796B;
                border-radius: 10px;
                padding: 8px 12px;
                margin: 4px 50px 4px 20px;
                color: #ECDBBA;
            }
            .timestamp {
                color: #aaa;
                font-size: 9px;
                text-align: right;
            }
        """)
        
        parent_layout.addWidget(self.chat_history)
        
        # Panel de entrada mejorado
        input_panel = QWidget()
        input_layout = QHBoxLayout(input_panel)
        input_layout.setContentsMargins(0, 10, 0, 0)
        input_layout.setSpacing(10)
        
        # Campo de entrada mejorado
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Escriba su mensaje aquí...")
        self.input_field.setMaximumHeight(80)
        self.input_field.setFont(self.default_font)
        self.input_field.setStyleSheet("""
            QTextEdit {
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        input_layout.addWidget(self.input_field)
        
        # Botones de acción mejorados
        button_panel = QWidget()
        button_layout = QVBoxLayout(button_panel)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        # Botón de envío 
        self.send_button = QPushButton("  Enviar")
        self.send_button.clicked.connect(self._on_send_message)
        button_layout.addWidget(self.send_button)
        
        # Botón de voz con toggle
        self.voice_toggle = QPushButton("  Voz: ON")
        self.voice_toggle.setCheckable(True)
        self.voice_toggle.setChecked(True)
        self.voice_toggle.clicked.connect(self._toggle_voice)
        button_layout.addWidget(self.voice_toggle)
        
        # Botón de limpiar
        clear_button = QPushButton("  Limpiar")
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
        title.setStyleSheet("color: #00B4A6;")
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
        group_box.setStyleSheet("background-color: #212134; padding: 10px;")
        
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título de sección
        section_title = QLabel("Apariencia")
        section_title.setFont(QFont(self.default_font.family(), 11, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #00B4A6;")
        layout.addWidget(section_title)
        
        # Selector de tema
        theme_layout = QHBoxLayout()
        theme_layout.setContentsMargins(0, 0, 0, 0)
        
        theme_label = QLabel("Tema:")
        theme_label.setFixedWidth(120)
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Oscuro", "Claro", "Sistema"])
        self.theme_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
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
        self.font_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #2A2A40;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00B4A6;
                border: 1px solid #00B4A6;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)
        
        self.font_size_label = QLabel("10 pt")
        self.font_size_label.setFixedWidth(40)
        self.font_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        font_layout.addWidget(self.font_slider)
        font_layout.addWidget(self.font_size_label)
        
        layout.addLayout(font_layout)
        
        parent_layout.addWidget(group_box)



    def _create_training_panel(self, tab_widget):
        """Crea el panel de entrenamiento del modelo"""
        training_tab = QWidget()
        tab_widget.addTab(training_tab, "Entrenamiento")
        
        training_layout = QVBoxLayout(training_tab)
        training_layout.setContentsMargins(20, 20, 20, 20)
        training_layout.setSpacing(15)
        
        # Título
        training_title = QLabel("Entrenamiento del Modelo")
        training_title.setFont(QFont(self.default_font.family(), 18, QFont.Weight.Bold))
        training_title.setStyleSheet("color: #00B4A6;")
        training_layout.addWidget(training_title)
        
        # Panel de control de entrenamiento
        training_frame = QFrame()
        training_frame.setFrameShape(QFrame.Shape.StyledPanel)
        training_frame.setFrameShadow(QFrame.Shadow.Raised)
        training_frame.setStyleSheet("background-color: #1E1E2E; padding: 15px; border-radius: 5px;")
        
        training_controls_layout = QVBoxLayout(training_frame)
        training_controls_layout.setSpacing(15)
        
        # Información sobre el entrenamiento
        training_info = QLabel("El entrenamiento mejora la capacidad del sistema para generar respuestas relevantes y coherentes basadas en el conocimiento acumulado.")
        training_info.setWordWrap(True)
        training_controls_layout.addWidget(training_info)
        
        # Configuración de entrenamiento
        config_group = QGroupBox("Configuración de Entrenamiento")
        config_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                color: #00B4A6;
            }
        """)
        
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)
        
        # Número de épocas
        epochs_layout = QHBoxLayout()
        epochs_layout.addWidget(QLabel("Épocas:"))
        
        self.epochs_input = QLineEdit()
        self.epochs_input.setPlaceholderText("5")
        self.epochs_input.setText("5")
        self.epochs_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        epochs_layout.addWidget(self.epochs_input)
        
        config_layout.addLayout(epochs_layout)
        
        # Tamaño de lote
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Tamaño de lote:"))
        
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("64")
        self.batch_input.setText("64")
        self.batch_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        batch_layout.addWidget(self.batch_input)
        
        config_layout.addLayout(batch_layout)
        
        # Tasa de aprendizaje
        lr_layout = QHBoxLayout()
        lr_layout.addWidget(QLabel("Tasa de aprendizaje:"))
        
        self.lr_input = QLineEdit()
        self.lr_input.setPlaceholderText("0.001")
        self.lr_input.setText("0.001")
        self.lr_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        lr_layout.addWidget(self.lr_input)
        
        config_layout.addLayout(lr_layout)
        
        # Validación cruzada
        validation_layout = QHBoxLayout()
        validation_layout.addWidget(QLabel("% para validación:"))
        
        self.validation_input = QLineEdit()
        self.validation_input.setPlaceholderText("20")
        self.validation_input.setText("20")
        self.validation_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        validation_layout.addWidget(self.validation_input)
        
        config_layout.addLayout(validation_layout)
        
        # Botones de control de entrenamiento
        buttons_layout = QHBoxLayout()
        
        self.train_button = QPushButton("Iniciar Entrenamiento")
        self.train_button.setStyleSheet("""
            QPushButton {
                background-color: #00B4A6;
                color: white;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00D1C1;
            }
        """)
        self.train_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.train_button.clicked.connect(self._start_training)
        buttons_layout.addWidget(self.train_button)
        
        self.stop_training_button = QPushButton("Detener Entrenamiento")
        self.stop_training_button.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F44336;
            }
        """)
        self.stop_training_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.stop_training_button.clicked.connect(self._stop_training)
        self.stop_training_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_training_button)
        
        config_layout.addLayout(buttons_layout)
        
        training_controls_layout.addWidget(config_group)
        
        # Estadísticas de entrenamiento
        stats_group = QGroupBox("Estadísticas del Modelo")
        stats_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                color: #00B4A6;
            }
        """)
        
        stats_layout = QVBoxLayout(stats_group)
        
        # Crear una tabla para estadísticas
        self.stats_table = QTextEdit()
        self.stats_table.setReadOnly(True)
        self.stats_table.setStyleSheet("""
            QTextEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        self.stats_table.setHtml("""
            <table width="100%" cellspacing="5">
                <tr>
                    <td><b>Estado:</b></td>
                    <td>No entrenado</td>
                </tr>
                <tr>
                    <td><b>Tamaño del vocabulario:</b></td>
                    <td>0 palabras</td>
                </tr>
                <tr>
                    <td><b>Datos de entrenamiento:</b></td>
                    <td>0 ejemplos</td>
                </tr>
                <tr>
                    <td><b>Precisión actual:</b></td>
                    <td>0%</td>
                </tr>
                <tr>
                    <td><b>Último entrenamiento:</b></td>
                    <td>Nunca</td>
                </tr>
            </table>
        """)
        
        stats_layout.addWidget(self.stats_table)
        
        training_controls_layout.addWidget(stats_group)
        
        # Progreso de entrenamiento
        progress_layout = QVBoxLayout()
        
        progress_layout.addWidget(QLabel("Progreso del entrenamiento:"))
        
        self.training_progress = QTextEdit()
        self.training_progress.setReadOnly(True)
        self.training_progress.setPlaceholderText("El progreso del entrenamiento se mostrará aquí...")
        self.training_progress.setStyleSheet("""
            QTextEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                background-color: #2A2A40;
                color: white;
                font-family: monospace;
            }
        """)
        self.training_progress.setMaximumHeight(150)
        progress_layout.addWidget(self.training_progress)
        
        training_controls_layout.addLayout(progress_layout)
        
        # Entrenamiento automático
        auto_training_layout = QHBoxLayout()
        
        self.auto_training_check = QCheckBox("Entrenamiento automático")
        self.auto_training_check.setStyleSheet("""
            QCheckBox {
                color: white;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #555;
                background-color: #2A2A40;
            }
            QCheckBox::indicator:checked {
                background-color: #00B4A6;
                border: 2px solid #00B4A6;
            }
        """)
        self.auto_training_check.setChecked(True)
        self.auto_training_check.stateChanged.connect(self._toggle_auto_training)
        auto_training_layout.addWidget(self.auto_training_check)
        
        auto_training_layout.addWidget(QLabel("Intervalo (horas):"))
        
        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("24")
        self.interval_input.setText("24")
        self.interval_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        auto_training_layout.addWidget(self.interval_input)
        
        training_controls_layout.addLayout(auto_training_layout)
        
        # Estado del entrenamiento
        self.training_status = QLabel("Estado: No entrenando")
        self.training_status.setStyleSheet("color: #999;")
        training_controls_layout.addWidget(self.training_status)
        
        # Añadir marco a layout principal
        training_layout.addWidget(training_frame)
        
        # Actualizar estado del entrenamiento
        self._update_training_status()
        
        return training_tab

    def _start_training(self):
        """Inicia el entrenamiento del modelo"""
        if not hasattr(self.ai_system, 'ml_engine') or not self.ai_system.ml_engine:
            QMessageBox.warning(
                self,
                "Error",
                "El motor de aprendizaje automático no está disponible."
            )
            return
        
        try:
            # Obtener parámetros de entrenamiento
            epochs = int(self.epochs_input.text() or "5")
            batch_size = int(self.batch_input.text() or "64")
            learning_rate = float(self.lr_input.text() or "0.001")
            validation_split = float(self.validation_input.text() or "20") / 100.0
            
            # Validar parámetros
            if epochs <= 0 or batch_size <= 0 or learning_rate <= 0 or validation_split <= 0 or validation_split >= 1:
                QMessageBox.warning(
                    self,
                    "Parámetros inválidos",
                    "Por favor, introduzca valores válidos para los parámetros de entrenamiento."
                )
                return
            
            # Obtener datos de entrenamiento (simplificado)
            # En un sistema real, esto se haría en un hilo separado
            self.training_progress.clear()
            self.training_progress.append("Preparando datos de entrenamiento...")
            
            # Actualizar estado
            self.training_status.setText("Estado: Entrenando")
            self.training_status.setStyleSheet("color: #00B4A6;")
            self.train_button.setEnabled(False)
            self.stop_training_button.setEnabled(True)
            
            # Simular entrenamiento (en un sistema real, se haría en un hilo)
            QMessageBox.information(
                self,
                "Entrenamiento iniciado",
                "El entrenamiento del modelo ha comenzado. Esto puede tardar varios minutos."
            )
            
            # Actualizar progreso (simulado)
            for i in range(5):
                self.training_progress.append(f"Época {i+1}/{epochs} - Precisión: {50 + i*10}% - Pérdida: {0.5 - i*0.1:.4f}")
                QApplication.processEvents()  # Permitir que la interfaz se actualice
                
            # Actualizar estado de finalización (simulado)
            self.training_status.setText("Estado: Finalizado")
            self.training_status.setStyleSheet("color: #4CAF50;")
            self.train_button.setEnabled(True)
            self.stop_training_button.setEnabled(False)
            
            # Actualizar estadísticas (simulado)
            self.stats_table.setHtml("""
                <table width="100%" cellspacing="5">
                    <tr>
                        <td><b>Estado:</b></td>
                        <td>Entrenado</td>
                    </tr>
                    <tr>
                        <td><b>Tamaño del vocabulario:</b></td>
                        <td>5000 palabras</td>
                    </tr>
                    <tr>
                        <td><b>Datos de entrenamiento:</b></td>
                        <td>1000 ejemplos</td>
                    </tr>
                    <tr>
                        <td><b>Precisión actual:</b></td>
                        <td>90%</td>
                    </tr>
                    <tr>
                        <td><b>Último entrenamiento:</b></td>
                        <td>Ahora</td>
                    </tr>
                </table>
            """)
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error al iniciar entrenamiento: {str(e)}"
            )
            
            # Restaurar estado
            self.training_status.setText("Estado: Error")
            self.training_status.setStyleSheet("color: #E53935;")
            self.train_button.setEnabled(True)
            self.stop_training_button.setEnabled(False)

    def _stop_training(self):
        """Detiene el entrenamiento en curso"""
        if not hasattr(self.ai_system, 'ml_engine') or not self.ai_system.ml_engine:
            return
        
        # En un sistema real, aquí se enviaría una señal para detener el entrenamiento
        
        QMessageBox.information(
            self,
            "Entrenamiento detenido",
            "El entrenamiento ha sido detenido."
        )
        
        # Actualizar estado
        self.training_status.setText("Estado: Detenido")
        self.training_status.setStyleSheet("color: #E53935;")
        self.train_button.setEnabled(True)
        self.stop_training_button.setEnabled(False)
        
        # Actualizar progreso
        self.training_progress.append("Entrenamiento detenido por el usuario.")

    def _toggle_auto_training(self):
        """Activa o desactiva el entrenamiento automático"""
        if not hasattr(self.ai_system, 'ml_engine') or not self.ai_system.ml_engine:
            return
        
        is_checked = self.auto_training_check.isChecked()
        self.interval_input.setEnabled(is_checked)
        
        if is_checked:
            # Activar entrenamiento automático
            try:
                interval_hours = int(self.interval_input.text() or "24")
                if interval_hours <= 0:
                    QMessageBox.warning(
                        self,
                        "Valor inválido",
                        "El intervalo debe ser un número positivo."
                    )
                    self.auto_training_check.setChecked(False)
                    return
                
                # En un sistema real, aquí se programaría el entrenamiento automático
                
                QMessageBox.information(
                    self,
                    "Entrenamiento automático",
                    f"El entrenamiento automático se realizará cada {interval_hours} horas."
                )
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Valor inválido",
                    "Por favor, introduzca un número válido para el intervalo."
                )
                self.auto_training_check.setChecked(False)
        else:
            # Desactivar entrenamiento automático
            # En un sistema real, aquí se cancelaría la programación
            
            QMessageBox.information(
                self,
                "Entrenamiento automático",
                "El entrenamiento automático ha sido desactivado."
            )

    def _update_training_status(self):
        """Actualiza el estado mostrado del entrenamiento"""
        if not hasattr(self.ai_system, 'ml_engine') or not self.ai_system.ml_engine:
            self.train_button.setEnabled(False)
            self.stop_training_button.setEnabled(False)
            self.auto_training_check.setEnabled(False)
            self.interval_input.setEnabled(False)
            self.training_status.setText("Estado: Motor ML no disponible")
            self.training_status.setStyleSheet("color: #E53935;")


    def _create_voice_panel(self, tab_widget):
        """Crea el panel de control de voz"""
        voice_tab = QWidget()
        tab_widget.addTab(voice_tab, "Voz")
        
        voice_layout = QVBoxLayout(voice_tab)
        voice_layout.setContentsMargins(20, 20, 20, 20)
        voice_layout.setSpacing(15)
        
        # Título
        voice_title = QLabel("Control de Voz")
        voice_title.setFont(QFont(self.default_font.family(), 18, QFont.Weight.Bold))
        voice_title.setStyleSheet("color: #00B4A6;")
        voice_layout.addWidget(voice_title)
        
        # Panel de configuración de voz
        voice_frame = QFrame()
        voice_frame.setFrameShape(QFrame.Shape.StyledPanel)
        voice_frame.setFrameShadow(QFrame.Shadow.Raised)
        voice_frame.setStyleSheet("background-color: #1E1E2E; padding: 15px; border-radius: 5px;")
        
        voice_config_layout = QVBoxLayout(voice_frame)
        voice_config_layout.setSpacing(15)
        
        # Información sobre la voz
        voice_info = QLabel("Configura las opciones de síntesis de voz del sistema.")
        voice_info.setWordWrap(True)
        voice_config_layout.addWidget(voice_info)
        
        # Configuración de idioma
        lang_layout = QHBoxLayout()
        
        lang_layout.addWidget(QLabel("Idioma:"))
        
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("es")
        self.language_input.setText("es")
        self.language_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        lang_layout.addWidget(self.language_input)
        
        voice_config_layout.addLayout(lang_layout)
        
        # Configuración de región
        region_layout = QHBoxLayout()
        
        region_layout.addWidget(QLabel("Región:"))
        
        self.region_input = QLineEdit()
        self.region_input.setPlaceholderText("com.mx")
        self.region_input.setText("com.mx")
        self.region_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        region_layout.addWidget(self.region_input)
        
        voice_config_layout.addLayout(region_layout)
        
        # Configuración de velocidad
        speed_layout = QHBoxLayout()
        
        speed_layout.addWidget(QLabel("Velocidad:"))
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #2A2A40;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00B4A6;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_value = QLabel("100%")
        speed_layout.addWidget(self.speed_value)
        
        # Conectar evento de cambio del slider
        self.speed_slider.valueChanged.connect(self._update_speed_value)
        
        voice_config_layout.addLayout(speed_layout)
        
        # Botones de control
        buttons_layout = QHBoxLayout()
        
        self.voice_on_button = QPushButton("Activar Voz")
        self.voice_on_button.setStyleSheet("""
            QPushButton {
                background-color: #00B4A6;
                color: white;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00D1C1;
            }
        """)
        self.voice_on_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.voice_on_button.clicked.connect(self._toggle_voice)
        buttons_layout.addWidget(self.voice_on_button)
        
        self.test_voice_button = QPushButton("Probar Voz")
        self.test_voice_button.setStyleSheet("""
            QPushButton {
                background-color: #6A7EC8;
                color: white;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #7C8ED9;
            }
        """)
        self.test_voice_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.test_voice_button.clicked.connect(self._test_voice)
        buttons_layout.addWidget(self.test_voice_button)
        
        voice_config_layout.addLayout(buttons_layout)
        
        # Espacio para mensajes de estado
        self.voice_status = QLabel("Estado: Activado")
        self.voice_status.setStyleSheet("color: #00B4A6;")
        voice_config_layout.addWidget(self.voice_status)
        
        # Añadir marco a layout principal
        voice_layout.addWidget(voice_frame)
        
        # Añadir espacio expansible al final
        voice_layout.addStretch(1)
        
        # Verificar el estado inicial de la voz
        self._update_voice_status()
        
        return voice_tab

    def _update_speed_value(self):
        """Actualiza el valor mostrado de velocidad"""
        speed = self.speed_slider.value()
        self.speed_value.setText(f"{speed}%")

    def _toggle_voice(self):
        """Activa o desactiva la síntesis de voz"""
        if hasattr(self.ai_system, 'voice_manager'):
            if self.ai_system.voice_manager:
                # Verificar estado actual
                is_active = self.voice_on_button.text() == "Desactivar Voz"
                
                if is_active:
                    # Desactivar voz
                    self.voice_on_button.setText("Activar Voz")
                    self.voice_on_button.setStyleSheet("""
                        QPushButton {
                            background-color: #00B4A6;
                            color: white;
                            border-radius: 4px;
                            padding: 8px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #00D1C1;
                        }
                    """)
                    self.voice_status.setText("Estado: Desactivado")
                    self.voice_status.setStyleSheet("color: #E53935;")
                else:
                    # Activar voz
                    self.voice_on_button.setText("Desactivar Voz")
                    self.voice_on_button.setStyleSheet("""
                        QPushButton {
                            background-color: #E53935;
                            color: white;
                            border-radius: 4px;
                            padding: 8px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #F44336;
                        }
                    """)
                    self.voice_status.setText("Estado: Activado")
                    self.voice_status.setStyleSheet("color: #00B4A6;")
                
                # TODO: Implementar la desactivación real de la voz
        else:
            QMessageBox.warning(
                self,
                "Error",
                "El gestor de voz no está disponible."
            )

    def _test_voice(self):
        """Prueba la síntesis de voz"""
        if hasattr(self.ai_system, 'voice_manager') and self.ai_system.voice_manager:
            # Obtener configuración actual
            language = self.language_input.text().strip() or "es"
            region = self.region_input.text().strip() or "com.mx"
            speed = self.speed_slider.value() / 100.0
            
            # Actualizar configuración si hay métodos disponibles
            if hasattr(self.ai_system.voice_manager, 'set_language'):
                self.ai_system.voice_manager.set_language(language)
            
            if hasattr(self.ai_system.voice_manager, 'set_voice'):
                self.ai_system.voice_manager.set_voice(region)
            
            # Texto de prueba
            test_text = "Saludos, Su Majestad. El sistema de voz está funcionando correctamente."
            
            # Generar voz
            self.ai_system.voice_manager.speak(test_text)
        else:
            QMessageBox.warning(
                self,
                "Error",
                "El gestor de voz no está disponible."
            )

    def _update_voice_status(self):
        """Actualiza el estado mostrado de la voz"""
        if hasattr(self.ai_system, 'voice_manager') and self.ai_system.voice_manager:
            if self.ai_system.voice_manager.is_running:
                self.voice_on_button.setText("Desactivar Voz")
                self.voice_on_button.setStyleSheet("""
                    QPushButton {
                        background-color: #E53935;
                        color: white;
                        border-radius: 4px;
                        padding: 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #F44336;
                    }
                """)
                self.voice_status.setText("Estado: Activado")
                self.voice_status.setStyleSheet("color: #00B4A6;")
            else:
                self.voice_on_button.setText("Activar Voz")
                self.voice_status.setText("Estado: Desactivado")
                self.voice_status.setStyleSheet("color: #E53935;")
        else:
            self.voice_on_button.setEnabled(False)
            self.test_voice_button.setEnabled(False)
            self.voice_status.setText("Estado: No disponible")
            self.voice_status.setStyleSheet("color: #E53935;")

    
    
    def _create_model_settings(self, parent_layout):
        """Crea la sección de configuración del modelo"""
        group_box = QFrame()
        group_box.setFrameShape(QFrame.Shape.StyledPanel)
        group_box.setFrameShadow(QFrame.Shadow.Raised)
        group_box.setStyleSheet("background-color: #212134; padding: 10px;")
        
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título de sección
        section_title = QLabel("Modelo de IA")
        section_title.setFont(QFont(self.default_font.family(), 11, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #00B4A6;")
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
        self.creativity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #2A2A40;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00B4A6;
                border: 1px solid #00B4A6;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)
        
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
        self.length_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        length_layout.addWidget(self.length_combo)
        
        layout.addLayout(length_layout)
        
        # Casilla de aprendizaje continuo
        learning_layout = QHBoxLayout()
        learning_layout.setContentsMargins(0, 0, 0, 0)
        
        self.continuous_learning = QCheckBox("Habilitar aprendizaje continuo")
        self.continuous_learning.setChecked(True)
        self.continuous_learning.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #555;
            }
            QCheckBox::indicator:checked {
                background-color: #00B4A6;
                border: 1px solid #00B4A6;
            }
        """)
        learning_layout.addWidget(self.continuous_learning)
        
        layout.addLayout(learning_layout)
        
        parent_layout.addWidget(group_box)
    
    def _create_system_settings(self, parent_layout):
        """Crea la sección de configuración del sistema"""
        group_box = QFrame()
        group_box.setFrameShape(QFrame.Shape.StyledPanel)
        group_box.setFrameShadow(QFrame.Shadow.Raised)
        group_box.setStyleSheet("background-color: #212134; padding: 10px;")
        
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título de sección
        section_title = QLabel("Sistema")
        section_title.setFont(QFont(self.default_font.family(), 11, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #00B4A6;")
        layout.addWidget(section_title)
        
        # Opciones de inicio
        startup_check = QCheckBox("Iniciar automáticamente con el sistema")
        startup_check.setChecked(False)
        startup_check.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #555;
            }
            QCheckBox::indicator:checked {
                background-color: #00B4A6;
                border: 1px solid #00B4A6;
            }
        """)
        layout.addWidget(startup_check)
        
        # Opciones de guardado
        save_check = QCheckBox("Guardar historial de conversaciones")
        save_check.setChecked(True)
        save_check.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #555;
            }
            QCheckBox::indicator:checked {
                background-color: #00B4A6;
                border: 1px solid #00B4A6;
            }
        """)
        layout.addWidget(save_check)
        
        # Opciones de actualizaciones
        update_check = QCheckBox("Buscar actualizaciones automáticamente")
        update_check.setChecked(True)
        update_check.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 1px solid #555;
            }
            QCheckBox::indicator:checked {
                background-color: #00B4A6;
                border: 1px solid #00B4A6;
            }
        """)
        layout.addWidget(update_check)
        
        # Ruta de datos
        data_layout = QHBoxLayout()
        data_layout.setContentsMargins(0, 0, 0, 0)
        
        data_label = QLabel("Directorio de datos:")
        data_layout.addWidget(data_label)
        
        data_path = QLineEdit()
        data_path.setText("./data")
        data_path.setReadOnly(True)
        data_path.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
            }
        """)
        data_layout.addWidget(data_path)
        
        browse_button = QPushButton("...")
        browse_button.setMaximumWidth(30)
        browse_button.clicked.connect(lambda: self._browse_directory(data_path))
        data_layout.addWidget(browse_button)
        
        layout.addLayout(data_layout)
        
        parent_layout.addWidget(group_box)
    
    def _create_knowledge_panel(self, tab_widget):
        """Crea el panel de gestión de conocimiento"""
        knowledge_tab = QWidget()
        tab_widget.addTab(knowledge_tab, "Conocimiento")
        
        knowledge_layout = QVBoxLayout(knowledge_tab)
        knowledge_layout.setContentsMargins(20, 20, 20, 20)
        knowledge_layout.setSpacing(15)
        
        # Título
        knowledge_title = QLabel("Base de Conocimiento")
        knowledge_title.setFont(QFont(self.default_font.family(), 18, QFont.Weight.Bold))
        knowledge_title.setStyleSheet("color: #00B4A6;")
        knowledge_layout.addWidget(knowledge_title)
        
        # Panel de pestañas para la base de conocimiento
        knowledge_tabs = QTabWidget()
        knowledge_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #1E1E2E;
            }
            QTabBar::tab {
                background-color: #2D2D44;
                color: #CCC;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #00B4A6;
                color: white;
            }
        """)
        
        # Pestaña para añadir hechos y conceptos
        facts_tab = QWidget()
        knowledge_tabs.addTab(facts_tab, "Hechos y Conceptos")
        
        facts_layout = QVBoxLayout(facts_tab)
        facts_layout.setContentsMargins(15, 15, 15, 15)
        facts_layout.setSpacing(10)
        
        # Entrada para nuevo hecho
        facts_layout.addWidget(QLabel("Añadir nuevo concepto o hecho:"))
        
        self.knowledge_input = QTextEdit()
        self.knowledge_input.setPlaceholderText("Escriba un nuevo concepto o hecho aquí...")
        self.knowledge_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        self.knowledge_input.setMinimumHeight(80)
        facts_layout.addWidget(self.knowledge_input)
        
        # Categoría e importancia
        meta_layout = QGridLayout()
        meta_layout.setColumnStretch(1, 1)
        
        meta_layout.addWidget(QLabel("Categoría:"), 0, 0)
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("General")
        self.category_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        meta_layout.addWidget(self.category_input, 0, 1)
        
        meta_layout.addWidget(QLabel("Importancia:"), 1, 0)
        self.importance_slider = QSlider(Qt.Orientation.Horizontal)
        self.importance_slider.setMinimum(1)
        self.importance_slider.setMaximum(10)
        self.importance_slider.setValue(5)
        self.importance_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #2A2A40;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00B4A6;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)
        meta_layout.addWidget(self.importance_slider, 1, 1)
        
        facts_layout.addLayout(meta_layout)
        
        # Botón para añadir a la base de conocimiento
        add_to_kb_button = QPushButton("Añadir a la Base de Conocimiento")
        add_to_kb_button.setStyleSheet("""
            QPushButton {
                background-color: #00B4A6;
                color: white;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00D1C1;
            }
            QPushButton:pressed {
                background-color: #00A091;
            }
        """)
        add_to_kb_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_to_kb_button.clicked.connect(self._add_to_knowledge_base)
        facts_layout.addWidget(add_to_kb_button)
        
        # Espacio para explorar la base de conocimiento
        facts_layout.addWidget(QLabel("Explorar base de conocimiento:"))
        
        # Búsqueda
        search_layout = QHBoxLayout()
        
        self.knowledge_search_input = QLineEdit()
        self.knowledge_search_input.setPlaceholderText("Buscar en base de conocimiento...")
        self.knowledge_search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        search_layout.addWidget(self.knowledge_search_input)
        
        search_button = QPushButton("Buscar")
        search_button.setStyleSheet("""
            QPushButton {
                background-color: #00B4A6;
                color: white;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #00D1C1;
            }
        """)
        search_button.clicked.connect(self._search_knowledge_base)
        search_layout.addWidget(search_button)
        
        facts_layout.addLayout(search_layout)
        
        # Resultados de búsqueda
        self.knowledge_results = QTextEdit()
        self.knowledge_results.setReadOnly(True)
        self.knowledge_results.setPlaceholderText("Los resultados de búsqueda aparecerán aquí...")
        self.knowledge_results.setStyleSheet("""
            QTextEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        facts_layout.addWidget(self.knowledge_results)
        
        # Pestaña para importar datos
        import_tab = QWidget()
        knowledge_tabs.addTab(import_tab, "Importar Datos")
        
        import_layout = QVBoxLayout(import_tab)
        import_layout.setContentsMargins(15, 15, 15, 15)
        import_layout.setSpacing(10)
        
        # TODO: Implementar importación de datos
        import_info = QLabel("Próximamente: Importación de datos desde archivos CSV, JSON, y otros formatos.")
        import_info.setWordWrap(True)
        import_layout.addWidget(import_info)
        
        knowledge_layout.addWidget(knowledge_tabs)
        
        # Panel para el recolector de conocimiento
        recolector_title = QLabel("Recolector de Conocimiento")
        recolector_title.setFont(QFont(self.default_font.family(), 18, QFont.Weight.Bold))
        recolector_title.setStyleSheet("color: #00B4A6;")
        knowledge_layout.addWidget(recolector_title)
        
        recolector_frame = QFrame()
        recolector_frame.setFrameShape(QFrame.Shape.StyledPanel)
        recolector_frame.setFrameShadow(QFrame.Shadow.Raised)
        recolector_frame.setStyleSheet("background-color: #1E1E2E; padding: 15px; border-radius: 5px;")
        
        recolector_layout = QVBoxLayout(recolector_frame)
        recolector_layout.setSpacing(15)
        
        recolector_info = QLabel("El recolector obtiene conocimiento automáticamente desde Internet para enriquecer la base de conocimiento del sistema.")
        recolector_info.setWordWrap(True)
        recolector_layout.addWidget(recolector_info)
        
        # Campo para añadir tema
        recolector_layout.addWidget(QLabel("Añadir tema para investigar:"))
        
        topic_layout = QHBoxLayout()
        
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Escriba un tema para investigar...")
        self.topic_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #2A2A40;
                color: white;
            }
        """)
        topic_layout.addWidget(self.topic_input)
        
        add_topic_button = QPushButton("Añadir Tema")
        add_topic_button.setStyleSheet("""
            QPushButton {
                background-color: #00B4A6;
                color: white;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #00D1C1;
            }
        """)
        add_topic_button.clicked.connect(self._add_harvesting_topic)
        topic_layout.addWidget(add_topic_button)
        
        recolector_layout.addLayout(topic_layout)
        
        # Botones de control
        buttons_layout = QHBoxLayout()
        
        self.start_harvester_button = QPushButton("Iniciar Recolector")
        self.start_harvester_button.setStyleSheet("""
            QPushButton {
                background-color: #00B4A6;
                color: white;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00D1C1;
            }
        """)
        self.start_harvester_button.clicked.connect(self._start_harvester)
        buttons_layout.addWidget(self.start_harvester_button)
        
        self.stop_harvester_button = QPushButton("Detener Recolector")
        self.stop_harvester_button.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F44336;
            }
        """)
        self.stop_harvester_button.setEnabled(False)
        self.stop_harvester_button.clicked.connect(self._stop_harvester)
        buttons_layout.addWidget(self.stop_harvester_button)
        
        recolector_layout.addLayout(buttons_layout)
        
        # Estado del recolector
        self.harvester_status = QLabel("Estado: Detenido")
        self.harvester_status.setStyleSheet("color: #E53935;")
        recolector_layout.addWidget(self.harvester_status)
        
        knowledge_layout.addWidget(recolector_frame)
        
        return knowledge_tab


    def _setup_timers(self):
        """Configura temporizadores para actualización periódica de la interfaz"""
        # Temporizador para actualizar estado del sistema
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_system_status)
        self.status_timer.start(5000)  # Actualizar cada 5 segundos
        
        # Temporizador para actualizar estado del recolector
        self.harvester_timer = QTimer(self)
        self.harvester_timer.timeout.connect(self._update_harvester_status)
        self.harvester_timer.start(3000)  # Actualizar cada 3 segundos
        
        # Temporizador para comprobar respuestas nuevas
        self.chat_timer = QTimer(self)
        self.chat_timer.timeout.connect(self._check_new_responses)
        self.chat_timer.start(1000)  # Comprobar cada segundo

    def _update_system_status(self):
        """Actualiza la información de estado del sistema en la barra de estado"""
        if not hasattr(self, 'ai_system') or not self.ai_system:
            return
        
        try:
            # Obtener fecha y hora actual
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Estado del sistema
            if self.ai_system.is_running:
                status_text = f"Sistema en ejecución | Última actualización: {current_time}"
            else:
                status_text = f"Sistema detenido | Última actualización: {current_time}"
            
            # Actualizar barra de estado
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(status_text)
        except Exception as e:
            print(f"Error al actualizar estado: {str(e)}")

    def _update_harvester_status(self):
        """Actualiza el estado mostrado del recolector de conocimiento"""
        if not hasattr(self, 'ai_system') or not self.ai_system or not hasattr(self.ai_system, 'knowledge_harvester'):
            return
        
        try:
            if not hasattr(self, 'harvester_status'):
                return
                
            # Obtener estado actual
            if self.ai_system.knowledge_harvester and self.ai_system.knowledge_harvester.is_running:
                # Obtener tamaño de la cola si está disponible
                if hasattr(self.ai_system.knowledge_harvester, 'topic_queue'):
                    try:
                        queue_size = self.ai_system.knowledge_harvester.topic_queue.qsize()
                        self.harvester_status.setText(f"Estado: En ejecución | Temas en cola: {queue_size}")
                    except:
                        self.harvester_status.setText("Estado: En ejecución")
                    
                    self.harvester_status.setStyleSheet("color: #00B4A6;")
                    
                    if hasattr(self, 'start_harvester_button') and hasattr(self, 'stop_harvester_button'):
                        self.start_harvester_button.setEnabled(False)
                        self.stop_harvester_button.setEnabled(True)
                else:
                    self.harvester_status.setText("Estado: En ejecución")
                    self.harvester_status.setStyleSheet("color: #00B4A6;")
            else:
                self.harvester_status.setText("Estado: Detenido")
                self.harvester_status.setStyleSheet("color: #E53935;")
                
                if hasattr(self, 'start_harvester_button') and hasattr(self, 'stop_harvester_button'):
                    self.start_harvester_button.setEnabled(True)
                    self.stop_harvester_button.setEnabled(False)
        except Exception as e:
            print(f"Error al actualizar estado del recolector: {str(e)}")

    def _check_new_responses(self):
        """Comprueba si hay nuevas respuestas del sistema"""
        # En un sistema real, esto verificaría respuestas asíncronas
        # Para esta implementación, es solo un marcador de posición
        pass

    def _add_message_to_history(self, role, message, timestamp=None):
        """Añade un mensaje al historial de chat con formato avanzado"""
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
        # Determinamos la clase CSS según el rol
        css_class = "user-message" if role == "user" else "assistant-message"
        
        # Formateamos el HTML para la burbuja de mensaje
        html = f"""
        <div class="{css_class}">
            {message}
            <div class="timestamp">{timestamp}</div>
        </div>
        """
        
        # Insertamos el HTML
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        cursor.insertBlock()  # Añade un bloque vacío como separador
        
        # Desplazamos al final del historial
        self.chat_history.moveCursor(QTextCursor.MoveOperation.End)

    def _add_harvesting_topic(self):
        """Añade un tema para el recolector de conocimiento"""
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(
                self,
                "Tema vacío",
                "Por favor, introduzca un tema para investigar."
            )
            return
            
        try:
            if hasattr(self.ai_system, 'knowledge_harvester'):
                success, message = self.ai_system.knowledge_harvester.add_topic(topic)
                
                if success:
                    QMessageBox.information(
                        self,
                        "Tema Añadido",
                        message
                    )
                    self.topic_input.clear()
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        message
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "El recolector de conocimiento no está disponible."
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo añadir el tema: {str(e)}"
            )

    def _start_harvester(self):
        """Inicia el recolector de conocimiento"""
        try:
            if hasattr(self.ai_system, 'knowledge_harvester'):
                if self.ai_system.knowledge_harvester.is_running:
                    QMessageBox.information(
                        self,
                        "Información",
                        "El recolector ya está en ejecución."
                    )
                    return
                    
                success = self.ai_system.knowledge_harvester.start()
                
                if success:
                    self.harvester_status.setText("Estado: En ejecución")
                    self.harvester_status.setStyleSheet("color: #00B4A6;")
                    self.start_harvester_button.setEnabled(False)
                    self.stop_harvester_button.setEnabled(True)
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "No se pudo iniciar el recolector."
                    )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo iniciar el recolector: {str(e)}"
            )

    def _stop_harvester(self):
        """Detiene el recolector de conocimiento"""
        try:
            if hasattr(self.ai_system, 'knowledge_harvester'):
                if not self.ai_system.knowledge_harvester.is_running:
                    return
                    
                success = self.ai_system.knowledge_harvester.stop()
                
                if success:
                    self.harvester_status.setText("Estado: Detenido")
                    self.harvester_status.setStyleSheet("color: #E53935;")
                    self.start_harvester_button.setEnabled(True)
                    self.stop_harvester_button.setEnabled(False)
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "No se pudo detener el recolector."
                    )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo detener el recolector: {str(e)}"
            )

    def _search_knowledge_base(self):
        """Busca en la base de conocimiento y muestra resultados"""
        query = self.knowledge_search_input.text().strip()
        if not query:
            self.knowledge_results.clear()
            self.knowledge_results.setPlainText("Por favor, introduzca un término de búsqueda.")
            return
            
        try:
            # Buscar en la base de conocimiento
            results = self.ai_system.knowledge_base.search_facts(query, limit=10)
            
            if not results:
                self.knowledge_results.clear()
                self.knowledge_results.setPlainText("No se encontraron resultados para la búsqueda.")
                return
                
            # Mostrar resultados con formato
            self.knowledge_results.clear()
            result_text = ""
            
            for i, result in enumerate(results, 1):
                category = result.get('category', 'General')
                importance = result.get('importance', 0.5)
                stars = "★" * int(importance * 5 // 1)
                
                result_text += f"{i}. {result['content']}\n"
                result_text += f"   Categoría: {category} | Relevancia: {stars}\n\n"
                
            self.knowledge_results.setPlainText(result_text)
        except Exception as e:
            self.knowledge_results.clear()
            self.knowledge_results.setPlainText(f"Error al buscar: {str(e)}")

    def _add_to_knowledge_base(self):
        """Añade un nuevo hecho a la base de conocimiento"""
        content = self.knowledge_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(
                self,
                "Contenido vacío",
                "Por favor, introduzca un hecho o concepto para añadir."
            )
            return
            
        category = self.category_input.text().strip() or "General"
        importance = self.importance_slider.value() / 10.0  # Convertir a escala 0-1
        
        try:
            fact_id = self.ai_system.knowledge_base.add_fact(content, category, importance)
            
            if fact_id:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Hecho añadido correctamente a la categoría '{category}'."
                )
                self.knowledge_input.clear()
                # Opcional: actualizar cualquier vista de conocimiento
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo añadir el hecho a la base de conocimiento."
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error al añadir hecho: {str(e)}"
            )

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
        
        # Añadir mensaje del usuario al historial con formato HTML
        current_time = datetime.now().strftime("%H:%M:%S")
        
        html = f"""
        <div class="user-message">
            {user_input}
            <div class="timestamp">{current_time}</div>
        </div>
        """
        
        # Insertar HTML
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        cursor.insertBlock()  # Añade un bloque vacío como separador
        
        # Limpiar campo de entrada
        self.input_field.clear()
        
        # Procesar mensaje en hilo separado
        self.worker = WorkerThread(self.ai_system.process_input, user_input, self.enable_voice)
        self.worker.update_signal.connect(self._on_response_ready)
        self.worker.start()
    
    def _on_response_ready(self, response):
        """Maneja la recepción de una respuesta del sistema de IA"""
        # Añadir respuesta al historial con formato HTML
        current_time = datetime.now().strftime("%H:%M:%S")
        
        html = f"""
        <div class="assistant-message">
            {response}
            <div class="timestamp">{current_time}</div>
        </div>
        """
        
        # Insertar HTML
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        cursor.insertBlock()  # Añade un bloque vacío como separador
        
        # Desplazar al final del historial
        self.chat_history.moveCursor(QTextCursor.MoveOperation.End)
        
        # Habilitar nuevamente el botón de envío
        self.send_button.setEnabled(True)
    
    def _toggle_voice(self):
        """Activa/desactiva la respuesta por voz"""
        self.enable_voice = self.voice_toggle.isChecked()
        
        if self.enable_voice:
            self.voice_toggle.setText("  Voz: ON")
        else:
            self.voice_toggle.setText("  Voz: OFF")
    
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
        # Verificación de seguridad
        from PyQt6.QtWidgets import QMainWindow
        if not isinstance(self, QMainWindow):
            print("ERROR: run() llamado desde un tipo de objeto incorrecto")
            print(f"Tipo actual: {type(self).__name__}")
            return 1
            
        print(f"Mostrando ventana principal (tipo: {type(self).__name__})...")
        self.show()
        
        # Retornar código de salida de la aplicación
        return self._qt_app.exec()
    

