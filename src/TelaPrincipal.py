import os
import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QComboBox,
    QWidget, QGridLayout, QMessageBox, QTextEdit, QSizePolicy, QFileDialog, QLineEdit, QVBoxLayout
)
from PyQt6.QtCore import QThreadPool, Qt, QSettings
from PyQt6.QtGui import QIcon, QTextCursor
from utils.Input import HoverButton
from AutomacaoBlume import Blume, AutomationTask

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuração da interface gráfica
        self.setStyleSheet("""
            QLabel {
                font-family: 'Open Sans';
                font-size: 12px;
                color: white;
            }
            QGroupBox {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 20px;
            }
            QGroupBox:title {
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
        """)

        # Configurações persistentes
        self.settings_path = "config.json"
        self.load_settings()

        # Configurar a janela principal
        self.setWindowTitle("LE - Automação de Coleta")
        self.setWindowIcon(QIcon("resources/logo.ico"))
        self.setGeometry(100, 100, 900, 550)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.df = pd.DataFrame()

        # Carregar configurações e definir layout
        self.load_settings()
        self.init_ui()
        self.threadpool = QThreadPool()

        # Carregar a planilha automaticamente, se o caminho estiver definido
        if self.data_path:
            self.load_data_file(self.data_path)
        else:
            self.select_data_file()

    def load_settings(self):
        """Carrega configurações salvas usando QSettings."""
        settings = QSettings(self.settings_path, QSettings.Format.IniFormat)
        self.save_directory = settings.value("save_directory", "")
        self.data_path = settings.value("data_path", "")

    def save_settings(self):
        """Salva configurações usando QSettings."""
        settings = QSettings(self.settings_path, QSettings.Format.IniFormat)
        settings.setValue("save_directory", self.save_directory)
        settings.setValue("data_path", self.data_path)
        settings.setValue("last_open_dir", os.path.dirname(self.data_path))
        settings.sync()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        top_layout = QGridLayout()

        # Diretório de Salvamento
        self.save_dir_field = QLineEdit(self)
        self.save_dir_field.setReadOnly(True)
        self.save_dir_field.setText(self.save_directory)
        top_layout.addWidget(QLabel("Local de Salvamento:"), 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.save_dir_field, 0, 1)
        self.save_dir_button = HoverButton("Selecionar Pasta", self)
        self.save_dir_button.clicked.connect(self.select_save_directory)
        top_layout.addWidget(self.save_dir_button, 0, 2)

        # Seleção de Planilha
        self.planilha_field = QLineEdit(self)
        self.planilha_field.setReadOnly(True)
        self.planilha_field.setText(self.data_path)
        top_layout.addWidget(QLabel("Planilha de dados:"), 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.planilha_field, 1, 1)
        self.planilha_button = HoverButton("Selecionar Planilha", self)
        self.planilha_button.clicked.connect(self.select_data_file)
        top_layout.addWidget(self.planilha_button, 1, 2)

        # Seleção de Operadora
        self.operadora_combo = QComboBox(self)
        self.operadora_combo.addItem("Selecione uma planilha primeiro")
        top_layout.addWidget(QLabel("Selecionar Operadora:"), 2, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.operadora_combo, 2, 1)

        self.confirm_button = HoverButton("Iniciar automação", self)
        self.confirm_button.clicked.connect(self.start_automation)
        top_layout.addWidget(self.confirm_button, 2, 2)

        self.layout.addLayout(top_layout)

        # Layout dos Logs
        logs_layout = QGridLayout()

        # Área para Log Técnico
        self.log_tecnico_area = QTextEdit(self)
        self.log_tecnico_area.setReadOnly(True)
        self.log_tecnico_area.setPlaceholderText("Log técnico")
        self.log_tecnico_area.setStyleSheet("""
            QTextEdit {
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                background-color: #262525;
                padding: 5px;
            }
        """)
        logs_layout.addWidget(self.log_tecnico_area, 0, 0, 2, 2)

        # Área para Log Faturas Coletadas
        self.faturas_coletadas_area = QTextEdit(self)
        self.faturas_coletadas_area.setReadOnly(True)
        self.faturas_coletadas_area.setPlaceholderText("Log faturas coletadas")
        self.faturas_coletadas_area.setStyleSheet("""
            QTextEdit {
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                background-color: #262525;
                padding: 5px;
            }
        """)
        logs_layout.addWidget(self.faturas_coletadas_area, 0, 2, 2, 2)

        logs_layout.setVerticalSpacing(10)
        logs_layout.setHorizontalSpacing(10)

        logs_layout.setColumnStretch(0, 2)
        logs_layout.setColumnStretch(1, 3)
        logs_layout.setColumnStretch(2, 2)
        logs_layout.setColumnStretch(3, 3)

        self.layout.addLayout(logs_layout)

        # Configurações adicionais de layout
        top_layout.setColumnStretch(0, 1)
        top_layout.setColumnStretch(1, 4)
        top_layout.setColumnStretch(2, 1)

        logs_layout.setRowStretch(0, 2)
        logs_layout.setRowStretch(1, 4)

        # Configurações de tamanho
        self.save_dir_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.planilha_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.operadora_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.confirm_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.save_dir_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.planilha_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.log_tecnico_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.faturas_coletadas_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def select_data_file(self):
        last_dir = QSettings(self.settings_path, QSettings.Format.IniFormat).value("last_open_dir", "")
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Planilha de Dados", last_dir, "Arquivos Excel (*.xlsx *.xlsm)")

        if file_path:
            self.load_data_file(file_path)

    def load_data_file(self, file_path):
        """Carrega a planilha de dados e atualiza a interface."""
        try:
            self.df = pd.read_excel(file_path)
            self.df = self.df[self.df['STATUS'] != 'COLETADO IA']
            self.df = self.df.sort_values(by='VENCIMENTO', ascending=True)

            self.data_path = file_path
            self.planilha_field.setText(file_path)

            # Atualiza o combo de operadoras
            self.operadora_combo.clear()
            operadoras = self.df['OPERADORA'].dropna().unique()
            self.operadora_combo.addItems(operadoras)

            self.save_settings()
        except KeyError as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar a planilha: Coluna '{e.args[0]}' ausente.")
            self.df = pd.DataFrame()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar a planilha: {e}")
            self.df = pd.DataFrame()

    def select_save_directory(self):
        last_save_dir = QSettings(self.settings_path, QSettings.Format.IniFormat).value("last_save_dir", "")
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar Diretório de Salvamento", last_save_dir)

        if dir_path:
            self.save_directory = dir_path
            self.save_dir_field.setText(dir_path)

            settings = QSettings(self.settings_path, QSettings.Format.IniFormat)
            settings.setValue("save_directory", dir_path)
            settings.setValue("last_save_dir", dir_path)

            self.save_settings()
        else:
            self.save_directory = ""

    def log_message(self, message, area="tecnico"):
        """Exibe mensagens nos logs adequados."""
        if area == "tecnico":
            self.log_tecnico_area.append(message)
            cursor = self.log_tecnico_area.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_tecnico_area.setTextCursor(cursor)
        elif area == "faturas":
            self.faturas_coletadas_area.append(message)
            cursor = self.faturas_coletadas_area.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.faturas_coletadas_area.setTextCursor(cursor)

    def start_automation(self):
        """Inicia o processo de automação."""
        selected_operadora = self.operadora_combo.currentText()

        if not self.save_directory:
            QMessageBox.warning(self, "Erro", "Selecione um diretório de salvamento primeiro.")
            return

        if not selected_operadora:
            QMessageBox.warning(self, "Erro", "Selecione uma operadora.")
            return

        if not self.data_path:
            QMessageBox.warning(self, "Erro", "Selecione uma planilha de dados primeiro.")
            return

        if self.df.empty:
            QMessageBox.warning(self, "Erro", "A planilha de dados ainda não foi carregada.")
            return

        user_data = self.df[self.df['OPERADORA'] == selected_operadora]
        if user_data.empty:
            QMessageBox.warning(self, "Erro", f"Nenhum dado encontrado para a operadora {selected_operadora}.")
            return

        if selected_operadora.upper() == "BLUME":
            automator = Blume(self, self.df)
        else:
            QMessageBox.warning(self, "Erro", f"Automação para a operadora {selected_operadora} não está implementada.")
            return

        task = AutomationTask(automator, user_data, self.log_message)
        self.threadpool.start(task)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec())
