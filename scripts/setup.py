"""Setup development environment."""

import sys
import subprocess
from pathlib import Path


def main():
    """Setup development environment."""
    print("🔧 Setting up Agent Toolkit development environment...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("✓ Base dependencies installed")
        
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", ".[dev,database,observability]"
        ], check=True)
        print("✓ Development dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)
    
    # Setup pre-commit hooks
    print("\n🪝 Setting up pre-commit hooks...")
    try:
        subprocess.run(["pre-commit", "install"], check=True)
        print("✓ Pre-commit hooks installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Pre-commit not installed, skipping...")
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    dirs = ["logs", "data", "configs"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    print("✓ Directories created")
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("  1. Run: uvicorn agent_toolkit.registry.api:app --reload")
    print("  2. Visit: http://localhost:8000/docs")
    print("  3. Run tests: pytest")


if __name__ == "__main__":
    main()
