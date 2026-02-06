# 🚀 Git Repository Setup Guide for iCapture

## ✅ What's Ready

- ✅ `.gitignore` created (excludes data, logs, cache)
- ✅ `README.md` exists (comprehensive documentation)
- ✅ Project code organized

---

## 📋 Step-by-Step Guide

### **Step 1: Install Git** (One-time)

#### Windows:
1. Download Git: https://git-scm.com/download/win
2. Run installer → **Use default settings** (just click Next)
3. Restart PowerShell/CMD after installation

#### Verify Installation:
```powershell
git --version
# Should show: git version 2.x.x
```

---

### **Step 2: Configure Git** (One-time)

```powershell
# Set your name (will appear on commits)
git config --global user.name "Your Name"

# Set your email
git config --global user.email "your.email@example.com"

# Verify
git config --list
```

---

### **Step 3: Create GitHub Account** (If you don't have one)

1. Go to: https://github.com/signup
2. Create free account
3. Verify email

---

### **Step 4: Initialize Git in Project**

```powershell
#Navigate to project
cd C:\Users\ASUS\IcaptureSystemV2

# Initialize Git repository
git init

# Check status (should see many "untracked files")
git status
```

---

### **Step 5: First Commit** (Save all code)

```powershell
# Add all files (respects .gitignore)
git add .

# Create first commit
git commit -m "Initial commit - iCapture Helmet Detection System"

# Verify commit
git log
```

---

### **Step 6: Create GitHub Repository**

1. Go to: https://github.com/new

2. Fill in details:
   - **Repository name:** `icapture-system`
   - **Description:** `No-Contact Helmet Violation Detection System for Odiongan`
   - **Visibility:** 
     - ✅ **Private** (recommended - protects your code)
     - OR Public (if you want it visible)
   - **DO NOT** check: ❌ Add README
   - **DO NOT** check: ❌ Add .gitignore
   - **DO NOT** check: ❌ Choose license

3. Click **"Create repository"**

4. **COPY the URL shown**, example:
   ```
   https://github.com/YOUR_USERNAME/icapture-system.git
   ```

---

### **Step 7: Link Local Code to GitHub**

```powershell
# Link to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/icapture-system.git

# Verify link
git remote -v

# Should show:
# origin  https://github.com/YOUR_USERNAME/icapture-system.git (fetch)
# origin  https://github.com/YOUR_USERNAME/icapture-system.git (push)
```

---

### **Step 8: Push Code to GitHub** 🚀

```powershell
# Rename branch to 'main'
git branch -M main

# Push all code to GitHub
git push -u origin main
```

**First time:** GitHub will ask for login
- Enter your GitHub username
- Enter your GitHub password OR Personal Access Token

---

### **Step 9: Verify on GitHub**

1. Go to: `https://github.com/YOUR_USERNAME/icapture-system`
2. You should see all your code!
3. **Share this URL** with professors, employers, etc.

---

## 🎯 **Your Repository URL Will Be:**

```
https://github.com/YOUR_USERNAME/icapture-system
```

Example:
```
https://github.com/JuanDelacruz/icapture-system
```

---

## 🔄 **Future Updates** (After initial setup)

Whenever you make changes:

```powershell
# 1. Check what changed
git status

# 2. Add changes
git add .

# 3. Commit with message
git commit -m "Added new feature: XYZ"

# 4. Push to GitHub
git push
```

---

## ⚠️ **IMPORTANT: Authentication**

### If GitHub asks for password repeatedly:

**Option 1: Personal Access Token (Recommended)**

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token
3. Select scopes: `repo` (full control)
4. Copy token
5. Use token as password when pushing

**Option 2: GitHub Desktop (Easiest)**

1. Download: https://desktop.github.com/
2. Sign in with GitHub
3. Clone repository
4. Use GUI to commit/push

---

## ✅ **Verification Checklist**

After setup, verify:

- [ ] Git installed: `git --version` works
- [ ] Git configured: `git config --list` shows name/email
- [ ] GitHub account created
- [ ] Repository created on GitHub
- [ ] Local repository initialized: `git status` works
- [ ] First commit made: `git log` shows commit
- [ ] Remote linked: `git remote -v` shows GitHub URL
- [ ] Code pushed: GitHub shows your files
- [ ] Repository URL shareable

---

## 🆘 **Troubleshooting**

### Error: "git is not recognized"
```powershell
# Git not installed or not in PATH
# Solution: Reinstall Git, restart PowerShell
```

### Error: "permission denied"
```powershell
# Wrong credentials
# Solution: Use Personal Access Token instead of password
```

### Error: "failed to push"
```powershell
# Remote URL wrong
# Solution:
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/icapture-system.git
git push -u origin main
```

### Error: "repository not found"
```powershell
# Repository doesn't exist or URL wrong
# Solution: Double-check GitHub repository exists and URL is correct
```

---

## 🎓 **Benefits for Your Thesis**

✅ **Backup:** Code safe even if laptop breaks  
✅ **Version Control:** Track all changes  
✅ **Collaboration:** Work with teammates  
✅ **Portfolio:** Show employers your work  
✅ **Defense:** Prove you built it (commit history)  
✅ **Deployment:** Easy to deploy from GitHub  

---

## 📧 **Need Help?**

If stuck, message me the error and I'll help troubleshoot!

**Common resources:**
- Git Basics: https://git-scm.com/doc
- GitHub Guides: https://guides.github.com/
- Personal Access Tokens: https://docs.github.com/en/authentication

---

**Ready to push your code to the cloud! 🚀**
