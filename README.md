# Floor Plan Checker

A web application that analyzes floor plan images using Google Gemini Vision Language Model API and provides actionable feedback on accessibility (ADA compliance), space efficiency, and general best practices.

## Features

- Upload floor plan images via web interface
- AI-powered analysis using Google Gemini VLM
- Feedback on:
  - **Accessibility**: ADA compliance, wheelchair access, door widths, clearances
  - **Space Efficiency**: Layout optimization, room proportions, wasted space
  - **Best Practices**: Room flow, natural light, functionality

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory:
```
GEMINI_API_KEY=your_api_key_here
```

3. Run the application:
```bash
python app.py
```

4. Open your browser to `http://localhost:5000`

## Usage

1. Upload a floor plan image (JPG, PNG, GIF, BMP, or WebP)
2. Click "Analyze Floor Plan"
3. Review the bullet-point feedback provided

## Requirements

- Python 3.8+
- Google Gemini API key
- Flask web framework

