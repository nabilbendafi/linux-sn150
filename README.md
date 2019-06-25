# Running Linux on Stormshield SNS appliances

This repository contains documentation and material to run Linux on Stormshield SNS appliances

Please refers to [Disclaimer](#disclaimer) before performing any action on your Stormshield SNS appliances as you may void warranty and/or brick your device.

## Table of Contents
 - [Introduction](#introduction)
   - [Technical stack](#technical-stack)
     - [Network interface](#network-interface)
     - [Internal storage](#internal-storage)
     - [Boot](#boot)
 - [U-boot](#u-boot)
   - [Dump SPI flash](#dump-spi-flash)
   - [Load in RAM](#load-in-ram)
   - [Build new version](#build-new-version)
 - [Linux](#linux)
 - [References](#references)
 - [Disclaimer](#disclaimer)
 - [Licence](#licence)

## Introduction

Stormshield [SN150](https://www.stormshield.com/fr/produits/sn150) is a [UTM](https://fr.wikipedia.org/wiki/Unified_threat_management)

### Technical stack

According to [RESTAURATION LOGICIELLE PAR CLÉ USB - FR](https://documentation.stormshield.eu/SNS/v3/fr/Content/PDF/SNS-UserGuidesAndTechnicalNotes/sns-fr-Restauration_logicielle_cle_USB_note_technique.pdf) documentation, Stormshield SNS uses [U-boot](https://www.denx.de/wiki/U-Boot) as bootloader.
So let get some information from the bootloader.

I assume that you have access to a Linux computer.

  - Power-off the SNS
  - Connect a USB cable from SNS USB port (_console_ or _IOIOI_) to your computer
    - You should now have a new Serial-over-USB device detected (ex. _/dev/ttyUSB0_), :
   ```
   0403:6015 Future Technology Devices International, Ltd Bridge(I2C/SPI/UART/FIFO)
   ```
  - Open a terminal and launch a serial terminal emulator (ex. _minicom_)
   ```
   $ minicom -D /dev/ttyUSB0
   ```
   Note: You might need to run above command as _sudo_ or add your user to _dialout_ group
  - Power on the SNS
```
U-Boot 2012.04.01-Semihalf_SW-R2.4 (Jun 10 2014 - 08:22:48)SN150


SoC:   Kirkwood 88F6281_A1
DRAM:  512 MiB
WARNING: Caches not enabled
SF:    Detected MX25L4005 with page size 64 KiB, total 512 KiB
In:    serial
Out:   serial
Err:   serial
Net:   egiga0, egiga1
switch port 4 disabled
88E6172 Initialized
Hit any key to stop autoboot:  3... 2... 1
```
  - Hit any key to abort boot sequence

So we already got some hardware caracteristics:
  - Marvell SoC Kirkwood **[88F6281](https://lafibre.info/images/free/201101_Marvell_Kirkwood_88F6281_2_Hardware_Spec.pdf)** revision A1
  - **512MB** SDRAM
  - Macronix SPI NOR Flash **[MX25L4005](https://www.mct.net/download/macronix/mx25l8005.pdf)**
  - Gigabit Ethernet Switch (**[88E6172](https://www.marvell.com/switching/link-street/)**) with 5 PHYs

Let's run _help_ command and see what we can use to learn more.
```
SN150>> help
?       - alias for 'help'
base    - print or set address offset
bdinfo  - print Board Info structure
boot    - boot default, i.e., run 'bootcmd'
bootd   - boot default, i.e., run 'bootcmd'
bootelf - Boot from an ELF image in memory
bootm   - boot application image from memory
bootp   - boot image via network using BOOTP/TFTP protocol
bootvx  - Boot vxWorks from an ELF image
cmp     - memory compare
coninfo - print console devices and information
cp      - memory copy
crc32   - checksum calculation
date    - get/set/reset date & time
dhcp    - boot image via network using DHCP/TFTP protocol
diskboot- boot from IDE device
echo    - echo args to console
editenv - edit environment variable
env     - environment handling commands
ext2load- load binary file from a Ext2 filesystem
ext2ls  - list files in a directory (default /)
fatinfo - print information about filesystem
fatload - load binary file from a dos filesystem
fatls   - list files in a directory (default /)
go      - start application at address 'addr'
help    - print command description/usage
ide     - IDE sub-system
iminfo  - print header information for application image
imxtract- extract a part of a multi-image
itest   - return true/false on integer compare
loadb   - load binary file over serial line (kermit mode)
loads   - load S-Record file over serial line
loady   - load binary file over serial line (ymodem mode)
loop    - infinite loop on address range
md      - memory display
mii     - MII utility commands
mm      - memory modify (auto-incrementing address)
mmc     - MMC sub-system
mtest   - simple RAM read/write test
mw      - memory write (fill)
nfs     - boot image via network using NFS protocol
nm      - memory modify (constant address)
ping    - send ICMP ECHO_REQUEST to network host
printenv- print environment variables
reset   - Perform RESET of the CPU
run     - run commands in an environment variable
saveenv - save environment variables to persistent storage
setenv  - set environment variables
sf      - SPI flash sub-system
sleep   - delay execution for some time
source  - run script from memory
tftpboot- boot image via network using TFTP protocol
usb     - USB sub-system
usbboot - boot from USB device
version - print monitor, compiler and linker version

```

Try _printenv_
```
SN150>> printenv 
baudrate=115200
bootcmd=mmc init; fatload mmc 1:2 ${loadaddr} ubldr; bootelf ${loadaddr}
bootdelay=5
bootusb=usb start; fatload usb 0:2 ${loadaddr} ubldr; bootelf ${loadaddr}
eth1addr=00:0D:B4:XX:XX:XX
ethact=egiga0
ethaddr=00:0D:B4:XX:XX:XX
loadaddr=0x1000
m_date=YYYY-DD-MM HH:MM:SS
m_name=Stormshield
m_product=SN150-A
serial#=XXXXXXXXXX
stderr=serial
stdin=serial
stdout=serial
```

#### Network interface

Mac adresses start with [00:0D:B4](https://hwaddress.com/oui-iab/00-0D-B4), which are registered by [NETASQ](https://wikipedia.org/wiki/NetASQ) name of the company before it was merged with [Arkoon](https://wikipedia.org/wiki/Arkoon_Network_Security) to form Stormshield.

```
SN150>> mii device
MII devices: 'egiga0' 'egiga1' 
Current device: 'egiga0'
SN150>> mii info
PHY 0x10: OUI = 0x3FC005, Model = 0x32, Rev = 0x01,  10baseT, HDX
PHY 0x11: OUI = 0x3FC005, Model = 0x32, Rev = 0x01,  10baseT, HDX
PHY 0x12: OUI = 0x3FC005, Model = 0x32, Rev = 0x01,  10baseT, HDX
PHY 0x13: OUI = 0x3FC005, Model = 0x32, Rev = 0x01,  10baseT, HDX
PHY 0x14: OUI = 0x3FC005, Model = 0x32, Rev = 0x01,  10baseT, HDX
PHY 0x15: OUI = 0x3FC005, Model = 0x32, Rev = 0x01,  10baseT, HDX
PHY 0x16: OUI = 0x3FC005, Model = 0x32, Rev = 0x01,  10baseT, HDX
PHY 0x1B: OUI = 0x0000, Model = 0x00, Rev = 0x00,  10baseT, HDX
PHY 0x1D: OUI = 0x0000, Model = 0x00, Rev = 0x00,  10baseT, HDX
```

#### Internal storage

```
SN150>> printenv 
...
bootcmd=mmc init; fatload mmc 1:2 ${loadaddr} ubldr; bootelf ${loadaddr}
bootdelay=5
bootusb=usb start; fatload usb 0:2 ${loadaddr} ubldr; bootelf ${loadaddr}
...
```

  * _bootcmd_ shows **mmi init**. This means that it has an MMC (or SDCARD) in it to boot from.

```
SN150>> mmc init
SDHC found. Card desciption is:
Manufacturer:       0x74, OEM "JE"
Product name:       "USD  ", revision 1.0
Serial number:      XXXXXXXXXX
Manufacturing date: 7/2013
CRC:                0x00, b0 = 0
mmc1 is available
```
We can list the content of the second partition (DOS/Windows FAT) of that MMC card.
```
SN150>> fatls mmc 1:2
   240307   ubldr

1 file(s), 0 dir(s)
```

  * _bootusb_ shows **usb start**. This means is has the ability to mount a USB drive and boot from it (ex. for recovery).

#### Boot

_bootcmd_ [U-boot](https://www.denx.de/wiki/U-Boot) variable defines a command string that is automatically executed when the initial countdown is not interrupted.

  * _bootcmd_ shows **fatload mmc 1:2 ${loadaddr} ubldr; bootelf ${loadaddr}**. In the internal MMC card a file named **ubldr** is loaded in memory at adress _${loadaddr}_. This binary is then executed by _bootelf_ command.

Let's try it.
```
SN150>> mmc init; fatload mmc 1:2 ${loadaddr} ubldr; bootelf ${loadaddr}
SDHC found. Card desciption is:
Manufacturer:       0x74, OEM "JE"
Product name:       "USD  ", revision 1.0
Serial number:      1316536818
Manufacturing date: 7/2013
CRC:                0x00, b0 = 0
mmc1 is available
reading ubldr

240307 bytes read
## Starting application at 0x04000054 ...
Consoles: U-Boot console  
Number of U-Boot devices: 2

NS-BSD/arm U-Boot loader, Revision 1.1
DRAM:    512MB

Device: disk
...
Kernel entry at 0x900100 ...
 dtbp = 0x80e8d340
Copyright (c) 1992-2013 The FreeBSD Project.
Copyright (c) 1979, 1980, 1983, 1986, 1988, 1989, 1991, 1992, 1993, 1994
        The Regents of the University of California. All rights reserved.
FreeBSD is a registered trademark of The FreeBSD Foundation.
NS-BSD 1.2.0.dev- #0: Tue Jun 17 09:36:05 CEST 2014
    build@buildmajtrunkarm.netasq.com:/usr/home/build/fw-SAMOA/sys-9.2/work/sys/arm/compile/NETASQ.S.NOSMP.HW.RELEASEm
gcc version 4.2.1 20070831 patched [FreeBSD]
...
```
We can see that **ubldr** is then loading a FreeBSD kernel based OS; read more on [FreeBSD ARM : Before Kernel](https://www.bsdcan.org/2017/schedule/attachments/424_before_kernel.pdf)

## Update U-boot

As we seen Stormshield SNS uses [U-boot](https://www.denx.de/wiki/U-Boot) during boot, but the version is a bit old.
```
SN150>> version

U-Boot 2012.04.01-Semihalf_SW-R2.4 (Jun 10 2014 - 08:22:48)SN150

arm-linux-gnueabi-gcc (GCC) 4.2.2
GNU ld (GNU Binutils for Ubuntu) 2.22
```

Let's use a newer version of U-boot to have more detail.

At boot, a Marvell Kirkwood board will load a **kwb** image that is then interpreted by Marvell's BootROM firmware. Boot image files will typically contain a second stage boot loader, such as [U-boot](https://www.denx.de/wiki/U-Boot).

On SNS, this image is stored and loaded from a SPI Flash memory.
```
SN150>> sf probe 0
SF: Unsupported manufacturer 00
Failed to initialize SPI flash at 0:0
SN150>> sf probe 1
SF:    Detected MX25L4005 with page size 64 KiB, total 512 KiB
```
And we can read its content as follow (ref. [Programming QSPI Flash
](https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/18842223/U-boot#U-boot-ProgrammingQSPIFlash))
```
SN150>> sf read 0x08000000 0 100
SN150>> md 08000000
08000000: 0800005a 00037a90 00000000 00000200    Z....z..........
08000010: 00600000 00600000 00000000 32010000    ..`...`........2
08000020: 00000040 00000000 00000000 00000000    @...............
08000030: 00000000 00000000 00000000 00000000    ................
08000040: ffd100e0 1b1b1b9b ffd01400 43000c30    ............0..C
08000050: ffd01404 37543000 ffd01408 22125441    .....0T7....AT."
08000060: ffd0140c 00000a32 ffd01410 000000cc    ....2...........
08000070: ffd01414 00000000 ffd01418 00000000    ................
08000080: ffd0141c 00000652 ffd01420 00000004    ....R... .......
08000090: ffd01424 0000f17f ffd01428 00085520    $.......(... U..
080000a0: ffd0147c 00008552 ffd0148c 00000000    |...R...........
080000b0: ffd01490 00000000 ffd01500 00000000    ................
080000c0: ffd01504 0ffffff1 ffd01508 10000000    ................
080000d0: ffd0150c 0ffffff5 ffd01514 00000000    ................
080000e0: ffd0151c 00000000 ffd01494 00120012    ................
080000f0: ffd01498 00000000 ffd0149c 0000e80f    ................

```

**DO NOT** erase/write its content if you don't kwow what you're doing !!!

### Load in RAM

Here is how to load in RAM a new [U-boot](https://www.denx.de/wiki/U-Boot) image over serial interface, keeping the original one (on SPI Flash memory) safe (for now).

  - Make sure your SNS has a Marvell Kirkwood BootROM version 1.21
```
SN150>> md ff00003c
ff00003c: 00000121 e3a00000 e59f222c e5921000    !.......,"......
...
```
Here 00000**121** means **v1.21**. So we are good. This means it can load image over serial. Really helpful in case you brick your SNS.
  - Make sure to have **u-boot-tools** installed on your computer.
    On _Debian_/_Ubuntu_i, install it by running:
```bash
sudo apt install u-boot-tools
```
  - Download a _U-boot_ build for a compatible board (same SoC). I'll use [u-boot.kwb](http://ftp.debian.org/debian/dists/stretch/main/installer-armel/current/images/kirkwood/u-boot/sheevaplug/u-boot.kwb) from [Upgrading u-boot on SheevaPlug
](https://www.cyrius.com/debian/kirkwood/sheevaplug/uboot-upgrade/). 

  - Run _kwboot_ (part of _u-boot-tools_)
```bash
kwboot -t -B 115200 /dev/ttyUSB0 -b u-boot.kwb
```
Note: In case of _/dev/ttyUSB0: Permission denied_, you might have to run the above command as _sudo_ or add your user to _dialout_ group.

  - Reboot (unplug and re-plug power) device.

You should see the file being transfered and loaded; giving you acces to U-boot.
```
Sending boot message. Please reboot the target.../
Sending boot image...
  0 % [......................................................................]
  1 % [......................................................................]
  3 % [......................................................................]
  5 % [......................................................................]
  7 % [......................................................................]
...
 98 % [.......................................]
[Type Ctrl-\ + c to quit]


U-Boot 2016.11+dfsg1-4 (Mar 27 2017 - 18:39:51 +0000)
Marvell-Sheevaplug

SoC:   Kirkwood 88F6281_A1
DRAM:  512 MiB
WARNING: Caches not enabled
NAND:  0 MiB
MMC:   MVEBU_MMC: 0
*** Warning - readenv() failed, using default environment

In:    serial
Out:   serial
Err:   serial
Net:   egiga0
Error: egiga0 address not set.

PHY reset timed out
88E1116 Initialized on egiga0
IDE:   ide_preinit failed
Hit any key to stop autoboot:  0 

no devices available
Wrong Image Format for bootm command
ERROR: can't get kernel image!
```

If it fails, just try again.
Do not pay attention to _Warning_ and _Error_, here.

Let's see if we can have more information.

```
=> mmc list
MVEBU_MMC: 0 (SD)
=> mmcinfo
Device: MVEBU_MMC
Manufacturer ID: 74
OEM: 4a45
Name: USD
Bus Speed: 50000000
Mode: SD High Speed (50MHz)
Rd Block Len: 512
SD version 3.0
High Capacity: Yes
Capacity: 3.8 GiB
Bus Width: 4-bit
Erase Group Size: 512 Bytes
```
Now we know that Internal MMC is SDHC card with **3.8GiB**


```
=> nand device

no devices available
=> ide info
Device 0: device type unknown
Device 1: device type unknown
```
This means that the device has no NAND internal storage, nor IDE device connected.

We can see that even if this [U-boot](https://www.denx.de/wiki/U-Boot) image bring some extra commands, it misses some, as we can see when typing `sf` command. (SheevaPlug has no SPI Flash memory, thus no need to brings `sf` command in image.
```
=> sf
Unknown command 'sf' - try 'help'
```

### Dump SPI Flash

As we said before, [U-boot](https://www.denx.de/wiki/U-Boot) lives on SNS SPI Flash memory. Let's dump it and make a backup. The easiest way to dump a flash memory is via an external reader device.
Unfortunately, we can't afford to open or even desoldering the flash for reading it; so conventional tools for reading SPI flash is not useful here.

Though, we can read its content on command line, using `sf` U-boot command.

Use [dump_spi.py](script/dump_spi.py) to dump the SPI Flash memory content to file.
This script basically runs multiple `sf` commands to load content in RAM and `md` commands to display RAM content on stdout. It concatenate output and convert the result to binary file in current directory (*dump_spi.kwb*).

Note: It relies on Python [pyserial](https://pypi.org/project/pyserial/) package.

**Test** that the dump is bootable (ref. to [Load in RAM](#load-in-ram)) and **save it cautiously**.

### Build new version

Let's build a new version of [U-boot](https://www.denx.de/wiki/U-Boot) up-to-date, that matches our hardware requirements.

 - Let's clone from GitHub
```
git clone https://github.com/u-boot/u-boot
```

We're gonna extend _arch/arm/mach-kirkwood/Kconfig_ to include board Stormshield SN150.

Then, according to [README.kwbimage](https://raw.githubusercontent.com/u-boot/u-boot/master/doc/README.kwbimage), we need to write a _Board specific configuration file_ (kwbimage.cfg)

Let's not re-invent the wheel. We have a running [U-boot](https://www.denx.de/wiki/U-Boot) and a dump file, use them.

```
SN150>> bdinfo
arch_number = 0x00000692
boot_params = 0x00000100
DRAM bank   = 0x00000000
-> start    = 0x00000000
-> size     = 0x10000000
DRAM bank   = 0x00000001
-> start    = 0x10000000
-> size     = 0x10000000
ethaddr     = 00:0D:B4:0E:9A:30
ip_addr     = 0.0.0.0
baudrate    = 115200 bps
TLB addr    = 0x1FFF0000
relocaddr   = 0x1FF66000
reloc off   = 0x1F966000
irq_sp      = 0x1FE55F5C
sp start    = 0x1FE55F50
FB base     = 0x00000000
```

This matches `#define MACH_TYPE_RD88F6281            1682` (0x692 = 1682) defined in _arch/arm/include/asm/mach-types.h_


```cfg
# Boot Media configurations
BOOT_FROM       spi     # Boot from SPI flash

# Configure RGMII-0 interface pad voltage to 1.8V
DATA 0xffd100e0 0x1b1b1b9b

DATA 0xffd01400 0x43000c30      # DDR Configuration register
# bit13-0:  0xc30, (3120 DDR2 clks refresh rate)
# bit23-14: 0x0,
# bit24:    0x1,   enable exit self refresh mode on DDR access
# bit25:    0x1,   required
# bit29-26: 0x0,
# bit31-30: 0x1,

DATA 0xffd01404 0x37543000      # DDR Controller Control Low
# bit4:     0x0, addr/cmd in smame cycle
# bit5:     0x0, clk is driven during self refresh, we don't care for APX
# bit6:     0x0, use recommended falling edge of clk for addr/cmd
# bit14:    0x0, input buffer always powered up
# bit18:    0x1, cpu lock transaction enabled
# bit23-20: 0x5, recommended value for CL=5 and STARTBURST_DEL disabled bit31=0
# bit27-24: 0x7, CL+2, STARTBURST sample stages, for freqs 400MHz, unbuffered DIMM

```

Now build your new [U-boot](https://www.denx.de/wiki/U-Boot) kwb image.

```bash
$ cd u-boot
$ make mrproper
$ make sn150_defconfig
$ make
```

## Linux

### Boot

A vanilla _Debian_ or _Arch_ should boot fine with **machid** _0x692_. 
Note: The mainline [U-boot](https://www.denx.de/wiki/U-Boot) command to set the machine id has since changed from _arcNumber_ to _machid_.

```
SN150>> setenv machid '0x692'
SN150>> setenv bootcmd_usb 'usb start; fatload usb 0:1 0x6400000 /uImage-ipfire-kirkwood; fatload usb 0:1 0x6800000 /uInit-ipfire-kirkwood'
setenv bootcmd 'setenv bootargs 'console=ttyS0,115200 root=/dev/sda3 rootdelay=5'; run bootcmd_usb; bootm 0x6400000 0x6800000'
saveenv
```

### Build

On _Debian_/_Ubuntu_ install cross-compilation toolchain
```bash
sudo apt install gcc-arm-linux-gnueabi
```

```bash
# Download Linux kernel source code
git clone https://github.com/torvalds/linux
cd linux

export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabi-
make multi_v5_defconfig

# Build kernel
make -j5 uImage modules
```

Congratulations ! You now have a Stormshield SNS running **Linux**.

## References

 * FreeBSD:
   * [rickvanderzwet wiki - DreamPlug](https://rickvanderzwet.nl/trac/personal/wiki/DreamPlug)
   * [FreeBSD on Marvell Kirkwood systems](https://wiki.freebsd.org/FreeBSD/arm/Kirkwood)
   * [FreeBSD/arm for Marvell Orion, Kirkwood and Discovery systems-on-chip](https://wiki.freebsd.org/FreeBSD/arm/Marvell)
   * [FreeBSD ARM : Before Kernel](https://www.bsdcan.org/2017/schedule/attachments/424_before_kernel.pdf)

 * U-boot:
   * [UART Booting HowTo for Selected Kirkwood Devices](https://forum.doozan.com/read.php?3,7852,7852)
   * [Pastebin - Boot Openwrt on RaidSonic ICY BOX](http://pastebin.lukaperkov.net/openwrt/20131124_kirkwood_openwrt.txt)
   * [booss.org - ZYXEL NSA310 U-BOOT VARIABLES TO BOOT LINUX FROM A USB STICK](https://booss.org/zyxel-nsa310-u-boot-variables-to-boot-linux-from-a-usb-stick/)
   * [Upgrading u-boot on SheevaPlug](https://www.cyrius.com/debian/kirkwood/sheevaplug/uboot-upgrade/)

 * Linux:
   * [Build your own kernel prepared for u-boot with device tree appended](http://lacie-nas.org/doku.php?id=making_kernel_with_dtb)
   * [Linux Kernel 5.1.0 Kirkwood package and Debian rootfs](https://forum.doozan.com/read.php?2,12096)
   * [How To: Running Fedora-ARM on Sheevaplug](https://fedoraproject.org/wiki/Architectures/ARM/PlatformSheevaplug)
   * [Updating the Kernel on the GuruPlug
](https://wiki.beyondlogic.org/index.php?title=Updating_the_kernel_on_the_GuruPlug)

 * Marvell SoC / Macronix NOR SPI Flash:
   * [Macronix MX25L4005, MX25L8005 Datasheet](https://www.mct.net/download/macronix/mx25l8005.pdf)
   * [Programming QSPI Flash](https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/18842223/U-boot#U-boot-ProgrammingQSPIFlash)
   * [88F6180, 88F6190, 88F6192, and 88F6281 Integrated Controller - Functional Specifications](https://wikidevi.com/files/Marvell/FS_88F6180_9x_6281_OpenSource.pdf)
