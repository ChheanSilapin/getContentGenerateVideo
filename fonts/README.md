# Font Bundling for Video Generator

## 📥 How to Bundle Cascadia Code Font

To include Cascadia Code font with your installer distribution:

### 1. Download Cascadia Code
1. Visit: https://github.com/microsoft/cascadia-code/releases
2. Download the latest `CascadiaCode-*.zip` file
3. Extract the ZIP file

### 2. Copy Font Files
Copy these files from the `ttf` folder to this `fonts` directory:
- `CascadiaCode-Regular.ttf`
- `CascadiaCode-Bold.ttf`
- `CascadiaCode-Italic.ttf`
- `CascadiaCode-BoldItalic.ttf`

### 3. Rebuild Installer
After placing the font files here, rebuild the installer using:
```bash
python build_installer.py
```

## 🔤 Font Fallback System

The application includes an intelligent font fallback system:

1. **Bundled Fonts**: Uses fonts from this directory if available
2. **System Fonts**: Falls back to best available system font:
   - Windows: Consolas → Courier New → Arial
   - macOS: Monaco → Menlo → Arial  
   - Linux: DejaVu Sans Mono → Liberation Mono → Arial

## 📁 Directory Structure
```
fonts/
├── README.md                 (this file)
├── CascadiaCode-Regular.ttf  (place here)
├── CascadiaCode-Bold.ttf     (place here)
├── CascadiaCode-Italic.ttf   (place here)
└── CascadiaCode-BoldItalic.ttf (place here)
```

## ✅ Verification

To test font detection:
```bash
python utils/font_manager.py
```

This will show:
- Available fonts on your system
- Selected font for the application
- Download instructions if Cascadia Code is missing

## 🚀 Alternative Fonts

If you prefer different fonts, you can place any TTF/OTF files here:
- **Fira Code**: https://github.com/tonsky/FiraCode
- **JetBrains Mono**: https://github.com/JetBrains/JetBrainsMono
- **Source Code Pro**: https://github.com/adobe-fonts/source-code-pro

The font manager will automatically detect and use the best available option.

## 📋 License Notes

- Cascadia Code: SIL Open Font License 1.1
- Make sure to comply with font licenses when distributing
- System fonts (Consolas, Arial, etc.) are already licensed for distribution

---

**Note**: Even without bundled fonts, the application will work perfectly with system fonts! 