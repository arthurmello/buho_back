from markdown_pdf import MarkdownPdf, Section
from pdf2docx import Converter
import os


def generate_doc(section_contents, user_output_files_directory, filename):
    pdf = MarkdownPdf(toc_level=2)
    for section_content in section_contents:
        pdf.add_section(Section(f"{section_content}"))

    if not os.path.exists(user_output_files_directory):
        os.makedirs(user_output_files_directory)

    pdf_file_path = os.path.join(user_output_files_directory, f"{filename}.pdf")
    if os.path.exists(pdf_file_path):
        os.remove(pdf_file_path)
    pdf.save(pdf_file_path)

    cv = Converter(pdf_file_path)
    doc_file_path = pdf_file_path.replace(".pdf", ".docx")
    cv.convert(doc_file_path)
    cv.close()
    return doc_file_path
