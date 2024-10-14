# config.py

# Google API Scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Google Drive Folder IDs
FOLDER_ID = '1DosoFD-WtRC2CWaq-HhoMYxZfl1fhoXY'  # Sample Folder where data is present (gotten from google's file sharing link)
FOLDER_MOVE_ID = "1v-o0k9b5EjgKh6DCsu5ZYdNDUdhnvFsv"  # Sample Folder where data is to be moved (gotten from google's file sharing link)

# File Paths
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"
TAGGING_MAP_FILE = "tagging_map.json"

# API Key for Groq (or any other service)
GROQ_API_KEY = "Enter Your API Key"

# LLM Configuration
LLM_MODEL = "llama-3.2-90b-text-preview"
LLM_SYSTEM_MESSAGE = "You are a File Categorizer"

# Categories for classification (optional if you're using the tagging_map.json)
CATEGORIES = [
    "Accounting",
    "Curation",
    "Development (contributed revenue generation)",
    "Employee resources (HR)",
    "Board of Directors",
    "Marketing",
    "Operations",
    "Programming",
    "Research"
]
