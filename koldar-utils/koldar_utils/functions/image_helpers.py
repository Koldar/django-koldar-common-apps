import io

from PIL.Image import Image
from PIL import Image as Image_module

from typing import Union


def get_aspect_ratio(image: Image) -> float:
    """
    Aspect ratio of the image

    :param image: image to check
    :return: width/height
    """
    return (1.0*image.width)/image.height

def get_image(image: Union[bytes, io.BytesIO, str, Image, bytearray]) -> Image:
    """
    Get  the image

    :param content: stuff that is convertible into an image
    :return: image in memory
    """

    if isinstance(image, str):
        with open(image, mode="rb") as f:
            array = f.read()
            blob = io.BytesIO(array)
        image = Image_module.open(image)
        return image
    elif isinstance(image, Image):
        return image
    elif isinstance(image, io.BytesIO):
        image = Image_module.open(image)
        return image
    elif isinstance(image, bytes):
        blob = io.BytesIO(image)
        image = Image_module.open(blob)
        return image
    elif isinstance(image, bytearray):
        blob = io.BytesIO(image)
        image = Image_module.open(blob)
        return image
    else:
        raise TypeError(f"invalid image {type(image)}!")



def is_valid_image(image: Image) -> bool:
    """
    Check if the image the user has passed in indeed a valid image or something totally
    different

    :param image: image to check
    :return: true if this is an image, false otherwise
    """
    try:
        image.verify()
    except Exception:
        return False
    else:
        return True


def scale_image(image: Image, new_width: int, new_height: int, keep_aspect_ratio: bool = True, in_place: bool = True) -> Image:
    """
    Scale an image

    :param image: image to rescale
    :param new_width: the new width the image will have
    :param new_height: the new height the image will have
    :param keep_aspect_ratio: if set, we will try to preserve the aspect ratio (width/height) of the image. If set,
        the return value will not have the exact new_width/new_height yuo have input.
    :return a **copy** of the given image
    """
    if not in_place:
        image = image.copy()
    if keep_aspect_ratio:
        image.thumbnail(size=(new_width, new_height))
    else:
        image.resize((new_width, new_height))
    return image
