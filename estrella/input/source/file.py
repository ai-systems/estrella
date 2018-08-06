from typing import List

from estrella.input.source import SourceReader

import os
import glob


def files_in_folder(path, ending=""):
    return [f for f in glob.iglob(os.path.join(path, "**", "*" + ending)) if not os.path.isdir(f)]


class MultipleFileReader(SourceReader):
    def __init__(self, ending=""):
        super().__init__()
        self.ending = ending

    def load(self, location, ending=None, **kwargs) -> List[str]:
        return [f.read() for f in files_in_folder(location, self.ending)]


class SingleFileReader(SourceReader):
    def load(self, location, **kwargs) -> List[str]:
        with open(location, "r") as f:
            return [f.read()]


class FileReader(SingleFileReader, MultipleFileReader):
    def load(self, location, **kwargs):
        if os.path.isdir(location):
            return MultipleFileReader.load(self, location, self.ending)
        else:
            return SingleFileReader.load(self, location)
