## Table of contents

- [VoiceCare: Offline Voice Reminder Assistant for Seniors](#voicecare-offline-voice-reminder-assistant-for-seniors)
  - [ Problem Statement](#-problem-statement)
  - [ Solution & Approach](#-solution--approach)
  - [ Key Features](#-key-features)
    - [ Privacy & Reliability](#-privacy--reliability)
    - [ User-Centric Design](#-user-centric-design)
    - [ Comprehensive Reminder Management](#-comprehensive-reminder-management)
  - [ Tech Stack](#-tech-stack)
  - [ Voice Recognition Models](#-voice-recognition-models)
    - [1. Google API Model](#1-google-api-model)
    - [2. Big Model (Vosk Large)](#2-big-model-vosk-large)
    - [3. Small Model (Vosk Small)](#3-small-model-vosk-small)
  - [ User Interface](#-user-interface)
    - [Main Components](#main-components)
    - [Reminder Management](#reminder-management)
  - [ Installation & Setup](#-installation--setup)
    - [Prerequisites](#prerequisites)
    - [Step 1: Clone the Repository](#step-1-clone-the-repository)
    - [Step 2: Create Virtual Environment (Recommended)](#step-2-create-virtual-environment-recommended)
    - [Step 3: Install Dependencies](#step-3-install-dependencies)
    - [Step 4: Download Vosk Models](#step-4-download-vosk-models)
    - [Step 5: Run the Application](#step-5-run-the-application)
  - [ Project Structure](#-project-structure)
  - [ Configuration](#-configuration)
  - [ Target Audience](#-target-audience)
  - [ Benefits](#-benefits)
  - [ Contributing](#-contributing)
  - [ License](#-license)
  - [ Support](#-support)

# VoiceCare: Offline Voice Reminder Assistant for Seniors

VoiceCare is an innovative offline voice reminder assistant specifically designed to empower elderly users. By operating entirely offline, VoiceCare eliminates the need for internet access and addresses privacy concerns associated with cloud-based solutions.

##  Problem Statement

Elderly individuals often struggle with memory, impacting their ability to follow daily routines like medication schedules or appointments. Existing digital reminders are often too complex, requiring internet connectivity and digital literacy. Additionally, online voice assistants raise privacy concerns and depend on stable internet connections.

##  Solution & Approach

VoiceCare bridges the digital divide by providing a voice-controlled, user-friendly interface that helps seniors manage their daily tasks and health routines effectively. Our approach focuses on three core principles:

- **Simplicity**: Intuitive design with minimal complexity
- **Accessibility**: Designed specifically for elderly users
- **Privacy**: Complete offline functionality with no data sharing

##  Key Features

###  Privacy & Reliability
- **Offline Functionality**: Operates entirely without internet, ensuring privacy and reliability
- **No Data Collection**: All data stays on the local device

###  User-Centric Design
- **Targeted User Base**: Specifically designed for elderly users
- **Simplified Interface**: Large, intuitive "SPEAK" button with clear audio prompts
- **Multilingual Support**: Supports regional languages like Hindi and Marathi

###  Comprehensive Reminder Management
- **Broadened Scope**: Manages daily life reminders from health tasks to general chores
- **Manual Entry**: Users can add new reminders directly from the UI
- **Task Completion**: Mark completed tasks with a simple "Done" button
- **Scheduled Reminders**: Triggers audible reminders at set times with UI updates
- **Recurring Reminders**: Support for setting reminders across multiple days of the week

##  Tech Stack

| Component | Technology |
|-----------|------------|
| **Speech Recognition** | Vosk (offline ASR) |
| **Intent Classification** | Rule-based pattern matching |
| **Text-to-Speech** | pyttsx3 |
| **Database** | SQLite |
| **Scheduling** | apscheduler |
| **User Interface** | PyQt5 |
| **Language Detection** | langdetect |
| **Audio Processing** | pygame.mixer |

##  Voice Recognition Models

VoiceCare supports three different speech recognition models to balance accuracy and performance:

### 1. Google API Model
- **Description**: Cloud-based speech recognition (requires internet)
- **Accuracy**: Highest accuracy
- **Use Case**: When internet connectivity is available and maximum accuracy is needed

### 2. Big Model (Vosk Large)
- **Model**: vosk-model-en-in-0.5
- **Description**: Large offline model with high accuracy
- **Size**: ~1.8GB
- **Accuracy**: High offline accuracy
- **Use Case**: When maximum offline accuracy is required

### 3. Small Model (Vosk Small)
- **Description**: Lightweight offline model
- **Size**: ~50MB
- **Accuracy**: Good for basic commands
- **Use Case**: Resource-constrained environments or quick responses

##  User Interface

### Main Components
- **Main Window**: Clean interface with prominent "Welcome to VoiceCare" header
- **SPEAK Button**: Large, accessible button for voice input
- **Status Display**: Real-time feedback area
- **Tabbed Sections**: Organized view for "Today", "Tomorrow", and "All Reminders"

### Reminder Management
- **Reminder Cards**: Individual entries displayed as distinct cards
- **Task Details**: Shows task description, time, and completion status
- **Recurring Indicators**: Displays "Repeats X more days" for recurring tasks
- **Add Reminder Dialog**: Simple popup for manual reminder entry

##  Installation & Setup

### Prerequisites
- Python 3.7 or higher
- Audio input/output capabilities
- Operating System: Windows, macOS, or Linux

### Step 1: Clone the Repository
```bash
git clone <https://github.com/AvdhutRokade/VoiceCare>
cd VoiceCare
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install Vosk pyttsx3 apscheduler PyQt5 langdetect pygame
```

**Note for Linux users**: You may need to install portaudio development headers:
```bash
sudo apt-get install portaudio19-dev
```

### Step 4: Download Vosk Models

#### Small and Big Models
These are typically included with the Vosk installation or can be found in the project's vosk folder.

#### Large Model (en-in-0.5)
1. Download the `vosk-model-en-in-0.5` model separately from here "https://alphacephei.com/vosk/models/vosk-model-en-in-0.5.zip"
2. Extract the model to a designated directory (i.e "vosk/")
3. Ensure `voicecare_final.py` is configured with the correct model path

### Step 5: Run the Application
```bash
python voiceCare_frontend.py
```

##  Project Structure

```
VoiceCare/
├── requirements.txt                    # Python dependencies and packages
├── voicecare_reminders.db             # SQLite database for storing reminders
├── Bigger Model/                      # Implementation using Vosk large model
│   ├── voicecare_final.py            #   Backend processing with big model
│   └── voicecare_frontend.py         #   PyQt5 user interface
├── GoogleSpeech recognition/          # Implementation using Google Speech API
│   ├── voiceCare_frontend.py         #   PyQt5 user interface for Google API
│   ├── VoiceCare_google.py           #   Backend with Google Speech integration
│   └── voicecare_reminders.db        #   Database for Google Speech version
├── Small Model/                       # Implementation using Vosk small model
│   ├── voicecare_final.py            #   Backend processing with small model
│   └── voicecare_frontend.py         #   PyQt5 user interface
├── vosk/                             # Vosk library files and dependencies
├── vosk-model-small-en-us-0.15/      # English (US) speech recognition model
└── vosk-model-small-hi-0.22/         # Hindi speech recognition model
```

##  Configuration

The application automatically detects and configures the available speech recognition models. You can modify the model selection in `voicecare_final.py` based on your requirements:

- For maximum accuracy: Use Google API (requires internet)
- For offline high accuracy: Use Big Model
- For resource efficiency: Use Small Model

##  Target Audience

VoiceCare is specifically designed for:
- Elderly individuals with memory challenges
- Users with limited digital literacy
- Anyone seeking a privacy-focused reminder system
- Caregivers managing multiple patient reminders

##  Benefits

- **Independence**: Helps seniors maintain independence in daily tasks
- **Privacy**: No data leaves the device
- **Accessibility**: Simple voice commands and large UI elements
- **Reliability**: Works without internet connectivity
- **Multilingual**: Supports local languages for natural interaction

##  Contributing

We welcome contributions to improve VoiceCare! Please feel free to:
- Report bugs or issues
- Suggest new features
- Submit pull requests
- Improve documentation


---

**VoiceCare** - Empowering seniors through simple, private, and reliable voice assistance.
