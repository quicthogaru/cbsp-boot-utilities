# --------------------------------------------------------------------
# Copyright (c) 2024 Qualcomm Innovation Center, Inc. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause-Clear
# --------------------------------------------------------------------

import requests
import subprocess
import os
import shutil
import platform
import stat

# URL of the file you want to download
file_url = 'https://raw.githubusercontent.com/tianocore/edk2/ef91b07388e1c0a50c604e5350eeda98428ccea6/BaseTools/Source/Python/Capsule/GenerateCapsule.py'
repo_url = 'https://github.com/tianocore/edk2.git'
common_url = "https://github.com/tianocore/edk2/tree/edk2-stable202008/BaseTools/Source/Python/Common"


def run_make_command(dir_path):
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        try:
            os.chdir(dir_path)
            subprocess.run(['make'], check=True)
            print(f"'make' command executed successfully in {dir_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error running 'make' command: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    else:
        print(f"Directory '{dir_path}' does not exist.")


def remove_directory(dir_path):
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        shutil.rmtree(dir_path)
        print(f"Directory '{dir_path}' has been removed.")
    else:
        print(f"Directory '{dir_path}' does not exist.")


def clone_repo(repo_url, clone_dir):
    try:

        # subprocess.run(['git', 'clone', repo_url, clone_dir], check=True)
        # print(f"Repository cloned into {clone_dir}")
        # os.chdir(clone_dir)
        # subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'], check=True)
        # print("initialization done")

        if os.path.exists(clone_dir) and os.path.isdir(clone_dir):
            print(f"Directory '{clone_dir}' already esists.")
        else:
            subprocess.run(['git', 'clone', repo_url, clone_dir], check=True)
            print(f"Repository cloned into {clone_dir}")
            os.chdir(clone_dir)
            subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'], check=True)
            print("initialization done")

    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")


def sync_single_dir(repo_url, branch, target_dir, local_path):

    if not os.path.exists(local_path):
        os.makedirs(local_path)
    
    subprocess.run(['git', 'init'], cwd=local_path)
    subprocess.run(['git', 'remote', 'add', 'origin', repo_url], cwd=local_path)
    subprocess.run(['git', 'config','core.sparseCheckout', 'true'], cwd=local_path)

    sparse_checkout_file = os.path.join(local_path, '.git/info/sparse-checkout')
    with open(sparse_checkout_file, 'w') as f:
        f.write("%s/\n" % (target_dir))
    
    subprocess.run(['git', 'pull', 'origin', branch], cwd=local_path)


response = requests.get(file_url)

if response.status_code == 200:
    with open('GenerateCapsule.py', 'wb') as file:
        file.write(response.content)
    print('GenerateCapsule_gsync.py File downloaded successfully')
else:
    print('Failed to download file')



def force_delete_folder(folder_path):

    def on_error(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    try:
        shutil.rmtree(folder_path, onerror=on_error)
        print("Folder %s deleted successfully" % (folder_path))
    except Exception as e:
        print("Failed to delete folder %s" % (folder_path))


def gen_exe_windows(dir_path):
    os.chdir(dir_path)
    # subprocess.run(['set', 'PYTHON_COMMAND="python3"'], check=True)
    subprocess.run(['edksetup.bat', 'Rebuild'], check=True)


if platform.system() == "Linux":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    clone_dir = os.path.join(base_dir, 'edk2')
    # remove_directory(clone_dir)
    clone_repo(repo_url, clone_dir)

    c_dir = os.path.join(clone_dir, 'BaseTools', 'Source', 'C')
    run_make_command(c_dir)

    genfv_path_linux = os.path.join(c_dir, 'bin', 'GenFv')
    genffs_path_linux = os.path.join(c_dir, 'bin', 'GenFfs')

    subprocess.run(['cp', "-r", genfv_path_linux, base_dir], check=True)
    print("Copied ", genfv_path_linux, " to ", base_dir)
    subprocess.run(['cp', "-r", genffs_path_linux, base_dir], check=True)
    print("Copied ", genffs_path_linux, " to ", base_dir)

    print("starting common folder sync")

    common_dir = os.path.join(base_dir, 'Common')
    local_path = os.path.join(base_dir + "Common_sync")
    Common_dir_path = os.path.join(local_path, "BaseTools", "Source", "Python", "Common")

    print(common_dir)

    sync_single_dir(repo_url, branch="edk2-stable202008", target_dir= 'BaseTools/Source/Python/Common', local_path=local_path)
    subprocess.run(['cp', "-r", Common_dir_path, base_dir], check=True)
    shutil.rmtree(local_path)

    print("Repository synced successfully!")

if platform.system() == "Windows":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    clone_dir = os.path.join(base_dir, 'edk2')
    # clone_repo(repo_url, clone_dir)
    # remove_directory(clone_dir)


    force_delete_folder(clone_dir)


    git_command = "git clone %s %s" % (repo_url, clone_dir)
    subprocess.run('cmd /c ' + git_command, check=True)

    

    gen_exe_windows(clone_dir)

    genfv_path_linux = os.path.join(clone_dir, 'BaseTools', 'Bin', 'Win32', 'GenFv.exe')
    genffs_path_linux = os.path.join(clone_dir, 'BaseTools', 'Bin', 'Win32', 'GenFfs.exe')

    print("Copying ", genfv_path_linux, " to ", base_dir)
    # subprocess.run(['cp', "-r", genfv_path_linux, base_dir], check=True)
    shutil.copy(genfv_path_linux, base_dir)
    print("Copied ", genfv_path_linux, " to ", base_dir)
    # subprocess.run(['cp', "-r", genffs_path_linux, base_dir], check=True)
    shutil.copy(genffs_path_linux, base_dir)
    print("Copied ", genffs_path_linux, " to ", base_dir)

    print("starting common folder sync")

    common_dir = os.path.join(base_dir, 'Common')
    local_path = os.path.join(base_dir, "Common_sync")
    Common_dir_path = os.path.join(local_path, "BaseTools", "Source", "Python", "Common")
    
    print("common_dir: ", common_dir)
    print("local_path: ", local_path)
    print("Common_dir_path: ", Common_dir_path)

    sync_single_dir(repo_url, branch="edk2-stable202008", target_dir= 'BaseTools/Source/Python/Common', local_path=local_path)
    print("Completed common folder sync")
    shutil.copytree(Common_dir_path, common_dir)
    force_delete_folder(local_path)

