#!/usr/bin/env python3
"""
PrintBot AI - Startup Script
============================
Easy startup for the automated POD system
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def setup_environment():
    """Setup virtual environment and install dependencies"""
    venv_path = Path("./venv")
    
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # Determine pip path
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:  # Unix/Mac
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    print("📦 Installing dependencies...")
    subprocess.run([str(pip_path), "install", "-r", "python/requirements.txt"], check=True)
    
    return str(python_path)


def create_directories():
    """Create necessary directories"""
    dirs = [
        "./data",
        "./data/designs",
        "./data/backups",
        "./logs"
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"📁 {d}")


def create_env_file():
    """Create .env template if it doesn't exist"""
    env_path = Path("./.env")
    
    if not env_path.exists():
        print("📝 Creating .env template...")
        env_content = """# PrintBot AI - Environment Configuration
# ========================================
# Copy this file to .env and fill in your values

# Shopify (Required)
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_admin_api_token
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret

# Printful (Required)
PRINTFUL_API_KEY=your_printful_api_key
PRINTFUL_STORE_ID=your_store_id

# OpenAI (Required)
OPENAI_API_KEY=your_openai_api_key

# Social Media (Optional)
INSTAGRAM_USERNAME_0=your_main_account
INSTAGRAM_PASSWORD_0=your_password
INSTAGRAM_USERNAME_1=backup_account_1
INSTAGRAM_PASSWORD_1=password_1
INSTAGRAM_USERNAME_2=backup_account_2
INSTAGRAM_PASSWORD_2=password_2

TIKTOK_USERNAME_0=your_main_account
TIKTOK_PASSWORD_0=your_password

# Email Notifications (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_email@gmail.com

# Emergency Contact (Optional)
EMERGENCY_CONTACT=your_phone_number

# Cloud Backup (Optional)
BACKUP_CLOUD_TOKEN=your_google_drive_or_dropbox_token
"""
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("📝 .env template created - please edit with your credentials")


def run_dashboard():
    """Run the React dashboard"""
    print("\n🚀 Starting Dashboard...")
    print("=" * 50)
    
    # Check if node_modules exists
    if not Path("./node_modules").exists():
        print("📦 Installing dashboard dependencies...")
        subprocess.run(["npm", "install"], check=True)
    
    # Start dev server
    subprocess.run(["npm", "run", "dev"], check=False)


def run_agents(python_path: str):
    """Run the Python agents"""
    print("\n🚀 Starting PrintBot AI Agents...")
    print("=" * 50)
    
    # Run the main orchestrator
    subprocess.run([python_path, "python/main.py"], check=False)


def main():
    parser = argparse.ArgumentParser(description="PrintBot AI - Automated POD System")
    parser.add_argument("--setup", action="store_true", help="Setup environment only")
    parser.add_argument("--agents-only", action="store_true", help="Run agents only (no dashboard)")
    parser.add_argument("--dashboard-only", action="store_true", help="Run dashboard only (no agents)")
    
    args = parser.parse_args()
    
    print("🤖 PrintBot AI - Automated Print-on-Demand System")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Setup
    if args.setup:
        print("\n📦 Setting up environment...")
        python_path = setup_environment()
        create_directories()
        create_env_file()
        print("\n✅ Setup complete!")
        print("📝 Next steps:")
        print("   1. Edit .env file with your API credentials")
        print("   2. Run: python start.py")
        return
    
    # Check if .env exists
    if not Path("./.env").exists():
        print("\n⚠️  .env file not found!")
        create_env_file()
        print("\n❌ Please edit .env with your credentials and run again")
        return
    
    # Setup if needed
    python_path = setup_environment()
    create_directories()
    
    # Run components
    if args.dashboard_only:
        run_dashboard()
    elif args.agents_only:
        run_agents(python_path)
    else:
        # Run both - agents in background, dashboard in foreground
        import threading
        
        agents_thread = threading.Thread(target=run_agents, args=(python_path,))
        agents_thread.daemon = True
        agents_thread.start()
        
        # Wait a moment for agents to start
        import time
        time.sleep(2)
        
        run_dashboard()


if __name__ == "__main__":
    main()
