import os
from concurrent.futures import ThreadPoolExecutor
import ast
import re

from buho_back.services.storage.file_management import (
    load_json,
    get_summaries_directory,
    get_output_files_directory,
)
from buho_back.services.storage.vectordb import get_vectordb
from buho_back.services.file_generation.ppt import generate_presentation
from buho_back.services.file_generation.doc import generate_doc
from buho_back.services.file_generation.xlsx import generate_xlsx
from buho_back.utils import ChatModel, concatenate_chunks
from buho_back.config import INSTRUCTIONS_DIRECTORY

chat_model = ChatModel()


def create_general_context_for_output_file(summaries_directory):
    context = ""
    for filename in os.listdir(summaries_directory):
        if os.path.isfile(os.path.join(summaries_directory, filename)):
            with open(os.path.join(summaries_directory, filename), "r") as file:
                summary_content = file.read()
            context += f'"{filename}":\n"{summary_content}"\n\n'
            return context


def write_final_prompt_for_section_generation(info_for_prompt):
    prompt = f"""You are writing a {info_for_prompt["filename"]} for an in investment bank, who's working on a deal.
            Here's some context on this deal: {info_for_prompt["general_context"]}.
            Here's some additional info: {info_for_prompt["chunk_context"]}
            More specifically, write a {info_for_prompt["section_name"]} for this {info_for_prompt["filename"]}.
            A {info_for_prompt["section_name"]} {info_for_prompt["description"]}.
            No need to include a conclusion unless specifically requested.
            No need to number sections either
        """

    if info_for_prompt["extension"] == ".pptx":
        prompt += """
            Your output should follow the following format:
            [
            {"type": "title", "title": "Welcome to the Presentation", "subtitle": "An Overview"},
            {"type": "content", "title": "Main Points", "bullet_points": ["Point 1", "Point 2", "Point 3"]},
            {"type": "table", "title": "Data Table", "table_data": [
                ["Header 1", "Header 2", "Header 3"],
                ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
                ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"],
            ]},
            {"type": "content", "title": "Conclusion", "bullet_points": ["Summary 1", "Summary 2"]}
            ]
            this is just an example of the format (how to create titles, tables, etc.)
            the actual content of the presentation is up to you.
            you are free to choose which types slides to use for each part of the presentation.
            Answer just with that structured list, nothing else."""
    if info_for_prompt["extension"] == ".docx":
        prompt += """
            Your output can use simple markdown markers, such as "#" for the section header, and "##" for subsection headers.
            Do not include page breaks.
            """
    return prompt


def generate_sections(instructions, filename, vectordb, summaries_directory):
    sections = instructions["sections"]
    extension = instructions["extension"]

    info_for_prompt = {}
    for section_name in sections.keys():
        info_for_prompt[section_name] = {}
        info_for_prompt[section_name]["filename"] = filename
        info_for_prompt[section_name]["general_context"] = (
            create_general_context_for_output_file(summaries_directory)
        )
        info_for_prompt[section_name]["section_name"] = section_name

        description = sections.get(section_name)
        info_for_prompt[section_name]["description"] = description
        chunks = vectordb.retrieve_chunks(text=description)
        info_for_prompt[section_name]["chunk_context"] = concatenate_chunks(chunks)
        info_for_prompt[section_name]["extension"] = extension

    def generate_section_content(section_name):
        final_prompt = write_final_prompt_for_section_generation(
            info_for_prompt[section_name]
        )
        answer = chat_model.invoke(final_prompt)
        return answer

    with ThreadPoolExecutor(max_workers=8) as executor:
        section_contents = list(
            executor.map(generate_section_content, info_for_prompt.keys())
        )

    return section_contents


def extract_structured_data(instructions, summaries_directory):
    pre_prompt_path = os.path.join(INSTRUCTIONS_DIRECTORY, instructions["pre_prompt"])
    if os.path.isfile(pre_prompt_path):
        with open(pre_prompt_path, "r") as file:
            pre_prompt = file.read()

    context = create_general_context_for_output_file(summaries_directory)
    prompt = pre_prompt + "\n\n" + context
    answer = chat_model.invoke(prompt)
    pattern = r"\{[^}]*\}"
    clean_answer = re.findall(pattern, answer)[0]
    structured_data = ast.literal_eval(clean_answer)

    return structured_data


def generate_file(filename, user, deal, user_parameters):
    summaries_directory = get_summaries_directory(user, deal)
    output_files_directory = get_output_files_directory(user, deal)
    vectordb = get_vectordb(user, deal)
    instructions = load_json(os.path.join(INSTRUCTIONS_DIRECTORY, f"{filename}.json"))
    extension = instructions["extension"]

    if extension == ".docx":
        section_contents = generate_sections(
            instructions, filename, vectordb, summaries_directory
        )
        output_file_path = generate_doc(
            section_contents, output_files_directory, filename
        )

    elif extension == ".pptx":
        section_contents = generate_sections(
            instructions, filename, vectordb, summaries_directory
        )
        content = ast.literal_eval(section_contents[0])
        output_file_path = generate_presentation(
            content, output_files_directory, filename
        )

    elif extension == ".xlsx":
        structured_data = extract_structured_data(instructions, summaries_directory)
        output_file_path = generate_xlsx(
            structured_data, output_files_directory, filename, user_parameters
        )

    return output_file_path
