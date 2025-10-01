#!/bin/bash

# Student CRM System - Setup Script
# This script automates the initial setup process

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "          Student Registration CRM System - Setup"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

# Check PostgreSQL
echo ""
echo "🔍 Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "   ✅ PostgreSQL is installed"
else
    echo "   ❌ PostgreSQL is not installed. Please install PostgreSQL first."
    exit 1
fi

# Create virtual environment
echo ""
echo "🔧 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
else
    echo "   ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "   ✅ Dependencies installed"

# Check for .env file
echo ""
echo "🔧 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "   Creating .env file from template..."
    cp .env.example .env
    
    # Generate secure keys
    echo "   🔐 Generating secure keys..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    ENCRYPTION_KEY=$(python3 -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())")
    
    # Update .env with generated keys
    sed -i "s/your-secret-key-change-this-in-production/$SECRET_KEY/" .env
    sed -i "s/your-jwt-secret-key-change-this/$JWT_SECRET/" .env
    sed -i "s/your-encryption-key-32-bytes-base64/$ENCRYPTION_KEY/" .env
    
    echo "   ✅ .env file created with secure keys"
    echo ""
    echo "   ⚠️  IMPORTANT: Please edit .env and configure:"
    echo "      - DATABASE_URL (PostgreSQL connection)"
    echo "      - SMTP settings (for email notifications)"
    echo ""
    read -p "   Press Enter after updating .env to continue..."
else
    echo "   ℹ️  .env file already exists"
fi

# Create database
echo ""
echo "🗄️  Database setup..."
read -p "   Enter PostgreSQL username (default: postgres): " pg_user
pg_user=${pg_user:-postgres}

read -p "   Enter database name (default: student_crm): " db_name
db_name=${db_name:-student_crm}

echo "   Creating database $db_name..."
PGPASSWORD=$(read -sp "   Enter PostgreSQL password: " password; echo $password)
export PGPASSWORD

if psql -U "$pg_user" -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
    echo "   ℹ️  Database $db_name already exists"
else
    createdb -U "$pg_user" "$db_name"
    echo "   ✅ Database created"
fi

# Update DATABASE_URL in .env
echo "   Updating DATABASE_URL in .env..."
sed -i "s|postgresql://username:password@localhost:5432/student_crm|postgresql://$pg_user:$PGPASSWORD@localhost:5432/$db_name|" .env

# Initialize database
echo ""
echo "🌱 Initializing database with tables and seed data..."
python3 init_db.py

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "                    ✅ Setup Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🚀 To start the application:"
echo "   1. Activate virtual environment: source venv/bin/activate"
echo "   2. Run the application: python run.py"
echo ""
echo "🌐 Access the application at: http://localhost:5000"
echo ""
echo "🔑 Default login credentials are displayed above"
echo ""
echo "═══════════════════════════════════════════════════════════════"
