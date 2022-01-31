import argparse
import platform
import os
import subprocess
import re
import sys
import shutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def get_NSIS_dir(args):
    """
    Get NSIS dir
    @param args: args from argparse module (see main)
    @return: NSIS dir
    """
    if args.makensis:
        return args.makensis
    else:
        p = subprocess.Popen(['where', 'makensis'], stdout=subprocess.PIPE)
        nsis_dir = p.communicate()[0].decode('utf-8').strip()
        if nsis_dir:
            return os.path.dirname(nsis_dir)
        else:
            print(
                'NSIS not found. Please install NSIS or specify its path with --makensis')
            sys.exit(1)

def check_EnVar_plugin(args):
    """
    Check if EnVar plugin is installed
    @param args: args from argparse module (see main)
    """
    nsis_dir = get_NSIS_dir(args)
    if not os.path.exists(os.path.join(nsis_dir, 'Contrib', 'EnVar')):
        print('EnVar plugin not found. Please install EnVar plugin(https://github.com/GsNSIS/EnVar/).')
        sys.exit(1)

def is_git_repo(path):
    """
    Check if path is git repo
    @param path: path to check
    @return: True if path is git repo
    """
    try:
        p = subprocess.Popen(['git', 'rev-parse', '--is-inside-work-tree'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
        out, err = p.communicate()
        if p.returncode != 0:
            return False
        else:
            return out.decode('utf-8').strip() == "true"
    except:
        return False


def get_git_repo_version(path):
    """
    Get git repo version
    @param path: path to git repo
    @return: git repo version
    """
    p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
    out, err = p.communicate()
    return out.decode('utf-8').strip()


def check_package(args):
    """
    Check package is installed
    @param args: args from argparse module (see main)
    """
    try:
        import requests
        print("find requests version: {}".format(requests.__version__))
    except ImportError:
        print("requests module is not installed")
        exit(1)

    try:
        import tqdm
        print("find tqdm version: {}".format(tqdm.__version__))
    except ImportError:
        print("tqdm module is not installed")
        exit(1)

    try:
        p = subprocess.Popen(
            ['gcc', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        err = err.decode('utf-8')
        version = re.findall(r'(\d+\.\d+\.\d+)', err)[0]
        print("find gcc version: {}".format(version))
    except:
        print("gcc module is not installed")
        exit(1)

    try:
        p = subprocess.Popen(
            ['nuitka', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        out = out.decode('utf-8').splitlines()[0]
        print("find nuitka version: {}".format(out))
    except:
        print("nuitka module is not installed")
        exit(1)

    try:
        p = subprocess.Popen(['git', '--version'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        out = out.decode('utf-8').split()[-1]
        print("find git version: {}".format(out))
    except:
        print("git module is not installed")
        exit(1)

    if platform.system() == "Windows":
        depends_path = os.path.join(os.path.expanduser(
            '~'), "AppData", "Local", "Nuitka", "Nuitka", "depends", "x86_64", "depends.exe")
        if os.path.exists(depends_path):
            print("find Dependency Walker for Nuitka")
        else:
            print("Dependency Walker for Nuitka is not installed")
            print("Begin to download Dependency Walker for Nuitka")
            os.makedirs(os.path.dirname(depends_path), exist_ok=True)
            if os.system(r"curl -L https://dependencywalker.com/depends22_x64.zip -o depends22_x64.zip && unzip depends22_x64.zip -d {}".format(os.path.dirname(depends_path))) != 0:
                print("Download Dependency Walker for Nuitka failed")
                exit(1)

    if args.pack:
        if not platform.platform().startswith("Windows"):
            print("Only Windows is supported for packaging")
            exit(1)
        if not args.makensis:
            p = subprocess.Popen(["makensis", "/VERSION"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if p.returncode != 0:
                print(
                    "makensis is not installed. You can set the path to makensis with --makensis")
                exit(1)
            else:
                print("find makensis version: {}".format(
                    out.decode("utf-8").strip()))
        else:
            p = subprocess.Popen([args.makensis, "/VERSION"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if p.returncode != 0:
                print("makensis is not installed")
                exit(1)
            else:
                print("find makensis version: {}".format(
                    out.decode("utf-8").strip()))
            check_EnVar_plugin(args)

    print("All modules are installed")


def build_package(args):
    """
    Build package
    @param args: args from argparse module (see main)
    """
    if args.pack and not platform.system() == "Windows":
        print("Only Windows is supported for packaging")
        exit(1)

    if not is_git_repo(os.path.dirname(os.path.abspath(__file__))):
        print("You must run this script from git repo")
        exit(1)

    version = args.version if args.version else get_git_repo_version(
        os.path.dirname(os.path.abspath(__file__)))
    print("building version: {}".format(version))

    if os.system("nuitka src/jdkmgr.py --mingw64 --standalone --output-dir=dist") != 0:
        print("nuitka build failed")
        exit(1)

    artifact_filename = "jdkmgr-{}-{}-{}".format(version,
                                                 platform.system(), platform.architecture()[0])
    os.makedirs("artifact", exist_ok=True)

    os.rename("dist/jdkmgr.dist", "dist/bin")
    shutil.rmtree("dist/jdkmgr.build")
    shutil.copytree("source", "dist/source")
    shutil.copy("LICENSE", "dist/LICENSE")

    if platform.system() == "Windows":
        if os.system("7z a -tzip -mx=9 artifact/{}.zip ./dist/*".format(artifact_filename)) != 0:
            print("7z failed")
            exit(1)
    else:
        if os.system("tar -czf artifact/{}.tar.gz dist".format(artifact_filename)) != 0:
            print("tar build failed")
            exit(1)

    if args.pack:
        makensis = "makensis" if not args.makensis else args.makensis
        p = subprocess.Popen([makensis, "/INPUTCHARSET", "UTF8", f"/DVERSION={version}", 'nsis/build.nsi'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            print("makensis build failed")
            print(err.decode('utf-8'))
            exit(1)
        shutil.move("nsis/Stetup.exe", "artifact/"+artifact_filename+".exe")
        print("build package {}.exe".format(artifact_filename))


def clean(args):
    """
    Clean build files
    @param args: args from argparse module (see main)
    """
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    print("clean build files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build script')
    parser.add_argument('--check', action='store_true',
                        help='Check if all dependencies are installed')
    parser.add_argument('--version', '-v', type=str, required=False,
                        help='Version of the application')
    parser.add_argument('--pack', action='store_true',
                        help='Pack the application (Windows Only)')
    parser.add_argument('--makensis', required=False,
                        help='Path to makensis (Windows Only)')
    parser.add_argument('--clean', action='store_true',
                        help='Clean build files')
    args = parser.parse_args()
    if args.check:
        check_package(args)
    elif args.clean:
        clean(args)
    else:
        check_package(args)
        build_package(args)
