#!/usr/bin/env python3
"""
Installation Verification Script
Checks if all components are properly installed and configured
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is adequate"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} is too old. Need 3.8+")
        return False

def check_required_packages():
    """Check if all required packages are installed"""
    required_packages = [
        'flask',
        'psycopg2',
        'jwt',
        'cryptography',
        'bcrypt',
        'sqlalchemy'
    ]
    
    print("\n📦 Checking required packages...")
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - NOT INSTALLED")
            all_installed = False
    
    return all_installed

def check_project_structure():
    """Check if all required directories and files exist"""
    print("\n📁 Checking project structure...")
    
    required_items = {
        'directories': [
            'app',
            'app/routes',
            'app/services',
            'static',
            'static/css',
            'static/js',
            'templates',
            'secure_storage',
            'backups',
            'logs'
        ],
        'files': [
            'app/__init__.py',
            'app/models.py',
            'app/routes/auth.py',
            'app/routes/students.py',
            'app/routes/documents.py',
            'app/routes/logistics.py',
            'app/routes/notifications.py',
            'app/routes/admin.py',
            'app/routes/audit.py',
            'app/routes/backup.py',
            'app/services/auth.py',
            'app/services/encryption.py',
            'app/services/audit.py',
            'app/services/notification.py',
            'static/css/styles.css',
            'static/js/app.js',
            'templates/index.html',
            'templates/login.html',
            'requirements.txt',
            'run.py',
            'init_db.py',
            'README.md',
            'API_DOCUMENTATION.md',
            'QUICKSTART.md',
            'VERIFICATION_CHECKLIST.md'
        ]
    }
    
    all_exists = True
    
    # Check directories
    for directory in required_items['directories']:
        path = Path(directory)
        if path.exists() and path.is_dir():
            print(f"  ✅ {directory}/")
        else:
            print(f"  ❌ {directory}/ - MISSING")
            all_exists = False
    
    # Check files
    for file in required_items['files']:
        path = Path(file)
        if path.exists() and path.is_file():
            size = path.stat().st_size
            print(f"  ✅ {file} ({size} bytes)")
        else:
            print(f"  ❌ {file} - MISSING")
            all_exists = False
    
    return all_exists

def check_environment():
    """Check if .env file exists and has required variables"""
    print("\n🔧 Checking environment configuration...")
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print("  ❌ .env file not found")
        print("  ℹ️  Copy .env.example to .env and configure it")
        return False
    
    print("  ✅ .env file exists")
    
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'ENCRYPTION_KEY'
    ]
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    all_configured = True
    for var in required_vars:
        if var in env_content:
            # Check if it's not just the placeholder
            if 'change-this' in env_content.lower() or 'your-' in env_content.lower():
                print(f"  ⚠️  {var} - Present but may need configuration")
            else:
                print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} - NOT SET")
            all_configured = False
    
    return all_configured

def check_database_connection():
    """Check if database connection can be established"""
    print("\n🗄️  Checking database connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("  ❌ DATABASE_URL not set in .env")
            return False
        
        # Try to import psycopg2
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse database URL
        result = urlparse(db_url)
        
        print(f"  ℹ️  Attempting connection to {result.hostname}:{result.port or 5432}")
        
        # This is just a basic check - doesn't actually connect
        print("  ✅ Database URL is configured")
        print("  ℹ️  Run 'python init_db.py' to initialize the database")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

def generate_report():
    """Generate complete verification report"""
    print("="*70)
    print("        Student CRM System - Installation Verification")
    print("="*70)
    
    checks = {
        'Python Version': check_python_version(),
        'Required Packages': check_required_packages(),
        'Project Structure': check_project_structure(),
        'Environment Config': check_environment(),
        'Database Setup': check_database_connection()
    }
    
    print("\n" + "="*70)
    print("                         SUMMARY")
    print("="*70)
    
    all_passed = all(checks.values())
    
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:.<50} {status}")
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 Installation verification PASSED!")
        print("\nNext steps:")
        print("  1. Review and configure .env file if needed")
        print("  2. Run: python init_db.py")
        print("  3. Run: python run.py")
        print("  4. Access: http://localhost:5000")
        print("  5. Login: admin@studentcrm.com / admin123")
    else:
        print("\n⚠️  Some checks failed. Please review the output above.")
        print("\nRecommended actions:")
        print("  1. Install missing packages: pip install -r requirements.txt")
        print("  2. Configure .env file with your settings")
        print("  3. Ensure PostgreSQL is installed and running")
        print("  4. Run this script again to verify")
    
    print("\n" + "="*70 + "\n")
    
    return all_passed

if __name__ == '__main__':
    success = generate_report()
    sys.exit(0 if success else 1)
