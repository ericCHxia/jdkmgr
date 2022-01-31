import ctypes
import requests
import os
import platform
from tqdm import tqdm
import zipfile
import hashlib
import tarfile


def is_admin() -> bool:
    """Check if the user is admin
    
    Example:
    >>> is_admin()

    Returns:
        bool: True if the user is admin, False otherwise.
    """
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


def create_link(src: str, dst: str) -> None:
    """Create a soft dir link
    
    In windows, it needs admin rights to create a soft link.
    
    Example:
    >>> create_link("/path/to/file", "/path/to/link")           # Linux
    >>> create_link("C:\\path\\to\\file", "C:\\path\\to\\link") # Windows

    Args:
        src (str): Source file
        dst (str): Destination file

    Raises:
        Exception: If the link already exists
    """
    if os.path.exists(dst):
        os.unlink(dst)
        return
    os.symlink(src, dst)


def download(url: str, dst: str, md5=None, sha1=None, sha256=None, sha512=None) -> None:
    """Download a file from a url and check the md5, sha1, sha256 and sha512 hashes if provided.

    If the file already exists and the hashes match, it will not download it again.
    If multiple hashes are provided, only one of them must match.
    The prority of the hashes is: md5, sha1, sha256, sha512.
    The prority is the same as the order of the arguments.
    If the prorty is lower than the provided hash, it will not be checked.
    The lowest priority is md5.
    The highest priority is sha512.
    
    Example:
    >>> download("https://example.com/file.zip", "file.zip", md5="d577273ff885c3f84dadb8578bb41399")
    >>> download("https://example.com/file.zip", "file.zip")

    Args:
        url (str): The url to download the file from.
        dst (str): The destination to download the file to.
        md5 (str, optional): The md5 hash of the file.
        sha1 (str, optional): The sha1 hash of the file.
        sha256 (str, optional): The sha256 hash of the file.
        sha512 (str, optional): The sha512 hash of the file.

    Raises:
        Exception: If the file already exists and the hashes don't match.
    """
    os.makedirs(os.path.split(dst)[0], exist_ok=True)
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    if os.path.exists(dst) and os.path.getsize(dst) == total_size_in_bytes:
        print(f"{dst} already exists")
        return
    block_size = 1024
    progress_bar = tqdm(total=total_size_in_bytes, unit='B', unit_scale=True)

    have_hash = md5 is not None or sha1 is not None or sha256 is not None or sha512 is not None
    if have_hash:
        hash_mod = "sha512" if sha512 is not None else "sha256" if sha256 is not None else "sha1" if sha1 is not None else "md5" if md5 is not None else None
        hash_value = sha512 if sha512 is not None else sha256 if sha256 is not None else sha1 if sha1 is not None else md5 if md5 is not None else None
        hash_func: hashlib.HASH = getattr(hashlib, hash_mod)()

    with open(dst, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
            hash_func.update(data)
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes and (not have_hash or hash_func.hexdigest() != hash_value):
        raise Exception(f"Download of {url} failed")


def extract_zip(src: str, dst: str, rename: str = None) -> None:
    """Extracts a zip file to the specified location.

    If rename is provided, it will rename the extracted directory to the specified name.

    Example:
    >>> extract_zip("file.zip", "path/to/extract/to")
    >>> extract_zip("file.zip", "path/to/extract/to", "new_name")

    Args:
        src (str): Source zip file
        dst (str): Destination to extract the zip file to
        rename (str, optional): Rename the extracted directory to this name
    
    Raises:
        Exception: If the new directory already exists when rename is provided or if the zip file is corrupted
    """
    os.makedirs(dst, exist_ok=True)
    with zipfile.ZipFile(src, 'r') as zip_ref:
        zip_ref.extractall(dst)
        dirname = zip_ref.namelist()[0]
    if rename is not None:
        os.rename(os.path.join(dst, dirname[:-1]), os.path.join(dst, rename))


def extract_targz(src: str, dst: str, rename: str = None) -> None:
    """Extracts a tar.gz file to the specified location.

    If rename is provided, it will rename the extracted directory to the specified name.
    
    Example:
    >>> extract_targz("file.tar.gz", "path/to/extract/to")
    >>> extract_targz("file.tar.gz", "path/to/extract/to", "new_name")

    Args:
        src (str): Source tar.gz file
        dst (str): Destination to extract the tar.gz file to
        rename (str, optional): Rename the extracted directory to this name
    
    Raises:
        Exception: If the new directory already exists when rename is provided or if the tar.gz file is corrupted
    """
    os.makedirs(dst, exist_ok=True)
    with tarfile.open(src, 'r:gz') as tar_ref:
        tar_ref.extractall(dst)
        dirname = tar_ref.getnames()[0]
    if rename is not None:
        os.rename(os.path.join(dst, dirname[:-1]), os.path.join(dst, rename))


def get_avaliable_arches():
    """Get the avaliable arches
    
    Example:
    >>> get_avaliable_arches()

    Returns:
        set: The avaliable arches
    
    Raises:
        Exception: If the architecture is not supported
    """
    if platform.machine() == "i386":
        return {"x86", "i686", "i386", "i586", "i486"}
    elif platform.machine() == "AMD64":
        return {"x86_64", "x86", "i386", "amd64"}
    elif platform.machine() == "aarch64":
        return {"aarch64", "armv7l", "armv6l", "armv8l", "armv8b", "armv8l", "armv8", "armv7", "armv6", "armv5", "armv4", "armv3", "armv2", "armv1", "arm"}
    elif platform.machine() == "armv7l":
        return {"armv7l", "armv6l", "armv8l", "armv8b", "armv8l", "armv8", "armv7", "armv6", "armv5", "armv4", "armv3", "armv2", "armv1", "arm"}
    else:
        raise Exception(f"Unknown architecture {platform.machine()}")
