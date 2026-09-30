#!/bin/bash
# PromptOps Logo Update Script
# This script synchronizes the logo across all required locations

echo "========================================"
echo "  PromptOps Logo Update Utility"
echo "========================================"
echo ""

# Check if source logo exists
SOURCE_LOGO="branding/promptops-logo.png"

if [ ! -f "$SOURCE_LOGO" ]; then
    echo "ERROR: Source logo not found at $SOURCE_LOGO"
    echo ""
    echo "Please save your new logo as: branding/promptops-logo.png"
    echo "Then run this script again."
    exit 1
fi

echo "[1/3] Backing up existing logos..."
if [ -f "assets/promptops-logo.png" ]; then
    cp "assets/promptops-logo.png" "assets/promptops-logo.png.backup"
    echo "  - Backed up assets/promptops-logo.png"
fi
if [ -f "frontend/dashboard/public/promptops-logo.png" ]; then
    cp "frontend/dashboard/public/promptops-logo.png" "frontend/dashboard/public/promptops-logo.png.backup"
    echo "  - Backed up frontend/dashboard/public/promptops-logo.png"
fi
echo ""

echo "[2/3] Copying new logo to all locations..."
cp "$SOURCE_LOGO" "assets/promptops-logo.png"
if [ $? -eq 0 ]; then
    echo "  ✓ Updated: assets/promptops-logo.png"
else
    echo "  ✗ Failed: assets/promptops-logo.png"
fi

cp "$SOURCE_LOGO" "frontend/dashboard/public/promptops-logo.png"
if [ $? -eq 0 ]; then
    echo "  ✓ Updated: frontend/dashboard/public/promptops-logo.png"
else
    echo "  ✗ Failed: frontend/dashboard/public/promptops-logo.png"
fi
echo ""

echo "[3/3] Verifying logo files..."
for file in "branding/promptops-logo.png" "assets/promptops-logo.png" "frontend/dashboard/public/promptops-logo.png"; do
    if [ -f "$file" ]; then
        echo "  ✓ Exists: $file"
    else
        echo "  ✗ Missing: $file"
    fi
done
echo ""

echo "========================================"
echo "  Logo Update Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Restart the frontend dev server to see changes"
echo "2. Clear browser cache (Ctrl+Shift+R)"
echo "3. Check login page and navigation bar"
echo ""
