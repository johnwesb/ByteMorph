from flask import Flask, request, send_file, render_template
import fitz  # PyMuPDF
import io
import zipfile
import os
import sys
import tempfile
import textwrap
from pdf2docx import Converter
from docx2pdf import convert as convert_docx

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'txt'}

def allowed_file(filename, allowed_types=None):
    if not allowed_types:
        allowed_types = ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_types

def get_safe_name(filename):
    # Fix: Keeps the original file name, casing, and spaces exactly as uploaded
    name = filename.rsplit('.', 1)[0]
    for c in r'\/:*?"<>|':  # Strip only illegal Windows path characters
        name = name.replace(c, '')
    return name.strip() if name.strip() else "bytemorph_document"

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
    except Exception: return "Failed to process document", 500

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
    except Exception: return "Failed to merge documents", 500

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
    except Exception: return "Failed to convert images", 500

@app.route('/api/extract-text', methods=['POST'])
def extract_text():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text_list = [page.get_text("text") for page in doc]
        doc.close()
        text = "\n\n".join(text_list)
        
        # Check if the PDF was just full of images with no digital text
        if not text.strip():
            text = "--- INFO: No digital text structures found on these pages. ---\n\nThis file is likely composed entirely of scanned images or rasterized graphics (like a screenshot). You will need OCR (Optical Character Recognition) software to extract text from pictures."
            
        buffer = io.BytesIO(text.encode('utf-8'))
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='text/plain', as_attachment=True, download_name=f"{safe_name}_extracted.txt")
    except Exception as e: return f"Failed to extract text data: {str(e)}", 500

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
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_split_pg{start+1}-{end+1}.pdf")
    except Exception: return "Failed to split document", 500

@app.route('/api/rotate-pdf', methods=['POST'])
def rotate_pdf():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400
    try:
        angle = int(request.form.get('angle', 90))
        mode = request.form.get('mode', 'all')
        page_range = request.form.get('range', '')
        
        doc = fitz.open(stream=file.read(), filetype="pdf")
        total = len(doc)
        target_pages = []

        if mode == 'all': target_pages = list(range(total))
        elif mode == 'odd': target_pages = [i for i in range(total) if (i + 1) % 2 != 0]
        elif mode == 'even': target_pages = [i for i in range(total) if (i + 1) % 2 == 0]
        elif mode == 'range' and page_range:
            for element in page_range.split(','):
                if '-' in element:
                    start, end = map(int, element.split('-'))
                    target_pages.extend(range(start - 1, end))
                else:
                    target_pages.append(int(element) - 1)

        for p_idx in target_pages:
            if 0 <= p_idx < total:
                doc[p_idx].set_rotation((doc[p_idx].rotation + angle) % 360)
            
        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()
        buffer.seek(0)
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_rotated.pdf")
    except Exception as e: return f"Failed to rotate document: {str(e)}", 500

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
    except Exception: return "Failed to protect document", 500

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
    except Exception: return "Failed to unlock document", 500

@app.route('/api/add-watermark', methods=['POST'])
def add_watermark():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400
    try:
        text = request.form.get('watermark_text', 'CONFIDENTIAL')
        size = int(request.form.get('size', 45))
        opacity = float(request.form.get('opacity', 0.25))
        
        doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in doc:
            rect = page.rect
            point = fitz.Point(rect.width / 4, rect.height / 2)
            # Safe text insertion across all PyMuPDF versions
            page.insert_text(point, text, fontsize=size, color=(0.8, 0.2, 0.2), fill_opacity=opacity, rotate=45, fontname="helv-b")
            
        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()
        buffer.seek(0)
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_watermarked.pdf")
    except Exception as e:
        print("Watermark Error:", str(e))
        return f"Failed to apply watermark matrix: {str(e)}", 500

@app.route('/api/compress-pdf', methods=['POST'])
def compress_pdf():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400
    try:
        level = int(request.form.get('level', 2))
        doc = fitz.open(stream=file.read(), filetype="pdf")
        buffer = io.BytesIO()
        
        # Lossless structural compression parameters
        if level == 1:
            doc.save(buffer, deflate=True, garbage=1)
        elif level == 2:
            doc.save(buffer, deflate=True, garbage=3, clean=True)
        else:
            doc.save(buffer, deflate=True, garbage=4, clean=True, linear=True)
            
        doc.close()
        buffer.seek(0)
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_compressed.pdf")
    except Exception as e:
        return f"Failed to compress document: {str(e)}", 500

@app.route('/api/pdf-to-word', methods=['POST'])
def pdf_to_word():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'pdf'}): return "Invalid file", 400
    tmp_pdf, tmp_docx = None, None
    try:
        fd1, tmp_pdf = tempfile.mkstemp(suffix=".pdf")
        os.close(fd1)
        fd2, tmp_docx = tempfile.mkstemp(suffix=".docx")
        os.close(fd2)

        file.save(tmp_pdf)
        cv = Converter(tmp_pdf)
        cv.convert(tmp_docx, start=0, end=None)
        cv.close()
        
        with open(tmp_docx, "rb") as f: buffer = io.BytesIO(f.read())
        buffer.seek(0)
        safe_name = get_safe_name(file.filename)
        return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', as_attachment=True, download_name=f"{safe_name}_converted.docx")
    except Exception as e: return "Internal engine layout translation failure", 500
    finally:
        if tmp_pdf and os.path.exists(tmp_pdf): os.remove(tmp_pdf)
        if tmp_docx and os.path.exists(tmp_docx): os.remove(tmp_docx)

@app.route('/api/doc-to-pdf', methods=['POST'])
def doc_to_pdf():
    file = request.files.get('file')
    if not file or not allowed_file(file.filename, {'docx', 'txt'}): return "Invalid file type", 400
    ext = file.filename.rsplit('.', 1)[1].lower()
    safe_name = get_safe_name(file.filename)

    if ext == 'txt':
        try:
            text = file.read().decode('utf-8', errors='ignore')
            doc = fitz.open()
            page = doc.new_page()
            y_text = 50
            for paragraph in text.split('\n'):
                lines = textwrap.wrap(paragraph, width=90)
                if not lines: y_text += 15
                for line in lines:
                    if y_text > 780:
                        page = doc.new_page()
                        y_text = 50
                    page.insert_text((50, y_text), line, fontsize=11, fontname="helv")
                    y_text += 15
            buffer = io.BytesIO()
            doc.save(buffer)
            doc.close()
            buffer.seek(0)
            return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_converted.pdf")
        except Exception: return "Failed to process text layout stream", 500

    elif ext == 'docx':
        tmp_docx, tmp_pdf = None, None
        try:
            if sys.platform == "win32":
                import pythoncom
                pythoncom.CoInitialize()

            fd1, tmp_docx = tempfile.mkstemp(suffix=".docx")
            os.close(fd1)
            fd2, tmp_pdf = tempfile.mkstemp(suffix=".pdf")
            os.close(fd2)

            file.save(tmp_docx)
            convert_docx(os.path.abspath(tmp_docx), os.path.abspath(tmp_pdf))
            
            with open(tmp_pdf, "rb") as f: buffer = io.BytesIO(f.read())
            buffer.seek(0)
            return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"{safe_name}_converted.pdf")
        except Exception:
            return "MS Word is NOT installed on this PC. Local DOCX to PDF conversion requires Microsoft Office to be installed locally to work.", 500
        finally:
            if sys.platform == "win32":
                try: import pythoncom; pythoncom.CoUninitialize()
                except: pass
            if tmp_docx and os.path.exists(tmp_docx): os.remove(tmp_docx)
            if tmp_pdf and os.path.exists(tmp_pdf): os.remove(tmp_pdf)

if __name__ == '__main__':
    from waitress import serve
    import webbrowser
    import threading
    import time

    def start_server():
        serve(app, host="127.0.0.1", port=5000)

    threading.Thread(target=start_server, daemon=True).start()
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:5000")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: pass