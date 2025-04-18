import sys
import os
import random
import time
import traceback
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QSizePolicy,
                             QLabel, QStackedWidget, QTextEdit, QRadioButton, QCheckBox)
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
from PyQt5.QtCore import Qt, QTimer
from backend import get_random_prompt

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
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.prompt = self.backend.get_prompt()
        self.current_index = 0

        self.text_display = QLabel(self.prompt)
        self.input_display = QLabel("")  # Show typed characters

        layout = QVBoxLayout()
        layout.addWidget(self.text_display)
        layout.addWidget(self.input_display)
        self.setLayout(layout)

    def keyPressEvent(self, event):
        if event.text():
            typed_char = event.text()
            if self.prompt[self.current_index] == typed_char:
                self.current_index += 1
                self.input_display.setText(self.prompt[:self.current_index])

                if self.current_index == len(self.prompt):
                    print("Typing completed!")
                    # Trigger results screen here
            else:
                print("Wrong character!")


    def load_prompt(self):
        self.prompt_text = get_random_prompt(settings["difficulty"])
        print(f"Loaded prompt: {self.prompt_text}")  # Debug: Check what prompt is loaded
        self.prompt_display.setText(self.prompt_text)
        self.textbox.clear()
        self.start_time = time.time()
        self.mistakes = 0
        self.timer.start(1000)

    def start_typing(self):
        file_path = EASY_PATH if settings["difficulty"] == "easy" else HARD_PATH
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                prompts = [line.strip() for line in f.readlines() if line.strip()]
            self.prompt_text = random.choice(prompts)
            self.prompt_display.setText(self.prompt_text)
            self.textbox.clear()
            self.start_time = time.time()
            self.mistakes = 0
            self.timer.start(1000)
        else:
            self.prompt_display.setText("No prompts found.")

    def update_timer(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.time_label.setText(f"Time: {minutes}:{seconds:02d}")

    def on_text_changed(self):
        typed = self.textbox.toPlainText()
        self.typed_text = typed

        # Count mistakes
        self.mistakes = sum(1 for i in range(min(len(typed), len(self.prompt_text))) if typed[i] != self.prompt_text[i])

        # Calculate WPM
        elapsed_minutes = (time.time() - self.start_time) / 60 if self.start_time else 1
        words_typed = len(typed.split())
        wpm = int(words_typed / elapsed_minutes)
        self.wpm_label.setText(f"WPM: {wpm}")

        # Update display color feedback (optional: style directly here)
        self.update_highlight()
        if typed == self.prompt_text:
            self.timer.stop()
            duration = int(time.time() - self.start_time)
            wpm = int(len(typed.split()) / (duration / 60))
            self.stacked_widget.widget(3).stats_label.setText(
                f"Finished!\nWPM: {wpm}\nMistakes: {self.mistakes}\nTime: {duration} seconds"
            )
            self.stacked_widget.setCurrentIndex(3)


    def update_highlight(self):
        cursor = self.textbox.textCursor()
        text = self.textbox.toPlainText()

        self.textbox.blockSignals(True)

        self.textbox.selectAll()
        default_fmt = QTextCharFormat()
        default_fmt.setForeground(QColor("black"))
        self.textbox.textCursor().mergeCharFormat(default_fmt)

        cursor.setPosition(0)
        for i in range(min(len(text), len(self.prompt_text))):
            fmt = QTextCharFormat()
            if text[i] == self.prompt_text[i]:
                fmt.setForeground(QColor("black"))
            else:
                fmt.setForeground(QColor("red"))
            cursor.setPosition(i)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            cursor.mergeCharFormat(fmt)

        self.textbox.blockSignals(False)

class ResultsScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.setStyleSheet("background-color: #000080; color: white;")
        layout = QVBoxLayout()
        self.stats_label = QLabel("Stats will show here.")
        layout.addWidget(self.stats_label)

        back_btn = QPushButton("Back to Start")
        back_btn.setStyleSheet("background-color: white; color: #000080;")
        back_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
        layout.addWidget(back_btn)

        self.setLayout(layout)

class LeaderboardScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.setStyleSheet("background-color: #000080; color: white;")
        layout = QVBoxLayout()
        self.board = QLabel("Leaderboard:")
        layout.addWidget(self.board)

        back_btn = QPushButton("Back")
        back_btn.setStyleSheet("background-color: white; color: #000080;")
        back_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def load_scores(self):
        if os.path.exists(LEADERBOARD_PATH):
            with open(LEADERBOARD_PATH, 'r') as f:
                content = f.read()
            self.board.setText("Leaderboard:\n" + content)
        else:
            self.board.setText("Leaderboard is empty.")

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