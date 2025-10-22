"""
Configuration settings for the migration tool
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Repository paths
BASE_DIR = Path(__file__).parent.parent
ALLOFACTOR_PATH = BASE_DIR / "allofactor"
ALLOFACTORSERVICE_PATH = BASE_DIR / "allofactorservice"

# Java source paths
ALLOFACTOR_SRC = ALLOFACTOR_PATH / "src" / "com" / "iris" / "allofactor"
ALLOFACTORSERVICE_SRC = ALLOFACTORSERVICE_PATH / "src" / "com" / "iris" / "allofactor"

# Service paths
SERVICES_PATH = ALLOFACTORSERVICE_SRC / "services"
SERVICES_IMPL_PATH = SERVICES_PATH / "impl"

# Facade and DAO paths
FACADE_PATH = ALLOFACTOR_SRC / "data" / "dao" / "facade"
DAO_PATH = ALLOFACTOR_SRC / "data" / "dao"

# Output paths
OUTPUT_DIR = BASE_DIR / "migration-tool" / "output"
CALL_GRAPHS_DIR = OUTPUT_DIR / "call_graphs"
CONVERTED_CODE_DIR = OUTPUT_DIR / "converted_code"

# Create output directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True)
CALL_GRAPHS_DIR.mkdir(exist_ok=True)
CONVERTED_CODE_DIR.mkdir(exist_ok=True)

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-4")

# Migration settings
MAX_METHOD_SIZE = 500  # Maximum lines per method for analysis
BATCH_SIZE = 10  # Number of methods to process in parallel
