import os

def get_resources_folder() -> str:
    return "src/resources/"

def get_resource_filename(name: str) -> str:
    return os.path.join(get_resources_folder(), name)