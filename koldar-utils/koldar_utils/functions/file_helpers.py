import os
from typing import Iterable, Callable


def get_all_files_st(directory: str, match: Callable[[str, str, bool], bool]) -> Iterable[str]:
    """
    List all the content of a folder satisfying a given criterion

    :param directory: root dir to consider. it won't be included in the output
    :param match: callabel that checks if an entity should be included in the output.
        - absolute path of the directory containing the entity
        - base name of the file/directory
        - true if it is a file, false if it is a directory
    """

    directory = os.path.abspath(directory)
    for folder, subfolders, files in os.walk(directory):
        for subfolder in subfolders:
            if match(os.path.abspath(folder), subfolder, False):
                yield os.path.abspath(os.path.join(directory, folder, subfolder))
        for file in files:
            if match(os.path.abspath(folder), file, True):
                yield os.path.abspath(os.path.join(directory, folder, file))


def get_all_files_ending_with(directory: str, extension: str) -> Iterable[str]:
    """
    Yields all the files in directory (direct and indirect() that ends with the specified extension
    """
    def match(parent_folder: str, file: str, is_file: bool) -> bool:
        if not is_file:
            return False
        return file.endswith("." + extension)

    yield from get_all_files_st(directory, match)
