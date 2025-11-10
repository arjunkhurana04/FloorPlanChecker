import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == '' or GEMINI_API_KEY == 'your_api_key_here':
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please create a .env file with your actual API key.")
GEMINI_API_KEY = GEMINI_API_KEY.strip()  # Remove any whitespace

# Model configuration
GEMINI_MODEL = 'gemini-2.5-flash'  # Supports vision capabilities
# Note: Google's Gemini models analyze images but don't generate new images
# For image generation, you may need to use Google's Imagen API separately
# Trying standard model name - if image generation model exists, update this
GEMINI_IMAGE_MODEL = 'gemini-2.5-flash'  # Fallback to standard model if image generation model not available

# Upload configuration
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
UPLOAD_FOLDER = 'uploads'

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

