"""
Student Registration CRM System - Main Entry Point
Run this file to start the application
"""
from app import create_app
from flask import render_template_string, send_from_directory
import os

app = create_app()

@app.route('/')
def index():
    """Serve the main application page"""
    with open('templates/index.html', 'r') as f:
        return render_template_string(f.read())

@app.route('/login.html')
def login():
    """Serve the login page"""
    with open('templates/login.html', 'r') as f:
        return render_template_string(f.read())

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"""
    ═══════════════════════════════════════════════════════════════
                  Student Registration CRM System
    ═══════════════════════════════════════════════════════════════
    
    🚀 Server starting on http://{host}:{port}
    
    📋 Before running, ensure:
       1. PostgreSQL is running
       2. Database is created
       3. Environment variables are set (.env file)
       4. Run 'python init_db.py' to initialize database
    
    🔐 Default Admin Credentials:
       Email: admin@studentcrm.com
       Password: admin123
    
    ═══════════════════════════════════════════════════════════════
    """)
    
    app.run(host=host, port=port, debug=debug)
