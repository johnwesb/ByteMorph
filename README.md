# 🗄️ ByteMorph

**ByteMorph** is a 100% offline, privacy-first web application for processing, securing, and manipulating PDF documents. 

Inspired by premium SaaS products, ByteMorph brings enterprise-grade document tools directly to your local machine. Because it runs entirely on a local Python Flask server, **your files never leave your device.** There are no cloud uploads, no data collection, and no file size limits—guaranteeing absolute security and privacy for your sensitive documents.

## ✨ Features

ByteMorph currently includes 11 powerful document utilities:

* 🖼️ **PDF to Image:** Convert document pages into high-quality PNGs (packaged in a ZIP).
* 📚 **Merge PDFs:** Combine multiple PDFs with visual drag-and-drop page rendering.
* 📸 **Images to PDF:** Turn a collection of images (JPG/PNG) into a single PDF.
* 📝 **Extract Text:** Pull raw text data out of any PDF document.
* ✂️ **Split PDF:** Extract specific page ranges into a new document.
* 🔄 **Rotate PDF:** Fix page orientation (90°, 180°, 270°).
* 🔒 **Protect PDF:** Encrypt documents with a secure password (AES-256).
* 🔓 **Unlock PDF:** Remove password protection from existing PDFs.
* 💧 **Add Watermark:** Stamp custom watermark text diagonally across every page.
* 📄 **PDF to Word:** Convert PDF layouts into editable Microsoft Word (`.docx`) files.
* 📕 **Word to PDF:** Convert Word documents into PDFs *(Requires MS Office installed locally)*.

## 🚀 Key Highlights

* **100% Local Processing:** Runs on your `localhost`. Zero network requests are made with your files.
* **In-Memory Architecture:** Files are processed directly in RAM using `io.BytesIO` and Python's `tempfile` module. No junk files are permanently saved to your hard drive.
* **Modern UI/UX:** Built with Tailwind CSS, featuring asynchronous file processing, drag-and-drop upload zones, and dynamic multi-step loading screens.
* **Visual Workspaces:** Integrated with Mozilla's `PDF.js` to render actual document pages directly in the browser for visual sorting and merging.

## 🛠️ Tech Stack

**Backend:**
* Python 3.x
* [Flask](https://flask.palletsprojects.com/) (Web Framework)
* [PyMuPDF / fitz](https://pymupdf.readthedocs.io/) (High-performance PDF engine)
* [Waitress](https://docs.pylonsproject.org/projects/waitress/en/latest/) (Production-grade WSGI server)
* `pdf2docx` & `docx2pdf` (Office suite conversions)

**Frontend:**
* HTML5 / Vanilla JavaScript
* [Tailwind CSS](https://tailwindcss.com/) (Styling)
* [SortableJS](https://sortablejs.github.io/Sortable/) (Drag-and-drop physics)
* [PDF.js](https://mozilla.github.io/pdf.js/) (Client-side PDF rendering)
* FontAwesome (Icons)

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/ByteMorph.git](https://github.com/yourusername/ByteMorph.git)
   cd ByteMorph
   ```

2. **Install the required Python dependencies:**
   It is recommended to use a virtual environment, but you can install directly via pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the local server:**
   ```bash
   python app.py
   ```

4. **Open the application:**
   Open your favorite web browser and navigate to:
   ```text
   http://localhost:5000
   ```

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).