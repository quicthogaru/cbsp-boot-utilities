# --------------------------------------------------------------------
# Copyright (c) 2024 Qualcomm Innovation Center, Inc. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause-Clear
# --------------------------------------------------------------------

import os
import subprocess
import argparse

def run_command(command, fail_on_error=False):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Command failed with return code {result.returncode}: {result.stderr}")
        print(result.stdout)
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

def main(args):

    if args.setup:
        run_command("python3 capsule_setup.py", fail_on_error=True)
    # Step 1: Generate SYSFW_VERSION.bin
    run_command(f"python3 SYSFW_VERSION_program.py -Gen -FwVer {args.fwver} -LFwVer {args.lfwver} -O SYSFW_VERSION.bin")
    
    # Step 2: Create FvUpdate.xml
    run_command(f'python3 UpdateFvXml.py -S {args.S} -T {args.t}')
    
    # Step 3: Create firmware volume
    run_command(f'python3 FVCreation.py firmware.fv "-FvType" "SYS_FW" "FvUpdate.xml" SYSFW_VERSION.bin {args.images}')
    
    # Step 4: Update JSON parameters
    run_command(f'python3 UpdateJsonParameters.py -j {args.config} -f SYS_FW -b SYSFW_VERSION.bin -pf firmware.fv -p {args.p} -x {args.x} -oc {args.oc} -g {args.guid}')
    
    # Step 5: Generate capsule
    run_command(f'python3 GenerateCapsule.py -e -j {args.config} -o {args.capsule} --capflag PersistAcrossReset -v')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combined script for Capsule generation")
    parser.add_argument('-fwver', required=True, help='Firmware version')
    parser.add_argument('-lfwver', required=True, help='Lowest supported firmware version')
    parser.add_argument('-config', required=True, help='Configuration JSON file')
    parser.add_argument('-p', required=True, help='Certificate file')
    parser.add_argument('-x', required=True, help='Root certificate file')
    parser.add_argument('-oc', required=True, help='Sub certificate file')
    parser.add_argument('-guid', required=True, help='FMP GUID')
    parser.add_argument('-capsule', required=True, help='Output capsule file name')
    parser.add_argument('-images', required=True, help='Images directory')
    parser.add_argument('-setup', action='store_true', help='Run capsule setup script')
    parser.add_argument("-S", "--StorageType", choices=["UFS", "EMMC"], required=True, help="Specify storage type: UFS or EMMC")
    parser.add_argument("-T", "--target", required=True, help="Specify target platform (e.g., QCS6490)")

    args = parser.parse_args()
    main(args)