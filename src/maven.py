import os
import platform
import json
from utils import download, extract, create_link, get_avaliable_arches
import argparse
import subprocess

class MavenManager:

    def __init__(self, parsers: argparse.ArgumentParser, maven_path=None) -> None:
        """Initialize MavenManager with maven_path

        Args:
            parsers (argparse.ArgumentParser): parser for MavenManager
            maven_path (str, optional): path to the maven.

        Raises:
            FileNotFoundError: if source/maven.json not found

        Examples:
            >>> maven = MavenManager()
            >>> maven = MavenManager("maven_3.6.3")
        """
        self.maven_path = maven_path
        maven_parser_ls = parsers.add_parser('ls', help='list all installed Maven and available Maven')
        maven_parser_ls.set_defaults(func=self.list)

        maven_parser_install = parsers.add_parser('install', help="install Maven")
        maven_parser_install.add_argument('name', help="Name of the Maven")
        maven_parser_install.set_defaults(func=self.install)

        maven_parser_use = parsers.add_parser('use', help="Select Maven")
        maven_parser_use.add_argument('name', type=str, help="Maven hash or Maven dir name")
        maven_parser_use.set_defaults(func=self.use)

        maven_parser_check = parsers.add_parser('check', help="Check if Maven environment is set up correctly")
        maven_parser_check.set_defaults(func=self.check)

        # load Maven sources
        if os.path.exists("source/maven.json"):
            with open("source/maven.json") as f:
                self.maven_sources = json.load(f)
        else:
            raise FileNotFoundError("No such file: source/maven.json")

        self.indstalled = {}
        self.indstalled_hash = set()
        if not os.path.exists("install"):
            os.makedirs("install")

        for i in os.listdir("install"):
            if i.startswith("maven_"):
                if os.path.exists(os.path.join("install", i, "release.json")) and (os.path.exists(os.path.join("install", i, "bin", "mvn")) or os.path.exists(os.path.join("install", i, "bin", "mvn.cmd"))):
                    with open(os.path.join("install", i, "release.json")) as f:
                        self.indstalled[i] = json.load(f)
                        self.indstalled_hash.add(
                            self.get_hash(self.indstalled[i]))

    @staticmethod
    def get_hash(maven_source: dict) -> str:
        """get hash of the JDK

        Examples:
        >>> maven = MavenManager()
        >>> maven.get_hash({"url": "https://archive.apache.org/dist/maven/maven-3/3.6.3/binaries/apache-maven-3.6.3-bin.zip", "md5": "c87c4caae590d48f90e02fc7e254dabe", "version": "3.6.3"})

        Args:
            maven_source (dict): maven source

        Returns:
            str: hash of the JDK
        """
        return maven_source["sha512"] if "sha512" in maven_source else maven_source["sha256"] if "sha256" in maven_source else maven_source["sha1"] if "sha1" in maven_source else maven_source["md5"] if "md5" in maven_source else None

    @staticmethod
    def get_hashs(maven_source: dict) -> list:
        """get hash of the JDK

        Examples:
        >>> maven = MavenManager()
        >>> maven.get_hashs({"url": "https://archive.apache.org/dist/maven/maven-3/3.6.3/binaries/apache-maven-3.6.3-bin.zip", "md5": "c87c4caae590d48f90e02fc7e254dabe", "version": "3.6.3"})

        Args:
            maven_source (dict): maven source

        Returns:
            dict: hash of the JDK
        """
        hashs = {}
        for i in ["sha512", "sha256", "sha1", "md5"]:
            if i in maven_source:
                hashs[i] = maven_source[i]
        return hashs

    @staticmethod
    def generate_name(maven_source: dict) -> str:
        """Generate a name for the Maven source with the following format: maven_<version>

        Args:
            maven_source (dict): maven source

        Returns:
            str: name of the JDK
        """
        return f"maven_{maven_source['version']}"

    def install(self, name: str, **kargs) -> bool:
        """install Maven

        Examples:
        >>> maven = MavenManager()
        >>> maven.install("maven_3.6.3")

        Args:
            name (str): name of the Maven

        Returns:
            bool: True if installed successfully else False
        """
        for i in self.maven_sources:
            if self.generate_name(i) == name:

                # check if already installed
                if self.get_hash(i) in self.indstalled_hash:
                    print(f"Maven {self.generate_name(i)} already installed")
                    return False

                file_name = os.path.split(i["url"])[1]
                file_path = os.path.join("cache", file_name)
                os.makedirs(os.path.join("cache"), exist_ok=True)
                download(i["url"], file_path, **self.get_hashs(i))
                extract(file_path, "install", self.generate_name(i))

                # create release.json
                with open(os.path.join("install", self.generate_name(i), "release.json"), "w") as f:
                    json.dump(i, f)
                self.indstalled[self.generate_name(i)] = i
                self.indstalled_hash.add(self.get_hash(i))

                return True
        
        print(f"No such Maven {name}")
        return False
    
    def use(self, name: str, **kargs) -> bool:
        """use Maven

        Examples:
        >>> maven = MavenManager()
        >>> maven.use("maven_3.6.3")

        Args:
            name (str): name of the Maven

        Returns:
            bool: True if used successfully else False
        """
        if name in self.indstalled:
            if os.path.exists("maven"):
                os.remove("maven")
            create_link(os.path.join("install", name), "maven")
            self.maven_path = name
            print(f"Maven {name} is used")
            return True
        else:
            print(f"No such Maven {name}")
            return False
    
    def list(self, **kargs) -> None:
        """list all installed Maven

        Examples:
        >>> maven = MavenManager()
        >>> maven.list()

        ToDo:
            add more info
            print sorted by version
        """
        print("Installed Maven:")
        for i in self.indstalled:
            print(f"  {i}",end="")
            if self.generate_name(self.indstalled[i]) == self.maven_path:
                print(" *")
            else:
                print()
        
        print("\nAvailable Maven:")
        available_maven = set()
        for i in self.maven_sources:
            if self.generate_name(i) not in self.indstalled:
                available_maven.add(self.generate_name(i))
        for i in available_maven:
            print(f"  {i}")

    def check(self, **kargs) -> None:
        """check if Maven environment is set up correctly

        Examples:
        >>> maven = MavenManager()
        >>> maven.check()
        """

        maven_home = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../maven"))
        env_maven_home = os.environ.get("MAVEN_HOME")
        if env_maven_home is None:
            print("MAVEN_HOME is not set")
            return False
        
        PATH = os.environ.get("PATH")
        if platform.system() == "Windows":
            PATH = PATH.split(";")
        else:
            PATH = PATH.split(":")
        
        PATH = [os.path.realpath(i) for i in PATH]
        maven_home_bin = os.path.realpath(os.path.join(maven_home, "bin"))
        if maven_home_bin not in PATH:
            print("PATH is not set correctly")
            if platform.system() == "Windows":
                print("Please add %MAVEN_HOME%\\bin to PATH")
            else:
                print("Please add $MAVEN_HOME/bin to PATH")
            return False
        
        if platform.system() == "Windows":
            p = subprocess.Popen(["cmd", "/c", "where", "mvn"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if p.returncode != 0:
                print("Maven is not installed")
                return False
            if os.path.realpath(os.path.dirname(out.decode("utf-8").split("\r\n")[0])) != maven_home_bin:
                print("Maven PATH is not set correctly")
                print("There exists a Maven in PATH but not in $MAVEN_HOME/bin")
                print("Please add $MAVEN_HOME/bin to PATH")
                return False

        print("Maven environment is set up correctly")
        return True