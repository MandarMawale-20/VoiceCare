import sqlite3
import speech_recognition as sr
import pyttsx3
import threading
import datetime
import re
import json
from apscheduler.schedulers.background import BackgroundScheduler
import time
import os
from langdetect import detect
import pygame
import queue
import logging

logger = logging.getLogger(__name__)

class VoiceCareAssistant:
    def __init__(self):
        self.tts_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        # Initialize components - removed Vosk initialization
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
        
        # Calibrate microphone
        self.calibrate_microphone()
        
        # Load existing reminders
        self.load_existing_reminders()
    
    def _tts_worker(self):
        """Worker thread for TTS queue processing"""
        while True:
            try:
                text, language = self.tts_queue.get()
                if text is None:  # Shutdown signal
                    break
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                self.tts_queue.task_done()
            except Exception as e:
                print(f"TTS Worker Error: {e}")
    
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
        """Convert text to speech using queue for thread safety"""
        self.tts_queue.put((text, language))
    
    def start_listening(self):
        def listen_thread():
            
            self.play_sound("start")
            
            try:
                # Use Google Speech Recognition directly
                result_text = self.listen_with_google()
                
                self.play_sound("end")
                
                if result_text:
                    self.process_voice_command(result_text)
                else:
                    self.speak("Sorry, I didn't catch that. Please try again.")

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.speak("There was an error. Please try again.")
                
        threading.Thread(target=listen_thread, daemon=True).start()
    
    def listen_with_google(self):
        """Listen using Google Speech Recognition"""
        try:
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Listening...")
                # Listen for audio with timeout and phrase time limit
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("Processing speech...")
            try:
                # Use Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                print(f"Google Speech Recognition result: {text}")
                return text
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
                return None
        except sr.WaitTimeoutError:
            print("Listening timeout")
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
            
            self.speak(response, language)
            
        except Exception as e:
            print(f"Error setting reminder: {e}")
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
            
        except Exception as e:
            print(f"Error querying schedule: {e}")
            self.speak("Sorry, I couldn't get your schedule right now.", language)
    
    def trigger_reminder(self, task, language='en', reminder_id=None, is_recurring=False):
        """Trigger a reminder at the scheduled time"""
        response = self.patterns[language]['responses']['reminder_triggered'].format(task=task)
        self.speak(response, language)
        
        # Update reminder status in database
        if reminder_id is not None:
            try:
                cursor = self.conn.cursor()
                
                # For now, just mark the reminder as inactive after it's triggered
                cursor.execute('UPDATE reminders SET active = 0 WHERE id = ?', (reminder_id,))
                self.conn.commit()
                

                
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
            
            # Log reminders to console instead of GUI
            if not reminders:
                print("No reminders for today.")
            else:
                for i, (task, time, is_recurring, remaining_days) in enumerate(reminders, 1):
                    time_obj = datetime.datetime.strptime(time, '%H:%M').time()
                    formatted_time = time_obj.strftime('%I:%M %p')
                    recurring_text = " (Repeats for " + str(remaining_days) + " more days)" if is_recurring and remaining_days > 0 else ""
                    print(f"{i}. {task} at {formatted_time}{recurring_text}")
        
        except Exception as e:
            print(f"Error updating display: {e}")
    
    def repeat_reminders(self):
        """Repeat today's reminders audibly"""
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
                    else:
                        self.speak(f"You have {len(reminders)} reminders today.")
                        time.sleep(1)  # Brief pause
                        
                        for i, (task, time_str) in enumerate(reminders, 1):
                            time_obj = datetime.datetime.strptime(time_str, '%H:%M').time()
                            formatted_time = time_obj.strftime('%I:%M %p')
                            self.speak(f"Reminder {i}: {task} at {formatted_time}")
                            time.sleep(0.5)  # Brief pause between reminders
                        
                except Exception as e:
                    print(f"Error repeating reminders: {e}")
                    self.speak("Sorry, I couldn't repeat your reminders.")

    def clear_all_reminders(self):
        """Clear all reminders after confirmation"""
        try:
            # Simple confirmation dialog
            cursor = self.conn.cursor()
            cursor.execute('UPDATE reminders SET active = 0')
            self.conn.commit()
            
            # Cancel all scheduled jobs
            for job in self.scheduler.get_jobs():
                self.scheduler.remove_job(job.id)
            
            self.update_reminders_display()
            self.speak("All reminders have been cleared.")
                
        except Exception as e:
            print(f"Error clearing reminders: {e}")
            self.status_label.config(text="Error clearing reminders", fg='#e74c3c')
    
    def load_existing_reminders(self):
        """Load and reschedule existing reminders from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, task, time, date, language, recurring, remaining_days 
                FROM reminders 
                WHERE active = 1 AND date >= ?
            ''', (datetime.date.today().strftime('%Y-%m-%d'),))
            
            reminders = cursor.fetchall()
            
            for reminder_id, task, time_str, date_str, language, is_recurring, remaining_days in reminders:
                try:
                    # Parse the saved date and time
                    reminder_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    reminder_time = datetime.datetime.strptime(time_str, '%H:%M').time()
                    reminder_datetime = datetime.datetime.combine(reminder_date, reminder_time)
                    
                    # Only schedule if it's in the future
                    if reminder_datetime > datetime.datetime.now():
                        self.scheduler.add_job(
                            func=self.trigger_reminder,
                            trigger="date",
                            run_date=reminder_datetime,
                            args=[task, language, reminder_id, bool(is_recurring)],
                            id=f"reminder_{reminder_id}"
                        )
                        print(f"Loaded reminder: {task} at {reminder_datetime}")
                    else:
                        # Mark as inactive if time has passed
                        cursor.execute('UPDATE reminders SET active = 0 WHERE id = ?', (reminder_id,))
                        
                except Exception as e:
                    print(f"Error loading reminder {reminder_id}: {e}")
            
            self.conn.commit()
            print(f"Loaded {len([r for r in reminders if datetime.datetime.combine(datetime.datetime.strptime(r[3], '%Y-%m-%d').date(), datetime.datetime.strptime(r[2], '%H:%M').time()) > datetime.datetime.now()])} active reminders")
            
        except Exception as e:
            print(f"Error loading existing reminders: {e}")
    
    def run(self):
        """Start the main application"""
        try:
            print("VoiceCare Assistant backend initialized successfully")
        except KeyboardInterrupt:
            print("Application interrupted by user")
        except Exception as e:
            print(f"Application error: {e}")
        finally:
            self.cleanup()
    
    def on_closing(self):
        """Handle application closing"""
        try:
            # Stop TTS worker
            self.tts_queue.put((None, None))  # Shutdown signal
            
            # Stop scheduler
            if self.scheduler.running:
                self.scheduler.shutdown()
            
            # Close database connection
            if hasattr(self, 'conn'):
                self.conn.close()
            
            # Quit pygame
            pygame.mixer.quit()
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'scheduler') and self.scheduler.running:
                self.scheduler.shutdown()
            if hasattr(self, 'conn'):
                self.conn.close()
            pygame.mixer.quit()
        except Exception as e:
            print(f"Cleanup error: {e}")


def main():
    """Main function to run the VoiceCare Assistant"""
    try:
        # Check for required dependencies
        required_modules = [
            'speech_recognition', 'pyttsx3', 'pygame', 
            'apscheduler', 'langdetect'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print("Missing required modules:")
            for module in missing_modules:
                print(f"  - {module}")
            print("\nPlease install them using:")
            print(f"pip install {' '.join(missing_modules)}")
            return
        
        # Create and run the assistant
        assistant = VoiceCareAssistant()
        assistant.run()
        
    except Exception as e:
        print(f"Failed to start VoiceCare Assistant: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()