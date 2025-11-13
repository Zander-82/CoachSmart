import sys

# Add your project directory to the Python path
path = '/home/your_username/CoachSmart'
if path not in sys.path:
    sys.path.insert(0, path)

# Import your Flask app
from app import app as application  # noqa

# Set the secret key for session management
application.secret_key = 'your-secret-key-here'  # Make sure this matches your app's secret key
