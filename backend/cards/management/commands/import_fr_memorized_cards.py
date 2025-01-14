from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file = None

    def handle(self, *args, **kwargs):
        file_name = kwargs.get("inputfile", None)

        if not file_name:
            return "no input file specified"
        self.open_input_file(file_name)

        if not self.file:
            return f"the {file_name} file was not found"

    def open_input_file(self, path):
        try:
            self.file = open(path)
        except FileNotFoundError:
            pass

    def add_arguments(self, parser):
        parser.add_argument("--inputfile", type=str,
                            help="path to an input file")