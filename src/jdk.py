import os
import platform
import json
from utils import download, extract_zip, create_link, get_avaliable_arches

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
            print(
                f"{i:15s} - {self.indstalled[i]['version']}({self.indstalled[i]['distribution']})", end="")
            if self.jdk_path == os.path.join("install", i):
                print(" - current")
            else:
                print()

        print("\nAvailable JDKs:")
        for i in self.jdk_sources:
            if platform.platform().__contains__(i["os"]) and i["arch"].lower() in get_avaliable_arches() and i["hash"] not in self.indstalled_hash:
                print(
                    f"{self.generate_name(i):15s} - {i['version']}({i['distribution']})")
