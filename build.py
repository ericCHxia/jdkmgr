import argparse
import platform
import os
import subprocess
import re
import sys
import shutil
import zipfile

os.chdir(os.path.dirname(os.path.abspath(__file__)))


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
    os.makedirs("artifact",exist_ok=True)

    os.rename("dist/jdkmgr.dist","dist/bin")
    shutil.rmtree("dist/jdkmgr.build")
    shutil.copytree("source","dist/source")
    shutil.copy("LICENSE","dist/LICENSE")

    if platform.system() == "Windows":
        z = zipfile.ZipFile(os.path.join("artifact",artifact_filename+".zip"), "w")
        for dirpath, dirnames, filenames in os.walk("dist"):
            for filename in filenames:
                z.write(os.path.join(dirpath, filename))
        z.close()
    else:
        if os.system("tar -czf artifact/{}.tar.gz dist".format(artifact_filename)) != 0:
            print("tar build failed")
            exit(1)

    if args.pack:
        p = subprocess.Popen([r'C:\Program Files (x86)\NSIS\makensis.exe', "/INPUTCHARSET", "UTF8",f"/DVERSION={version}", 'nsis/build.nsi'],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            print("makensis build failed")
            print(err.decode('utf-8'))
            exit(1)
        shutil.move("nsis/Stetup.exe", "artifact/"+artifact_filename+".exe")
        print("build package {}.exe".format(artifact_filename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build script')
    parser.add_argument('--check', action='store_true',
                        help='Check if all dependencies are installed')
    parser.add_argument('--version','-v', type=str, required=False,
                        help='Version of the application')
    parser.add_argument('--pack', action='store_true',
                        help='Pack the application (Windows Only)')
    parser.add_argument('--makensis', required=False,
                        help='Path to makensis (Windows Only)')
    args = parser.parse_args()
    if args.check:
        check_package(args)
    else:
        check_package(args)
        build_package(args)
