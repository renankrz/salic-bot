"""Janela principal da GUI do Salic Bot"""

import logging
import os
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyle,
    QStyleOptionButton,
    QVBoxLayout,
    QWidget,
)

from ..bot import SalicBot
from ..logging_setup import configurar_logging
from ..models.projeto import Projeto
from ..paths import LOGS_DIR, SCREENSHOTS_DIR
from ..settings import ConfigManager

logger = logging.getLogger(__name__)


class BotWorker(QThread):
    """Thread para executar o bot sem travar a GUI"""

    finished = Signal(int, int)  # despesas_ok, total
    error = Signal(str)

    def __init__(self, bot: SalicBot):
        super().__init__()
        self.bot = bot

    def run(self):
        try:
            despesas_ok, total = self.bot.executar()
            self.finished.emit(despesas_ok, total)
        except Exception as e:
            self.error.emit(str(e))


class CustomCheckBox(QCheckBox):
    def paintEvent(self, event):
        # Desenha o checkbox nativo (label/texto)
        super().paintEvent(event)

        # Localiza o retângulo do indicador
        option = QStyleOptionButton()
        self.initStyleOption(option)
        rect = self.style().subElementRect(
            QStyle.SubElement.SE_CheckBoxIndicator, option, self
        )

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(rect, QColor("#1a1a1a"))

        # Borda clara
        painter.setPen(QPen(QColor("#aaaaaa"), 1))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

        # Check mark quando marcado
        if self.isChecked():
            painter.setPen(QColor("#00ff00"))
            font = painter.font()
            font.setPixelSize(rect.height() + 4)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "✓")

        painter.end()


class MainWindow(QWidget):
    """Janela principal do Salic Bot"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.config = ConfigManager()
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("Salic Bot")
        self.setFixedWidth(420)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # --- Título ---
        titulo = QLabel("Salic Bot")
        titulo.setStyleSheet(
            "font-size: 20px; font-weight: bold; font-family: monospace;"
        )
        layout.addWidget(titulo)

        # --- Seção: Configurações da Sessão ---
        sec_config = QLabel("Configurações da Sessão")
        sec_config.setStyleSheet(
            "font-weight: bold; font-family: monospace; margin-top: 24px;"
        )
        layout.addWidget(sec_config, alignment=Qt.AlignCenter)

        # 1) Mecanismo
        layout.addWidget(self._label("Mecanismo:"))
        self.mecanismo_combo = QComboBox()
        self.mecanismo_combo.addItems(["Mecenato", "FNC", "Recurso do Tesouro"])
        layout.addWidget(self.mecanismo_combo)

        # 2) Proponente
        layout.addWidget(self._label("Proponente:"))
        self.proponente_input = QLineEdit()
        self.proponente_input.setPlaceholderText("CNPJ somente dígitos")
        layout.addWidget(self.proponente_input)

        # 3) PRONAC
        layout.addWidget(self._label("PRONAC:"))
        self.pronac_input = QLineEdit()
        self.pronac_input.setPlaceholderText("Número do PRONAC")
        layout.addWidget(self.pronac_input)

        # 4) CSV de despesas
        layout.addWidget(self._label("CSV de despesas:"))
        csv_layout = QHBoxLayout()
        self.despesas_csv_input = QLineEdit()
        self.despesas_csv_input.setPlaceholderText("Selecione o CSV de despesas")
        self.despesas_csv_input.setReadOnly(True)
        csv_layout.addWidget(self.despesas_csv_input)
        btn_browse_csv = QPushButton("...")
        btn_browse_csv.setFixedWidth(36)
        btn_browse_csv.clicked.connect(self._selecionar_csv)
        csv_layout.addWidget(btn_browse_csv)
        layout.addLayout(csv_layout)

        # 5) Pasta de Comprovantes
        layout.addWidget(self._label("Pasta de Comprovantes:"))
        comprovantes_layout = QHBoxLayout()
        self.comprovantes_dir_input = QLineEdit()
        self.comprovantes_dir_input.setPlaceholderText(
            "Selecione a pasta de comprovantes"
        )
        self.comprovantes_dir_input.setReadOnly(True)
        comprovantes_layout.addWidget(self.comprovantes_dir_input)
        btn_browse_comprovantes = QPushButton("...")
        btn_browse_comprovantes.setFixedWidth(36)
        btn_browse_comprovantes.clicked.connect(self._selecionar_pasta_comprovantes)
        comprovantes_layout.addWidget(btn_browse_comprovantes)
        layout.addLayout(comprovantes_layout)

        # 5) Checkbox Dry Run
        self.dry_run_check = CustomCheckBox("Dry Run (insere mas não salva)")
        self.dry_run_check.setStyleSheet("font-family: monospace; margin-top: 8px")
        layout.addWidget(self.dry_run_check)

        # --- Seção: Credenciais ---
        sec_cred = QLabel("Credenciais")
        sec_cred.setStyleSheet(
            "font-weight: bold; font-family: monospace; margin-top: 24px;"
        )
        layout.addWidget(sec_cred, alignment=Qt.AlignCenter)

        # 1) CPF
        layout.addWidget(self._label("CPF:"))
        self.cpf_input = QLineEdit()
        self.cpf_input.setPlaceholderText("Somente dígitos")
        layout.addWidget(self.cpf_input)

        # 2) Senha
        layout.addWidget(self._label("Senha:"))
        self.senha_input = QLineEdit()
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.senha_input)

        # 3) Checkbox "Lembrar credenciais"
        self.lembrar_check = CustomCheckBox("Lembrar credenciais")
        self.lembrar_check.setStyleSheet("font-family: monospace; margin-top: 8px")
        self.lembrar_check.setChecked(self.config.has_saved_credentials())
        layout.addWidget(self.lembrar_check)

        # --- Botão RODAR ---
        self.btn_rodar = QPushButton("RODAR")
        self.btn_rodar.setStyleSheet(
            "font-family: monospace; font-size: 14px; font-weight: bold; "
            "padding: 8px; margin-top: 18px;"
        )
        self.btn_rodar.clicked.connect(self._rodar)
        layout.addWidget(self.btn_rodar)

        # --- Status ---
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-family: monospace; color: gray;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Pré-preencher com valores do ConfigManager (QSettings/keyring/.env/default)
        mecanismo = self.config.get_for_gui("mecanismo")
        idx = self.mecanismo_combo.findText(mecanismo)
        if idx >= 0:
            self.mecanismo_combo.setCurrentIndex(idx)

        self.proponente_input.setText(self.config.get_for_gui("proponente"))
        self.pronac_input.setText(self.config.get_for_gui("pronac"))
        self.despesas_csv_input.setText(self.config.get_for_gui("despesas_csv"))
        self.comprovantes_dir_input.setText(self.config.get_for_gui("comprovantes_dir"))
        self.cpf_input.setText(self.config.get_for_gui("cpf"))
        self.senha_input.setText(self.config.get_for_gui("senha"))

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-family: monospace;")
        return lbl

    def _selecionar_csv(self):
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "Selecionar CSV de despesas", "", "CSV (*.csv)"
        )
        if arquivo:
            self.despesas_csv_input.setText(arquivo)

    def _selecionar_pasta_comprovantes(self):
        pasta = QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta de Comprovantes"
        )
        if pasta:
            self.comprovantes_dir_input.setText(pasta)

    def _rodar(self):
        # Validação
        proponente = self.proponente_input.text().strip()
        pronac_text = self.pronac_input.text().strip()
        despesas_csv = self.despesas_csv_input.text().strip()
        comprovantes_dir = self.comprovantes_dir_input.text().strip()
        cpf = self.cpf_input.text().strip()
        senha = self.senha_input.text().strip()

        erros = []
        if not proponente:
            erros.append("Proponente é obrigatório.")
        if not pronac_text:
            erros.append("PRONAC é obrigatório.")
        else:
            try:
                int(pronac_text)
            except ValueError:
                erros.append("PRONAC deve ser numérico.")
        if not despesas_csv:
            erros.append("CSV de despesas é obrigatório.")
        if not comprovantes_dir:
            erros.append("Pasta de Comprovantes é obrigatória.")
        if not cpf:
            erros.append("CPF é obrigatório.")
        if not senha:
            erros.append("Senha é obrigatória.")

        if erros:
            QMessageBox.warning(self, "Campos inválidos", "\n".join(erros))
            return

        mecanismo = self.mecanismo_combo.currentText()
        pronac = int(pronac_text)

        projeto = Projeto(
            mecanismo=mecanismo,
            proponente=proponente,
            pronac=pronac,
        )

        # Salvar preferências no QSettings
        self.config.save_preferences(
            mecanismo, proponente, pronac_text, despesas_csv, comprovantes_dir
        )

        # Salvar credenciais no keyring se checkbox marcado
        if self.lembrar_check.isChecked():
            self.config.save_credentials(cpf, senha)

        headless = os.getenv("HEADLESS", "False").lower() == "true"
        slow_mo = int(os.getenv("SLOW_MO", "100"))

        logger.info("=" * 60)
        logger.info("Salic Bot - Automação de Prestação de Contas (GUI)")
        logger.info("=" * 60)
        if self.dry_run_check.isChecked():
            logger.info("Modo DRY RUN ativado — comprovantes NÃO serão salvos")
        logger.info(
            "Iniciando execução | mecanismo=%s | proponente=%s | pronac=%s",
            mecanismo,
            proponente,
            pronac,
        )

        bot = SalicBot(
            headless=headless,
            slow_mo=slow_mo,
            projeto=projeto,
            despesas_csv=despesas_csv,
            comprovantes_dir=comprovantes_dir,
            cpf=cpf,
            senha=senha,
            dry_run=self.dry_run_check.isChecked(),
        )

        self.btn_rodar.setEnabled(False)
        self.status_label.setText("Executando...")
        self.status_label.setStyleSheet("font-family: monospace; color: orange;")

        self.worker = BotWorker(bot)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, despesas_ok: int, total: int):
        self.btn_rodar.setEnabled(True)
        logs_path = str(Path(LOGS_DIR).resolve())

        if despesas_ok == total and total > 0:
            logger.info(
                "Execução concluída com sucesso! (%d/%d despesas incluídas)",
                despesas_ok,
                total,
            )
            self.status_label.setText(f"Concluído: {despesas_ok}/{total} despesas OK")
            self.status_label.setStyleSheet("font-family: monospace; color: green;")
            QMessageBox.information(
                self,
                "Concluído",
                f"Execução concluída com sucesso!\n"
                f"{despesas_ok}/{total} despesas incluídas.\n\n"
                f"Logs: {logs_path}",
            )
        elif despesas_ok > 0:
            logger.warning(
                "Execução concluída com erros! (%d/%d despesas incluídas)",
                despesas_ok,
                total,
            )
            self.status_label.setText(f"Parcial: {despesas_ok}/{total} despesas OK")
            self.status_label.setStyleSheet("font-family: monospace; color: orange;")
            QMessageBox.warning(
                self,
                "Concluído com erros",
                f"Execução concluída com erros.\n"
                f"{despesas_ok}/{total} despesas incluídas.\n\n"
                f"Logs: {logs_path}",
            )
        else:
            logger.error(
                "Execução falhou! (%d/%d despesas incluídas)", despesas_ok, total
            )
            self.status_label.setText(f"Falhou: {despesas_ok}/{total}")
            self.status_label.setStyleSheet("font-family: monospace; color: red;")
            QMessageBox.critical(
                self,
                "Falha",
                f"Execução falhou!\n"
                f"{despesas_ok}/{total} despesas incluídas.\n\n"
                f"Logs: {logs_path}",
            )

    def _on_error(self, msg: str):
        self.btn_rodar.setEnabled(True)
        logger.error("Erro durante execução: %s", msg)
        self.status_label.setText("Erro!")
        self.status_label.setStyleSheet("font-family: monospace; color: red;")
        QMessageBox.critical(self, "Erro", f"Erro durante a execução:\n{msg}")


RETRO_STYLE = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: "Courier New", Courier, monospace;
    font-size: 13px;
}
QLabel {
    color: #c0c0c0;
}
QLineEdit {
    background-color: #1a1a1a;
    color: #00ff00;
    border: 1px solid #555;
    padding: 4px;
    font-family: "Courier New", Courier, monospace;
}
QLineEdit:focus {
    border: 1px solid #00ff00;
}
QComboBox {
    background-color: #1a1a1a;
    color: #00ff00;
    border: 1px solid #555;
    padding: 4px;
    font-family: "Courier New", Courier, monospace;
}
QComboBox QAbstractItemView {
    background-color: #1a1a1a;
    color: #00ff00;
    selection-background-color: #005500;
}
QComboBox::drop-down {
    border: none;
}
QPushButton {
    background-color: #3a3a3a;
    color: #00ff00;
    border: 1px solid #555;
    padding: 6px 12px;
    font-family: "Courier New", Courier, monospace;
}
QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #00ff00;
}
QPushButton:pressed {
    background-color: #005500;
}
QPushButton:disabled {
    color: #555;
    border-color: #333;
}
"""


def iniciar_gui():
    """Inicializa e exibe a GUI do Salic Bot"""
    configurar_logging(logs_dir=LOGS_DIR)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    app = QApplication([])
    app.setStyleSheet(RETRO_STYLE)

    window = MainWindow()
    window.show()

    return app.exec()
