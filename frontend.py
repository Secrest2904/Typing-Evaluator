import sys
import os
import random
import time
import traceback
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QSizePolicy,
                             QLabel, QStackedWidget, QTextEdit, QRadioButton, QCheckBox, 
                             QLineEdit)
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
from PyQt5.QtCore import Qt, QTimer
from backend import get_random_prompt, save_to_leaderboard

LEADERBOARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files", "leaderboard.txt")

# Exception hook for clearer error reporting
def excepthook(type, value, tb):
    print("".join(traceback.format_exception(type, value, tb)))

sys.excepthook = excepthook

# File paths
EASY_PATH = "Easy.txt"
HARD_PATH = "Hard.txt"
LEADERBOARD_PATH = "leaderboard.txt"

# Settings
settings = {
    "difficulty": "easy",
    "show_timer": True,
    "show_wpm": True
}

class TitleScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget  # Store the stacked widget as an instance attribute
        self.setStyleSheet("background-color: #000080; color: white;")

        layout = QVBoxLayout()

        self.history_btn = QPushButton("History")
        self.start_btn = QPushButton("Start Writing")
        self.settings_btn = QPushButton("Settings")

        for btn in (self.history_btn, self.start_btn, self.settings_btn):
            btn.setStyleSheet("background-color: white; color: #000080; font-size: 18px;")
            layout.addWidget(btn)

        self.setLayout(layout)
        self.start_btn.clicked.connect(self.go_to_typing)
        self.settings_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.history_btn.clicked.connect(lambda: [self.stacked_widget.widget(4).load_scores(), self.stacked_widget.setCurrentIndex(4)])

    def go_to_typing(self):
        self.stacked_widget.widget(1).load_prompt()
        self.stacked_widget.setCurrentIndex(1)


class SettingsScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.setStyleSheet("background-color: #000080; color: white;")
        layout = QVBoxLayout()

        self.easy_radio = QRadioButton("Easy")
        self.hard_radio = QRadioButton("Hard")
        self.easy_radio.setChecked(True)

        self.timer_checkbox = QCheckBox("Show Timer")
        self.timer_checkbox.setChecked(True)
        self.wpm_checkbox = QCheckBox("Show WPM")
        self.wpm_checkbox.setChecked(True)

        back_btn = QPushButton("Back")
        back_btn.setStyleSheet("background-color: white; color: #000080;")
        back_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))

        difficulty_label = QLabel("Difficulty:")
        difficulty_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(difficulty_label)

        layout.addWidget(self.easy_radio)
        layout.addWidget(self.hard_radio)
        layout.addWidget(self.timer_checkbox)
        layout.addWidget(self.wpm_checkbox)
        layout.addWidget(back_btn)
        self.setLayout(layout)

        self.easy_radio.toggled.connect(self.update_settings)
        self.hard_radio.toggled.connect(self.update_settings)
        self.timer_checkbox.toggled.connect(self.update_settings)
        self.wpm_checkbox.toggled.connect(self.update_settings)

    def update_settings(self):
        settings["difficulty"] = "easy" if self.easy_radio.isChecked() else "hard"
        settings["show_timer"] = self.timer_checkbox.isChecked()
        settings["show_wpm"] = self.wpm_checkbox.isChecked()

class TypingScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.setStyleSheet("background-color: #000080; color: white;")
        self.stacked_widget = stacked_widget
        self.layout = QVBoxLayout()

        self.wpm_label = QLabel("WPM: 0")
        self.time_label = QLabel("Time: 0:00")
        self.prompt_text = ""
        self.typed_text = ""
        self.error_indices = set()
        self.start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.prompt_display = QLabel()
        self.prompt_display.setWordWrap(True)
        self.prompt_display.setStyleSheet("color: lightgrey; font-size: 16px;")

        self.textbox = QTextEdit()
        self.textbox.setStyleSheet("background-color: white; color: black; font-size: 16px;")
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

        # Stop typing if it exceeds prompt
        if len(typed) > len(self.prompt_text):
            self.textbox.blockSignals(True)
            self.textbox.setPlainText(typed[:len(self.prompt_text)])
            self.textbox.blockSignals(False)
            return

        self.typed_text = typed

        # Record mistake positions once
        for i in range(len(typed)):
            if typed[i] != self.prompt_text[i] and i not in self.error_indices:
                self.error_indices.add(i)

        # WPM calc (5 chars = 1 word)
        elapsed_minutes = max((time.time() - self.start_time) / 60, 0.01)
        wpm = int((len(typed) / 5) / elapsed_minutes)
        self.wpm_label.setText(f"WPM: {wpm}")

        # Highlight
        self.update_highlight()

        # Check finish
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
        self.setStyleSheet("background-color: #000080; color: white;")
        self.stacked_widget = stacked_widget

        layout = QVBoxLayout()

        self.stats_label = QLabel("Stats will show here.")
        layout.addWidget(self.stats_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        layout.addWidget(self.name_input)

        submit_btn = QPushButton("Submit to Leaderboard")
        submit_btn.setStyleSheet("background-color: white; color: #000080;")
        submit_btn.clicked.connect(self.submit_score)
        layout.addWidget(submit_btn)

        back_btn = QPushButton("Back to Start")
        back_btn.setStyleSheet("background-color: white; color: #000080;")
        back_btn.clicked.connect(self.go_home)
        layout.addWidget(back_btn)

        self.setLayout(layout)
        self.wpm = 0
        self.mistakes = 0
        self.duration = 0

    def set_stats(self, wpm, mistakes, duration):
        self.wpm = wpm
        self.mistakes = mistakes
        self.duration = duration
        self.stats_label.setText(
            f"Finished!\nWPM: {wpm}\nMistakes: {mistakes}\nTime: {duration} seconds"
        )

    def submit_score(self):
        name = self.name_input.text().strip() or "Anonymous"
        from backend import save_to_leaderboard
        save_to_leaderboard(name, self.wpm, self.mistakes, settings["difficulty"])
        self.name_input.clear()
        self.go_home()

    def go_home(self):
        self.stacked_widget.widget(4).load_scores()
        self.stacked_widget.setCurrentIndex(0)

class LeaderboardScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.setStyleSheet("background-color: #000080; color: white;")
        self.stacked_widget = stacked_widget
        layout = QVBoxLayout()
        self.board = QLabel("Leaderboard:")
        self.board.setStyleSheet("font-size: 16px;")
        self.board.setWordWrap(True)

        layout.addWidget(self.board)

        clear_btn = QPushButton("Clear Leaderboard")
        clear_btn.setStyleSheet("background-color: red; color: white;")
        clear_btn.clicked.connect(self.clear_leaderboard)
        layout.addWidget(clear_btn)

        back_btn = QPushButton("Back")
        back_btn.setStyleSheet("background-color: white; color: #000080;")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def load_scores(self):
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]
            easy_scores = [line for line in lines if line.lower().startswith("easy")]
            hard_scores = [line for line in lines if line.lower().startswith("hard")]

            content = "Leaderboard:\n\n"
            if easy_scores:
                content += "📗 Easy:\n" + "\n".join(easy_scores) + "\n\n"
            if hard_scores:
                content += "📘 Hard:\n" + "\n".join(hard_scores)
            self.board.setText(content)
        else:
            self.board.setText("Leaderboard is empty.")

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