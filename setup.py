"""
Interactive Setup Wizard for Invoice Data Extractor.

Verifies Python, Tesseract, dependencies, and creates configuration.
"""

import sys
import os
import subprocess
import platform
from pathlib import Path


REQUIRED_DIRS = ["sample_invoices", "output", "logs", "cache"]
REQUIREMENTS_FILE = "requirements.txt"
ENV_EXAMPLE = ".env.example"
ENV_FILE = ".env"


def print_header():
    print("\n" + "=" * 60)
    print("   Invoice Data Extractor - Setup Wizard")
    print("=" * 60)
    print()


def check_python_version():
    print("[1/5] Checking Python version...")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ERROR: Python 3.8+ is required!")
        return False
    print("  OK")
    return True


def check_tesseract():
    print("\n[2/5] Checking Tesseract OCR...")
    tesseract_cmd = None

    try:
        result = subprocess.run(
            ["tesseract", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            print(f"  Found: {version_line}")
            tesseract_cmd = "tesseract"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if not tesseract_cmd and platform.system() == "Windows":
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for path in common_paths:
            if os.path.isfile(path):
                print(f"  Found: {path}")
                tesseract_cmd = path
                break

    if not tesseract_cmd:
        print("  WARNING: Tesseract OCR not found!")
        print()
        print("  Please install Tesseract OCR:")
        if platform.system() == "Windows":
            print("    1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            print("    2. Run the installer")
            print(
                "    3. Re-run this setup wizard, or manually set TESSERACT_CMD in .env"
            )
        elif platform.system() == "Darwin":
            print("    brew install tesseract")
        else:
            print("    sudo apt-get install tesseract-ocr")
        print()
        return None

    print("  OK")
    return tesseract_cmd


def check_poppler():
    print("\n[3/5] Checking poppler (for PDF support)...")
    try:
        from pdf2image import convert_from_path

        print("  pdf2image is installed")
        try:
            result = subprocess.run(["pdftoppm", "-h"], capture_output=True, timeout=5)
            print("  poppler is available")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("  WARNING: poppler not found - PDF support will not work")
            print()
            if platform.system() == "Windows":
                print(
                    "    Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases"
                )
                print("    Add to PATH or set POPPLER_PATH in .env")
            elif platform.system() == "Darwin":
                print("    brew install poppler")
            else:
                print("    sudo apt-get install poppler-utils")
            print()
    except ImportError:
        print("  pdf2image not installed (will be installed with dependencies)")
    return True


def install_dependencies():
    print("\n[4/5] Installing Python dependencies...")
    if not os.path.exists(REQUIREMENTS_FILE):
        print(f"  ERROR: {REQUIREMENTS_FILE} not found!")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print("  All dependencies installed successfully")
            return True
        else:
            print(f"  ERROR: Failed to install dependencies")
            print(f"  {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("  ERROR: Installation timed out")
        return False


def create_directories():
    print("\n[5/5] Creating directories and configuration...")
    for dir_name in REQUIRED_DIRS:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_name}/")

    gitkeep = Path("sample_invoices") / ".gitkeep"
    gitkeep.touch(exist_ok=True)

    return True


def create_env_file(tesseract_cmd=None):
    if not os.path.exists(ENV_FILE) and os.path.exists(ENV_EXAMPLE):
        import shutil

        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        print(f"  Created: {ENV_FILE} from {ENV_EXAMPLE}")

    if tesseract_cmd and tesseract_cmd != "tesseract":
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, "r") as f:
                content = f.read()
            if "TESSERACT_CMD=" in content:
                content = content.replace(
                    "TESSERACT_CMD=", f"TESSERACT_CMD={tesseract_cmd}"
                )
            else:
                content += f"\nTESSERACT_CMD={tesseract_cmd}\n"
            with open(ENV_FILE, "w") as f:
                f.write(content)
            print(f"  Set TESSERACT_CMD={tesseract_cmd} in {ENV_FILE}")


def verify_imports():
    print("\nVerifying imports...")
    modules = [
        ("streamlit", "streamlit"),
        ("pytesseract", "pytesseract"),
        ("PIL", "Pillow"),
        ("cv2", "opencv-python-headless"),
        ("pdf2image", "pdf2image"),
        ("dotenv", "python-dotenv"),
        ("pandas", "pandas"),
        ("regex", "regex"),
        ("dateutil", "python-dateutil"),
        ("numpy", "numpy"),
    ]

    all_ok = True
    for module_name, pip_name in modules:
        try:
            __import__(module_name)
            print(f"  OK: {pip_name}")
        except ImportError:
            print(f"  MISSING: {pip_name}")
            all_ok = False

    try:
        from ocr import OCRExtractor

        print("  OK: ocr.py")
    except Exception as e:
        print(f"  ERROR importing ocr.py: {e}")
        all_ok = False

    try:
        from extractor import FieldExtractor

        print("  OK: extractor.py")
    except Exception as e:
        print(f"  ERROR importing extractor.py: {e}")
        all_ok = False

    try:
        from utils import InvoiceProcessor

        print("  OK: utils.py")
    except Exception as e:
        print(f"  ERROR importing utils.py: {e}")
        all_ok = False

    return all_ok


def main():
    print_header()

    checks = []

    checks.append(("Python Version", check_python_version()))
    tesseract_cmd = check_tesseract()
    checks.append(("Tesseract OCR", tesseract_cmd is not None))
    check_poppler()
    checks.append(("Dependencies", install_dependencies()))
    checks.append(("Directories", create_directories()))
    create_env_file(tesseract_cmd)
    checks.append(("Module Imports", verify_imports()))

    print("\n" + "=" * 60)
    print("   Setup Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        symbol = "OK" if passed else "FAIL"
        print(f"  [{symbol}] {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("Setup complete! Run: streamlit run app.py")
    else:
        print("Setup has warnings/errors. See above for details.")
        print("You can still try: streamlit run app.py")
    print()


if __name__ == "__main__":
    main()
