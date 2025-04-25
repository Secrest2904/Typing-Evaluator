import sys
import os
import random
import time
import traceback
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QSizePolicy,
                             QLabel, QStackedWidget, QTextEdit, QRadioButton, QCheckBox, 
                             QLineEdit)
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import Qt, QTimer
from backend import get_random_prompt, save_to_leaderboard
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from PyQt5.QtCore import QPropertyAnimation

def fade_in_widget(widget, duration=500):
    effect = QGraphicsOpacityEffect()
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(0)
    animation.setEndValue(1)
    animation.start()
    widget._fade_animation = animation


LEADERBOARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files", "leaderboard.txt")

def excepthook(type, value, tb):
    print("".join(traceback.format_exception(type, value, tb)))

sys.excepthook = excepthook

# Settings
settings = {
    "difficulty": "easy",
    "show_timer": True,
    "show_wpm": True
}

class TitleScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget

        self.setStyleSheet("""
            QWidget {
                background-color: #001f3f;
                color: white;
            }
            QPushButton {
                background-color: white;
                color: #001f3f;
                font-size: 18px;
                padding: 10px;
                margin: 5px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #cccccc;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 40, 50, 40)

        title_label = QLabel("🏆 Typing Trainer")
        title_label.setFont(QFont("Arial", 26, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.start_btn = QPushButton("🚀 Start Typing")
        self.settings_btn = QPushButton("⚙️ Settings")
        self.history_btn = QPushButton("📜 Leaderboard")

        layout.addWidget(self.start_btn)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.history_btn)

        self.setLayout(layout)

        self.start_btn.clicked.connect(self.go_to_typing)
        self.settings_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.history_btn.clicked.connect(lambda: [
            self.stacked_widget.widget(4).load_scores(),
            self.stacked_widget.setCurrentIndex(4)
        ])

    def go_to_typing(self):
        self.stacked_widget.widget(1).load_prompt()
        self.stacked_widget.setCurrentIndex(1)
    def showEvent(self, event):
        fade_in_widget(self)



class SettingsScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #001f3f;
                color: white;
            }
            QRadioButton, QCheckBox {
                font-size: 16px;
                padding: 5px;
            }
            QPushButton {
                background-color: white;
                color: #001f3f;
                font-size: 16px;
                padding: 6px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #cccccc;
            }
        """)
        self.stacked_widget = stacked_widget

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        header = QLabel("⚙️ Settings")
        header.setFont(QFont("Arial", 22, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        difficulty_label = QLabel("Select Difficulty:")
        difficulty_label.setFont(QFont("Arial", 16))
        layout.addWidget(difficulty_label)

        self.easy_radio = QRadioButton("Easy")
        self.hard_radio = QRadioButton("Hard")
        self.easy_radio.setChecked(True)

        layout.addWidget(self.easy_radio)
        layout.addWidget(self.hard_radio)

        self.timer_checkbox = QCheckBox("Show Timer")
        self.timer_checkbox.setChecked(True)
        self.wpm_checkbox = QCheckBox("Show WPM")
        self.wpm_checkbox.setChecked(True)

        layout.addWidget(self.timer_checkbox)
        layout.addWidget(self.wpm_checkbox)

        layout.addSpacing(20)

        back_btn = QPushButton("🔙 Back to Home")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(back_btn)

        self.setLayout(layout)

        # Connect signals
        self.easy_radio.toggled.connect(self.update_settings)
        self.hard_radio.toggled.connect(self.update_settings)
        self.timer_checkbox.toggled.connect(self.update_settings)
        self.wpm_checkbox.toggled.connect(self.update_settings)
    def showEvent(self, event):
        fade_in_widget(self)


    def update_settings(self):
        settings["difficulty"] = "easy" if self.easy_radio.isChecked() else "hard"
        settings["show_timer"] = self.timer_checkbox.isChecked()
        settings["show_wpm"] = self.wpm_checkbox.isChecked()

class TypingScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget

        self.setStyleSheet("""
            QWidget {
                background-color: #001f3f;
                color: white;
            }
            QLabel {
                font-size: 16px;
                padding: 4px;
            }
            QTextEdit {
                background-color: white;
                color: black;
                font-size: 16px;
                padding: 10px;
                border-radius: 8px;
            }
        """)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(40, 30, 40, 30)

        title_label = QLabel("🖊️ Typing Challenge")
        title_label.setFont(QFont("Arial", 22, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)

        self.wpm_label = QLabel("WPM: 0")
        self.wpm_label.setFont(QFont("Arial", 16))
        self.time_label = QLabel("Time: 0:00")
        self.time_label.setFont(QFont("Arial", 16))

        self.prompt_text = ""
        self.typed_text = ""
        self.error_indices = set()
        self.start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.prompt_display = QLabel()
        self.prompt_display.setWordWrap(True)
        self.prompt_display.setStyleSheet("color: White; font-size: 18px;")
        self.prompt_display.setFont(QFont("Arial", 18, QFont.Bold))
        self.prompt_display.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.textbox = QTextEdit()
        self.textbox.textChanged.connect(self.on_text_changed)

        self.layout.addWidget(self.prompt_display)
        self.layout.addWidget(self.wpm_label)
        self.layout.addWidget(self.time_label)
        self.layout.addWidget(self.textbox)

        self.setLayout(self.layout)

    def load_prompt(self):
        self.prompt_text = get_random_prompt(settings["difficulty"])
        self.prompt_display.setText(self.prompt_text)
        self.textbox.clear()
        self.start_time = time.time()
        self.error_indices = set()
        self.timer.start(1000)

    def update_timer(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.time_label.setText(f"Time: {minutes}:{seconds:02d}")

    def on_text_changed(self):
        if not self.start_time:
            return
        typed = self.textbox.toPlainText()

        if len(typed) > len(self.prompt_text):
            self.textbox.blockSignals(True)
            self.textbox.setPlainText(typed[:len(self.prompt_text)])
            self.textbox.blockSignals(False)
            return

        self.typed_text = typed

        for i in range(len(typed)):
            if typed[i] != self.prompt_text[i] and i not in self.error_indices:
                self.error_indices.add(i)

        elapsed_minutes = max((time.time() - self.start_time) / 60, 0.01)
        wpm = int((len(typed) / 5) / elapsed_minutes)
        self.wpm_label.setText(f"WPM: {wpm}")

        self.update_highlight()

        if len(typed) == len(self.prompt_text):
            self.timer.stop()
            duration = int(time.time() - self.start_time)
            results_screen = self.stacked_widget.widget(3)
            results_screen.set_stats(wpm, len(self.error_indices), duration)
            self.stacked_widget.setCurrentIndex(3)

    def update_highlight(self):
        self.textbox.blockSignals(True)
        cursor = self.textbox.textCursor()
        cursor.beginEditBlock()

        text = self.textbox.toPlainText()
        fmt_correct = QTextCharFormat()
        fmt_correct.setForeground(QColor("black"))

        fmt_wrong = QTextCharFormat()
        fmt_wrong.setForeground(QColor("red"))

        cursor.setPosition(0)
        for i in range(len(text)):
            cursor.setPosition(i)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            fmt = fmt_wrong if i in self.error_indices else fmt_correct
            cursor.mergeCharFormat(fmt)

        cursor.endEditBlock()
        self.textbox.blockSignals(False)

class ResultsScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget

        self.setStyleSheet("""
            QWidget {
                background-color: #001f3f;
                color: white;
            }
            QLabel {
                font-size: 16px;
            }
            QLineEdit {
                background-color: white;
                color: black;
                font-size: 16px;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton {
                background-color: white;
                color: #001f3f;
                font-size: 16px;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #cccccc;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        header = QLabel("🏁 Results")
        header.setFont(QFont("Arial", 22, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.stats_label = QLabel("Stats will show here.")
        self.stats_label.setFont(QFont("Arial", 16))
        self.stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name...")
        layout.addWidget(self.name_input)

        submit_btn = QPushButton("📋 Submit to Leaderboard")
        submit_btn.clicked.connect(self.submit_score)
        layout.addWidget(submit_btn)

        back_btn = QPushButton("🔙 Back to Start")
        back_btn.clicked.connect(self.go_home)
        layout.addWidget(back_btn)

        self.setLayout(layout)

        self.wpm = 0
        self.mistakes = 0
        self.duration = 0
    def showEvent(self, event):
        fade_in_widget(self)

    def set_stats(self, wpm, mistakes, duration):
        self.wpm = wpm
        self.mistakes = mistakes
        self.duration = duration
        self.stats_label.setText(
            f"🎯 Finished!\n\n🕒 Time: {duration} sec\n⌨️ WPM: {wpm}\n❌ Mistakes: {mistakes}"
        )

    def submit_score(self):
        name = self.name_input.text().strip() or "Anonymous"
        save_to_leaderboard(name, self.wpm, self.mistakes, settings["difficulty"])
        self.name_input.clear()
        self.go_home()

    def go_home(self):
        self.stacked_widget.widget(4).load_scores()
        self.stacked_widget.setCurrentIndex(0)

class LeaderboardScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget

        self.setStyleSheet("""
            QWidget {
                background-color: #001f3f;
                color: white;
            }
            QLabel {
                font-size: 16px;
            }
            QPushButton {
                background-color: white;
                color: #001f3f;
                font-size: 16px;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #cccccc;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        header = QLabel("🏅 Leaderboard")
        header.setFont(QFont("Arial", 22, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.board = QLabel("Scores will load here.")
        self.board.setFont(QFont("Courier New", 14))  # Monospaced font for scores
        self.board.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.board.setWordWrap(True)
        layout.addWidget(self.board)

        clear_btn = QPushButton("🧹 Clear Leaderboard")
        clear_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        clear_btn.clicked.connect(self.clear_leaderboard)
        layout.addWidget(clear_btn)

        back_btn = QPushButton("🔙 Back to Menu")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def load_scores(self):
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]
            easy_scores = [line for line in lines if line.lower().startswith("easy")]
            hard_scores = [line for line in lines if line.lower().startswith("hard")]

            content = ""
            if easy_scores:
                content += "📗 Easy Mode:\n" + "\n".join(easy_scores) + "\n\n"
            if hard_scores:
                content += "📘 Hard Mode:\n" + "\n".join(hard_scores)
            self.board.setText(content)
        else:
            self.board.setText("Leaderboard is empty.")
    def showEvent(self, event):
        fade_in_widget(self)

    def clear_leaderboard(self):
        open(LEADERBOARD_FILE, 'w').close()
        self.board.setText("Leaderboard cleared.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    stacked_widget = QStackedWidget()

    title_screen = TitleScreen(stacked_widget)
    typing_screen = TypingScreen(stacked_widget)
    settings_screen = SettingsScreen(stacked_widget)
    results_screen = ResultsScreen(stacked_widget)
    leaderboard_screen = LeaderboardScreen(stacked_widget)

    stacked_widget.addWidget(title_screen)       # 0
    stacked_widget.addWidget(typing_screen)      # 1
    stacked_widget.addWidget(settings_screen)    # 2
    stacked_widget.addWidget(results_screen)     # 3
    stacked_widget.addWidget(leaderboard_screen) # 4

    stacked_widget.setFixedSize(600, 400)
    stacked_widget.show()
    sys.exit(app.exec_())