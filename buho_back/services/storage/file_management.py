import os
import shutil
import json
from pathlib import Path
from buho_back.config import DATA_DIRECTORY
from pathlib import Path


def clear_path(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"{path} cleared!")
        elif os.path.isfile(path):
            os.remove(path)
            print(f"{path} file deleted!")


def dump_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w+") as f:
        json.dump(data, f)


def load_json(path):
    try:
        with open(path) as file:
            result = json.load(file)
    except Exception as e:
        print(f"Can't load json from {path}. Error: {e}")
        result = []
    return result


def get_vectordb_directory(user, deal):
    return os.path.join(f"{DATA_DIRECTORY}", user, deal, "vectordb")


def get_summaries_directory(user, deal):
    return os.path.join(f"{DATA_DIRECTORY}", user, deal, "summaries")


def get_input_files_directory(user, deal):
    return os.path.join(f"{DATA_DIRECTORY}", user, deal, "input_files")


def get_output_files_directory(user, deal):
    return os.path.join(f"{DATA_DIRECTORY}", user, deal, "output_files")


def get_chat_history_file(user, deal):
    return os.path.join(f"{DATA_DIRECTORY}", user, deal, "chat_history.json")


def get_qa_tracker_directory(user, deal):
    return os.path.join(f"{DATA_DIRECTORY}", user, deal, "qa_tracker")


def get_deals_for_user(user):
    try:
        user_directory = os.path.join(f"{DATA_DIRECTORY}", user)
        sub_directories = os.listdir(user_directory)
        print(sub_directories)
        deals = [
            entry
            for entry in sub_directories
            if os.path.isdir(os.path.join(user_directory, entry))
        ]
    except Exception as e:
        print(f"Failed to get deals for user {user}. Error: {e}")
        deals = []
    return deals


def create_deal_for_user(user, deal):
    try:
        deal_directory = os.path.join(f"{DATA_DIRECTORY}", user, deal)
        os.makedirs(deal_directory)
        message = "Deal created successfully!"
    except Exception as e:
        message = f"Failed to crete deal {deal} for user {user}. Error: {e}"
    return message


def delete_deal_for_user(user, deal):
    try:
        deal_directory = os.path.join(f"{DATA_DIRECTORY}", user, deal)
        clear_path(deal_directory)
        message = "Deal deleted successfully!"
    except Exception as e:
        message = f"Failed to delete deal {deal} for user {user}. Error: {e}"
    return message


def create_folder_for_user(user, deal, folder_path):
    try:
        directory = os.path.join(get_input_files_directory(user, deal), folder_path)
        os.makedirs(directory)
        message = "Folder created successfully!"
    except Exception as e:
        message = f"Failed to create folder {folder_path} for user {user}. Error: {e}"
    return message


def move_file_or_folder(origin, destination, user, deal):
    try:
        origin_path = os.path.join(get_input_files_directory(user, deal), origin)
        destination_path = os.path.join(
            get_input_files_directory(user, deal), destination
        )
        shutil.move(str(origin_path), str(destination_path))
        message = "Folder moved successfully!"
    except Exception as e:
        message = f"Failed to move {origin} to {destination}. Error: {e}"
    print(message)
    return message


def list_files_and_folders(user, deal):
    def build_items(directory, base_directory, current_path):
        folder_items = []
        file_items = []
        for entry in os.scandir(directory):
            relative_path = os.path.join(current_path, entry.name)
            if entry.is_dir():
                folder_items.append(
                    {
                        "name": entry.name,
                        "type": "folder",
                        "path": relative_path,
                        "items": build_items(entry.path, base_directory, relative_path),
                    }
                )
            elif entry.is_file():
                file_items.append(
                    {"name": entry.name, "type": "file", "path": relative_path}
                )
        return folder_items + file_items

    deal_directory = get_input_files_directory(user, deal)
    return build_items(deal_directory, deal_directory, "")


def delete_object_for_user(user, deal, obj):
    try:
        input_files_directory = get_input_files_directory(user, deal)
        obj_path = os.path.join(input_files_directory, obj)
        print(obj_path)
        clear_path(obj_path)
        message = "Object deleted successfully!"
    except Exception as e:
        message = (
            f"Failed to delete object {obj} for user {user}, deal {deal}. Error: {e}"
        )
    return message


def list_files(path):
    items = []

    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = os.path.join(root, name)
            items.append(os.path.relpath(file_path, path))

    return items
