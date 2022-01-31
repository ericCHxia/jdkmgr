import ctypes
import requests
import os
import platform
from tqdm import tqdm
import zipfile
import hashlib

def is_admin() -> bool:
    """
    Check if the user is admin
    @return: True or False
    """
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


def create_link(src: str, dst: str) -> None:
    """
    Create a soft dir link
    @param src: source dir
    @param dst: target dir
    """
    if os.path.exists(dst):
        os.unlink(dst)
        return
    os.symlink(src, dst)


def download(url: str, dst: str, md5=None, sha1=None, sha256=None, sha512=None) -> None:
    """
    Download a file from a url and check the md5, sha1, sha256 and sha512 hashes if provided.
    If the file already exists and the hashes match, it will not download it again.
    If multiple hashes are provided, only one of them must match.
    The prority of the hashes is: md5, sha1, sha256, sha512.
    The prority is the same as the order of the arguments.
    If the prorty is lower than the provided hash, it will not be checked.
    The lowest priority is md5.
    The highest priority is sha512.
    @param url: URL to download the file from
    @param dst: Destination to download the file to
    @param md5: MD5 hash to check against
    @param sha1: SHA1 hash to check against
    @param sha512: SHA512 hash to check against
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


def extract_zip(src: str, dst: str, rename: str) -> None:
    """
    Extracts a zip file to the specified location and rename the dir.
    @param src: Source zip file
    @param dst: Destination to extract the zip file to
    @param rename: Rename the extracted dir to this name
    """
    os.makedirs(dst, exist_ok=True)
    with zipfile.ZipFile(src, 'r') as zip_ref:
        zip_ref.extractall(dst)
        dirname = zip_ref.namelist()[0]
    os.rename(os.path.join(dst, dirname[:-1]), os.path.join(dst, rename))


def get_avaliable_arches():
    """
    Get the avaliable arches
    @return: Set of avaliable arches
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
