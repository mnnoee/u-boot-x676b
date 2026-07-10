// SPDX-License-Identifier: GPL-2.0+
/*
 * Board USB init for Infinix X676B (MT6789)
 * Probes MUSB device and registers UDC for fastboot
 */

#include <common.h>
#include <dm.h>
#include <usb.h>

int board_usb_init(int index, enum usb_init_type init)
{
	struct udevice *dev;
	int ret;

	if (init != USB_INIT_DEVICE)
		return -ENODEV;

	/* Find and probe the MUSB USB gadget device */
	ret = uclass_get_device_by_driver(UCLASS_USB_GADGET_GENERIC,
					  DM_DRIVER_GET(mtk_musb), &dev);
	if (ret) {
		printf("MUSB: board_usb_init: device not found: %d\n", ret);
		return ret;
	}

	printf("MUSB: board_usb_init: device probed successfully\n");
	return 0;
}
