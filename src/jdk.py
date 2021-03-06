import os
import platform
import json
import argparse
from utils import download, extract_zip, create_link, get_avaliable_arches


class JDKManager:
    """JDK Manager

    JDK Manager class for managing JDKs and JDK links in the system.
    It can install JDKs from the internet and use them.
    It can also list all installed JDKs and available JDKs.
    You can change the default JDK by using the `use` method.
    It is able to switch between different JDKs by changing the `jdk` link.

    Attentions:
        - JDKs are installed in the `install` directory.
        - JDK links are created in the `jdk` directory.
        - In windows, making a link needs administrator privileges.

    Attributes:
        jdk_path (str): The path of the current JDK.
        indstalled (dict): A dictionary of installed JDKs.
        indstalled_hash (set): A set of installed JDK hashes.

    Typical usage:
        >>> jdk = JDKManager()
        >>> jdk.install("jdk_17.0.1_ms")
        >>> jdk.use("jdk_17.0.1_ms")
        >>> jdk.list()
    """

    def __init__(self, parsers: argparse.ArgumentParser, jdk_path=None) -> None:
        """Initialize JDK Manager with current JDK path

        Args:
            parsers (argparse.ArgumentParser): The argument parser.
            jdk_path (str): The path of the current JDK.

        Raises:
            FileNotFoundError: If the source file of JDKs is not found.
        """
        self.jdk_path = jdk_path
        parser_ls = parsers.add_parser('ls')
        parser_ls.set_defaults(func=self.list)

        parser_install = parsers.add_parser('install')
        parser_install.add_argument('name', help="Name of the JDK")
        parser_install.set_defaults(func=self.install)

        parser_use = parsers.add_parser('use')
        parser_use.add_argument(
            'name', type=str, help="JDK hash or JDK dir name")
        parser_use.set_defaults(func=self.use)

        parser_check = parsers.add_parser('check')
        parser_check.set_defaults(func=self.check)

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
        """Generate a name for the JDK

        Args:
            jdk_source (dict): The source of the JDK.

        Returns:
            str: The name of the JDK.

        Examples:
            >>> jdk = JDKManager()
            >>> jdk.generate_name({"version": "17.0.0", "abbreviate": "AMZ", "arch": "x64", "os": "windows", "distribution": "Amazon"})
            'jdk_17.0.0_amz'

        Raises:
            KeyError: If the source of the JDK is not complete.
        """
        return f"jdk_{jdk_source['version']}_{jdk_source['abbreviate'].lower()}"

    def install(self, name: str, **kargs) -> bool:
        """install JDK

        It can install JDKs from the internet or from the local directory.
        If the JDK package is not found, it will download it from the internet.
        If the JDK is already installed, it will not be installed again.
        And it will generate a release.json file for the JDK.

        Args:
            name (str): The name of the JDK.

        Returns:
            bool: True if the JDK is installed successfully; False otherwise.

        Examples:
            >>> jdk = JDKManager()
            >>> jdk.install("jdk_17.0.1_ms")
            True

        Raises:
            KeyError: If the source of the JDK is not complete.
            DownloadError: If the JDK Link is unavailable.
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

    def use(self, name: str, **kargs):
        """Use JDK

        It can use a JDK by changing the `jdk` link.
        In windows, it needs administrator privileges.

        Args:
            name (str): The name of the JDK.

        Returns:
            bool: True if the JDK is used successfully; False otherwise.

        Examples:
            >>> jdk = JDKManager()
            >>> jdk.install("jdk_17.0.1_ms")
            True
            >>> jdk.use("jdk_17.0.1_ms")
            True

        Raises:
            FileNotFoundError: If the JDK is not installed.
        """
        for i in self.indstalled:
            if self.indstalled[i]["hash"].startswith(name) or i == name:
                if os.path.exists("jdk"):
                    os.remove("jdk")
                self.jdk_path = os.path.join("install", i)
                create_link(os.path.join("install", i), "jdk")
                print(
                    f"JDK {self.indstalled[i]['version']}({self.indstalled[i]['distribution']}) is now used")
                return True
        print(f"No such JDK {name}")
        return False

    def list(self, **kargs):
        """List All JDKs

        It can list all installed JDKs and all available JDKs.
        The current JDK will be marked with `*`

        Examples:
            >>> jdk = JDKManager()
            >>> jdk.install("jdk_17.0.1_ms")
            True
            >>> jdk.list()
        """
        print("Installed JDKs:")
        for i in self.indstalled:
            print(
                f"{i:15s} - {self.indstalled[i]['version']}({self.indstalled[i]['distribution']})", end="")
            if self.jdk_path == os.path.join("install", i):
                print(" *")
            else:
                print()

        print("\nAvailable JDKs:")
        for i in self.jdk_sources:
            if platform.platform().__contains__(i["os"]) and i["arch"].lower() in get_avaliable_arches() and i["hash"] not in self.indstalled_hash:
                print(
                    f"{self.generate_name(i):15s} - {i['version']}({i['distribution']})")

    def check(self, **kargs):
        """Check JDK

        It can check the environment of the JDK is correct.

        Returns:
            bool: True if the JDK environment is correct; False otherwise.

        Examples:
            >>> jdk = JDKManager()
            >>> jdk.install("jdk_17.0.1_ms")
            True
            >>> jdk.use("jdk_17.0.1_ms")
            True
            >>> jdk.check()
            True
        """
        
        java_home = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../jdk"))
        env_java_home = os.path.realpath(os.environ.get("JAVA_HOME"))
        if not java_home == env_java_home:
            print(f"JAVA_HOME is not set correctly.\nIt should be {java_home} instead of {os.environ['JAVA_HOME']}.\nPlease set JAVA_HOME to {java_home}")
            return False
        
        PATH = os.environ.get("PATH")
        if platform.system() == "Windows":
            PATH = PATH.split(";")
        else:
            PATH = PATH.split(":")
        PATH = [os.path.realpath(i) for i in PATH]
        java_home_bin = os.path.realpath(os.path.join(java_home, "bin"))
        if not java_home_bin in PATH:
            print(f"PATH is not set correctly.")
            if platform.system() == "Windows":
                print("You should add %JAVA_HOME%\\bin to PATH.")
            else:
                print("You should add $JAVA_HOME/bin to PATH.")
            return False
        print("JDK environment is correct.")
        return True