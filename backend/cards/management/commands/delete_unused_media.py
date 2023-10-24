import os
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db.models import Q
from django.conf import settings
from django.db.models import FileField

# reused from:
# https://www.algotech.solutions/blog/python/deleting-unused-django-media-files/


class Command(BaseCommand):
    help = "This command deletes all media files from the MEDIA_ROOT directory"
    "which are no longer referenced by any of the models from installed_apps"
    def handle(self, *args, **options):
        all_models = apps.get_models()
        physical_files = set()
        db_files = set()
        # Get all files from the database
        for model in all_models:
            file_fields = []
            filters = Q()
            for f_ in model._meta.fields:
                if isinstance(f_, FileField):
                    file_fields.append(f_.name)
                    is_null = {'{}__isnull'.format(f_.name): True}
                    is_empty = {'{}__exact'.format(f_.name): ''}
                    filters &= Q(**is_null) | Q(**is_empty)
            # only retrieve the models which have non-empty,
            # non-null file fields
            if file_fields:
                files = model.objects.exclude(filters).values_list(
                    *file_fields, flat=True).distinct()
                db_files.update(files)
        # Get all files from the MEDIA_ROOT, recursively
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if media_root is not None:
            for relative_root, dirs, files in os.walk(media_root):
                for file_ in files:
                    # Compute the relative file path to the media directory,
                    # so it can be compared to the values from the db
                    relative_file = os.path.join(os.path.relpath(
                        relative_root, media_root), file_)
                    physical_files.add(relative_file)
        # Compute the difference and delete those files
        deletables = physical_files - db_files
        if deletables:
            for file_ in deletables:
                os.remove(os.path.join(media_root, file_))
            # Bottom-up - delete all empty folders
            for relative_root, dirs, files in os.walk(
                    media_root, topdown=False):
                for dir_ in dirs:
                    if not os.listdir(os.path.join(relative_root, dir_)):
                        os.rmdir(os.path.join(relative_root, dir_))

