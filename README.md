# 🏋️‍♂️ CoachSmart

Your personal sports training planner with AI-powered feedback.

## Features

- 🏃 Create, view, edit, and delete custom training plans
- 🤖 AI Coach provides adaptive feedback and tips
- 💾 Save your plans with a built-in SQLite database
- 💻 Works seamlessly on mobile and desktop
- 🎨 Modern, accessible, and easy-to-navigate interface

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Zander-82/CoachSmart.git
   cd CoachSmart
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Set up the environment**
   ```bash
   # On Windows
   set FLASK_APP=app.py
   set FLASK_ENV=development
   
   # On macOS/Linux
   export FLASK_APP=app.py
   export FLASK_ENV=development
   ```

2. **Initialize the database**
   ```bash
   flask shell
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```

3. **Run the development server**
   ```bash
   flask run
   ```

4. **Open in your browser**
   Visit `http://127.0.0.1:5000` in your web browser.

## Project Structure

```
CoachSmart/
├── app.py                # Main application file
├── requirements.txt      # Python dependencies
├── instance/             # Instance folder (created automatically)
│   └── coachsmart.db     # SQLite database (created after first run)
├── static/               # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── add_plan.html     # Add new training plan
    ├── edit_plan.html    # Edit existing plan
    └── ai_coach.html     # AI Coach page
```

## Deployment to PythonAnywhere

1. **Create a PythonAnywhere account** at [pythonanywhere.com](https://www.pythonanywhere.com/)

2. **Upload your code**
   - Option 1: Connect your GitHub repository
   - Option 2: Upload files manually via the web interface

3. **Set up a virtual environment**
   - Go to the "Consoles" tab and start a new console
   ```bash
   mkvirtualenv --python=/usr/bin/python3.8 venv
   workon venv
   pip install -r requirements.txt
   ```

4. **Configure the web app**
   - Go to the "Web" tab
   - Click "Add a new web app"
   - Choose "Manual Configuration" (not "Flask")
   - Select Python 3.8 or higher
   - In the WSGI configuration file, update it to point to your app:
     ```python
     import sys
     path = '/home/yourusername/CoachSmart'
     if path not in sys.path:
         sys.path.append(path)
     
     from app import app as application
     ```

5. **Set up the database**
   - In the PythonAnywhere console:
     ```bash
     cd ~/CoachSmart
     python
     >>> from app import app, db
     >>> app.app_context().push()
     >>> db.create_all()
     ```

6. **Configure static files**
   - In the "Web" tab, scroll to "Static files"
   - Add a mapping for `/static/` to `/home/yourusername/CoachSmart/static`

7. **Reload your web app**
   - Click the green "Reload" button on the web app page

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Icons by [Font Awesome](https://fontawesome.com/)
