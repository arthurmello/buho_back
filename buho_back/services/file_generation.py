import os
from concurrent.futures import ThreadPoolExecutor
from markdown_pdf import MarkdownPdf, Section
from pdf2docx import Converter
from buho_back.services.storage import load_json, get_vector_store
from buho_back.services.retriever import retrieve_chunks
from buho_back.services.context import concatenate_chunks
from buho_back.config import settings
from buho_back.utils import chat_model

summaries_directory = settings.SUMMARIES_DIRECTORY
output_files_directory = settings.OUTPUT_FILES_DIRECTORY


def create_general_context_for_output_file(user_summaries_directory):
    context = ""
    for filename in os.listdir(user_summaries_directory):
        if os.path.isfile(os.path.join(user_summaries_directory, filename)):
            with open(os.path.join(user_summaries_directory, filename), "r") as file:
                summary_content = file.read()
            context += f'"{filename}":\n"{summary_content}"\n\n'
            return context


def write_final_prompt_for_section_generation(info_for_prompt):
    prompt = f"""You are writing a {info_for_prompt["filename"]} for an in investment bank, who's working on a deal.
            Here's some context on this deal: {info_for_prompt["general_context"]}.
            Here's some additional info: {info_for_prompt["chunk_context"]}
            More specifically, write a {info_for_prompt["section_name"]} for this {info_for_prompt["filename"]}.
            A {info_for_prompt["section_name"]} {info_for_prompt["description"]}.
        """
    return prompt


def generate_file(filename, user_id):
    user_summaries_directory = os.path.join(summaries_directory, user_id)
    user_output_files_directory = os.path.join(output_files_directory, user_id)
    user_vector_store = get_vector_store(user_id)
    template = load_json(f"buho_back/templates/{filename}.json")

    info_for_prompt = {}
    for section_name in template.keys():
        info_for_prompt[section_name] = {}
        info_for_prompt[section_name]["filename"] = filename
        info_for_prompt[section_name]["general_context"] = (
            create_general_context_for_output_file(user_summaries_directory)
        )
        info_for_prompt[section_name]["section_name"] = section_name

        description = template.get(section_name)
        info_for_prompt[section_name]["description"] = description
        chunks = retrieve_chunks(user_vector_store, description)
        info_for_prompt[section_name]["chunk_context"] = concatenate_chunks(chunks)

    def generate_section_content(section_name):
        final_prompt = write_final_prompt_for_section_generation(
            info_for_prompt[section_name]
        )
        answer = chat_model.invoke(final_prompt).content
        return answer

    with ThreadPoolExecutor(max_workers=8) as executor:
        section_contents = list(
            executor.map(generate_section_content, info_for_prompt.keys())
        )

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
