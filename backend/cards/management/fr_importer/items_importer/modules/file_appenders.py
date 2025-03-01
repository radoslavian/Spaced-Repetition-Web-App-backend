import os.path
from django.core.files import File
from django.db.models import Model

from cards.models import Image


class FileAppender:
    DatabaseFileModel: Model
    file_field: str

    def __init__(self, file_path: str):
        self._file_instance = None
        self._file_path = file_path

    @property
    def file_instance(self):
        if self._file_instance is None:
            # get instance from the db or save?
            # calculate sha/md5 hash and use it to get the file instance
            # from the database
            self.save_file()
        return self._file_instance

    def save_file(self):
        with open(self._file_path, "rb") as opened_file:
            file = File(opened_file, name=self.file_name)
            self._create_file_instance(file)

    def _create_file_instance(self, file: File):
        parameter = {self.file_field: file}
        self._file_instance = self.DatabaseFileModel(**parameter)
        self._file_instance.save()

    @property
    def file_name(self) -> str:
        return os.path.basename(self._file_path)


class ImageFileAppender(FileAppender):
    DatabaseFileModel = Image
    file_field = "image"
