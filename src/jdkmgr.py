import sys
import os
import ctypes
import requests
from tqdm import tqdm
import zipfile
import json
import platform
import argparse

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


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


def download(url: str, dst: str) -> None:
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
    with open(dst, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")


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


class JDKManager:

    def __init__(self, jdk_path=None) -> None:
        """
        JDK Manager class
        @param jdk_path: JDK path
        """
        self.jdk_path = jdk_path

        # load JDK sources
        if os.path.exists("source/jdk.json"):
            with open("source/jdk.json") as f:
                self.jdk_sources = json.load(f)
        else:
            raise FileNotFoundError("No such file: source/jdk.json")

        self.indstalled = {}
        self.indstalled_hash = set()
        if not os.path.exists("install"):
            os.makedirs("install")
        
        for i in os.listdir("install"):
            if i.startswith("jdk_"):
                if os.path.exists(os.path.join("install", i, "release.json")) and (os.path.exists(os.path.join("install", i, "bin", "javac")) or os.path.exists(os.path.join("install", i, "bin", "javac.exe"))):
                    with open(os.path.join("install", i, "release.json")) as f:
                        self.indstalled[i] = json.load(f)
                        self.indstalled_hash.add(self.indstalled[i]["hash"])

    @staticmethod
    def generate_name(jdk_source: dict) -> str:
        """
        Generate a name for the JDK
        @param jdk_source: JDK source
        @return: Name of the JDK
        """
        return f"jdk_{jdk_source['version']}_{jdk_source['abbreviate'].lower()}"

    def install(self, name: str, **kargs) -> bool:
        """
        install JDK
        @param name: Name of the JDK
        @return: True if installed successfully else False
        """
        for i in self.jdk_sources:
            if self.generate_name(i) == name and platform.platform().__contains__(i["os"]) and i["arch"].lower() in get_avaliable_arches():

                # check if already installed
                if i["hash"] in self.indstalled_hash:
                    print(f"JDK {self.generate_name(i)} already installed")
                    return False

                file_name = os.path.split(i["url"])[1]
                file_path = os.path.join("cache", file_name)
                os.makedirs(os.path.join("cache"), exist_ok=True)
                download(i["url"], file_path)
                install_name = self.generate_name(i)
                extract_zip(file_path, "install", install_name)

                # write realse info
                with open(os.path.join("install", install_name, "release.json"), "w") as f:
                    json.dump(i, f)
                self.indstalled[install_name] = i
                self.indstalled_hash.add(i["hash"])
                return True
        
        print(f"No such JDK: {name}")
        return False

    def use(self, jdk: str, **kargs):
        """
        Use JDK
        @param jdk: JDK hash or JDK dir name
        """
        for i in self.indstalled:
            if self.indstalled[i]["hash"].startswith(jdk) or i == jdk:
                if os.path.exists("jdk"):
                    os.remove("jdk")
                self.jdk_path = os.path.join("install", i)
                create_link(os.path.join("install", i), "jdk")
                print(
                    f"JDK {self.indstalled[i]['version']}({self.indstalled[i]['distribution']}) is now used")
                return True
        print(f"No such JDK {jdk}")
        return False

    def list(self, **kargs):
        """
        List All JDKs
        """
        print("Installed JDKs:")
        for i in self.indstalled:
            print(f"{i:15s} - {self.indstalled[i]['version']}({self.indstalled[i]['distribution']})",end="")
            if self.jdk_path == os.path.join("install", i):
                print(" - current")
            else:
                print()

        print("\nAvailable JDKs:")
        for i in self.jdk_sources:
            if platform.platform().__contains__(i["os"]) and i["arch"].lower() in get_avaliable_arches() and i["hash"] not in self.indstalled_hash:
                print(f"{self.generate_name(i):15s} - {i['version']}({i['distribution']})")


if __name__ == '__main__':
    config = {}
    if os.path.exists("config.json"):
        with open("config.json") as f:
            config = json.load(f)
    manager = JDKManager(config.get("jdk", None))

    parser = argparse.ArgumentParser(description="JDK Manager")
    subparsers = parser.add_subparsers()

    parser_ls = subparsers.add_parser('ls')
    parser_ls.set_defaults(func=manager.list)

    parser_install = subparsers.add_parser('install')
    parser_install.add_argument('name', help="Name of the JDK")
    parser_install.set_defaults(func=manager.install)

    parser_use = subparsers.add_parser('use')
    parser_use.add_argument('jdk', type=str, help="JDK hash or JDK dir name")
    parser_use.set_defaults(func=manager.use)

    args = parser.parse_args()
    if args.__contains__("func"):
        args.func(**args.__dict__)
    else:
        parser.print_help()
        exit(1)

    config["jdk"] = manager.jdk_path
    with open("config.json", "w") as f:
        json.dump(config, f)
