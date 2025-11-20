#!/bin/bash

# PDF Cleaning Tool - System Dependencies Setup Script
# Compatible with Replit and standard Linux environments

set -e

echo "=========================================="
echo "PDF Cleaning Tool - Setup Script"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect environment
if [ -n "$REPL_ID" ]; then
    print_info "Detected Replit environment"
    IS_REPLIT=true
else
    print_info "Detected standard Linux environment"
    IS_REPLIT=false
fi

# Check if running with sufficient privileges
if [ "$IS_REPLIT" = true ]; then
    print_info "Replit environment - using Nix package manager"
    
    # Check if nix is available
    if ! command -v nix-env &> /dev/null; then
        print_error "Nix package manager not found. This should not happen on Replit."
        exit 1
    fi
    
    print_info "Installing system dependencies via Nix..."
    
    # Note: On Replit, we'll use the packager_tool instead
    # This script serves as documentation and fallback
    print_warn "Please use the Replit packager tool to install system dependencies."
    print_info "Required packages: tesseract, poppler_utils, ghostscript"
    
else
    # Standard Linux environment
    print_info "Checking for package manager..."
    
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt-get"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
    else
        print_error "No supported package manager found (apt-get, yum, dnf)"
        exit 1
    fi
    
    print_info "Using package manager: $PKG_MANAGER"
    
    # Check for sudo
    if [ "$EUID" -ne 0 ]; then
        if command -v sudo &> /dev/null; then
            SUDO="sudo"
            print_warn "Script not running as root. Will use sudo for installations."
        else
            print_error "This script requires root privileges or sudo."
            exit 1
        fi
    else
        SUDO=""
    fi
    
    # Update package list
    print_info "Updating package list..."
    $SUDO $PKG_MANAGER update -y
    
    # Install Tesseract OCR with Arabic and English language data
    print_info "Installing Tesseract OCR..."
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        $SUDO apt-get install -y tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng
    elif [ "$PKG_MANAGER" = "yum" ] || [ "$PKG_MANAGER" = "dnf" ]; then
        $SUDO $PKG_MANAGER install -y tesseract tesseract-langpack-ara tesseract-langpack-eng
    fi
    
    # Install Poppler utilities (pdftotext, pdfinfo, etc.)
    print_info "Installing Poppler utilities..."
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        $SUDO apt-get install -y poppler-utils
    elif [ "$PKG_MANAGER" = "yum" ] || [ "$PKG_MANAGER" = "dnf" ]; then
        $SUDO $PKG_MANAGER install -y poppler-utils
    fi
    
    # Install Ghostscript
    print_info "Installing Ghostscript..."
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        $SUDO apt-get install -y ghostscript
    elif [ "$PKG_MANAGER" = "yum" ] || [ "$PKG_MANAGER" = "dnf" ]; then
        $SUDO $PKG_MANAGER install -y ghostscript
    fi
    
    # Install ImageMagick (optional)
    print_info "Installing ImageMagick (optional)..."
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        $SUDO apt-get install -y imagemagick || print_warn "ImageMagick installation failed (optional)"
    elif [ "$PKG_MANAGER" = "yum" ] || [ "$PKG_MANAGER" = "dnf" ]; then
        $SUDO $PKG_MANAGER install -y ImageMagick || print_warn "ImageMagick installation failed (optional)"
    fi
fi

# Verify installations
print_info "Verifying installations..."

check_command() {
    if command -v $1 &> /dev/null; then
        print_info "$1 is installed ✓"
        $1 --version 2>&1 | head -n 1
        return 0
    else
        print_warn "$1 is NOT installed ✗"
        return 1
    fi
}

echo ""
check_command tesseract
check_command pdftotext
check_command gs
check_command convert || print_warn "ImageMagick (convert) is optional"

# Check Python and pip
echo ""
print_info "Checking Python environment..."
if command -v python3 &> /dev/null; then
    print_info "Python3 is installed ✓"
    python3 --version
else
    print_error "Python3 is NOT installed"
    exit 1
fi

if command -v pip3 &> /dev/null; then
    print_info "pip3 is installed ✓"
else
    print_error "pip3 is NOT installed"
    exit 1
fi

# Install Python dependencies
echo ""
print_info "Installing Python dependencies from requirements.txt..."
pip3 install -r requirements.txt

# Create config.yaml if it doesn't exist
if [ ! -f "config.yaml" ]; then
    print_info "Creating config.yaml from example..."
    cp config.yaml.example config.yaml
    print_info "config.yaml created. Please review and adjust settings as needed."
else
    print_info "config.yaml already exists. Skipping..."
fi

# Create necessary directories
print_info "Ensuring directory structure exists..."
mkdir -p context output report scripts services

# Summary
echo ""
echo "=========================================="
print_info "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Place your PDF files in the 'context/' directory"
echo "2. Review and adjust 'config.yaml' settings"
echo "3. Run the cleaning script:"
echo "   python3 scripts/clean_pdfs.py"
echo ""
echo "For preview mode (recommended first run):"
echo "   python3 scripts/clean_pdfs.py --preview"
echo ""
