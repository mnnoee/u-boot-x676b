# U-Boot X676B — Dump последних 5 версий образов

## v51 — Исправление PHY base address
- **Файл**: `uboot-lk-x676b-v51.img`
- **Изменение**: `USB20_PHY_BASE` изменён с `0x11110800` (MT8518) на `0x11f40000` (MT6789)
- **Результат**: PHY probe НЕ работает (ENOMEM), PC не видит USB
- **Причина**: `mt_usb_phy_poweron()` пишет в неправильный PHY. Нужен правильный tphy driver

## v52 — Проброс PHY перед MUSB probe
- **Файл**: `uboot-lk-x676b-v52.img`
- **Изменение**: Добавлен `uclass_get_device_by_name(UCLASS_PHY, "t-phy@11f40000")` в `board_usb_init`
- **Результат**: PHY probe failed: -12 (ENOMEM). PC не видит USB
- **Причина**: PHY node в DTS имеет неправильную структуру — child `u2port0` имеет `reg = <0 0x700>` (относительный) вместо абсолютного адреса

## v53 — Bootmenu + отключение автобута
- **Файл**: `uboot-lk-x676b-v53.img`
- **Изменение**: `mtk-phone.env` — `bootdelay=0`, `bootcmd=run menucmd`, bootmenu с "Fastboot USB" первой опцией
- **Результат**: Bootmenu появляется сразу. PC не видит USB

## v54 — Исправление PHY DTS (абсолютные адреса)
- **Файл**: `uboot-lk-x676b-v54.img`
- **Изменения в `mt6789.dtsi`**:
  - Убран `reg` с родительского узла `u2phy` (как в реальном DTB)
  - Дочерний `u2port0`: `reg = <0 0x11f40000 0 0x700>` (абсолютный адрес вместо относительного `<0 0x700>`)
  - Убран `mediatek,eye-src`
- **Результат**: PHY probe OK! `MUSB: PHY probed OK`. Но PC всё ещё не видит USB
- **Проблема**: `musb_g_reset()` вызывает `musb_g_disconnect()` (pullup off) но НЕ включает pullup обратно после USB reset

## v55 — Исправление pullup после USB reset
- **Файл**: `uboot-lk-x676b-v55.img`
- **Изменение в `musb_gadget.c`**: Добавлен блок `#ifdef __UBOOT__` в конец `musb_g_reset()` — если `musb->softconnect` был 1 до reset, переключает pullup обратно
- **Ожидание**: PC видит USB устройство, `fastboot devices` работает

---

## Итого что исправлено за сессию

1. **reg-names mismatch** — `reg-names = "mac", "ippc"` с одним reg entry ломал `dev_read_addr_ptr()`. Убран из dtsi
2. **Clock names** — `"main", "mcu", "univpll"` → `"usbpll", "usbmcu", "usb"` (как ожидает MUSB driver)
3. **PHY base address** — `0x11110800` → `0x11f40000`
4. **PHY DTS structure** — child node `u2port0` теперь с абсолютным адресом reg
5. **MUSB reg format** — `<0 0x11200000 0 0x10000>` (2+2 ячейки) вместо `<0 0x11200000 0 0x10000>` (4 ячейки) — исправлено для совместимости с `soc@0` `#address-cells=1`
6. **DM_USB_GADGET=n** — используется old-style `usb_gadget_register_driver` из `musb_uboot.c`
7. **board_usb_init** — триггерит DM probe MUSB через `uclass_get_device_by_seq`
8. **Bootmenu** — `bootdelay=0`, bootmenu сразу при загрузке
9. **musb_g_reset pullup fix** — pullup переключается обратно после USB reset

---

## Реальный DTB (из vendor_boot)

Ключевые ноды из `заметки/devtree/real_base.dtb`:

```
usb: usb0@11200000 {
    compatible = "mediatek,mt6789-usb20";
    reg = <0x00 0x11200000 0x00 0x10000 0x00 0x11f40000 0x00 0x10000>;
    clocks = <0x2b 0x22 0x2a 0x1d 0x3b 0x0d>;
    clock-names = "sys_clk", "ref_clk", "src_clk";
    phys = <0x63 0x03>;
    mode = <0x02>;
    num_eps = <0x10>;
    dr_mode = "otg";
};

u2phy0: usb-phy@11f40000 {
    compatible = "mediatek,generic-tphy-v2";
    u2port0: usb-phy@11f40000 {
        reg = <0x00 0x11f40000 0x00 0x700>;
        mediatek,eye-vrt = <0x04>;
        mediatek,eye-term = <0x04>;
        mediatek,rev4 = <0x01>;
        mediatek,discth = <0x07>;
    };
};
```

---

## Источники

- `заметки/devtree/` — реальный DTB из vendor_boot
- `src_linux/mtk_g99-mainline/` — mainline Linux kernel (уже загрузился!)
- `src_linux/u-boot-mt6789/` — official U-Boot for MT6789 (JamiKettunen fork)
- U-Boot source: `/workdir/git/heliog99/u-boot-mtk-g99/`
