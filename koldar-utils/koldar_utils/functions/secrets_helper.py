import secrets


def get_random_alphanum_str(length: int) -> str:
    """
    Create a random string of alphanumeric characters, cryptographically secure

    :param length: length of the string to build
    :return: string
    """
    return ''.join(map(lambda x: secrets.choice("qwertyuiopasdfghjklzxcvbnm1234567890"), range(length)))

