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


def download(url: str, dst: str, md5=None, sha1=None, sha512=None) -> None:
    """
    Downloads a file from a URL With Progressbar and saves it to the specified location.
    @param url: URL to download from
    @param dst: Destination to save the file to
    """
    os.makedirs(os.path.split(dst)[0], exist_ok=True)
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    if os.path.exists(dst) and os.path.getsize(dst) == total_size_in_bytes:
        print(f"{dst} already exists")
        return
    block_size = 1024
    progress_bar = tqdm(total=total_size_in_bytes, unit='B', unit_scale=True)

    have_hash = md5 is not None or sha1 is not None or sha512 is not None
    if have_hash:
        hash_mod = "sha512" if sha512 else "sha1" if sha1 else "md5"
        hash_value = sha512 if sha512 else sha1 if sha1 else md5
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
