# WhatsApp Desktop Blur for Windows 11

A privacy-focused application that blurs WhatsApp Desktop content to prevent others from seeing your messages and contacts on your laptop. The content is revealed when you hover your mouse over the blurred area.

## Features

- 🔒 **Privacy Protection**: Automatically blurs WhatsApp Desktop content
- 🖱️ **Hover to Reveal**: Mouse hover temporarily removes blur
- ⌨️ **Keyboard Shortcut**: Quick toggle with `Ctrl+Shift+B`
- 🎯 **System Tray**: Easy access from system tray icon
- ⚙️ **Configurable**: Toggle blur and hover modes
- 🚀 **Auto-Detection**: Automatically detects WhatsApp Desktop window

## Requirements

- Windows 11 (or Windows 10)
- Python 3.7 or higher
- WhatsApp Desktop application

## Installation

### Option 1: Quick Setup
1. Download or clone this repository
2. Double-click `run.bat` to automatically install dependencies and start the application

### Option 2: Manual Setup
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python whatsapp_blur.py
   ```

### Option 3: Setup Script
1. Run the setup script to install dependencies and create a desktop shortcut:
   ```bash
   python setup.py
   ```

## Usage

1. **Start the Application**: Run using any of the installation methods above
2. **Open WhatsApp Desktop**: The blur effect will automatically apply
3. **Toggle Blur**: Press `Ctrl+Shift+B` to toggle blur on/off
4. **Hover to Reveal**: Move your mouse over the blurred area to temporarily see content
5. **System Tray**: Right-click the tray icon for quick settings

## Keyboard Shortcuts

- `Ctrl+Shift+B`: Toggle blur on/off

## Configuration

Access settings through:
- Right-click the system tray icon → "Settings"
- Or through the tray menu options

### Available Settings:
- **Enable/Disable Blur**: Turn the entire blur feature on/off
- **Hover Mode**: Toggle hover-to-reveal functionality
- **View Instructions**: See usage instructions and shortcuts

## How It Works

1. The application monitors for WhatsApp Desktop windows
2. When detected, it creates a semi-transparent overlay with blur effect
3. Mouse hover events temporarily hide the overlay
4. The overlay automatically repositions when WhatsApp window moves
5. Global keyboard shortcut allows quick toggling

## Troubleshooting

### Application won't start
- Ensure Python 3.7+ is installed
- Run `pip install -r requirements.txt` manually
- Check Windows permissions for Python applications

### Blur doesn't appear
- Make sure WhatsApp Desktop is running
- Try toggling with `Ctrl+Shift+B`
- Check system tray icon and settings

### Keyboard shortcut not working
- Ensure no other application is using `Ctrl+Shift+B`
- Run the application as administrator if needed
- Check Windows keyboard shortcut conflicts

## Dependencies

- `pywin32`: Windows API access
- `pystray`: System tray functionality  
- `Pillow`: Image processing
- `keyboard`: Global keyboard shortcuts
- `psutil`: Process monitoring

## Privacy & Security

This application:
- ✅ Runs locally on your machine
- ✅ Does not transmit any data
- ✅ Does not access WhatsApp messages
- ✅ Only creates visual overlay effects
- ✅ Open source and auditable

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

If you encounter issues:
1. Check the troubleshooting section
2. Verify your Python and Windows versions
3. Open an issue with detailed error information

---

**Note**: This application is designed specifically for Windows 11/10 and requires WhatsApp Desktop to be installed.