from django.conf import settings
from django.core.files.storage import FileSystemStorage


class CustomFileSystemStorage(FileSystemStorage):
    def __init__(self, location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL):
        location = 'upload/'  # 你想要的自定义存储位置
        super().__init__(location, base_url)
