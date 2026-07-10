# Infinix X676B — U-Boot Project State

## Project Goal

Replace stock LK (Little Kernel) bootloader with U-Boot on Infinix Note 12 Pro (X676B) with MediaTek MT6789/MT8781 SoC, to enable booting Android and eventually booting from SD card.

## Constraints & Rules

- User communicates in Russian
- Use ADB shell (not SSH — sshd on device died)
- Save all work files to `/workdir/git/heliog99/u-boot-x676b/`
- Do NOT run `sudo pacman` — ask user to install packages
- Use existing venv at `/workdir/git/heliog99/mtkclient/venv/` for Python packages
- Clone large repos to `/workdir/git/heliog99/` with `--depth=1`
- Always provide flash/rollback commands to user, don't flash yourself
- User has root access on device (su works via ADB)
- User has CH340 USB-UART adapter connected (921600 baud, testpoints found near fingerprint connector)
- User has picocom for UART log capture

---

## Hardware

- **SoC**: MediaTek Helio G99 (MT6789), ARM64, 2x A76 + 6x A55
- **RAM**: 8 GB (4+4 banks)
- **Storage**: SK Hynix H9QT1G6DN6X132 UFS 2.2, 238.3 GB
- **Display**: 1080x2400 AMOLED, framebuffer at `0xfe0c8000` (from real device DT)
- **SD Card**: Yes, via `mmc@11240000` (MTK SDHC2), 32GB card present
- **UFS LUNs**: sda (4MB boot), sdb (4MB boot), sdc (238GB main)
- **UART**: ttyS0 at 0x11002000, 921600 baud, testpoints near fingerprint connector (6 pins)

### Correct compatible strings (from real device DT, NOT default mt6789.dtsi)

| Device | U-Boot DTS (old) | Real Device DT |
|--------|------------------|----------------|
| Watchdog | `mediatek,mt8781-wdt` | `mediatek,mt6789-wdt` |
| UFS | `mediatek,mt6789-ufshci` | `mediatek,mt8183-ufshci` |
| USB | `mediatek,mt8518-musb` | `mediatek,mt6789-usb20` |
| MMC | `mediatek,mt8183-mmc` | `mediatek,mt6789-mmc` |
| pinctrl | `mediatek,mt6789-pinctrl` | `mediatek,mt6789-pinctrl` ✓ |

---

## Kernel cmdline (from stock LK `/proc/cmdline`)

```
console=tty0 root=/dev/ram loglevel=8 8250.nr_uarts=4 initcall_debug=1 mtk_printk_ctrl.disable_uart=1 bootopt=64S3,32N2,64N2 PN=x676b_h891 arm64.nomte tkv=294930432 bootconfig
```

- `mtk_printk_ctrl.disable_uart=1` — UART disabled in kernel by default, must set to `0` for debug
- `bootopt=64S3,32N2,64N2` — boot partition sizes
- `PN=x676b_h891` — product name
- `arm64.nomte` — no MTE (memory tagging)
- `tkv=294930432` — TKV version
- `bootconfig` — uses Android Boot Configuration (bootconfig.txt in boot image)

---

## Android Image Structure

### boot.img
- Header version: **v4**
- Kernel: gzip compressed, ~19 MB, starts at offset 0x1000 from boot.img start
- No embedded DTB in kernel
- DTB comes from vendor_boot.img

### vendor_boot.img
- Header version: **v4**, page_size=0x1000
- Ramdisk: LZ4 compressed, ~26 MB, loadAddr=0x66f00000
- DTB: wrapped in DTBO header (magic `d7b7ab1e`), actual DTB at offset +0x40
- DTB is a **base DTB** (contains /chosen, /memory, /cpus, /soc)
- Partition on device is only 2-4 MB — DTB (at offset 26MB) is NOT fully in the partition

### dtbo.img (from firmware)
- 8MB, 1 entry, DTB at offset 0x40 (56KB)
- DTB magic: `d00dfeed` (valid)
- Contains camera/pinctrl overlays
- Used as FDT source for bootm in U-Boot

### bootconfig.txt (Android Boot Configuration)
- Contains ramdisk size, serial numbers, FSPM, MCDT entries
- Can be appended to kernel cmdline or provided as separate file

---

## Boot Flow

```
Preloader → U-Boot (in lk_a/lk_b) → boot.img kernel → Android
```

- Preloader is proprietary (cannot be replaced)
- U-Boot replaces LK in lk_a/lk_b partitions
- `gimme-uboot.py` from `liblk` packages U-Boot binary into LK image format
- Flash via `fastboot flash lk_a/lk_b`

---

## Key U-Boot Issues Found

### 1. Framebuffer crash (partially fixed)
- **Problem**: simple-framebuffer at `0xfe0c8000` causes Synchronous Abort
- **Root cause**: Address not mapped in U-Boot MMU
- **Fix**: Removed simple-framebuffer from DTS, address used only by splash (no crash now)
- **Status**: Splash image doesn't display but doesn't crash

### 2. MUSB gadget compile failure (NOT FIXED)
- **Problem**: `CONFIG_USB_MUSB_GADGET` fails to compile
- **Error**: Missing `dma_init()`, `dma_poll_complete()`, `dma_unmap_single()` functions
- **Root cause**: MediaTek musb_dma module is incomplete for this SoC
- **Fix attempted**: Added `CONFIG_ARCH_DMA_PADDR_LEN=64` — didn't help
- **Status**: fastboot over USB not working

### 3. Button support (partially fixed)
- **Problem**: No working button input in U-Boot
- **Hardware**: MediaTek KP controller at `0x11012000` (ADC-based)
- **Fix**: Added `CONFIG_BUTTON=y` and `CONFIG_BUTTON_ADC=y` with custom keys definition
- **Keys configured**: Volume Up (code 115), Volume Down (code 114), Power (code 116)
- **Status**: DTS for KP/ADC keys not fully implemented — needs proper ADC channel DTS

### 4. Kernel panic at boot (NOT FIXED)
- **Problem**: Kernel panics immediately after loading
- **Root cause**: DTBO DTB used as FDT is not fully compatible with device hardware
- **Error in boot log**:
  ```
  [    0.344825] Kernel panic - not syncing: Attempted to kill init! exitcode=0x0000000b
  [    0.344825] CPU: 7 PID: 1 Comm: swapper/0 Not tainted 4.19.191+ #1
  [    0.344825] Call trace:
  [    0.344825]  dump_backtrace+0x0/0x1c0
  [    0.344825]  show_stack+0x24/0x30
  [    0.344825]  dump_stack_lvl+0x68/0x84
  [    0.344825]  dump_stack+0x14/0x1c
  [    0.344825]  panic+0x13c/0x334
  [    0.344825]  do_exit+0x7b0/0x960
  [    0.344825]  do_group_exit+0x44/0xa8
  [    0.344825]  __arm64_sys_exit_group+0x7c/0x84
  [    0.344825]  el0_svc_common+0xb4/0x110
  [    0.344825]  do_el0_svc+0x2c/0x84
  [    0.344825]  el0_svc+0x20/0x30
  [    0.344825]  el0_sync_handler+0x78/0xf0
  [    0.344825]  el0_sync+0x174/0x180
  ```
- **Status**: Kernel tries to run init, fails, exits with SIGILL

### 5. Display (NOT FIXED)
- **Problem**: No display output on screen
- **Root cause**: simple-framebuffer removed, no DRM driver loaded
- **Status**: Splash image not visible, display driver not implemented

---

## What Was Accomplished

1. ✅ Full reverse engineering of device hardware (compatible strings, memory map, partition layout)
2. ✅ Created U-Boot defconfig for Infinix X676B
3. ✅ Created device tree (mt6789-infinix-x676b.dts) based on real device DT
4. ✅ Built U-Boot 2025.10-rc5 from ellyq/u-boot-mtk-g99 fork
5. ✅ Created `gimme-uboot.py` workflow to package U-Boot into LK format
6. ✅ Identified correct framebuffer address (0xfe0c8000) from real device DT
7. ✅ Found UART testpoints on device
8. ✅ Booted U-Boot successfully (menu shows on UART)
9. ✅ Kernel loads and starts (but panics — wrong DTB)
10. ✅ Identified all compatible string mismatches between DTS and real device
11. ✅ Identified crash cause: simple-framebuffer at 0xfe0c8000 not mapped in MMU
12. ✅ Added full kernel cmdline from stock LK (with `mtk_printk_ctrl.disable_uart=0`)
13. ✅ Added `panic=10` for debug
14. ✅ Enabled ADC button support
15. ✅ Enabled various fastboot/USB configs
16. ✅ Patched bootm.c to use `fdt_addr_r` when set (FDT override patch)
17. ✅ Unpacked firmware images for analysis
18. ✅ Found all compatible strings from real device DT via /sys/firmware/fdt
19. ✅ Created U-Boot env file (mtk-phone.env) with extensive debug configs
20. ✅ Removed simple-framebuffer from DTS (v32)
21. ✅ Added bootconfig.txt content to env file

---

## What Still Needs Fixing

1. **Kernel panic** — DTBO DTB not fully compatible with device hardware, need correct base DTB
2. **Display** — simple-framebuffer doesn't work, need proper display driver (DRM/MTK DRM)
3. **Button support** — ADC buttons need proper DTS with adc-keys
4. **USB fastboot** — MUSB gadget compile error
5. **U-Boot boot menu on screen** — currently only on UART
6. **Boot from SD card** — long term goal

---

## U-Boot Configuration (mt6789_infinix_x676b_defconfig key settings)

```
CONFIG_ARCH_MEDIATEK=y
CONFIG_TARGET_MT6789=y
CONFIG_DEFAULT_DEVICE_TREE="mt6789-infinix-x676b"
CONFIG_BOOT_SCRIPT_OFFSET=0x0
CONFIG_ENV_IS_IN_MMC=y
CONFIG_ENV_ADDR=0x0
CONFIG_ENV_FAT_DEVICE_AND_PART="mmc1:1"
CONFIG_ENV_FAT_FILE="uboot.env"
CONFIG_ENV_SIZE=0x80000
CONFIG_ENV_SIZE_LIST="128k,128k,512k,128k"
CONFIG_PREBOOT="echo env test;fastboot 10"
CONFIG_SYS_REDUNDAND_ENVIRONMENT=y
CONFIG_SPL_BOOTIDLE=y
CONFIG_CMD_BOOTMENU=y
CONFIG_CMD_FASTBOOT=y
CONFIG_CMD_FB_TEST=y
CONFIG_CMD_GPT=y
CONFIG_CMD_PSTORE=y
CONFIG_CMD_PSTORE_MEM=y
CONFIG_PSTORE=y
CONFIG_PSTORE_RAM=y
CONFIG_ANDROID_BOOT_IMAGE=y
CONFIG_BUTTON=y
CONFIG_BUTTON_ADC=y
CONFIG_DM_REGULATOR_FIXED=y
CONFIG_DM_REGULATOR=y
CONFIG_DM_REGULATOR_GPIO=y
CONFIG_VIDEO=y
CONFIG_VIDEO_LOGO=y
CONFIG_VIDEO_BMP_RLE8=y
CONFIG_SPLASH_SCREEN=y
CONFIG_SPLASH_SOURCE=y
CONFIG_CMD_BMP=y
CONFIG_CMD_PANIC=y
CONFIG_AUTOBOOT_KEYED=y
CONFIG_AUTOBOOT_DELAY_STR="1"
CONFIG_AUTOBOOT_KEYED=y
CONFIG_AUTOBOOT_STOP_KEY="volume-down"
CONFIG_AUTOBOOT_STOP_KEY_2="volume-up"
CONFIG_CMD_BOOTD=y
CONFIG_CMD_SOURCE=y
CONFIG_DM_MMC=y
CONFIG_MMC=y
CONFIG_MMC_MTK=y
CONFIG_FDT=y
CONFIG_CMD_FDT=y
CONFIG_FDT_FIXUP_PARTITIONS=y
CONFIG_SPL=y
CONFIG_SPL_MMC=y
CONFIG_SPL_DM_MMC=y
CONFIG_SPL_FS=y
CONFIG_SPL_FS_FAT=y
CONFIG_SPL_LIBDISK_SUPPORT=y
CONFIG_SYS_MMC_ENV_DEV=1
CONFIG_ANDROID_AB=y
CONFIG_USB=y
CONFIG_USB_GADGET=y
CONFIG_USB_GADGET_MANUFACTURER="MediaTek"
CONFIG_USB_GADGET_VENDOR_NUM=0x0E8D
CONFIG_USB_GADGET_PRODUCT_NUM=0x0003
CONFIG_CI_UDC=y
CONFIG_DRIVERS_USB_MUSB=y
CONFIG_DRIVERS_USB_MUSB_GADGET=y
```

---

## Key Files

### Project working directory
- `/workdir/git/heliog99/u-boot-x676b/` — all project files
  - `lk_a_dump.img` — original LK dump (4MB, for rollback)
  - `uboot-lk-x676b-v32.img` — latest U-Boot LK image (ready to flash)
  - `u-boot-v32.bin` — latest U-Boot binary
  - `mt6789-infinix-x676b.dts` — device tree for U-Boot
  - `mt6789_infinix_x676b_defconfig` — U-Boot defconfig
  - `uart-log-*.txt` — all UART logs from testing
  - `dtb_from_firmware.bin` — extracted DTB from firmware dtbo.img

### U-Boot source (modified)
- `/workdir/git/heliog99/u-boot-mtk-g99/` — U-Boot source tree (ellyq fork)
  - `arch/arm/dts/mt6789-infinix-x676b.dts` — device tree (edited)
  - `arch/arm/dts/mt6789.dtsi` — base SoC DTS (unmodified)
  - `configs/mt6789_infinix_x676b_defconfig` — build config (edited)
  - `board/mediatek/mtk-phone.env` — U-Boot env file (edited extensively)
  - `boot/bootm.c` — patched with fdt_addr_r override (lines ~500-520)
  - `gimme-uboot.py` — tool to package U-Boot into LK format

### Firmware / analysis
- `/workdir/git/heliog99/firmware/Infinix_Note_12_Pro_X676B_MT6789_V2385_221208_MXML/Firmware/` — stock firmware files
- `/workdir/git/heliog99/unpack/` — unpacked boot.img, vendor_boot.img, dtbo.img
- `/workdir/git/heliog99/unpack/vendor_boot/vendor_boot.json` — vendor_boot metadata
- `/workdir/git/heliog99/unpack/dtbo/dtbo.json` — dtbo metadata
- `/workdir/git/heliog99/mtkclient/` — mtkclient tool (with venv)

### External references
- `https://github.com/ellyq/u-boot-mtk-g99` — U-Boot fork for MT6789
- `https://github.com/linux-mediatek/linux/tree/mt6789-next` — Linux kernel fork (being cloned to `/workdir/git/heliog99/linux/`)
- `https://wiki.postmarketos.org/wiki/MediaTek_Helio_G99_(MT6789/MT8781)` — postmarketOS wiki

---

## Boot Patch Applied

File: `boot/bootm.c` around line 500-520 — adds `fdt_addr_r` override so bootm uses the DTB from dtbo_a instead of the embedded DTB in boot.img. This allows using a different DTB than what's in the boot image.

---

## UART Log (boot sequence, key points)

1. Preloader runs (not logged)
2. U-Boot starts, shows menu:
   ```
   MMC/SD Card: MediaTek:SDHC:1 (eMMC)          234.2MiB (119,936 x 2048)   MMC/SD Card
   MMC/SD Card: MediaTek:SDHC:2 (SD Card)         29.7GiB (61,388,800 x 512) SD Card
   ```
3. U-Boot shows env vars, test messages
4. U-Boot loads boot.img, reads kernel (~19MB)
5. U-Boot loads ramdisk (~26MB)
6. U-Boot applies DTBO (fdt apply command)
7. U-Boot boots kernel with bootm
8. Kernel starts, but panics with "Attempted to kill init!"

---

## Next Steps

1. **Find correct base DTB** — extract from vendor_boot.img DTB or find in Linux kernel tree for MT6789
2. **Fix display** — investigate DRM/MTK DRM driver, find correct display registers
3. **Fix kernel boot** — proper DTB compatibility, correct compatible strings
4. **Fix button support** — proper ADC keys DTS
5. **Fix USB fastboot** — resolve MUSB gadget compile issues
