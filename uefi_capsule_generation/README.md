# Capsule Generation Tools

## 1. Introduction to the Capsule Generation Tools

Capsule Generation Tools are specialized utilities designed to create capsule files, which are essential for performing firmware updates on various devices. These tools streamline the process of packaging firmware updates into a format that can be easily deployed and applied to the target hardware.

## 2. Overview of the Capsule Generation Tools

The tools can be run on both Windows and Linux environments, providing flexibility for different development setups. By using OpenSSL for certificate generation and signing, the tools ensure that the firmware updates are secure and authenticated.

## 3. Working of the Host Signing Tool

### 3.1 Pre-requisites to Run the Tool

**For Linux:**
1. **OpenSSL**: A toolkit for the Transport Layer Security (TLS) and Secure Sockets Layer (SSL) protocols.
2. **Python3**: A programming language that is widely used for scripting and automation.
3. **GIT** : version control system.

**For Windows:**
1. **OpenSSL**: Same as above.
2. **Python3**: Same as above.
3. **GIT** : version control system.
4. **Visual Studio with C++ Development Tools**: An integrated development environment (IDE) from Microsoft, which includes tools for C++ development.

Before starting the capsule generation process, you need to generate OpenSSL certificates as mentioned in https://github.com/tianocore/tianocore.github.io/wiki/Capsule-Based-System-Firmware-Update-Generate-Keys. These certificates should be placed in a separate folder named 'Certificates'.

Sample Certificates folder:
```
QcFMPCert.pem
QcFMPRoot.pub.pem
QcFMPSub.pub.pem
```

The `QcFMPRoot.cer` (or `NewRoot.cer`) should be converted to a hex value and to be provided in the BOOT DT [will be part of xbl_config.elf] at node `/sw/uefi/uefiplat/QcCapsuleRootCert` using QDTE tool

For more information on QDTE Tool, please refer https://docs.qualcomm.com/bundle/publicresource/topics/80-70017-4/tools.html?vproduct=1601111740013072&version=1.3&facet=Boot#qdte

Need to use BinToHex.py tool to convert `NewRoot.cer` to a Hex value

```
python3 BinToHex.py  NewRoot.cer  NewRoot.inc

Usage:
BintoHex.py  <InputFile> <OutputFile>
```
- This NewRoot.inc has the cert value, which need to be provided in the Boot DT at `/sw/uefi/uefiplat/QcCapsuleRootCert` [Using QDTE tool].


## 4. Steps to Generate Capsule Files
 Clone this using "git clone https://github.com/quic/cbsp-boot-utilities.git" and enter in to  directory **cbsp-boot-utilities/uefi_capsule_generation/**
1. **Setup the Environment:**
   ```sh
   python3 capsule_setup.py
   ```

2. **Generate Firmware Version bin File:**
   ```sh
   python3 SYSFW_VERSION_program.py -Gen -FwVer 0.0.A.B -LFwVer 0.0.0.0 -O SYSFW_VERSION.bin
   ```


   where A, B are the version numbers<p>
   -Gen: Generate a new firmware version file.<p>
   -FwVer: Specifies the firmware version.<p>
   -LFwVer: Specifies the lowest firmware version.<p>
   -O: Output file name.<p>

   ```
   python3 SYSFW_VERSION_program.py  --PrintAll SYSFW_VERSION.bin 
   ```
   - Then above command will print the Firmware Verions in the .bin file
   
   
3. **Create Firmware Volume (FV):**

      ***\* Ensure the /Images folder contains all the required firmware images for Capsule generation***<p>
      ***\* Update FvUpdate.xml with FwEntry for each firmware image, referencing the corresponding image in the /Images folder.***<p>
      ***\* Please refer FirmwarePartitions.md for Partitions related information***
   ```sh
   python3 FVCreation.py firmware.fv "-FvType" "SYS_FW" "FvUpdate.xml" SYSFW_VERSION.bin Images/
   ```
  
   firmware.fv: The firmware volume file.<p>
   -FvType: Type of firmware volume.<p>
   FvUpdate_UFS.xml: XML file for firmware update.<p>
   SYSFW_VERSION.bin: The firmware version file generated in the previous step.<p>
   Images/: Directory containing the images.<p>

4. **Update JSON Parameters:**
   ```sh
   python3 UpdateJsonParameters.py -j config.json -f SYS_FW -b SYSFW_VERSION.bin -pf firmware.fv -p Certificates/QcFMPCert.pem -x Certificates/QcFMPRoot.pub.pem -oc Certificates/QcFMPSub.pub.pem -g <ESRT GUID>
   ```


   -j config.json: JSON configuration file.<p>
   -f SYS_FW: Firmware type.<p>
   -b SYSFW_VERSION.bin: Firmware version file.<p>
   -pf firmware.fv: Firmware volume file.<p>
   -p Certificates/QcFMPCert.pem: Certificate file.<p>
   -x Certificates/QcFMPRoot.pub.pem: Root public certificate.<p>
   -oc Certificates/QcFMPSub.pub.pem: Subordinate public certificate.<p>
   -g <ESRT GUID>: ESRT GUID.<p>
       ESRT GUIDs :<p>
      -   QCS6490 ESRT GUID: 6F25BFD2-A165-468B-980F-AC51A0A45C52<p>
      -   QCS9100 ESRT GUID: 78462415-6133-431C-9FAE-48F2BAFD5C71<p>
      -   QCS8300 ESRT GUID: 8BF4424F-E842-409C-80BE-1418E91EF343<p>
      -   QCS615 ESRT GUID: 9FD379D2-670E-4BB3-86A1-40497E6E17B0<p>

5. **Generate the Capsule File:**
   ```sh
   python3 GenerateCapsule.py -e -j config.json -o <capsule_name>.cap --capflag PersistAcrossReset -v
   ```

   -e : Enable capsule generation.<p>
   -j : config.json: JSON configuration file.<p>
   -o : <capsule_name>.cap: Output capsule file.<p>
   --capflag : PersistAcrossReset: Flag to persist across reset.<p>
   -v: Verbose mode.<p>

   ```
   python3 GenerateCapsule.py  --dump-info capsule.cap 
   ```
   - The above command witll dump the info from Capsule headers.

##
Instead of above 5 steps we can execute the below single script
#              
 Master script for Capsule Generation:

   You can use the following Master script to run all the above steps in single step:.
   ```
   python3 capsule_creator.py -fwver 0.0.A.B -lfwver 0.0.0.0 -config config.json -p Certificates/QcFMPCert.pem -x Certificates/QcFMPRoot.pub.pem -oc Certificates/QcFMPSub.pub.pem -guid <ESRT GUID> -capsule <capsule_name>.cap -images /Images -setup
   ```
   The **-setup** parameter is optional and can be used for the initial setup. You can omit it in subsequent runs
