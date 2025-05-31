import sqlite3
import speech_recognition as sr
import pyttsx3
import tkinter as tk
from tkinter import ttk, font
import threading
import datetime
import re
import json
from apscheduler.schedulers.background import BackgroundScheduler
import time
import os
from langdetect import detect
import pygame
import vosk
import pyaudio
import queue
import logging

logger = logging.getLogger(__name__)

class VoiceCareAssistant:
    def __init__(self):
        def __init__(self):
            self.tts_queue = queue.Queue()
            self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self.tts_thread.start()
                # Initialize components
        # Get the directory where this script is located
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Build model paths relative to this file
        model_en_path = os.path.join(base_dir, "vosk", "vosk-model-small-en-us-0.15")
        model_hi_path = os.path.join(base_dir, "vosk", "vosk-model-small-hi-0.22")
        
        # Check if models exist before loading
        if os.path.exists(model_en_path):
            self.vosk_model_en = vosk.Model(model_en_path)
            self.vosk_rec_en = vosk.KaldiRecognizer(self.vosk_model_en, 16000)
        else:
            self.vosk_model_en = None
            self.vosk_rec_en = None
            
        if os.path.exists(model_hi_path):
            self.vosk_model_hi = vosk.Model(model_hi_path)
            self.vosk_rec_hi = vosk.KaldiRecognizer(self.vosk_model_hi, 16000)
        else:
            self.vosk_model_hi = None
            self.vosk_rec_hi = None
            
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Initialize pygame for sound effects
        pygame.mixer.init()
        
        # Create a queue for thread-safe GUI updates
        self.gui_queue = queue.Queue()
        
        # Database setup
        self.setup_database()
        
        # Language patterns
        self.setup_language_patterns()
        
        # Configure TTS
        self.setup_tts()
        
        # GUI setup
        self.setup_gui()
        
        # Calibrate microphone
        self.calibrate_microphone()
        
        # Load existing reminders
        self.load_existing_reminders()
    
    def setup_database(self):
        """Initialize SQLite database for reminders"""
        self.conn = sqlite3.connect('voicecare_reminders.db', check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                time TEXT NOT NULL,
                date TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recurring INTEGER DEFAULT 0,
                remaining_days INTEGER DEFAULT 0,
                original_id INTEGER DEFAULT NULL
            )
        ''')
        self.conn.commit()
    
    def setup_language_patterns(self):
        """Setup multilingual patterns for intent recognition"""
        self.patterns = {
            'en': {
                'set_reminder': [
                    r'remind me to (.+) at (\d{1,2}):?(\d{0,2})?\s*(am|pm|a\.m\.|p\.m\.|o\'clock)?(\s+for\s+(\d+)\s+days)?',
                    r'set reminder for (.+) at (\d{1,2}):?(\d{0,2})?\s*(am|pm|a\.m\.|p\.m\.|o\'clock)?(\s+for\s+(\d+)\s+days)?',
                    r'remember (.+) at (\d{1,2}):?(\d{0,2})?\s*(am|pm|a\.m\.|p\.m\.|o\'clock)?(\s+for\s+(\d+)\s+days)?'
                ],
                'query_schedule': [
                    r'what do i have today',
                    r'my reminders',
                    r'what are my tasks',
                    r'schedule for today'
                ],
                'responses': {
                    'reminder_set': "Got it. I will remind you at {time} to {task}.",
                    'reminder_set_recurring': "Got it. I will remind you at {time} to {task} for the next {days} days.",
                    'no_reminders': "You have no reminders for today.",
                    'reminders_list': "You have {count} reminders today: {reminders}",
                    'reminder_triggered': "Reminder: {task}",
                    'not_understood': "Sorry, I didn't get that. Can you repeat?",
                    'listening': "Press the blue button and speak your task.",
                    'ready': "VoiceCare is ready. How can I help you today?"
                }
            },
            'hi': {
                'set_reminder': [
                    r'मुझे (.+) की याद दिलाओ (\d{1,2}):?(\d{0,2})\s*(am|pm|सुबह|शाम)?(\s+(\d+)\s+दिन)?',
                    r'(.+) के लिए रिमाइंडर सेट करो (\d{1,2}):?(\d{0,2})\s*(am|pm|सुबह|शाम)?(\s+(\d+)\s+दिन)?'
                ],
                'query_schedule': [
                    r'आज मेरे रिमाइंडर क्या हैं',
                    r'मेरी अनुसूची',
                    r'मेरे कार्य'
                ],
                'responses': {
                    'reminder_set': "ठीक है, {time} बजे आपको {task} याद दिलाऊँगा।",
                    'reminder_set_recurring': "ठीक है, {time} बजे {task} अगले {days} दिनों तक याद दिलाऊँगा।",
                    'no_reminders': "आज के लिए कोई रिमाइंडर नहीं हैं।",
                    'reminders_list': "आज आपके {count} रिमाइंडर हैं: {reminders}",
                    'reminder_triggered': "रिमाइंडर: {task}",
                    'not_understood': "माफ़ कीजिए, मैं समझ नहीं पाया। कृपया दोहराएँ।",
                    'listening': "नीले बटन को दबाएँ और बोलें।",
                    'ready': "VoiceCare तैयार है। मैं आपकी कैसे मदद कर सकता हूँ?"
                }
            }
        }
    
    def setup_tts(self):
        """Configure text-to-speech engine"""
        voices = self.tts_engine.getProperty('voices')
        # Set to a clear, slower voice suitable for elderly users
        if voices:
            self.tts_engine.setProperty('voice', voices[0].id)
        self.tts_engine.setProperty('rate', 150)  # Slower speech rate
        self.tts_engine.setProperty('volume', 0.9)
    
    def setup_gui(self):
        """Create the main GUI interface"""
        self.root = tk.Tk()
        self.root.title("VoiceCare Assistant")
        self.root.geometry("600x500")
        self.root.configure(bg='#f0f8ff')
        
        # Configure fonts for elderly users
        self.large_font = font.Font(family="Arial", size=18, weight="bold")
        self.medium_font = font.Font(family="Arial", size=14)
        self.button_font = font.Font(family="Arial", size=16, weight="bold")
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#f0f8ff')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="VoiceCare Assistant", 
                              font=font.Font(family="Arial", size=24, weight="bold"),
                              bg='#f0f8ff', fg='#2c3e50')
        title_label.pack(pady=20)
        
        # Status display
        self.status_label = tk.Label(main_frame, text="Ready to help you!", 
                                   font=self.large_font, bg='#f0f8ff', fg='#27ae60')
        self.status_label.pack(pady=10)
        
        # Big microphone button
        self.mic_button = tk.Button(main_frame, text="SPEAK", 
                                   font=font.Font(family="Arial", size=20, weight="bold"),
                                   bg='#3498db', fg='white', activebackground='#2980b9',
                                   width=15, height=3, command=self.start_listening,
                                   relief='raised', bd=5)
        self.mic_button.pack(pady=30)
        
        # Instructions
        instructions = tk.Label(main_frame, 
                        text="Press the SPEAK button and say:\n" +
                        "- 'Remind me to take medicine at 6 PM'\n" +
                        "- 'What are my reminders today?'\n" +
                        "- 'Remind me to take medicine at 8 PM for 5 days'",
                        font=self.medium_font, bg='#f0f8ff', fg='#34495e',
                        justify='left')
        instructions.pack(pady=20)
        
        # Reminders display
        self.reminders_frame = tk.Frame(main_frame, bg='#ecf0f1', relief='sunken', bd=2)
        self.reminders_frame.pack(fill='both', expand=True, pady=10)
        
        tk.Label(self.reminders_frame, text="Today's Reminders:", 
                font=self.medium_font, bg='#ecf0f1', fg='#2c3e50').pack(pady=5)
        
        self.reminders_text = tk.Text(self.reminders_frame, font=self.medium_font,
                                     height=6, wrap='word', bg='white')
        self.reminders_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg='#f0f8ff')
        button_frame.pack(pady=10)
        
        self.repeat_button = tk.Button(button_frame, text="Repeat Reminders", 
                                      font=self.button_font, bg='#e67e22', fg='white',
                                      command=self.repeat_reminders, width=15)
        self.repeat_button.pack(side='left', padx=5)
        
        self.clear_button = tk.Button(button_frame, text="Clear All", 
                                     font=self.button_font, bg='#e74c3c', fg='white',
                                     command=self.clear_all_reminders, width=10)
        self.clear_button.pack(side='left', padx=5)
        
        # Update reminders display
        self.update_reminders_display()
        
        # Start GUI queue processing
        self.process_gui_queue()
        
        # Welcome message
        self.speak("VoiceCare is ready. How can I help you today?")
    
    def process_gui_queue(self):
        """Process GUI updates from the queue (thread-safe)"""
        try:
            while True:
                update_func = self.gui_queue.get_nowait()
                update_func()
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_gui_queue)
    
    def queue_gui_update(self, func):
        """Queue a GUI update function for thread-safe execution"""
        self.gui_queue.put(func)
    
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"Microphone calibration failed: {e}")
    
    def play_sound(self, sound_type):
        """Play audio cues"""
        try:
            if sound_type == "start":
                # Create a simple beep sound
                pygame.mixer.Sound.play(pygame.mixer.Sound(buffer=b'\x00\x80' * 1000))
            elif sound_type == "end":
                pygame.mixer.Sound.play(pygame.mixer.Sound(buffer=b'\x80\x00' * 1000))
        except:
            pass  # Ignore sound errors
    
    def speak(self, text, language='en'):
        """Convert text to speech"""
        def tts_thread():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
        
        threading.Thread(target=tts_thread, daemon=True).start()
    
    def start_listening(self):
        def listen_thread():
            # Queue GUI updates instead of direct updates
            self.queue_gui_update(lambda: self.mic_button.config(state='disabled', bg='#e74c3c', text='LISTENING...'))
            self.queue_gui_update(lambda: self.status_label.config(text="Listening... Please speak now", fg='#e74c3c'))
            
            self.play_sound("start")
            
            try:
                # Try to use Vosk if available, otherwise fallback to speech_recognition
                if self.vosk_model_en:
                    result_text = self.listen_with_vosk()
                else:
                    result_text = self.listen_with_sr()
                
                self.play_sound("end")
                
                if result_text:
                    self.process_voice_command(result_text)
                else:
                    self.queue_gui_update(lambda: self.status_label.config(text="Could not understand. Try again.", fg='#e74c3c'))
                    self.speak("Sorry, I didn't catch that. Please try again.")

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.queue_gui_update(lambda: self.status_label.config(text=error_msg, fg='#e74c3c'))
                self.speak("There was an error. Please try again.")
            finally:
                self.queue_gui_update(lambda: self.mic_button.config(state='normal', bg='#3498db', text='SPEAK'))
                
        threading.Thread(target=listen_thread, daemon=True).start()
    
    def listen_with_vosk(self):
        """Listen using Vosk (offline recognition)"""
        try:
            model = self.vosk_model_en
            rec = vosk.KaldiRecognizer(model, 16000)
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()

            result_text = ""
            start_time = time.time()
            while True:
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    result_text = result.get('text', '')
                    break
                elif time.time() - start_time > 8:  # 8 seconds timeout
                    break
                    
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            return result_text
        except Exception as e:
            print(f"Vosk recognition error: {e}")
            return None
    
    def listen_with_sr(self):
        """Listen using speech_recognition library"""
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
                return None
        except Exception as e:
            print(f"Microphone error: {e}")
            return None
    
    def detect_language(self, text):
        """Detect language of the input text"""
        try:
            detected = detect(text)
            if detected in ['hi', 'mr']:  # Hindi or Marathi
                return 'hi'
            else:
                return 'en'
        except:
            return 'en'  # Default to English
    
    def words_to_numbers(self, text):
        """Convert word numbers to digits"""
        word_to_num = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12'
        }
        for word, num in word_to_num.items():
            text = re.sub(r'\b' + word + r'\b', num, text)
        return text
    
    def process_voice_command(self, text):
        """Process the recognized voice command"""
        text = text.lower().strip()
        text = self.words_to_numbers(text)
        language = self.detect_language(text)
        print(f"Recognized: {text} (Language: {language})")
        
        # Check for reminder setting
        for pattern in self.patterns[language]['set_reminder']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.handle_set_reminder(match, text, language)
                return
        
        # Check for schedule query
        for pattern in self.patterns[language]['query_schedule']:
            if re.search(pattern, text, re.IGNORECASE):
                self.handle_query_schedule(language)
                return
        
        # Fallback - not understood
        response = self.patterns[language]['responses']['not_understood']
        self.queue_gui_update(lambda: self.status_label.config(text="Command not recognized", fg='#e74c3c'))
        self.speak(response, language)
    
    def handle_set_reminder(self, match, text, language):
        """Handle setting a new reminder"""
        try:
            recurring_days = 0
            
            if language == 'hi':
                # Different pattern for Hindi
                if 'बजे' in text:
                    parts = text.split('बजे')
                    time_part = parts[0].strip().split()[-1]
                    
                    # Check for recurring pattern in the Hindi text
                    if 'दिन साठी' in text:
                        recurring_match = re.search(r'(\d+)\s+दिन साठी', text)
                        if recurring_match:
                            recurring_days = int(recurring_match.group(1))
                            print(f"Recurring days detected: {recurring_days}")
                    
                    task_part = parts[1].strip() if len(parts) > 1 else parts[0].split(time_part)[0].strip()
                    if not task_part:
                        task_part = parts[0].split(time_part)[0].strip()
                    hour = int(re.findall(r'\d+', time_part)[0])
                    minute = 0
                else:
                    return
            else:
                groups = match.groups()
                task_part = groups[0].strip()
                hour = int(groups[1])
                minute = int(groups[2]) if groups[2] else 0
                
                # Check for recurring days in English command
                if len(groups) > 5 and groups[5]:
                    recurring_days = int(groups[5])
                    print(f"Recurring days detected: {recurring_days}")
                
                # Handle AM/PM
                if len(groups) > 3 and groups[3]:
                    am_pm = groups[3].lower()
                    print(f"AM/PM indicator: {am_pm}")
                    
                    # Check for PM (afternoon/evening)
                    if any(pm_indicator in am_pm for pm_indicator in ['pm', 'p.m.']):
                        if hour != 12:  # 12 PM is already correct
                            hour += 12
                        print(f"PM detected, hour adjusted to: {hour}")
                    
                    # Check for AM (morning)
                    elif any(am_indicator in am_pm for am_indicator in ['am', 'a.m.']):
                        if hour == 12:  # 12 AM should be 0
                            hour = 0
                        print(f"AM detected, hour adjusted to: {hour}")
                
                # Default assumption for times without AM/PM: if hour < 7, assume PM
                elif 1 <= hour <= 6:
                    print(f"Time {hour}:{minute} has no AM/PM indicator, assuming PM")
                    hour += 12
            
            # Create reminder time
            today = datetime.date.today()
            reminder_time = datetime.time(hour, minute)
            reminder_datetime = datetime.datetime.combine(today, reminder_time)
            
            # Print debug info about the time calculation
            print(f"Setting reminder for: {hour}:{minute} ({reminder_time.strftime('%I:%M %p')})")
            print(f"Current time: {datetime.datetime.now().strftime('%I:%M %p')}")
            
            # If time has passed today, schedule for tomorrow
            if reminder_datetime <= datetime.datetime.now():
                print("Time has already passed today, scheduling for tomorrow")
                today = today + datetime.timedelta(days=1)
                reminder_datetime = datetime.datetime.combine(today, reminder_time)
            
            # Save to database
            cursor = self.conn.cursor()
            
            if recurring_days > 0:
                # This is a recurring reminder
                print(f"Setting up recurring reminder for {recurring_days} days")
                original_reminder_id = None
                
                # Create reminders for each day
                for day_offset in range(recurring_days):
                    reminder_date = today + datetime.timedelta(days=day_offset)
                    reminder_datetime_for_day = datetime.datetime.combine(reminder_date, reminder_time)
                    
                    # Skip if the time has already passed today and it's the first day
                    if day_offset == 0 and reminder_datetime_for_day <= datetime.datetime.now():
                        print(f"Skipping first day as time has passed")
                        continue
                        
                    # Insert into database
                    cursor.execute('''
                        INSERT INTO reminders (task, time, date, language, recurring, remaining_days, original_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        task_part, 
                        reminder_time.strftime('%H:%M'), 
                        reminder_date.strftime('%Y-%m-%d'), 
                        language, 
                        1, 
                        recurring_days - day_offset,
                        original_reminder_id
                    ))
                    
                    reminder_id = cursor.lastrowid
                    
                    # Set original_id for the first reminder
                    if original_reminder_id is None:
                        original_reminder_id = reminder_id
                        # Update the first reminder with its own ID as original
                        cursor.execute('''
                            UPDATE reminders SET original_id = ? WHERE id = ?
                        ''', (original_reminder_id, original_reminder_id))
                    
                    # Schedule the reminder
                    self.scheduler.add_job(
                        func=self.trigger_reminder,
                        trigger="date",
                        run_date=reminder_datetime_for_day,
                        args=[task_part, language, reminder_id, True],
                        id=f"reminder_{reminder_id}"
                    )
                
                self.conn.commit()
                
                # Respond to user with recurring reminder message
                response = self.patterns[language]['responses']['reminder_set_recurring'].format(
                    time=reminder_time.strftime('%I:%M %p'), task=task_part, days=recurring_days)
                self.queue_gui_update(lambda: self.status_label.config(text="Recurring reminder set successfully!", fg='#27ae60'))
                
            else:
                # Regular single reminder
                cursor.execute('''
                    INSERT INTO reminders (task, time, date, language)
                    VALUES (?, ?, ?, ?)
                ''', (task_part, reminder_time.strftime('%H:%M'), today.strftime('%Y-%m-%d'), language))
                self.conn.commit()
                
                reminder_id = cursor.lastrowid
                
                # Schedule the reminder
                self.scheduler.add_job(
                    func=self.trigger_reminder,
                    trigger="date",
                    run_date=reminder_datetime,
                    args=[task_part, language, reminder_id, False],
                    id=f"reminder_{reminder_id}"
                )
                
                # Respond to user with single reminder message
                response = self.patterns[language]['responses']['reminder_set'].format(
                    time=reminder_time.strftime('%I:%M %p'), task=task_part)
                self.queue_gui_update(lambda: self.status_label.config(text="Reminder set successfully!", fg='#27ae60'))
            
            self.speak(response, language)
            
            # Update display
            self.queue_gui_update(self.update_reminders_display)
            
        except Exception as e:
            print(f"Error setting reminder: {e}")
            self.queue_gui_update(lambda: self.status_label.config(text="Error setting reminder", fg='#e74c3c'))
            self.speak("Sorry, I couldn't set that reminder. Please try again.", language)
    
    def handle_query_schedule(self, language):
        """Handle querying today's schedule"""
        try:
            today = datetime.date.today().strftime('%Y-%m-%d')
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT task, time, recurring, remaining_days FROM reminders 
                WHERE date = ? AND active = 1 
                ORDER BY time
            ''', (today,))
            
            reminders = cursor.fetchall()
            
            if not reminders:
                response = self.patterns[language]['responses']['no_reminders']
                self.speak(response, language)
            else:
                reminder_list = []
                for task, time, is_recurring, remaining_days in reminders:
                    time_obj = datetime.datetime.strptime(time, '%H:%M').time()
                    formatted_time = time_obj.strftime('%I:%M %p')
                    
                    reminder_text = f"{task} at {formatted_time}"
                    if is_recurring and remaining_days > 0:
                        reminder_text += f" (repeating for {remaining_days} days)"
                    
                    reminder_list.append(reminder_text)
                
                reminders_text = ", ".join(reminder_list)
                response = self.patterns[language]['responses']['reminders_list'].format(
                    count=len(reminders), reminders=reminders_text)
                self.speak(response, language)
            
            self.queue_gui_update(lambda: self.status_label.config(text="Schedule retrieved", fg='#27ae60'))
            
        except Exception as e:
            print(f"Error querying schedule: {e}")
            self.speak("Sorry, I couldn't get your schedule right now.", language)
    
    def trigger_reminder(self, task, language='en', reminder_id=None, is_recurring=False):
        """Trigger a reminder at the scheduled time"""
        response = self.patterns[language]['responses']['reminder_triggered'].format(task=task)
        self.speak(response, language)
        
        # Update GUI to highlight the reminder (thread-safe)
        def update_gui():
            self.status_label.config(text=f"REMINDER: {task}", fg='#e74c3c')
            self.root.bell()  # System bell sound
            
            # Flash the window to get attention
            self.root.attributes('-topmost', True)
            self.root.after(3000, lambda: self.root.attributes('-topmost', False))
        
        self.queue_gui_update(update_gui)
        
        # Update reminder status in database
        if reminder_id is not None:
            try:
                cursor = self.conn.cursor()
                
                # For now, just mark the reminder as inactive after it's triggered
                cursor.execute('UPDATE reminders SET active = 0 WHERE id = ?', (reminder_id,))
                self.conn.commit()
                
                # Update the display
                self.queue_gui_update(self.update_reminders_display)
                
            except Exception as e:
                print(f"Error updating reminder status: {e}")
    
    def update_reminders_display(self):
        try:
            today = datetime.date.today().strftime('%Y-%m-%d')
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT task, time, recurring, remaining_days FROM reminders 
                WHERE date = ? AND active = 1 
                ORDER BY time
            ''', (today,))
            
            reminders = cursor.fetchall()
            
            self.reminders_text.delete(1.0, tk.END)
            
            if not reminders:
                self.reminders_text.insert(tk.END, "No reminders for today.\n\nPress SPEAK to add a reminder!")
            else:
                for i, (task, time, is_recurring, remaining_days) in enumerate(reminders, 1):
                    time_obj = datetime.datetime.strptime(time, '%H:%M').time()
                    formatted_time = time_obj.strftime('%I:%M %p')
                    
                    # Add recurring indicator
                    recurring_text = ""
                    if is_recurring and remaining_days > 0:
                        recurring_text = f" (Repeats for {remaining_days} more days)"
                    
                    # Correct string formatting
                    self.reminders_text.insert(tk.END, f"{i}. {task} at {formatted_time}{recurring_text}\n")
        
        except Exception as e:
            print(f"Error updating display: {e}")
            self.reminders_text.delete(1.0, tk.END)
            self.reminders_text.insert(tk.END, "Error loading reminders.")
    
    def repeat_reminders(self):
        """Repeat today's reminders audibly"""
        def repeat_thread():
            try:
                today = datetime.date.today().strftime('%Y-%m-%d')
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT task, time FROM reminders 
                    WHERE date = ? AND active = 1 
                    ORDER BY time
                ''', (today,))
                
                reminders = cursor.fetchall()
                
                if not reminders:
                    self.speak("You have no reminders for today.")
                    self.queue_gui_update(lambda: self.status_label.config(text="No reminders to repeat", fg='#f39c12'))
                else:
                    self.speak(f"You have {len(reminders)} reminders today.")
                    time.sleep(1)  # Brief pause
                    
                    for i, (task, time_str) in enumerate(reminders, 1):
                        time_obj = datetime.datetime.strptime(time_str, '%H:%M').time()
                        formatted_time = time_obj.strftime('%I:%M %p')
                        self.speak(f"Reminder {i}: {task} at {formatted_time}")
                        time.sleep(0.5)  # Brief pause between reminders
                    
                    self.queue_gui_update(lambda: self.status_label.config(text="Reminders repeated", fg='#27ae60'))
                    
            except Exception as e:
                print(f"Error repeating reminders: {e}")
                self.speak("Sorry, I couldn't repeat your reminders.")
                self.queue_gui_update(lambda: self.status_label.config(text="Error repeating reminders", fg='#e74c3c'))
        
        threading.Thread(target=repeat_thread, daemon=True).start()
    
    def clear_all_reminders(self):
        """Clear all active reminders for today"""
        try:
            today = datetime.date.today().strftime('%Y-%m-%d')
            cursor = self.conn.cursor()
            
            # Get reminders to be cleared for feedback
            cursor.execute('''
                SELECT COUNT(*) FROM reminders 
                WHERE date = ? AND active = 1
            ''', (today,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Mark reminders as inactive
                cursor.execute('''
                    UPDATE reminders SET active = 0 
                    WHERE date = ? AND active = 1
                ''', (today,))
                self.conn.commit()
                
                # Cancel scheduled jobs
                cursor.execute('''
                    SELECT id FROM reminders 
                    WHERE date = ? AND active = 0
                ''', (today,))
                reminder_ids = cursor.fetchall()
                
                for (reminder_id,) in reminder_ids:
                    try:
                        self.scheduler.remove_job(f"reminder_{reminder_id}")
                    except:
                        pass  # Job might not exist
                
                self.update_reminders_display()
                self.status_label.config(text=f"Cleared {count} reminders", fg='#e67e22')
                self.speak(f"Cleared {count} reminders for today.")
            else:
                self.status_label.config(text="No reminders to clear", fg='#f39c12')
                self.speak("No reminders to clear.")
                
        except Exception as e:
            print(f"Error clearing reminders: {e}")
            self.status_label.config(text="Error clearing reminders", fg='#e74c3c')
            self.speak("Sorry, I couldn't clear your reminders.")
    
    def load_existing_reminders(self):
        """Load and reschedule existing reminders from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, task, time, date, language, recurring, remaining_days FROM reminders 
                WHERE active = 1
            ''', )
            
            reminders = cursor.fetchall()
            current_time = datetime.datetime.now()
            
            for reminder_id, task, time_str, date_str, language, is_recurring, remaining_days in reminders:
                try:
                    # Parse reminder datetime
                    reminder_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    reminder_time = datetime.datetime.strptime(time_str, '%H:%M').time()
                    reminder_datetime = datetime.datetime.combine(reminder_date, reminder_time)
                    
                    # Only reschedule future reminders
                    if reminder_datetime > current_time:
                        self.scheduler.add_job(
                            func=self.trigger_reminder,
                            trigger="date",
                            run_date=reminder_datetime,
                            args=[task, language, reminder_id, is_recurring],
                            id=f"reminder_{reminder_id}"
                        )
                        print(f"Rescheduled reminder {reminder_id}: {task} at {reminder_datetime}")
                    else:
                        # Mark past reminders as inactive
                        cursor.execute('UPDATE reminders SET active = 0 WHERE id = ?', (reminder_id,))
                        
                except Exception as e:
                    print(f"Error rescheduling reminder {reminder_id}: {e}")
                    continue
            
            self.conn.commit()
            print(f"Loaded {len(reminders)} existing reminders")
            
        except Exception as e:
            print(f"Error loading existing reminders: {e}")
    
    def cleanup_old_reminders(self):
        """Clean up old inactive reminders (run periodically)"""
        try:
            # Remove reminders older than 7 days
            cutoff_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            cursor = self.conn.cursor()
            cursor.execute('''
                DELETE FROM reminders 
                WHERE date < ? AND active = 0
            ''', (cutoff_date,))
            self.conn.commit()
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old reminders")
                
        except Exception as e:
            print(f"Error cleaning up old reminders: {e}")
    
    def on_closing(self):
        """Handle application shutdown"""
        try:
            # Stop the scheduler
            if hasattr(self, 'scheduler') and self.scheduler.running:
                self.scheduler.shutdown()
            
            # Close database connection
            if hasattr(self, 'conn'):
                self.conn.close()
            
            # Clean up pygame
            try:
                pygame.mixer.quit()
            except:
                pass
            
            print("VoiceCare Assistant shutting down...")
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            self.root.destroy()
    
    def run(self):
        """Start the application"""
        try:
            # Set up window close handler
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Schedule periodic cleanup (daily at midnight)
            self.scheduler.add_job(
                func=self.cleanup_old_reminders,
                trigger="cron",
                hour=0,
                minute=0,
                id="cleanup_job"
            )
            
            # Start the GUI main loop
            print("Starting VoiceCare Assistant...")
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("Application interrupted by user")
            self.on_closing()
        except Exception as e:
            print(f"Critical error in main loop: {e}")
            self.on_closing()

def main():
    """Main entry point"""
    try:
        app = VoiceCareAssistant()
        app.run()
    except Exception as e:
        print(f"Failed to start VoiceCare Assistant: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()