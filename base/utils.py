from PIL import Image, ImageOps
from io import BytesIO


def work_directory_path(instance, filename):
    return 'works/{0}/{1}'.format(instance.customer, filename)


def photo_resizer(image: Image, size: int) -> BytesIO:
    output = BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.thumbnail((size, size))
    image = ImageOps.exif_transpose(image)
    image.save(output, format='JPEG', quality=100)
    output.seek(0)
    return output
