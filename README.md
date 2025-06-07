# Udder Hygiene Data Automation Project

## Project Structure
```
udder-hygiene-automation/
├── README.md
├── requirements.txt
├── index.html                    # Web demo interface
├── ocr_automation_backend.py     # OCR processing and Flask API
├── automated_workflow_script.py  # Automated workflow scheduler
├── setup.py                      # Setup script
├── config.json                   # Configuration file
├── uploads/                      # Temporary upload folder
├── exports/                      # Export output folder
├── processed/                    # Archived processed files
├── errors/                       # Failed processing files
└── logs/                         # Log files
```

## Installation Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Tesseract OCR installed on your system

#### Installing Tesseract OCR:

**Windows:**
```bash
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
# Or use Chocolatey:
choco install tesseract
```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install tesseract-ocr
```

### 2. Project Setup

1. Create a new directory for the project:
```bash
mkdir udder-hygiene-automation
cd udder-hygiene-automation
```

2. Create the required directories:
```bash
mkdir uploads exports processed errors logs
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration

Create a `config.json` file with your settings:

```json
{
  "watch_folder": "./watch",
  "processed_folder": "./processed",
  "output_folder": "./exports",
  "error_folder": "./errors",
  "email_settings": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender": "your-email@gmail.com",
    "password": "your-app-password",
    "recipients": ["recipient1@email.com", "recipient2@email.com"]
  },
  "schedule_time": "08:00",
  "enable_realtime": true
}
```

## Running the Application

### Option 1: Web Demo
1. Open `index.html` in a web browser
2. Use the "Load Demo Data" button to see it in action
3. Or drag and drop your own scanned documents

### Option 2: Flask API Server
```bash
python ocr_automation_backend.py
```
The API will be available at `http://localhost:5000`

### Option 3: Automated Workflow
```bash
python automated_workflow_script.py
```
This will start the automated monitoring and scheduled processing.

## Requirements.txt
```
opencv-python==4.8.1.78
pytesseract==0.3.10
Pillow==10.1.0
PyMuPDF==1.23.8
pandas==2.1.4
openpyxl==3.1.2
Flask==3.0.0
Flask-CORS==4.0.0
numpy==1.26.2
schedule==1.2.0
watchdog==3.0.0
```

## Testing the System

1. **Test OCR Processing**:
   ```python
   from ocr_automation_backend import UdderHygieneOCR
   
   processor = UdderHygieneOCR()
   data = processor.process_file("sample_scan.pdf")
   print(data)
   ```

2. **Test Web API**:
   ```bash
   # Start the Flask server
   python ocr_automation_backend.py
   
   # In another terminal, test the demo endpoint
   curl http://localhost:5000/api/demo
   ```

3. **Test Automation**:
   - Place a sample PDF/image in the watch folder
   - The system should automatically process it

## Sample Data Format

The OCR system expects scanned documents with data in this format:
```
Date: 2025-03-26
Farm: Sunnyside Farm

Group A
85, 92, 88

Group B  
78, 81, 79

Group C
91, 89, 93
```