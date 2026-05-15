from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import io
import zipfile
import os
import tempfile
from pdf2docx import Converter
from docx2pdf import convert as convert_docx

app = Flask(__name__)

# --- SECURITY HELPERS ---
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx'}

def allowed_file(filename, allowed_types=None):
    if not allowed_types:
        allowed_types = ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_types

def get_safe_name(filename):
    safe = secure_filename(filename.rsplit('.', 1)[0])
    return safe if safe else "bytemorph_document"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/pdf-to-image', methods=['POST'])
def pdf_to_image():
    if 'file' not in request.files: return "No file part", 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400

    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i in range(len(doc)):
                img_bytes = doc.load_page(i).get_pixmap(dpi=150).tobytes("png")
                zip_file.writestr(f"page_{i + 1}.png", img_bytes)
        doc.close() 
        zip_buffer.seek(0)
        
        safe_name = get_safe_name(file.filename)
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name=f"{safe_name}_images.zip")
    except Exception:
        return "Failed to process document", 500

@app.route('/api/merge-pdfs', methods=['POST'])
def merge_pdfs():
    files = request.files.getlist('files')
    if not files or files[0].filename == '': return "No files", 400

    try:
        merged_doc = fitz.open()
        for file in files:
            if allowed_file(file.filename, {'pdf'}):
                doc = fitz.open(stream=file.read(), filetype="pdf")
                merged_doc.insert_pdf(doc)
                doc.close()
        
        buffer = io.BytesIO(merged_doc.tobytes())
        merged_doc.close()
        
        safe_name = get_safe_name(files[0].filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_merged.pdf")
    except Exception:
        return "Failed to merge documents", 500

@app.route('/api/images-to-pdf', methods=['POST'])
def images_to_pdf():
    files = request.files.getlist('files')
    if not files or files[0].filename == '': return "No files", 400

    try:
        pdf_doc = fitz.open()
        for file in files:
            if allowed_file(file.filename, {'png', 'jpg', 'jpeg'}):
                ext = file.filename.rsplit('.', 1)[1].lower()
                img_doc = fitz.open(stream=file.read(), filetype=ext)
                pdf_bytes = img_doc.convert_to_pdf()
                pdf_doc.insert_pdf(fitz.open("pdf", pdf_bytes))
                img_doc.close()
        
        buffer = io.BytesIO(pdf_doc.tobytes())
        pdf_doc.close()
        
        safe_name = get_safe_name(files[0].filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_compiled.pdf")
    except Exception:
        return "Failed to convert images", 500

@app.route('/api/extract-text', methods=['POST'])
def extract_text():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400

    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "\n\n".join([page.get_text() for page in doc])
        doc.close()
        
        buffer = io.BytesIO(text.encode('utf-8'))
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='text/plain', as_attachment=True, download_name=f"{safe_name}_text.txt")
    except Exception:
        return "Failed to extract text", 500

@app.route('/api/split-pdf', methods=['POST'])
def split_pdf():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400

    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        start = max(0, int(request.form.get('start', 1)) - 1)
        end = max(0, int(request.form.get('end', 1)) - 1)
        if end < start: end = start
        end = min(end, len(doc) - 1)
        
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=end)
        
        buffer = io.BytesIO(new_doc.tobytes())
        doc.close()
        new_doc.close()
        
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_split_{start+1}to{end+1}.pdf")
    except Exception:
        return "Failed to split document", 500

@app.route('/api/rotate-pdf', methods=['POST'])
def rotate_pdf():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400

    try:
        angle = int(request.form.get('angle', 90))
        doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in doc:
            page.set_rotation(angle)
            
        buffer = io.BytesIO(doc.tobytes())
        doc.close()
        
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_rotated.pdf")
    except Exception:
        return "Failed to rotate document", 500

@app.route('/api/protect-pdf', methods=['POST'])
def protect_pdf():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400

    try:
        password = request.form.get('password', '')
        doc = fitz.open(stream=file.read(), filetype="pdf")
        buffer = io.BytesIO()
        doc.save(buffer, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password)
        doc.close()
        buffer.seek(0)
        
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_protected.pdf")
    except Exception:
        return "Failed to protect document", 500

@app.route('/api/unlock-pdf', methods=['POST'])
def unlock_pdf():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400

    try:
        password = request.form.get('password', '')
        doc = fitz.open(stream=file.read(), filetype="pdf")
        if not doc.authenticate(password):
            doc.close()
            return "Incorrect password", 401
            
        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()
        buffer.seek(0)
        
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_unlocked.pdf")
    except Exception:
        return "Failed to unlock document", 500

@app.route('/api/add-watermark', methods=['POST'])
def add_watermark():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400

    try:
        watermark_text = request.form.get('watermark_text', 'CONFIDENTIAL')
        doc = fitz.open(stream=file.read(), filetype="pdf")
        
        for page in doc:
            rect = page.rect
            p = fitz.Point(rect.width / 4, rect.height / 2)
            page.insert_text(p, watermark_text, fontsize=60, color=(0.8, 0.2, 0.2), fill_opacity=0.3, rotate=-45)
            
        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()
        buffer.seek(0)
        
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_watermarked.pdf")
    except Exception:
        return "Failed to add watermark", 500

@app.route('/api/pdf-to-word', methods=['POST'])
def pdf_to_word():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400

    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            file.save(tmp_pdf.name)
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
                cv = Converter(tmp_pdf.name)
                cv.convert(tmp_docx.name)
                cv.close()
                
                with open(tmp_docx.name, "rb") as f:
                    buffer = io.BytesIO(f.read())
                    
        os.remove(tmp_pdf.name)
        os.remove(tmp_docx.name)
        
        buffer.seek(0)
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', as_attachment=True, download_name=f"{safe_name}_converted.docx")
    except Exception:
        return "Failed to convert to Word", 500

@app.route('/api/word-to-pdf', methods=['POST'])
def word_to_pdf():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'docx'}): return "Invalid file", 400

    try:
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            file.save(tmp_docx.name)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                convert_docx(os.path.abspath(tmp_docx.name), os.path.abspath(tmp_pdf.name))
                
                with open(tmp_pdf.name, "rb") as f:
                    buffer = io.BytesIO(f.read())
                    
        os.remove(tmp_docx.name)
        os.remove(tmp_pdf.name)
        
        buffer.seek(0)
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_converted.pdf")
    except Exception as e:
        return "Failed to convert Word. Ensure Microsoft Word is installed on your PC.", 500

if __name__ == '__main__':
    from waitress import serve
    import webview
    import threading
    import time

    def start_server():
        # Waitress serves the Flask app silently in the background
        serve(app, host="127.0.0.1", port=5000)

    # 1. Start the backend server in a separate thread
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    # 2. Give the server a split second to boot up
    time.sleep(1)

    # 3. Launch the native desktop window (No URL bar, no tabs!)
    # text_select=False makes it feel like an app instead of a webpage
    webview.create_window('ByteMorph', 'http://127.0.0.1:5000', width=1280, height=850, text_select=False)
    webview.start()