import os
from app import create_app

app = create_app()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
