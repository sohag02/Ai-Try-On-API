from urllib.parse import urlparse
import os


def get_base_url(url: str) -> str:
    """
    Extract the base URL from a full URL.

    Parameters:
        url (str): The full URL to extract the base URL from.

    Returns:
        str: The base URL.
    """
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.netloc}"
    return base_url


if __name__ == '__main__':
    print(get_base_url('http://localhost:5000/upload'))


def move_to_result_folder(file_path, result_folder):
    file_name = os.path.basename(file_path)
    result_dir = os.path.join(os.path.dirname(file_path), result_folder)
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    result_file_path = os.path.join(result_dir, file_name)
    os.rename(file_path, result_file_path)
    return f'{result_folder}/{file_name}'
