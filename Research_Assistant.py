import sys
import re
import os
import pypandoc
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QFileDialog, 
                             QMessageBox, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy)
import PyPDF2
from openai import OpenAI

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    pdf_text = ""
    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    pdf_text += text
    except Exception as e:
        return f"Error reading PDF: {e}"
    return pdf_text

# Function to extract text from DOC/DOCX
def extract_text_from_doc(doc_path):
    doc_text = ""
    try:
        doc_text = pypandoc.convert_file(doc_path, 'plain')
    except Exception as e:
        return f"Error reading DOC/DOCX: {e}"
    return doc_text

# Function to extract text from TXT
def extract_text_from_txt(txt_path):
    txt_text = ""
    try:
        with open(txt_path, "r", encoding="utf-8") as file:
            txt_text = file.read()
    except Exception as e:
        return f"Error reading TXT: {e}"
    return txt_text

# Function to preprocess the text
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    text = re.sub(r'[^\w\s]', '', text)  # Remove non-alphanumeric characters except spaces
    return text

# Function to answer questions using OpenAI API
def answer_question(api_key, question, context):
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(model="gpt-4o-mini",  
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Context: {context}\nQuestion: {question}"}
        ],
        max_tokens=5000,
        temperature=0.6)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error with OpenAI API: {e}"

class DocumentChatbot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.preprocessed_text = ""
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Author: Pravash Bista')
        self.setGeometry(100, 100, 1200, 800)  # Size window appropriately

        # Apply dark mode stylesheet
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
                color: #E0E0E0;
                font-size: 24px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QLabel, QLineEdit, QPushButton, QTextEdit {
                font-size: 24px;
            }
            QPushButton {
                background-color: #444;
                color: #E0E0E0;
                border: none;
                padding: 10px;
                border-radius: 1px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QTextEdit {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        layout = QVBoxLayout()

        # API Key Input
        self.api_key_label = QLabel('OpenAI API Key:')
        self.api_key_entry = QLineEdit()
        self.api_key_entry.setEchoMode(QLineEdit.Password)

        # Document File Selection
        self.file_label = QLabel('Select Document:')
        self.file_path_label = QLabel('')
        self.load_file_button = QPushButton('Load Document')
        self.load_file_button.clicked.connect(self.load_file)

        # Chat Box
        self.chat_box = QTextEdit('Assistant: Hello, I\'m your Document Assistant. Please upload the document and ask your question.')
        self.chat_box.setReadOnly(True)
        self.chat_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Question Entry
        self.question_label = QLabel('Your Question:')
        self.question_entry = QLineEdit()
        self.question_entry.returnPressed.connect(self.get_answer)  # Bind Enter key to get_answer

        # Ask Button
        self.ask_button = QPushButton('Ask')
        self.ask_button.clicked.connect(self.get_answer)

        # Save Output Button
        self.save_output_button = QPushButton('Save Output')
        self.save_output_button.clicked.connect(self.save_output)

        # Layout setup
        api_layout = QHBoxLayout()
        api_layout.addWidget(self.api_key_label)
        api_layout.addWidget(self.api_key_entry)

        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_path_label)
        file_layout.addWidget(self.load_file_button)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.ask_button)
        buttons_layout.addWidget(self.save_output_button)

        layout.addLayout(api_layout)
        layout.addLayout(file_layout)
        layout.addWidget(self.chat_box)
        layout.addWidget(self.question_label)
        layout.addWidget(self.question_entry)
        layout.addLayout(buttons_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open Document', '', 'All Files (*);;PDF files (*.pdf);;DOC/DOCX files (*.doc *.docx);;Text files (*.txt)')
        if file_path:
            file_name = os.path.basename(file_path)
            self.file_path_label.setText(file_name)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.pdf']:
                text = extract_text_from_pdf(file_path)
            elif file_ext in ['.doc', '.docx']:
                text = extract_text_from_doc(file_path)
            elif file_ext in ['.txt']:
                text = extract_text_from_txt(file_path)
            else:
                QMessageBox.critical(self, 'Error', 'Unsupported file format.')
                return

            if "Error" in text:
                QMessageBox.critical(self, 'Error', text)
                return

            self.preprocessed_text = preprocess_text(text)
            QMessageBox.information(self, 'Info', 'Document loaded and text extracted.')

    def get_answer(self):
        api_key = self.api_key_entry.text()
        if not api_key:
            QMessageBox.critical(self, 'Error', 'Please enter your OpenAI API key.')
            return

        if not self.preprocessed_text:
            QMessageBox.critical(self, 'Error', 'Please load a document.')
            return

        question = self.question_entry.text()
        if not question:
            QMessageBox.critical(self, 'Error', 'Please enter a question.')
            return

        answer = answer_question(api_key, question, self.preprocessed_text)
        self.chat_box.append(f"You: {question}\nAssistant: {answer}\n")
        self.question_entry.clear()

    def save_output(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Output', '', 'Text files (*.txt)')
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(self.chat_box.toPlainText())
                QMessageBox.information(self, 'Info', 'Output saved successfully.')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f"Error saving file: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DocumentChatbot()
    ex.show()
    exit_code = app.quit()
    sys.exit(exit_code)
    #exit_code = app.exec_()
    #sys.exit(exit_code)