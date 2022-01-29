import os
import json
import platform
import argparse
from jdk import JDKManager

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

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
