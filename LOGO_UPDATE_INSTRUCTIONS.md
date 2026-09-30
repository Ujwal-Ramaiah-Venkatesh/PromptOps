# 🎨 PromptOps Logo Update Instructions

## Step-by-Step Guide to Replace the Logo

### 📥 Step 1: Save the New Logo

1. **Right-click** on the new logo image you have
2. **Save As** → Name it: `promptops-logo.png`
3. **Save to:** `C:\Users\pqm847\Documents\PromptOps\branding\promptops-logo.png`

**Important:** The file must be saved as `promptops-logo.png` in the `branding` folder.

---

### 🔄 Step 2: Run the Update Script

#### **For Windows:**
```bash
cd C:\Users\pqm847\Documents\PromptOps
update_logo.bat
```

#### **For Linux/Mac:**
```bash
cd C:\Users\pqm847\Documents\PromptOps
chmod +x update_logo.sh
./update_logo.sh
```

The script will automatically:
- ✅ Backup your old logos (`.backup` extension)
- ✅ Copy the new logo to all 3 required locations
- ✅ Verify all files are in place

---

### 📍 Logo Files Updated (3 locations)

The script synchronizes the logo to:

1. **`branding/promptops-logo.png`** - Source of truth
2. **`assets/promptops-logo.png`** - For documentation
3. **`frontend/dashboard/public/promptops-logo.png`** - Web app & favicon

---

### 🌐 Step 3: See the Changes in the UI

#### **1. Restart Frontend (if running)**
```bash
# Stop the current dev server (Ctrl+C)
cd frontend/dashboard
npm start
```

#### **2. Clear Browser Cache**
- **Chrome/Edge:** Press `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
- **Or:** Open DevTools (F12) → Right-click refresh → "Empty Cache and Hard Reload"

#### **3. Check Logo Appears in:**
- ✅ **Login Page** - Logo should be 100x100px at the top
- ✅ **Navigation Bar** - Logo should be 48x48px in the top-left corner
- ✅ **Browser Tab** - Favicon should show the new logo

---

### 🔍 Verify Logo Updates

Run this command to check all logo files are updated:

```bash
# Windows PowerShell
Get-ChildItem -Recurse -Filter "promptops-logo.png" | Select-Object FullName, Length, LastWriteTime

# Linux/Mac
find . -name "promptops-logo.png" -exec ls -lh {} \;
```

**Expected Output:** All 3 files should have the same size and recent timestamp.

---

### 📂 Manual Update (Alternative Method)

If you prefer to update manually:

```bash
# Windows
copy branding\promptops-logo.png assets\promptops-logo.png
copy branding\promptops-logo.png frontend\dashboard\public\promptops-logo.png

# Linux/Mac
cp branding/promptops-logo.png assets/promptops-logo.png
cp branding/promptops-logo.png frontend/dashboard/public/promptops-logo.png
```

---

### 🎯 Where the Logo Appears

#### **Frontend UI (2 places):**
1. **Login Page** (`LoginPage.tsx`)
   - Size: 100x100px
   - Location: Top center of login card
   - Path: `/promptops-logo.png`

2. **Navigation Bar** (`App.tsx`)
   - Size: 48x48px  
   - Location: Top-left corner next to "PromptOps" text
   - Path: `/promptops-logo.png`

#### **Browser Favicon:**
- **File:** `frontend/dashboard/index.html`
- **Reference:** `<link rel="icon" type="image/png" href="/promptops-logo.png" />`

#### **Documentation (6 files):**
- `README.md` - Main project README (300px width)
- `DEPLOYMENT.md` - Deployment guide (200px width)
- `api_gateway/README.md` - API Gateway docs (200px width)
- `frontend/dashboard/README.md` - Dashboard docs (200px width)
- `branding/LOGO_USAGE.md` - Logo usage guidelines
- `docs/archive/miscellaneous/LOGO_CHECKLIST.md` - Logo checklist

---

### 🔧 Troubleshooting

#### **Issue 1: Logo not updating in browser**
**Solution:**
```bash
# Hard refresh
Ctrl + Shift + R (Windows)
Cmd + Shift + R (Mac)

# Or clear all browser cache
# Chrome: Settings → Privacy → Clear browsing data
```

#### **Issue 2: Logo still shows old version**
**Solution:**
```bash
# Restart the dev server
cd frontend/dashboard
# Stop with Ctrl+C
npm start
```

#### **Issue 3: Script fails to copy files**
**Solution:**
```bash
# Check file permissions
# Windows: Right-click → Properties → Security
# Linux/Mac: chmod 644 branding/promptops-logo.png
```

#### **Issue 4: Logo appears distorted**
**Solution:**
- Ensure the logo is saved as PNG format
- Recommended size: 2322x1824px or similar square/circular aspect ratio
- The UI will auto-scale to required sizes

---

### ✅ Verification Checklist

After updating, verify:

- [ ] New logo saved to `branding/promptops-logo.png`
- [ ] Update script ran successfully
- [ ] All 3 logo files have same size/timestamp
- [ ] Frontend dev server restarted
- [ ] Browser cache cleared
- [ ] Logo appears on login page (100x100px)
- [ ] Logo appears in navigation bar (48x48px)
- [ ] Favicon updated in browser tab
- [ ] Logo looks sharp and not distorted

---

### 📊 Logo Specifications

**Current Logo Design:**
- **Style:** Camera aperture with letter "P" in center
- **Colors:** Deep purple (#3d3177) and white
- **Format:** PNG with transparent background
- **Dimensions:** 2322x1824px (original)
- **Aspect Ratio:** Roughly square/circular
- **File Size:** ~5MB (will be auto-optimized by browser)

**Display Sizes:**
- Login Page: 100x100px
- Navigation Bar: 48x48px
- Favicon: 32x32px (auto-scaled)
- README: 200-300px width

---

### 🚀 Quick Command Reference

```bash
# Update logo (Windows)
update_logo.bat

# Update logo (Linux/Mac)
./update_logo.sh

# Verify updates
ls -lh branding/promptops-logo.png assets/promptops-logo.png frontend/dashboard/public/promptops-logo.png

# Restart frontend
cd frontend/dashboard && npm start

# View in browser
http://localhost:3000
```

---

### 📞 Need Help?

If you encounter issues:
1. Check the backup files (`.backup` extension)
2. Review the `LOGO_CHECKLIST.md` document
3. Verify file paths match exactly
4. Ensure PNG format and reasonable file size

---

## 🎉 That's It!

Once you complete these steps, your new PromptOps logo will be live across:
- ✅ All documentation
- ✅ Login page
- ✅ Navigation bar
- ✅ Browser favicon
- ✅ Package manifests

The logo will automatically appear in all the right places because the code references remain unchanged - they all point to `/promptops-logo.png`.
