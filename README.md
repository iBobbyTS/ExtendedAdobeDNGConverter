# Extended Adobe DNG Converter

**Extended Adobe DNG Converter** is a graphical frontend built with [Flet](https://flet.dev/) for Adobe's official [DNG Converter](https://helpx.adobe.com/ca/camera-raw/using/adobe-dng-converter.html). It adds extended options such as JPEG XL compression, batch processing, flexible output naming, and intuitive settings for professional workflows.

> ⚠️ **Note:** Adobe DNG Converter (ADC) must be installed on your system for this tool to function. This is a frontend and does not replace or re-implement ADC.

---

## ✨ Features
- Everything from the official Adobe DNG Converter except "Extract Original RAW" function
- Choose between JPEG XL and JPEG compression
- Set compression level and quality
- Easier control on debayer, JPEG preview, Camera RAW version, DNG version, resolution  

---

## 📷 Screenshots
![Extended Adobe DNG Converter](/img/full_controls.jpg)

Multiple Language Support
![multiple language support](/img/2_language.jpg)

---

## 🖥️ Supported Platforms

- ✅ **Windows**
- ✅ **macOS**
- ❌ **Linux is not supported** (Adobe DNG Converter is not available on Linux)

---

## 📦 Download & Installation

Pre-built binaries for macOS and Windows will be available soon on the [Releases page](https://github.com/iBobbyTS/ExtendedAdobeDNGConverter/releases/tag/V1.0).

Alternatively, you can build from source:

### 🐍 Run from Source

```bash
# Clone the repo
cd ExtendedAdobeDNGConverter

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

---

## 🛠️ Build Instructions

### macOS

```bash
sh build_macos.sh
```

### Windows

```cmd
build_windows.cmd
```

---

## ⚠️ Required Software

You **must** have the official [Adobe DNG Converter](https://helpx.adobe.com/ca/camera-raw/using/adobe-dng-converter.html) installed on your system. This application acts as a frontend and communicates with ADC.

---

## 📄 License

Licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or pull requests.

---
