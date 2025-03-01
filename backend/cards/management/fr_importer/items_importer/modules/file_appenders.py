import os.path
from os import PathLike

from django.core.files import File
from django.db import IntegrityError, transaction
from django.db.models import Model

from cards.models import Image
from cards.utils.helpers import get_file_hash


class FileAppender:
    DatabaseFileModel: Model
    file_field: str
    hash_field: str

    def __init__(self, file_path: str):
        self._file_instance = None
        self._file_path = self.validate_path(file_path)

    @staticmethod
    def validate_path(file_path: str | PathLike):
        if os.path.exists(file_path):
            return file_path
        else:
            raise FileNotFoundError

    @property
    def file_instance(self):
        if self._file_instance is None:
            try:
                with transaction.atomic():
                    self.save_file()
            except IntegrityError:
                self._file_instance = self._get_file_by_hash()
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

    def _get_file_by_hash(self) -> Model:
        with open(self._file_path, "rb") as file:
            file_hash_digest = get_file_hash(File(file))
        search_parameter = {self.hash_field: file_hash_digest}
        return self.DatabaseFileModel.objects.get(**search_parameter)


class ImageFileAppender(FileAppender):
    DatabaseFileModel = Image
    file_field = "image"
    hash_field = "sha1_digest"
