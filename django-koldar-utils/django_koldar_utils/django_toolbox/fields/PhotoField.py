import io
import math
import os
import uuid
from typing import Tuple, List, Dict, Optional, Union

from PIL.Image import Image
from datasize import DataSize
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models, transaction
from django.db.models.fields.files import ImageFieldFile
from django.core.files.images import ImageFile

from django_koldar_utils.django_toolbox.AbstractDjangoField import AbstractDjangoField
from django_koldar_utils.django_toolbox.validators import validators
from koldar_utils.functions import image_helpers, math_helpers, secrets_helper


class PhotoFieldFile(ImageFieldFile):

    def delete(self, save=True):
        super().delete(save=save)

    def save(self, name, content, save=True, *args, **kwargs) -> Image:
        """
        An upgraded version of ImageField.save().
        Save the image to the "uploaded_to" storage.

        The method can accept a pillow Image, a path or even a byte array.
        It will automatically delete the previous image and scale the image correctly.
        This method will persist the image to the storage as well.
        """

        image: Union[Image, str, bytes, bytearray] = content

        # get the image to set
        image = image_helpers.get_image(content)

        # save image last value
        new_profile_image = name
        previous_image = self.name
        # Check validators

        # this will delete the previous image in the storage
        if self.field.delete_previous_image:
            if previous_image != self.field.default or (previous_image == self.field.default and self.field.delete_default_if_commanded):
                self.delete(save=False)

        # invoke validators (if any)
        for v in self.field.validators:
            v(image)

        # after validation, we need to scale the picture, if needed
        w = math_helpers.bound(image.width, self.field.min_width, self.field.max_width)
        h = math_helpers.bound(image.height, self.field.min_height, self.field.max_height)
        if w != image.width or h != image.height:
            image = image_helpers.scale_image(image, w, h)

        # ok, now save the picture. Convert image into blob
        b = io.BytesIO()
        image.save(b, format=image.format)
        result = super().save(new_profile_image, File(b), *args, **kwargs)

        return result


class PhotoField(models.ImageField):
    """
    A picture that is automatically resized to a maximum value
    if the user sends a bigger picture. The behavior is independent on validators
    """

    attr_class = PhotoFieldFile
    description = "Represents a photo the user uploads"

    def __init__(self, *args, image_format: str = None, delete_previous_image:bool = True, delete_default_if_commanded: bool = False, min_width: int = 32, min_height: int = 32, max_width: int = 256, max_height: int = 256, **kwargs):
        self.min_width = min_width
        """
        minimum width a picture can have
        """
        self.min_height = min_height
        """
        maximum width a picture can have
        """
        self.max_width = max_width
        """
        minimum height a picture can have
        """
        self.max_height = max_height
        """
        maximum height a picture can have
        """
        self.delete_previous_image = delete_previous_image
        """
        If true, we will delete the image from the physical system
        """
        self.delete_default_if_commanded = delete_default_if_commanded
        """
        If delete_previous_image is set and the iamge is the defualt one,
        we will delete the default image. If this is not what you wnat, set ti to false
        """
        self.image_format: Optional[str] = image_format
        """
        The format of the images that we will store in the database.
        If None we will not perform any conversion betweent he uploaded pictures and the persisted ones
        """

        super().__init__(*args, **kwargs)

    def deconstruct(self) -> Tuple[str, str, List[any], Dict[str, any]]:
        name, path, args, kwargs = super().deconstruct()
        kwargs["min_width"] = self.min_width
        kwargs["min_height"] = self.min_height
        kwargs["max_width"] = self.max_width
        kwargs["max_height"] = self.max_height
        kwargs["delete_previous_image"] = self.delete_previous_image
        kwargs["delete_default_if_commanded"] = self.delete_default_if_commanded
        kwargs["image_format"] = self.image_format

        return name, path, args, kwargs

    def to_python(self, image) -> Optional[Image]:
        if image is None:
            return None

        if isinstance(image, bytes):
            im = Image.open(io.BytesIO(image))
        elif isinstance(image, str):
            im = Image.open(image.encode("utf8"))
        elif isinstance(image, Image):
            im = image
        else:
            raise TypeError(f"Cannot handle type {type(image)}!")

        return im


