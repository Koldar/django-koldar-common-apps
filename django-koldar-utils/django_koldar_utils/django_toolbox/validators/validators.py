import abc

from django.core.exceptions import ValidationError


def validate_image_min_width(value_to_check, min_width: int = 32):
    if not (value_to_check.width >= min_width):
        raise ValidationError(f"image has width {value_to_check.width}, which is less than the minimum one {min_width}!")


def validate_image_max_width(value_to_check, max_width: int = 512):
    if not (value_to_check.width <= max_width):
        raise ValidationError(f"image has width {value_to_check.width}, which is greater than the maximum one {max_width}!")


def validate_image_min_height(value_to_check, min_height: int = 32):
    if not (value_to_check.height >= min_height):
        raise ValidationError(f"image has height {value_to_check.width}, which is less than the minimum one {min_height}!")


def validate_image_max_height(value_to_check, max_height: int = 512):
    if not (value_to_check.height <= max_height):
        raise ValidationError(f"image has height {value_to_check.width}, which is greater than the maximum one {max_height}!")


def validate_image_aspect_ratio(value_to_check, threshold: float = 0.8):
    if value_to_check.width > value_to_check.height:
        ratio = value_to_check.height / value_to_check.width
    else:
        ratio = value_to_check.width / value_to_check.height
    if not (ratio >= threshold):
        raise ValidationError(f"image has an aspect ratio {ratio}, which is less than the maximum one {threshold}!")


def validate_image_should_be_horizontal(value_to_check):
    ratio = value_to_check.width/value_to_check.height
    if not (ratio >= 1):
        raise ValidationError(f"image should be an horizontal one, but the aspect ratio is {ratio}!")


def validate_image_should_be_vertical(value_to_check):
    ratio = value_to_check.width/value_to_check.height
    if not (ratio <= 1):
        raise ValidationError(f"image should be an vertical one, but the aspect ratio is {ratio}!")
