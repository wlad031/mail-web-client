import os

AppConfig = {
    'DEBUG_MODE': True,
    'HOST': '0.0.0.0',
    'PORT': int(os.environ.get("PORT", 5001))
}

ServerConfig = {
    'HOST': '0.0.0.0',
    'PORT': int(os.environ.get("PORT", 5000))
}