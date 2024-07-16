import os
from concurrent.futures import ThreadPoolExecutor

from buho_back.services.storage import load_json, get_vector_store
from buho_back.services.retriever import retrieve_chunks
from buho_back.services.context import concatenate_chunks
from buho_back.services.file_generation.ppt import generate_presentation
from buho_back.services.file_generation.doc import generate_doc
from buho_back.config import settings
from buho_back.utils import chat_model
import ast

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
            No need to include a conclusion unless specifically requested.
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
    return prompt


def generate_file(filename, user_id):
    user_summaries_directory = os.path.join(summaries_directory, user_id)
    user_output_files_directory = os.path.join(output_files_directory, user_id)
    user_vector_store = get_vector_store(user_id)
    instructions = load_json(f"buho_back/instructions/{filename}.json")
    sections = instructions["sections"]
    extension = instructions["extension"]
    info_for_prompt = {}
    for section_name in sections.keys():
        info_for_prompt[section_name] = {}
        info_for_prompt[section_name]["filename"] = filename
        info_for_prompt[section_name]["general_context"] = (
            create_general_context_for_output_file(user_summaries_directory)
        )
        info_for_prompt[section_name]["section_name"] = section_name

        description = sections.get(section_name)
        info_for_prompt[section_name]["description"] = description
        chunks = retrieve_chunks(user_vector_store, description)
        info_for_prompt[section_name]["chunk_context"] = concatenate_chunks(chunks)
        info_for_prompt[section_name]["extension"] = extension

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

    if extension == ".docx":
        output_file_path = generate_doc(
            section_contents, user_output_files_directory, filename
        )

    elif extension == ".pptx":
        content = ast.literal_eval(section_contents[0])
        output_file_path = generate_presentation(
            content, user_output_files_directory, filename
        )

    return output_file_path
