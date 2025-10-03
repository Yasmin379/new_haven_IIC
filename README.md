# HAVEN - Mental Health Platform

## 🌟 Overview

HAVEN is a comprehensive mental health support platform that combines AI-powered chatbot support, professional specialist connections, and personal wellness tracking tools. The platform prioritizes user privacy with anonymous cheerful usernames and implements a Guardian Protocol for crisis detection.

## ✨ Features

### 🤖 AI Companion (BUDDY)
- RAG-powered chatbot using Google Gemini Pro
- Guardian Protocol for crisis detection
- 24/7 emotional support
- Context-aware responses from curated knowledge base

### 👥 Multi-Role System
- **Users**: Students and individuals seeking mental health support
- **Specialists**: Mental health professionals (Psychologists, Psychiatrists, Counselors, etc.)
- **Admin**: Full administrative access via Django admin panel

### 🔐 Privacy & Security
- Auto-generated cheerful usernames (e.g., CalmStar123, JoyfulPanda456)
- No real names displayed in specialist bookings
- Secure authentication system
- Confidential journal entries

### 📊 Wellness Tools
- **Journal**: Digital diary with mood tracking
- **Mood Check**: PHQ-2 and GAD-2 distress screening
- **Study Tracker**: Pomodoro-style study logging
- **Booking System**: Connect with verified specialists
- **Relaxation**: Breathing exercises and calming sounds

## 🛠️ Tech Stack

- **Backend**: Django 5.2+, Python 3.10
- **Database**: PostgreSQL
- **AI/ML**: Google Gemini Pro, LangChain, ChromaDB
- **Frontend**: Bootstrap 5, Custom CSS with cheerful color palette
- **APIs**: Google Generative AI

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 12 or higher
- Google API Key (from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Step 1: Clone the Repository

```bash
cd haven-Avishkar
```

### Step 2: Create and Activate Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DB_USER=postgres
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

# Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key_here

# Django Secret Key
SECRET_KEY=your_django_secret_key_here
```

### Step 5: Create PostgreSQL Database

```bash
# Open PostgreSQL command line
psql -U postgres

# Create database
CREATE DATABASE haven_db;

# Exit psql
\q
```

### Step 6: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 7: Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### Step 8: Setup RAG Knowledge Base

```bash
python setup_rag.py
```

This will:
- Create sample mental health knowledge documents
- Index them into ChromaDB vector store
- Test the retrieval system

### Step 9: Create Static Directories

```bash
python manage.py collectstatic --noinput
```

### Step 10: Run the Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to see the application!

## 🎨 Design Philosophy

HAVEN uses a **cheerful, mood-elevating color palette**:
- Soft Yellows (#FFD700)
- Light Greens (#98FB98)
- Pale Blues (#87CEEB)
- Light Pink (#FFB6C1)
- Lavender (#E6E6FA)

All UI elements feature **floating card aesthetics** with:
- Rounded borders (15px)
- Soft box shadows
- Smooth transitions
- Bouncing/floating animations

## 🔑 User Roles & Access

### Standard User
- **Login**: Use email and password
- **Dashboard**: `user_dashboard.html`
- **Features**: Journal, BUDDY chat, mood check, study tracker, booking

### Specialist
- **Login**: Use email and password
- **Dashboard**: `specialist_dashboard.html`
- **View**: Only anonymous usernames in bookings
- **Features**: Booking management, appointment notes

### Admin
- **Login**: Via `/admin/` with superuser credentials
- **Access**: Full database management
- **Features**: User management, specialist verification, system monitoring

## 📱 Usage Guide

### For Users

1. **Sign Up**: Create account (your cheerful username is auto-generated)
2. **Dashboard**: Access all features from your personalized dashboard
3. **Chat with BUDDY**: Get 24/7 AI-powered emotional support
4. **Journal**: Write daily entries and track your mood
5. **Mood Check**: Complete PHQ-2 and GAD-2 assessments
6. **Book Sessions**: Connect with verified specialists

### For Specialists

1. **Sign Up**: Select "Mental Health Specialist" during registration
2. **Verification**: Contact admin for account verification
3. **Dashboard**: View bookings with anonymous client usernames only
4. **Manage Sessions**: Confirm/complete appointments
5. **Add Notes**: Document session observations (private)

### For Admins

1. **Login**: Access `/admin/` with superuser credentials
2. **Verify Specialists**: Mark specialist profiles as verified
3. **Monitor**: View mood logs, journal entries (for safety)
4. **Manage**: Users, bookings, daily motivations

## 🧠 RAG System (BUDDY)

### Knowledge Base

Default topics include:
- Mental Health Basics
- Coping Strategies
- Crisis Resources
- Study Wellness
- Relationships & Communication

### Adding Custom Content

1. Create `.txt` files in `knowledge_base/` directory
2. Run `python setup_rag.py` to re-index
3. BUDDY will use new content in responses

### Guardian Protocol

BUDDY implements a 3-step safety system:

1. **Safety Check**: Scans for crisis keywords
2. **Retrieval**: Fetches relevant context from knowledge base
3. **Generation**: Creates empathetic, fact-based responses

If crisis keywords detected → Returns helpline information immediately

## 🗄️ Database Schema

### Core Models
- `UserProfile`: Extended user data with cheerful username
- `SpecialistProfile`: Professional credentials and availability
- `JournalEntry`: User diary entries with mood ratings
- `MoodLog`: PHQ-2 and GAD-2 assessment results
- `CounselorBooking`: Specialist appointment system
- `StudyLog`: Study session tracking
- `ChatSession`: BUDDY conversation sessions
- `ChatMessage`: Individual chat messages
- `DailyMotivation`: Daily inspirational messages

## 🎯 API Endpoints

### Chat API
```
POST /api/chat/
Body: { "message": "user message" }
Response: { "response": "AI response", "status": "success", "is_emergency": false }
```

## 🔧 Configuration

### Database Settings
Edit `Haven_project/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'haven_db',
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Google API Configuration
```python
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
```

## 🚀 Production Deployment

### Security Checklist
- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up proper logging
- [ ] Configure database backups

### Recommended Setup
- Use Gunicorn/uWSGI for WSGI server
- Nginx for reverse proxy and static files
- PostgreSQL with SSL
- Redis for caching (optional)
- Celery for background tasks (optional)

## 📊 Admin Tasks

### Create Daily Motivations
```python
python manage.py shell

from haven.models import DailyMotivation
from datetime import date

DailyMotivation.objects.create(
    date=date.today(),
    message="Your positive message here 🌟",
    is_active=True
)
```

### Verify Specialists
1. Login to `/admin/`
2. Go to Specialist Profiles
3. Check "Is verified" checkbox
4. Save

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
# Windows: Check Services
# Linux/Mac: sudo systemctl status postgresql
```

### RAG Setup Fails
```bash
# Ensure Google API key is set
echo %GOOGLE_API_KEY%  # Windows
echo $GOOGLE_API_KEY   # Linux/Mac

# Check API key validity at Google AI Studio
```

### Static Files Not Loading
```bash
python manage.py collectstatic --clear
python manage.py collectstatic --noinput
```

## 📞 Crisis Resources

If you or someone you know is in crisis:
- **National Suicide Prevention Lifeline**: 988 (US)
- **Crisis Text Line**: Text HOME to 741741
- **Emergency Services**: 911 (US) or local emergency number

## 📄 License

This project is created for educational purposes.

## 👥 Contributing

This is an educational project. For any improvements or bug fixes, please document them thoroughly.

## 🙏 Acknowledgments

- Google Gemini Pro for AI capabilities
- LangChain for RAG implementation
- Django community for excellent documentation
- Bootstrap for responsive UI components

---

**Remember: HAVEN is a support tool, not a replacement for professional mental health care. Always seek professional help when needed.**

🌟 **LIFE IS BEAUTIFUL** 🌟

