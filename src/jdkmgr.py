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
    manager = JDKManager(config.get("jdk", None))
    maven_manager = MavenManager(config.get("maven", None))

    parser = argparse.ArgumentParser(description="JDK Manager")
    subparsers = parser.add_subparsers()

    subparsers_java = subparsers.add_parser("java", help="JDK").add_subparsers()
    subparsers_maven = subparsers.add_parser("mvn", help="Maven").add_subparsers()

    parser_ls = subparsers_java.add_parser('ls')
    parser_ls.set_defaults(func=manager.list)

    parser_install = subparsers_java.add_parser('install')
    parser_install.add_argument('name', help="Name of the JDK")
    parser_install.set_defaults(func=manager.install)

    parser_use = subparsers_java.add_parser('use')
    parser_use.add_argument('name', type=str, help="JDK hash or JDK dir name")
    parser_use.set_defaults(func=manager.use)
    
    maven_parser_ls = subparsers_maven.add_parser('ls')
    maven_parser_ls.set_defaults(func=maven_manager.list)

    maven_parser_install = subparsers_maven.add_parser('install')
    maven_parser_install.add_argument('name', help="Name of the Maven")
    maven_parser_install.set_defaults(func=maven_manager.install)

    maven_parser_use = subparsers_maven.add_parser('use')
    maven_parser_use.add_argument('name', type=str, help="Maven hash or Maven dir name")
    maven_parser_use.set_defaults(func=maven_manager.use)

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
