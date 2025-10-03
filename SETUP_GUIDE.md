# HAVEN - Quick Setup Guide

## 🚀 Quick Start (5 Minutes)

### 1. Database Setup

Open PostgreSQL and create the database:

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE haven_db;

-- Verify
\l

-- Exit
\q
```

### 2. Environment Variables

Create a `.env` file in the project root with:

```env
DB_USER=postgres
DB_PASSWORD=root@123
DB_HOST=localhost
DB_PORT=5432
GOOGLE_API_KEY=your_google_api_key_here
SECRET_KEY=django-insecure-5%m^_n=r*^y8#30705ee+tzjcf6$lvwa$_jx60ev#lfcb=f2hh
```

**Important**: Get your Google API Key from: https://makersuite.google.com/app/apikey

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

Expected output: "Applying migrations... OK"

### 4. Create Admin User

```bash
python manage.py createsuperuser
```

Enter:
- Username: admin
- Email: admin@haven.com
- Password: (your choice, min 8 characters)

### 5. Setup RAG Knowledge Base

```bash
python setup_rag.py
```

This will create sample mental health documents and index them for BUDDY.

Expected output: "HAVEN RAG setup completed successfully!"

### 6. Run the Server

```bash
python manage.py runserver
```

Visit: **http://localhost:8000**

## 🎯 Test the Application

### Test User Flow:

1. **Homepage**: Go to http://localhost:8000
2. **Sign Up**: Click "Get Started"
   - Enter details
   - Select "User" role
   - Select gender for username generation
   - Submit
3. **Note Your Cheerful Username**: It will be displayed after signup!
4. **Login**: Use your email and password
5. **Dashboard**: You'll see your personalized dashboard
6. **Chat with BUDDY**: Click the BUDDY robot icon
7. **Test Crisis Detection**: Type "I'm feeling suicidal" (will trigger helpline message)
8. **Test Normal Chat**: Type "How can I manage stress?"

### Test Specialist Flow:

1. **Sign Up**: Create new account
2. **Select**: "Mental Health Specialist" role
3. **Choose Specialty**: e.g., "Psychologist"
4. **Login**: After account creation
5. **Note**: You'll see "pending verification" message
6. **Admin Verification**: 
   - Go to http://localhost:8000/admin/
   - Login with superuser credentials
   - Navigate to "Specialist Profiles"
   - Find your specialist account
   - Check "Is verified" checkbox
   - Save
7. **Re-login**: Now you can see bookings

### Test Admin Flow:

1. **Visit**: http://localhost:8000/admin/
2. **Login**: With superuser credentials
3. **Explore**: All models and data

## 📋 Quick Commands Reference

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Setup RAG
python setup_rag.py

# Run server
python manage.py runserver

# Run on different port
python manage.py runserver 8080

# Create static files
python manage.py collectstatic

# Django shell
python manage.py shell

# Database shell
python manage.py dbshell
```

## 🔍 Testing Checklist

- [ ] Homepage loads
- [ ] Signup creates user with cheerful username
- [ ] Login redirects to correct dashboard
- [ ] User can write journal entry
- [ ] User can complete mood check
- [ ] Chat with BUDDY works
- [ ] Crisis detection triggers helpline message
- [ ] Specialist signup creates specialist profile
- [ ] Admin can verify specialists
- [ ] Booking system works
- [ ] Study tracker logs sessions

## 🐛 Common Issues & Solutions

### Issue: ModuleNotFoundError
**Solution**: Install requirements
```bash
pip install -r requirements.txt
```

### Issue: Database connection failed
**Solution**: Check PostgreSQL is running and credentials in `.env` are correct

### Issue: Google API Key error in RAG setup
**Solution**: 
1. Get API key from https://makersuite.google.com/app/apikey
2. Add to `.env` file: `GOOGLE_API_KEY=your_key_here`
3. Re-run `python setup_rag.py`

### Issue: Static files not loading
**Solution**:
```bash
python manage.py collectstatic --noinput
```

### Issue: CSRF verification failed
**Solution**: Clear browser cookies or use incognito mode

### Issue: Port already in use
**Solution**: Use different port
```bash
python manage.py runserver 8080
```

## 📊 Sample Data Creation

### Create Daily Motivations

```bash
python manage.py shell
```

Then run:
```python
from haven.models import DailyMotivation
from datetime import date, timedelta

# Create motivations for next 7 days
messages = [
    "Every new day is a fresh start. You've got this! 🌟",
    "Believe in yourself. You are stronger than you think! 💪",
    "Small steps lead to big changes. Keep going! 🌱",
    "Your mental health matters. Take care of yourself today! 💚",
    "You are worthy of love, respect, and happiness! ✨",
    "Progress, not perfection. Be kind to yourself! 🌸",
    "Today is full of possibilities. Embrace them! 🌈"
]

for i, msg in enumerate(messages):
    DailyMotivation.objects.get_or_create(
        date=date.today() + timedelta(days=i),
        defaults={'message': msg, 'is_active': True}
    )

print("Created 7 daily motivations!")
exit()
```

### Create Test Specialist

Via Django shell:
```python
from django.contrib.auth.models import User
from haven.models import SpecialistProfile

user = User.objects.create_user(
    username='dr.smith@haven.com',
    email='dr.smith@haven.com',
    password='testpass123',
    first_name='John',
    last_name='Smith'
)

specialist = SpecialistProfile.objects.create(
    user=user,
    specialty='psychologist',
    experience_years=10,
    bio='Experienced psychologist specializing in anxiety and depression.',
    is_verified=True
)

print(f"Created specialist: Dr. {user.get_full_name()}")
exit()
```

## 🎨 Customization Tips

### Change Color Palette
Edit `static/css/haven.css`:
```css
:root {
    --haven-primary: #YOUR_COLOR;
    --haven-secondary: #YOUR_COLOR;
    /* etc. */
}
```

### Add New Knowledge Documents
1. Create `.txt` file in `knowledge_base/`
2. Run `python setup_rag.py`

### Customize Username Generation
Edit `haven/models.py` in `UserProfile.generate_cheerful_username()` method

## 📱 Mobile Testing

The application is responsive! Test on:
- Chrome DevTools (F12 → Toggle Device Toolbar)
- Real mobile devices
- Different screen sizes

## 🔐 Security Reminders

For Production:
1. Change `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Configure `ALLOWED_HOSTS`
4. Use strong database passwords
5. Enable HTTPS
6. Keep API keys secret

## 📞 Support Resources

If you encounter issues:
1. Check error messages carefully
2. Review Django logs
3. Check PostgreSQL logs
4. Verify all dependencies are installed
5. Ensure virtual environment is activated

## ✅ All Set!

You're now ready to use HAVEN! Start by creating a user account and exploring the features.

**Remember**: This is a mental health support tool. Always seek professional help for serious mental health concerns.

🌟 **LIFE IS BEAUTIFUL** 🌟

