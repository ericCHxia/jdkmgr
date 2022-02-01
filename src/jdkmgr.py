import os
import json
import platform
import argparse
from jdk import JDKManager
from maven import MavenManager

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

if __name__ == '__main__':
    config = {}
    if os.path.exists("config.json"):
        with open("config.json") as f:
            config = json.load(f)

    parser = argparse.ArgumentParser(description="JDK Manager")
    subparsers = parser.add_subparsers()

    subparsers_java = subparsers.add_parser("java", help="JDK").add_subparsers()
    subparsers_maven = subparsers.add_parser("mvn", help="Maven").add_subparsers()

    manager = JDKManager(subparsers_java, config.get("jdk", None))
    maven_manager = MavenManager(subparsers_maven, config.get("maven", None))

    args = parser.parse_args()
    if args.__contains__("func"):
        args.func(**args.__dict__)
    else:
        parser.print_help()
        exit(1)

    config["jdk"] = manager.jdk_path
    config["maven"] = maven_manager.maven_path
    with open("config.json", "w") as f:
        json.dump(config, f)
