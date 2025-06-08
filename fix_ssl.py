#!/usr/bin/env python3
"""
SSL Certificate Fix Script for macOS
Run this if you're getting SSL certificate verification errors.
"""

import subprocess
import sys
import os
import ssl
import certifi

def fix_certificates():
    """Fix SSL certificates on macOS."""
    print("🔧 SSL Certificate Fix for macOS")
    print("=" * 40)
    
    # Method 1: Update certificates using pip
    print("\n1️⃣ Updating certificates via pip...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "certifi"], check=True)
        print("✅ Certificates updated via pip")
    except subprocess.CalledProcessError as e:
        print(f"❌ pip update failed: {e}")
    
    # Method 2: Install Certificates (if Python.org installation)
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    cert_command_path = f"/Applications/Python {python_version}/Install Certificates.command"
    
    print(f"\n2️⃣ Looking for Certificate Installer...")
    if os.path.exists(cert_command_path):
        print(f"✅ Found: {cert_command_path}")
        print("Run this command in Terminal:")
        print(f'"{cert_command_path}"')
    else:
        print("❌ Certificate installer not found (not python.org installation)")
    
    # Method 3: Environment variable fix
    print(f"\n3️⃣ Setting certificate environment variables...")
    cert_file = certifi.where()
    print(f"Certificate file location: {cert_file}")
    
    # Add to shell profile
    shell_profiles = ["~/.bashrc", "~/.zshrc", "~/.bash_profile"]
    export_line = f"export SSL_CERT_FILE={cert_file}"
    export_line2 = f"export REQUESTS_CA_BUNDLE={cert_file}"
    
    print(f"\nAdd these lines to your shell profile:")
    print(f"echo '{export_line}' >> ~/.zshrc")
    print(f"echo '{export_line2}' >> ~/.zshrc")
    print(f"source ~/.zshrc")
    
    # Method 4: Manual certificate update
    print(f"\n4️⃣ Manual certificate update...")
    try:
        # Test SSL connection
        context = ssl.create_default_context()
        print(f"Default SSL context created successfully")
        print(f"Certificate verification: {context.verify_mode}")
    except Exception as e:
        print(f"SSL context error: {e}")
    
    print(f"\n📋 Summary:")
    print(f"- Python version: {sys.version}")
    print(f"- Certifi version: {certifi.__version__}")
    print(f"- Certificate bundle: {certifi.where()}")

def test_openrouter_connection():
    """Test OpenRouter connection with different SSL settings."""
    print(f"\n🧪 Testing OpenRouter Connection...")
    
    import requests
    
    test_url = "https://openrouter.ai/api/v1/models"
    
    # Test 1: With SSL verification
    print(f"Test 1: With SSL verification...")
    try:
        response = requests.get(test_url, timeout=10, verify=True)
        print(f"✅ SSL verification successful: {response.status_code}")
    except Exception as e:
        print(f"❌ SSL verification failed: {e}")
    
    # Test 2: Without SSL verification
    print(f"Test 2: Without SSL verification...")
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(test_url, timeout=10, verify=False)
        print(f"✅ No SSL verification successful: {response.status_code}")
    except Exception as e:
        print(f"❌ No SSL verification failed: {e}")

if __name__ == "__main__":
    fix_certificates()
    test_openrouter_connection()
    
    print(f"\n🚀 Next Steps:")
    print(f"1. Restart your terminal")
    print(f"2. Run: python test_api.py")
    print(f"3. If still failing, the app will use sync client automatically")