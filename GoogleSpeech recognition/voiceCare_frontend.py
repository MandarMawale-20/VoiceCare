from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTabWidget, QScrollArea, QFrame,
                             QDialog, QLineEdit, QTextEdit, QGridLayout, QMessageBox)
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer, QDateTime, QDate
import sys
import threading
import datetime
import sqlite3

from VoiceCare_google import VoiceCareAssistant


class ModifiedVoiceCareAssistant(VoiceCareAssistant):
    """Modified assistant that works without Tkinter GUI"""
    
    def __init__(self):
        # Initialize components without GUI
        super().__init__()
        import queue
        self.tts_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        # Initialize components - removed Vosk initialization
        import speech_recognition as sr
        import pyttsx3
        from apscheduler.schedulers.background import BackgroundScheduler
        import pygame
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Initialize pygame for sound effects
        pygame.mixer.init()
        
        # Database setup
        self.setup_database()
        
        # Language patterns
        self.setup_language_patterns()
        
        # Configure TTS
        self.setup_tts()
        
        # Calibrate microphone
        self.calibrate_microphone()
        
        # Load existing reminders
        self.load_existing_reminders()
    
    def setup_gui(self):
        """Skip GUI setup since we're using PyQt5"""
        pass
    def queue_gui_update(self, func):
        # Do nothing, or optionally call func() directly if safe
        pass

    def update_reminders_display(self):
        pass

    def process_gui_queue(self):
        pass

    def on_closing(self):
        # Only clean up non-GUI resources
        try:
            self.tts_queue.put((None, None))
            if self.scheduler.running:
                self.scheduler.shutdown()
            if hasattr(self, 'conn'):
                self.conn.close()
            # pygame.mixer.quit()
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def cleanup(self):
        # Only clean up non-GUI resources
        try:
            if hasattr(self, 'scheduler') and self.scheduler.running:
                self.scheduler.shutdown()
            if hasattr(self, 'conn'):
                self.conn.close()
            # pygame.mixer.quit()
        except Exception as e:
            print(f"Cleanup error: {e}")


class ReminderCard(QFrame):
    def __init__(self, task, time_str, reminder_id, assistant, is_recurring=False, days_left=0):
        super().__init__()
        self.reminder_id = reminder_id
        self.assistant = assistant
        
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 10px;
                border: 1px solid #dcdcdc;
            }
        """)

        layout = QHBoxLayout()
        self.setLayout(layout)

        left = QVBoxLayout()
        task_label = QLabel(task)
        task_label.setFont(QFont("Arial", 14, QFont.Bold))
        time_label = QLabel(time_str)
        time_label.setFont(QFont("Arial", 12))
        time_label.setStyleSheet("color: #888;")

        left.addWidget(task_label)
        left.addWidget(time_label)

        if is_recurring and days_left > 0:
            repeat_label = QLabel(f"Repeats {days_left} more days")
            repeat_label.setStyleSheet("color: #d35400; font-size: 12px")
            left.addWidget(repeat_label)

        layout.addLayout(left)
        layout.addStretch()

        done_btn = QPushButton("✓")
        done_btn.setFixedSize(32, 32)
        done_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; border-radius: 16px;")
        done_btn.clicked.connect(self.mark_done)
        layout.addWidget(done_btn)

    def mark_done(self):
        # Mark as inactive in database
        try:
            cursor = self.assistant.conn.cursor()
            cursor.execute('UPDATE reminders SET active = 0 WHERE id = ?', (self.reminder_id,))
            self.assistant.conn.commit()
            
            # Remove scheduled job
            try:
                self.assistant.scheduler.remove_job(f"reminder_{self.reminder_id}")
            except:
                pass
                
        except Exception as e:
            print(f"Error marking reminder as done: {e}")
        
        self.setStyleSheet("background-color: #ecf0f1; border-radius: 10px; padding: 10px;")
        for child in self.findChildren(QPushButton):
            child.setEnabled(False)


class AddReminderDialog(QDialog):
    def __init__(self, assistant, parent=None):
        super().__init__(parent)
        self.assistant = assistant
        self.parent_window = parent
        self.setWindowTitle("Add Reminder")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Task (e.g., take medicine)")

        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("Time (e.g., 6:00 PM or 18:00)")

        self.days_input = QLineEdit()
        self.days_input.setPlaceholderText("Repeat for how many days? (optional)")

        self.add_btn = QPushButton("Add Reminder")
        self.add_btn.setStyleSheet("background-color: #3498db; color: white; padding: 8px; font-weight: bold; border-radius: 5px;")
        self.add_btn.clicked.connect(self.add_reminder)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("background-color: #95a5a6; color: white; padding: 8px; font-weight: bold; border-radius: 5px;")
        self.cancel_btn.clicked.connect(self.reject)

        layout.addWidget(QLabel("Task:"))
        layout.addWidget(self.task_input)
        layout.addWidget(QLabel("Time:"))
        layout.addWidget(self.time_input)
        layout.addWidget(QLabel("Recurring Days (optional):"))
        layout.addWidget(self.days_input)
        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def add_reminder(self):
        task = self.task_input.text().strip()
        time_str = self.time_input.text().strip()
        days = self.days_input.text().strip()

        if not task or not time_str:
            QMessageBox.warning(self, "Missing Info", "Please enter both task and time")
            return

        # Create the voice command
        command = f"remind me to {task} at {time_str}"
        if days and days.isdigit():
            command += f" for {days} days"

        # Process the command through the assistant
        try:
            self.assistant.process_voice_command(command)
            QMessageBox.information(self, "Success", "Reminder added successfully!")
            
            # Refresh the parent window's display
            if self.parent_window:
                self.parent_window.refresh_reminders()
                
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add reminder: {str(e)}")


class VoiceCareUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize the modified assistant without GUI
        self.assistant = ModifiedVoiceCareAssistant()
        
        self.setWindowTitle("VoiceCare Assistant")
        self.resize(920, 620)
        self.setStyleSheet("background-color: #f0f6fa;")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # Header
        nav = QHBoxLayout()
        app_label = QLabel("👋 Welcome to VoiceCare")
        app_label.setFont(QFont("Arial", 20, QFont.Bold))
        nav.addWidget(app_label)
        nav.addStretch()

        # Status label
        self.status_label = QLabel("Ready to help!")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("color: #27ae60; padding: 5px;")
        nav.addWidget(self.status_label)

        self.mic_btn = QPushButton("🎤 SPEAK")
        self.mic_btn.setFixedSize(120, 48)
        self.mic_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px; 
                background-color: #3498db; 
                color: white; 
                border-radius: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.mic_btn.clicked.connect(self.handle_mic_click)
        nav.addWidget(self.mic_btn)

        main_layout.addLayout(nav)

        # Tabs for different views
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: none; 
                background-color: white;
                border-radius: 10px;
            }
            QTabBar::tab { 
                background: #dff1fd; 
                padding: 12px 20px; 
                border-radius: 10px; 
                margin: 2px; 
                font-weight: bold; 
            }
            QTabBar::tab:selected { 
                background: #3498db; 
                color: white; 
            }
        """)

        # Create tabs
        self.today_tab = self.create_reminders_tab()
        self.tomorrow_tab = self.create_reminders_tab()
        self.all_tab = self.create_reminders_tab()
        
        self.tabs.addTab(self.today_tab, "Today")
        self.tabs.addTab(self.tomorrow_tab, "Tomorrow")
        self.tabs.addTab(self.all_tab, "All Reminders")

        main_layout.addWidget(self.tabs)

        # Voice instruction label
        self.voice_label = QLabel("Click 'SPEAK' and say: 'Remind me to take medicine at 6 PM' or use the + button")
        self.voice_label.setStyleSheet("""
            color: #555; 
            font-size: 14px; 
            padding: 12px; 
            border: 1px solid #ccc; 
            border-radius: 8px; 
            background-color: #ffffff;
        """)
        main_layout.addWidget(self.voice_label)

        # Floating add button
        self.add_btn = QPushButton("+")
        self.add_btn.setParent(self)
        self.add_btn.setFixedSize(56, 56)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; 
                color: white; 
                font-size: 28px; 
                border-radius: 28px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        self.add_btn.clicked.connect(self.show_add_dialog)

        # Timer to refresh reminders periodically
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_reminders)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

        # Initial load of reminders
        self.refresh_reminders()

    def create_reminders_tab(self):
        """Create a tab widget for displaying reminders"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        inner = QWidget()
        inner_layout = QVBoxLayout()
        inner_layout.setAlignment(Qt.AlignTop)
        inner.setLayout(inner_layout)
        
        scroll.setWidget(inner)
        layout.addWidget(scroll)
        tab.setLayout(layout)
        
        return tab

    def get_reminders_for_date(self, date_str):
        """Get reminders for a specific date"""
        try:
            cursor = self.assistant.conn.cursor()
            cursor.execute('''
                SELECT id, task, time, recurring, remaining_days 
                FROM reminders 
                WHERE date = ? AND active = 1 
                ORDER BY time
            ''', (date_str,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching reminders: {e}")
            return []

    def refresh_reminders(self):
        """Refresh all reminder displays"""
        try:
            today = datetime.date.today().strftime('%Y-%m-%d')
            tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Update each tab
            self.update_tab_reminders(self.today_tab, today, "No reminders for today")
            self.update_tab_reminders(self.tomorrow_tab, tomorrow, "No reminders for tomorrow")
            self.update_all_reminders_tab()
            
        except Exception as e:
            print(f"Error refreshing reminders: {e}")

    def update_tab_reminders(self, tab, date_str, empty_message):
        """Update reminders for a specific tab"""
        try:
            reminders = self.get_reminders_for_date(date_str)
            
            # Get the scroll area and inner widget
            scroll_area = tab.findChild(QScrollArea)
            inner_widget = scroll_area.widget()
            layout = inner_widget.layout()
            
            # Clear existing widgets
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            if not reminders:
                # Show empty message
                empty_label = QLabel(empty_message)
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setStyleSheet("color: #888; font-size: 16px; padding: 20px;")
                layout.addWidget(empty_label)
            else:
                # Add reminder cards
                for reminder_id, task, time_str, is_recurring, days_left in reminders:
                    time_obj = datetime.datetime.strptime(time_str, '%H:%M').time()
                    formatted_time = time_obj.strftime('%I:%M %p')
                    
                    card = ReminderCard(
                        task=task,
                        time_str=formatted_time,
                        reminder_id=reminder_id,
                        assistant=self.assistant,
                        is_recurring=bool(is_recurring),
                        days_left=days_left or 0
                    )
                    layout.addWidget(card)
            
            layout.addStretch()
            
        except Exception as e:
            print(f"Error updating tab reminders: {e}")

    def update_all_reminders_tab(self):
        """Update the 'All Reminders' tab"""
        try:
            cursor = self.assistant.conn.cursor()
            cursor.execute('''
                SELECT id, task, time, date, recurring, remaining_days 
                FROM reminders 
                WHERE active = 1 
                ORDER BY date, time
            ''')
            all_reminders = cursor.fetchall()
            
            # Get the scroll area and inner widget
            scroll_area = self.all_tab.findChild(QScrollArea)
            inner_widget = scroll_area.widget()
            layout = inner_widget.layout()
            
            # Clear existing widgets
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            if not all_reminders:
                empty_label = QLabel("No active reminders")
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setStyleSheet("color: #888; font-size: 16px; padding: 20px;")
                layout.addWidget(empty_label)
            else:
                current_date = None
                for reminder_id, task, time_str, date_str, is_recurring, days_left in all_reminders:
                    # Add date separator if needed
                    if date_str != current_date:
                        current_date = date_str
                        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                        
                        if date_obj == datetime.date.today():
                            date_label_text = "Today"
                        elif date_obj == datetime.date.today() + datetime.timedelta(days=1):
                            date_label_text = "Tomorrow"
                        else:
                            date_label_text = date_obj.strftime('%B %d, %Y')
                        
                        date_label = QLabel(date_label_text)
                        date_label.setFont(QFont("Arial", 16, QFont.Bold))
                        date_label.setStyleSheet("color: #2c3e50; padding: 10px 0 5px 0;")
                        layout.addWidget(date_label)
                    
                    # Add reminder card
                    time_obj = datetime.datetime.strptime(time_str, '%H:%M').time()
                    formatted_time = time_obj.strftime('%I:%M %p')
                    
                    card = ReminderCard(
                        task=task,
                        time_str=formatted_time,
                        reminder_id=reminder_id,
                        assistant=self.assistant,
                        is_recurring=bool(is_recurring),
                        days_left=days_left or 0
                    )
                    layout.addWidget(card)
            
            layout.addStretch()
            
        except Exception as e:
            print(f"Error updating all reminders tab: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_floating_button()

    def adjust_floating_button(self):
        self.add_btn.move(self.width() - 80, self.height() - 120)

    def show_add_dialog(self):
        dialog = AddReminderDialog(self.assistant, self)
        dialog.exec_()

    def handle_mic_click(self):
        self.voice_label.setText("Listening... Please speak now")
        self.status_label.setText("Listening...")
        self.status_label.setStyleSheet("color: #e74c3c; padding: 5px;")
        self.mic_btn.setText("🎤 LISTENING...")
        self.mic_btn.setEnabled(False)
        
        def listen_thread():
            try:
                # Use the correct method name from the original assistant
                result_text = self.assistant.listen_with_google()
                
                if result_text:
                    # Process the command
                    self.assistant.process_voice_command(result_text)
                    
                    # Update UI
                    self.voice_label.setText(f"You said: '{result_text}' - Processing...")
                    self.status_label.setText("Command processed!")
                    self.status_label.setStyleSheet("color: #27ae60; padding: 5px;")
                    
                    # Refresh reminders after a short delay
                    QTimer.singleShot(1000, self.refresh_reminders)
                else:
                    self.voice_label.setText("Could not understand. Please try again.")
                    self.status_label.setText("Not understood")
                    self.status_label.setStyleSheet("color: #e74c3c; padding: 5px;")
                    
            except Exception as e:
                self.voice_label.setText(f"Error: {str(e)}")
                self.status_label.setText("Error occurred")
                self.status_label.setStyleSheet("color: #e74c3c; padding: 5px;")
            finally:
                self.mic_btn.setText("🎤 SPEAK")
                self.mic_btn.setEnabled(True)
        
        threading.Thread(target=listen_thread, daemon=True).start()

    def closeEvent(self, event):
        """Handle application closing"""
        try:
            if hasattr(self.assistant, 'on_closing'):
                self.assistant.on_closing()
        except Exception as e:
            print(f"Error during shutdown: {e}")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoiceCareUI()
    window.show()
    sys.exit(app.exec_())