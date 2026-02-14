import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import create_app
from app.config.settings import Config

app = create_app()

if __name__ == '__main__':
    print(f"🚀 TrustLens backend running on port {Config.PORT}")
    app.run(host='0.0.0.0', port=Config.PORT, debug=False, use_reloader=False)
