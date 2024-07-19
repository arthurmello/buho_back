from markdown_pdf import MarkdownPdf, Section
from pdf2docx import Converter
import os
from docx import Document


def remove_section_breaks(doc_file_path):
    document = Document(doc_file_path)
    for i, section in enumerate(document.sections):
        if i > 0:  # Skip the first section
            section.start_type = 0  # Set section break type to continuous
    document.save(doc_file_path)


def generate_doc(section_contents, user_output_files_directory, filename):
    pdf = MarkdownPdf(toc_level=2)

    combined_content = "\n\n".join(section_contents)
    print(combined_content)
    pdf.add_section(Section(combined_content))

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

    remove_section_breaks(doc_file_path)
    return doc_file_path
