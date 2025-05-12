
# Test simple para verificar que PyQt6 funciona correctamente
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test de PyQt6")
        self.setGeometry(100, 100, 400, 200)
        
        layout = QVBoxLayout()
        
        label = QLabel("Si puedes ver esta ventana, PyQt6 está funcionando correctamente!")
        layout.addWidget(label)
        
        button = QPushButton("Cerrar")
        button.clicked.connect(self.close)
        layout.addWidget(button)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    print("Ventana de prueba mostrada. ¿Puedes verla?")
    sys.exit(app.exec())
