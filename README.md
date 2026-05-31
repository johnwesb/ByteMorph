# ByteMorph

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

ByteMorph is a secure, offline-first document processing application. It provides a local web interface for manipulating PDF files without relying on cloud services, ensuring absolute data privacy. Built with Python, Flask, and PyMuPDF, it offers native-level performance within a standard web browser.

## Features

ByteMorph provides 11 distinct document processing utilities:

* **Format Conversion:** PDF to Image (PNG archive), Images to PDF, PDF to Word (DOCX), and Word to PDF.
* **Document Manipulation:** Merge multiple PDFs, Split specific page ranges, and Rotate page orientation.
* **Security:** Apply AES-256 password encryption, Unlock protected documents, and apply custom Watermarks.
* **Data Extraction:** Extract raw text data from PDF structures.

## Architecture

The application operates entirely on `localhost`, preventing any external network requests during file processing.

* **Backend:** Python, Flask, Waitress (WSGI production server).
* **Core Processing:** PyMuPDF (`fitz`) for PDF manipulation, `pdf2docx` and `docx2pdf` for Office conversions.
* **Frontend:** HTML5, Tailwind CSS, vanilla JavaScript, and Mozilla's `PDF.js` for client-side document rendering.

## Installation for Developers

To run ByteMorph from the source code, ensure you have Python 3.10 or higher installed.

1. Clone the repository:
git clone https://github.com/yourusername/ByteMorph.git
cd ByteMorph

2. Create and activate a virtual environment (Recommended):
python -m venv venv
source venv/bin/activate

3. Install dependencies:
pip install -r requirements.txt

4. Run the application:
python app.py

The application will automatically launch in your default web browser at http://127.0.0.1:5000.

## Building the Executable (Windows)

To package ByteMorph into a standalone `.exe` for distribution without requiring Python installation on the host machine, use PyInstaller.

pip install pyinstaller
pyinstaller --name ByteMorph --windowed --add-data "templates;templates" --hidden-import docx2pdf --hidden-import pdf2docx --hidden-import waitress app.py

The compiled output will be located in the `dist/ByteMorph/` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.