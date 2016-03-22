import os

AppConfig = {
    'DEBUG_MODE': True,
    'HOST': os.environ.get('HOST', '0.0.0.0'),
    'PORT': int(os.environ.get('PORT', 5001)),
    'FORM_SECRET_KEY': os.urandom(16),
    'MAIL_PER_PAGE': 10,
    'TEMPLATE_FOLDER': '../templates',
    'STATIC_FOLDER': '../static'
}

ServerConfig = {
    'API_URL': os.environ.get('API_URL', 'http://127.0.0.1:5000/api'),
    'HEADERS': {'Content-Type': 'application/json'}
}
