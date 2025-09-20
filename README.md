# WhatsApp Desktop Blur for Windows 11 🔒

A privacy-focused application that creates a blur overlay on WhatsApp Desktop to prevent others from seeing your messages and contacts. Features **automatic startup** and **fast response**.

## ✨ Features

- 🔒 **Privacy Blur**: Blurred overlay to hide your WhatsApp content
- 🖱️ **Hover to Reveal**: Mouse hover temporarily removes blur
- ⌨️ **Quick Toggle**: `Ctrl+Alt+Q` keyboard shortcut
- 🚀 **Auto-Startup**: Starts automatically when Windows boots
- 🎯 **Smart Detection**: Automatically detects and follows WhatsApp window
- ⚡ **Fast Response**: 0.2s monitoring for instant blur activation
- 🧹 **Clean Console**: No deprecated warnings or spam logs
- 📍 **System Tray**: Easy access and settings from notification area

## 🔧 Requirements

- **Windows 11** (or Windows 10)
- **Python 3.9+** (recommended: Python 3.13)
- **WhatsApp Desktop** application
- **Git** (for cloning repository)

## 🚀 Installation

### 📦 **Method 1: Full Installation (Recommended)**

1. **Clone the repository:**

   ```bash
   git clone https://github.com/YonatanAriel/Whatsapp-blur.git
   cd Whatsapp-blur
   ```

2. **Run the installer (as Administrator):**

   ```bash
   # Right-click PowerShell and "Run as administrator"
   python install_whatsapp_blur.py
   ```

   This will:

   - ✅ Install all dependencies
   - ✅ Set up the app in `C:\Users\Public\WhatsApp Blur\`
   - ✅ Create desktop shortcut
   - ✅ Configure auto-startup

### ⚡ **Method 2: Quick Manual Setup**

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**

   ```bash
   python whatsapp_blur_final.py
   ```

3. **Set up auto-startup (optional):**
   ```bash
   python setup_auto_startup.py
   ```

### 🖥️ **Method 3: Second Laptop Deployment**

Perfect for setting up on additional computers:

1. **Clone and deploy in one command:**

   ```bash
   git clone https://github.com/YonatanAriel/Whatsapp-blur.git
   cd Whatsapp-blur
   python deploy_second_laptop.py
   ```

   This automatically:

   - ✅ Installs all dependencies
   - ✅ Sets up the application
   - ✅ Configures auto-startup
   - ✅ Tests the installation

## 🎮 Usage

### **Starting the App**

- **Auto-Start**: Automatically starts silently when Windows boots (if configured)
- **Manual Start**: Double-click desktop shortcut or run from system tray
- **From Code**: `pythonw whatsapp_blur.py` in the installation directory (runs silently)

### **Using the Blur**

1. **Open WhatsApp Desktop** - Blur automatically applies
2. **Toggle**: Press `Ctrl+Alt+Q` to turn blur on/off
3. **Hover**: Move mouse over blur to temporarily reveal content
4. **Settings**: Right-click system tray icon for options

### **System Tray Access**

The app runs in your **System Tray** (notification area) - this is the area in the bottom-right corner of your Windows taskbar, next to the clock and volume icons. Look for a small blur icon there.

- **Right-click** the tray icon for:
  - Toggle blur on/off
  - Settings and configuration
  - Exit application

**Note**: If you don't see the icon immediately, click the small arrow (^) in the system tray to expand hidden icons.

## 🔐 Permissions Required

For the app to work properly, you need to grant **screenshot permissions**:

1. **Open Windows Settings** (Windows key + I)
2. **Go to Privacy & Security** → **App permissions** → **Screenshots**
3. **Turn ON** "Allow apps to take screenshots"

Without this permission, the blur overlay won't appear.

## ⌨️ Keyboard Shortcuts

| Shortcut     | Action             |
| ------------ | ------------------ |
| `Ctrl+Alt+Q` | Toggle blur on/off |

## 🔧 Configuration

The app includes several configuration options:

- **Enable/Disable Blur**: Complete blur control
- **Hover Mode**: Toggle hover-to-reveal functionality
- **Auto-Startup**: Configure Windows boot startup

## 📋 Technical Details

### **Blur Technology**

- Uses **tkinter overlay** for blur effect
- **Fast window detection** and following
- **Efficient image processing** for smooth performance

### **Performance Optimizations**

- **0.2s monitoring intervals** for fast response
- **Throttled logging** to prevent console spam
- **Efficient memory management** with proper cleanup
- **Smart window detection** prioritizing active WhatsApp instances

### **Dependencies (Auto-installed)**

```
pywin32==311          # Windows API access
pystray==0.19.4       # System tray functionality
Pillow>=11.3.0        # Image processing (latest)
keyboard==0.13.5      # Global keyboard shortcuts
psutil==5.9.6         # Process monitoring
numpy>=2.3.0          # Advanced glass effect processing
```

## 🛠️ Troubleshooting

### **App won't start**

```bash
# Check Python version (need 3.9+)
python --version

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Run as administrator
# Right-click PowerShell → "Run as administrator"
python install_whatsapp_blur.py
```

### **Blur doesn't appear**

- **Check permissions**: Ensure Windows screenshot permissions are enabled (see Permissions Required section above)
- Ensure WhatsApp Desktop is running and visible
- Press `Ctrl+Alt+Q` to toggle
- Check system tray icon status (look for blur icon in notification area)

### **Auto-startup not working**

```bash
# Reconfigure auto-startup
python setup_auto_startup.py

# Or check Task Manager > Startup tab
# Look for "WhatsApp Blur" entry
```

## 🔐 Privacy & Security

This application:

- ✅ **100% Local**: Runs entirely on your machine
- ✅ **No Data Transmission**: Never sends data anywhere
- ✅ **No Message Access**: Only creates visual overlays
- ✅ **Open Source**: Fully auditable code
- ✅ **No Network**: Doesn't require internet connection
- ✅ **Windows Only**: Designed specifically for Windows security model

## 🚀 What's New in Latest Version

- ⚡ **Faster response** - 0.2s monitoring intervals
- 🧹 **Clean console** - No deprecated PIL warnings or spam logs
- 📱 **Auto-startup** - Boots with Windows automatically
- 🖥️ **Easy deployment** - One-script setup for multiple laptops
- 🔧 **Better permissions** - Clear Windows settings guidance

## 📦 File Structure

```
Whatsapp-blur/
├── whatsapp_blur_final.py      # Main application (latest)
├── install_whatsapp_blur.py    # Full installer script
├── setup_auto_startup.py       # Auto-startup configuration
├── deploy_second_laptop.py     # Second laptop deployment
├── auto_update.py              # Update deployment script
├── create_shortcut.py          # Desktop shortcut creator
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly on Windows 11
5. Submit a pull request

## 📞 Support

If you encounter issues:

1. **Check this README** - Most common issues are covered
2. **Update to latest version** - Many issues are already fixed
3. **Run as administrator** - Solves most permission issues
4. **Open an issue** with:
   - Windows version
   - Python version
   - Error messages/screenshots
   - Steps to reproduce

## 📄 License

This project is open source. Feel free to modify and distribute.

---

**🎯 Perfect for**: Privacy-conscious users, shared computers, public spaces, screen sharing, presentations

**✨ Experience the difference**: Fast, reliable privacy protection with automatic startup and easy system tray access!
