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

class VoiceCareAssistant:
    def __init__(self):
        # Initialize components
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
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Check if we need to add new columns for recurring reminders
            cursor.execute("PRAGMA table_info(reminders)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns if needed
            if 'recurring' not in columns:
                cursor.execute('ALTER TABLE reminders ADD COLUMN recurring INTEGER DEFAULT 0')
            if 'remaining_days' not in columns:
                cursor.execute('ALTER TABLE reminders ADD COLUMN remaining_days INTEGER DEFAULT 0')
            if 'original_id' not in columns:
                cursor.execute('ALTER TABLE reminders ADD COLUMN original_id INTEGER DEFAULT NULL')
        else:
            # Create the table if it doesn't exist
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
                    r'मला (.+) की आठवण करून दे (\d{1,2}):?(\d{0,2}) वाजता(\s+(\d+)\s+दिवस साठी)?',
                    r'(.+) की आठवण (\d{1,2}):?(\d{0,2}) वाजता करून दे(\s+(\d+)\s+दिवस साठी)?',
                    r'(\d{1,2}):?(\d{0,2}) वाजता (.+) आठवण करून दे(\s+(\d+)\s+दिवस साठी)?'
                ],
                'query_schedule': [
                    r'आज माझे काय काम आहे',
                    r'माझे आठवण',
                    r'आज का शेड्यूल'
                ],
                'responses': {
                    'reminder_set': "ठीक आहे, मी {time} वाजता {task} ची आठवण करून देईन.",
                    'reminder_set_recurring': "ठीक आहे, मी {time} वाजता {task} ची आठवण पुढील {days} दिवसांसाठी करून देईन.",
                    'no_reminders': "आज तुमच्यासाठी कोणतीही आठवण नाही.",
                    'reminders_list': "आज तुमच्याकडे {count} आठवण आहेत: {reminders}",
                    'reminder_triggered': "आठवण: {task}",
                    'not_understood': "माफ करा, मला समजले नाही. पुन्हा सांगाल का?",
                    'listening': "निळे बटण दाबा आणि तुमचे काम सांगा.",
                    'ready': "VoiceCare तयार आहे. आज मी तुमची कशी मदत करू शकतो?"
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
        self.mic_button = tk.Button(main_frame, text="🎤 SPEAK", 
                                   font=font.Font(family="Arial", size=20, weight="bold"),
                                   bg='#3498db', fg='white', activebackground='#2980b9',
                                   width=15, height=3, command=self.start_listening,
                                   relief='raised', bd=5)
        self.mic_button.pack(pady=30)
        
        # Instructions
        instructions = tk.Label(main_frame, 
                               text="Press the SPEAK button and say:\n" +
                                    "• 'Remind me to take medicine at 6 PM'\n" +
                                    "• 'What are my reminders today?'\n" +
                                    "• 'मला ५ वाजता औषध घेण्याची आठवण करून दे'\n" +
                                    "• 'Remind me to take medicine at 8 PM for 5 days'",
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
        
        # Welcome message
        self.speak("VoiceCare is ready. How can I help you today?")
    
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
                self.tts_engine.stop() # Stop any ongoing speech
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
        
        threading.Thread(target=tts_thread, daemon=True).start()
    
    def start_listening(self):
        """Start voice recognition in a separate thread"""
        def listen_thread():
            self.mic_button.config(state='disabled', bg='#e74c3c', text='🎤 LISTENING...')
            self.status_label.config(text="Listening... Please speak now", fg='#e74c3c')
            self.play_sound("start")
            
            try:
                with self.microphone as source:
                    # Listen for audio with timeout
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                
                self.status_label.config(text="Processing...", fg='#f39c12')
                
                # Recognize speech using offline recognition (you'd need to set up Vosk here)
                # For now, using Google's API but you should replace with Vosk
                text = self.recognizer.recognize_google(audio)
                
                self.play_sound("end")
                self.process_voice_command(text)
                
            except sr.WaitTimeoutError:
                self.status_label.config(text="No speech detected. Try again.", fg='#e74c3c')
                self.speak("I didn't hear anything. Please try again.")
            except sr.UnknownValueError:
                self.status_label.config(text="Could not understand. Try again.", fg='#e74c3c')
                self.speak("Sorry, I didn't get that. Can you repeat?")
            except Exception as e:
                self.status_label.config(text=f"Error: {str(e)}", fg='#e74c3c')
                self.speak("There was an error. Please try again.")
            finally:
                self.mic_button.config(state='normal', bg='#3498db', text='🎤 SPEAK')
                if self.status_label.cget('text') != "Could not understand. Try again.":
                    self.status_label.config(text="Ready to help you!", fg='#27ae60')
        
        threading.Thread(target=listen_thread, daemon=True).start()
    
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
    
    def process_voice_command(self, text):
        """Process the recognized voice command"""
        text = text.lower().strip()
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
        self.status_label.config(text="Command not recognized", fg='#e74c3c')
        self.speak(response, language)
    
    def handle_set_reminder(self, match, text, language):
        """Handle setting a new reminder"""
        try:
            recurring_days = 0
            
            if language == 'hi':
                # Different pattern for Hindi
                if 'वाजता' in text:
                    parts = text.split('वाजता')
                    time_part = parts[0].strip().split()[-1]
                    
                    # Check for recurring pattern in the Hindi text
                    if 'दिवस साठी' in text:
                        recurring_match = re.search(r'(\d+)\s+दिवस साठी', text)
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
                self.status_label.config(text="Recurring reminder set successfully!", fg='#27ae60')
                
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
                self.status_label.config(text="Reminder set successfully!", fg='#27ae60')
            
            self.speak(response, language)
            
            # Update display
            self.update_reminders_display()
            
        except Exception as e:
            print(f"Error setting reminder: {e}")
            self.status_label.config(text="Error setting reminder", fg='#e74c3c')
            self.speak("Sorry, I couldn't set that reminder. Please try again.", language)

    def handle_query_schedule(self, language):
        """Handle querying today's schedule"""
        try:
            today = datetime.date.today().strftime('%Y-%m-%d')
            cursor = self.conn.cursor()
            
            # Check if the recurring columns exist
            cursor.execute("PRAGMA table_info(reminders)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'recurring' in columns and 'remaining_days' in columns:
                cursor.execute('''
                    SELECT task, time, recurring, remaining_days FROM reminders 
                    WHERE date = ? AND active = 1 
                    ORDER BY time
                ''', (today,))
            else:
                cursor.execute('''
                    SELECT task, time FROM reminders 
                    WHERE date = ? AND active = 1 
                    ORDER BY time
                ''', (today,))
            
            reminders = cursor.fetchall()
            
            if not reminders:
                response = self.patterns[language]['responses']['no_reminders']
                self.speak(response, language)
            else:
                reminder_list = []
                
                if 'recurring' in columns and 'remaining_days' in columns:
                    for task, time, is_recurring, remaining_days in reminders:
                        time_obj = datetime.datetime.strptime(time, '%H:%M').time()
                        formatted_time = time_obj.strftime('%I:%M %p')
                        
                        reminder_text = f"{task} at {formatted_time}"
                        if is_recurring and remaining_days > 0: # Corrected conditional
                            reminder_text += f" (repeating for {remaining_days} more days)" # Corrected string
                        reminder_list.append(reminder_text) # Appended to list
                else:
                    for task, time in reminders:
                        time_obj = datetime.datetime.strptime(time, '%H:%M').time()
                        formatted_time = time_obj.strftime('%I:%M %p')
                        reminder_list.append(f"{task} at {formatted_time}")
                
                reminders_text = ", ".join(reminder_list)
                response = self.patterns[language]['responses']['reminders_list'].format(
                    count=len(reminders), reminders=reminders_text)
                self.speak(response, language)
            
            self.status_label.config(text="Schedule retrieved", fg='#27ae60')
            
        except Exception as e:
            print(f"Error querying schedule: {e}")
            self.speak("Sorry, I couldn't get your schedule right now.", language)
    
    def trigger_reminder(self, task, language='en', reminder_id=None, is_recurring=False):
        """Trigger a reminder at the scheduled time"""
        response = self.patterns[language]['responses']['reminder_triggered'].format(task=task)
        self.speak(response, language)
        
        # Update GUI to highlight the reminder
        self.status_label.config(text=f"REMINDER: {task}", fg='#e74c3c')
        self.root.bell()  # System bell sound
        
        # Flash the window to get attention
        self.root.attributes('-topmost', True)
        self.root.after(3000, lambda: self.root.attributes('-topmost', False))
        
        # Update reminder status in database
        if reminder_id is not None:
            try:
                cursor = self.conn.cursor()
                
                # For now, just mark the reminder as inactive after it's triggered
                cursor.execute('UPDATE reminders SET active = 0 WHERE id = ?', (reminder_id,))
                self.conn.commit()
                
                # Update the display
                self.update_reminders_display()
                
            except Exception as e:
                print(f"Error updating reminder status: {e}") # Added print statement for error
                
    def update_reminders_display(self):
        """Update the reminders display in the GUI"""
        try:
            today = datetime.date.today().strftime('%Y-%m-%d')
            cursor = self.conn.cursor()
            
            # Check if the recurring columns exist
            cursor.execute("PRAGMA table_info(reminders)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'recurring' in columns and 'remaining_days' in columns:
                cursor.execute('''
                    SELECT task, time, recurring, remaining_days FROM reminders 
                    WHERE date = ? AND active = 1 
                    ORDER BY time
                ''', (today,)) # Added comma for single element tuple
            else:
                cursor.execute('''
                    SELECT task, time FROM reminders 
                    WHERE date = ? AND active = 1 
                    ORDER BY time
                ''', (today,)) # Added comma for single element tuple
            
            reminders = cursor.fetchall()
            self.reminders_text.delete(1.0, tk.END)
            
            if not reminders:
                self.reminders_text.insert(tk.END, "No active reminders for today.") # Added message for no reminders
            else:
                display_texts = []
                if 'recurring' in columns and 'remaining_days' in columns:
                    for task, time, is_recurring, remaining_days in reminders:
                        time_obj = datetime.datetime.strptime(time, '%H:%M').time()
                        formatted_time = time_obj.strftime('%I:%M %p')
                        text = f"• {task} at {formatted_time}"
                        if is_recurring and remaining_days > 0:
                            text += f" (Repeats for {remaining_days} more days)"
                        display_texts.append(text)
                else:
                    for task, time in reminders:
                        time_obj = datetime.datetime.strptime(time, '%H:%M').time()
                        formatted_time = time_obj.strftime('%I:%M %p')
                        display_texts.append(f"• {task} at {formatted_time}")
                self.reminders_text.insert(tk.END, "\n".join(display_texts)) # Added join with newline
        
        except Exception as e:
            print(f"Error updating reminders display: {e}") # Added print statement for error
            self.reminders_text.delete(1.0, tk.END)
            self.reminders_text.insert(tk.END, "Error loading reminders.")
    
    def repeat_reminders(self):
        """Repeat today's reminders aloud"""
        self.handle_query_schedule('en') # Added default language
    
    def clear_all_reminders(self):
        """Clear all reminders for today""" # Corrected docstring
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM reminders') # Clears all reminders
            self.conn.commit()

            # Remove all jobs from scheduler
            for job in self.scheduler.get_jobs():
                job.remove()
            
            self.update_reminders_display()
            self.status_label.config(text="All reminders cleared.", fg='#27ae60')
            self.speak("All reminders have been cleared.")
        except Exception as e:
            print(f"Error clearing reminders: {e}") # Added print statement for error
            self.status_label.config(text="Error clearing reminders.", fg='#e74c3c')
            self.speak("Sorry, I couldn't clear the reminders.")
            
    def load_existing_reminders(self):
        """Load and reschedule existing reminders from database"""
        try:
            today = datetime.date.today().strftime('%Y-%m-%d')
            cursor = self.conn.cursor()
            
            # Check if the recurring columns exist
            cursor.execute("PRAGMA table_info(reminders)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'recurring' in columns and 'remaining_days' in columns:
                cursor.execute('''
                    SELECT id, task, time, language, recurring, remaining_days FROM reminders 
                    WHERE date = ? AND active = 1
                ''', (today,))
                
                reminders = cursor.fetchall()
                
                for reminder_id, task, time_str, language, is_recurring, remaining_days in reminders:
                    time_obj = datetime.datetime.strptime(time_str, '%H:%M').time()
                    reminder_datetime = datetime.datetime.combine(datetime.date.today(), time_obj)
                    
                    # Only schedule if the time hasn't passed
                    if reminder_datetime > datetime.datetime.now():
                        self.scheduler.add_job(
                            func=self.trigger_reminder,
                            trigger="date",
                            run_date=reminder_datetime,
                            args=[task, language or 'en', reminder_id, bool(is_recurring)],
                            id=f"reminder_{reminder_id}"
                        )
                        print(f"Loaded reminder: {task} at {time_str} (Recurring: {bool(is_recurring)}, Days left: {remaining_days})")
            else:
                # Fallback to load without recurring info
                cursor.execute('''
                    SELECT id, task, time, language FROM reminders 
                    WHERE date = ? AND active = 1
                ''', (today,))
                
                reminders = cursor.fetchall()
                
                for reminder_id, task, time_str, language in reminders:
                    time_obj = datetime.datetime.strptime(time_str, '%H:%M').time()
                    reminder_datetime = datetime.datetime.combine(datetime.date.today(), time_obj)
                    
                    # Only schedule if the time hasn't passed
                    if reminder_datetime > datetime.datetime.now():
                        self.scheduler.add_job(
                            func=self.trigger_reminder,
                            trigger="date",
                            run_date=reminder_datetime,
                            args=[task, language or 'en', reminder_id, False],
                            id=f"reminder_{reminder_id}"
                        )
                        print(f"Loaded reminder: {task} at {time_str}")
        
        except Exception as e:
            print(f"Error loading existing reminders: {e}")
    
    def run(self):
        """Start the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
    
    def on_closing(self):
        """Clean up when closing the application"""
        try:
            self.scheduler.shutdown()
            self.conn.close()
        except:
            pass
        self.root.quit()

if __name__ == "__main__":
    # Install required packages note
    print("VoiceCare Assistant Starting...")
    print("Required packages: pip install speechrecognition pyttsx3 langdetect apscheduler pygame")
    
    try:
        app = VoiceCareAssistant()
        app.run()
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install speechrecognition pyttsx3 langdetect apscheduler pygame")
    except Exception as e:
        print(f"Error starting application: {e}")
