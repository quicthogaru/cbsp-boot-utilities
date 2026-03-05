# Capsule Generation Tools

## 1. Introduction to the Capsule Generation Tools

Capsule Generation Tools are specialized utilities designed to create capsule
files, which are essential for performing firmware updates on various devices.
These tools streamline the process of packaging firmware updates into a format
that can be easily deployed and applied to the target hardware.

## 2. Overview of the Capsule Generation Tools

The tools can be run on both Windows and Linux environments, providing
flexibility for different development setups. By using OpenSSL for certificate
generation and signing, the tools ensure that the firmware updates are secure
and authenticated.

## 3. Working of the Host Signing Tool

### 3.1 Pre-requisites to Run the Tool

**For Linux:**

1. **OpenSSL**: A toolkit for the Transport Layer Security (TLS) and Secure
   Sockets Layer (SSL) protocols.
1. **Python3**: A programming language widely used for scripting and
   automation.
1. **GIT**: version control system.

**For Windows:**

1. **OpenSSL**: Same as above.
1. **Python3**: Same as above.
1. **GIT**: version control system.
1. **Visual Studio with C++ Development Tools**: An integrated development
   environment (IDE) from Microsoft, including tools for C++ development.

Before starting the capsule generation process, you need to generate OpenSSL
certificates as mentioned in
[Capsule-Based System Firmware Update - Generate Keys][capsule-keys].
These certificates should be placed in a separate folder named 'Certificates'.

[capsule-keys]: https://github.com/tianocore/tianocore.github.io/wiki/Capsule-Based-System-Firmware-Update-Generate-Keys

Sample Certificates folder:

```
QcFMPCert.pem
QcFMPRoot.pub.pem
QcFMPSub.pub.pem
```

The `QcFMPRoot.cer` (or `NewRoot.cer`) should be converted to a hex value and
provided in the BOOT DT [will be part of `xbl_config.elf`] at node
`/sw/uefi/uefiplat/QcCapsuleRootCert` using QDTE tool.

For more information on the QDTE Tool, refer to the
[QDTE Tool documentation][qdte-tool].

[qdte-tool]: https://docs.qualcomm.com/bundle/publicresource/topics/80-70017-4/tools.html?vproduct=1601111740013072&version=1.3&facet=Boot#qdte

Use `BinToHex.py` to convert `NewRoot.cer` to a Hex value:

```
python3 BinToHex.py  NewRoot.cer  NewRoot.inc

Usage:
BintoHex.py  <InputFile> <OutputFile>
```

This `NewRoot.inc` contains the cert value, which needs to be provided in the
Boot DT at `/sw/uefi/uefiplat/QcCapsuleRootCert` (using QDTE tool).

## 4. Steps to Generate Capsule Files

Clone the repository and enter the
`cbsp-boot-utilities/uefi_capsule_generation/` directory:

```sh
git clone https://github.com/quic/cbsp-boot-utilities.git
```

1. **Setup the Environment:**

   ```sh
   python3 capsule_setup.py
   ```

1. **Generate Firmware Version bin File:**

   ```sh
   python3 SYSFW_VERSION_program.py \
     -Gen -FwVer 0.0.A.B -LFwVer 0.0.0.0 -O SYSFW_VERSION.bin
   ```

   Where A and B are the version numbers:

   - `-Gen`: Generate a new firmware version file.
   - `-FwVer`: Specifies the firmware version.
   - `-LFwVer`: Specifies the lowest firmware version.
   - `-O`: Output file name.

   To print the Firmware Versions in the `.bin` file:

   ```sh
   python3 SYSFW_VERSION_program.py --PrintAll SYSFW_VERSION.bin
   ```

1. **Generate/Update FvUpdate.xml with Firmware entries:**

   This script generates the `FvUpdate.xml` file with firmware entries:

   ```sh
   python3 UpdateFvXml.py -S <StorageType> -T <Target>
   ```

   or using a local partition configuration file:

   ```sh
   python3 UpdateFvXml.py -F <partition.conf>
   ```

   - `-S <StorageType>`: Storage type, `EMMC` or `UFS`.
   - `-T <Target>`: Target platform, `QCS6490`, `QCS9100`, `QCS8300`,
     or `QCS615`.
   - `-F <partition.conf>`: Path to a local `partition.conf` file.

   Once `FvUpdate.xml` is generated, update the `Operation` field for
   each firmware entry as needed. By default the operation is set to
   `IGNORE`.

1. **Create Firmware Volume (FV):**

   - Ensure the `/Images` folder contains all the required firmware images
     for Capsule generation.
   - Update `FvUpdate.xml` with `FwEntry` for each firmware image,
     referencing the corresponding image in the `/Images` folder.
   - Refer to `FirmwarePartitions.md` for Partitions related information.

   ```sh
   python3 FVCreation.py firmware.fv "-FvType" "SYS_FW" \
     "FvUpdate.xml" SYSFW_VERSION.bin Images/
   ```

   - `firmware.fv`: The firmware volume file.
   - `-FvType`: Type of firmware volume.
   - `FvUpdate_UFS.xml`: XML file for firmware update.
   - `SYSFW_VERSION.bin`: The firmware version file generated in the
     previous step.
   - `Images/`: Directory containing the images.

1. **Update JSON Parameters:**

   ```sh
   python3 UpdateJsonParameters.py \
     -j config.json \
     -f SYS_FW \
     -b SYSFW_VERSION.bin \
     -pf firmware.fv \
     -p Certificates/QcFMPCert.pem \
     -x Certificates/QcFMPRoot.pub.pem \
     -oc Certificates/QcFMPSub.pub.pem \
     -g <ESRT GUID>
   ```

   - `-j config.json`: JSON configuration file.
   - `-f SYS_FW`: Firmware type.
   - `-b SYSFW_VERSION.bin`: Firmware version file.
   - `-pf firmware.fv`: Firmware volume file.
   - `-p Certificates/QcFMPCert.pem`: Certificate file.
   - `-x Certificates/QcFMPRoot.pub.pem`: Root public certificate.
   - `-oc Certificates/QcFMPSub.pub.pem`: Subordinate public certificate.
   - `-g <ESRT GUID>`: ESRT GUID.

   ESRT GUIDs:

   - QCS6490 ESRT GUID: `6F25BFD2-A165-468B-980F-AC51A0A45C52`
   - QCS9100 ESRT GUID: `78462415-6133-431C-9FAE-48F2BAFD5C71`
   - QCS8300 ESRT GUID: `8BF4424F-E842-409C-80BE-1418E91EF343`
   - QCS615 ESRT GUID: `9FD379D2-670E-4BB3-86A1-40497E6E17B0`

2. **Generate the Capsule File:**

   ```sh
   python3 GenerateCapsule.py \
     -e -j config.json \
     -o <capsule_name>.cap \
     --capflag PersistAcrossReset \
     -v
   ```

   - `-e`: Enable capsule generation.
   - `-j config.json`: JSON configuration file.
   - `-o <capsule_name>.cap`: Output capsule file.
   - `--capflag PersistAcrossReset`: Flag to persist across reset.
   - `-v`: Verbose mode.

   To dump info from the Capsule headers:

   ```sh
   python3 GenerateCapsule.py --dump-info capsule.cap
   ```

## 5. Alternative: Master Script

Instead of the above 5 steps, use the following master script to run all
steps at once:

```sh
python3 capsule_creator.py \
  -fwver 0.0.A.B \
  -lfwver 0.0.0.0 \
  -config config.json \
  -p Certificates/QcFMPCert.pem \
  -x Certificates/QcFMPRoot.pub.pem \
  -oc Certificates/QcFMPSub.pub.pem \
  -guid <ESRT GUID> \
  -capsule <capsule_name>.cap \
  -images /Images \
  -setup \
  -S <StorageType> \
  -T <Target>
```

 - `-S <StorageType>`: Storage type, `EMMC` or `UFS`.
 - `-T <Target>`: Target platform, `QCS6490`, `QCS9100`, `QCS8300`,
   or `QCS615`.

The **-setup** parameter is optional and can be used for the initial setup.
You can omit it in subsequent runs.
