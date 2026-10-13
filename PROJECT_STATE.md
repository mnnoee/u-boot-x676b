# Infinix X676B — состояние проекта / Project state

**Задача:** заменить стоковый LK (Little Kernel) на U-Boot на Infinix Note 12 Pro
(X676B, MediaTek MT6789 / Helio G99), чтобы получить рабочий загрузчик с
управлением по USB и загрузкой Android, а в конечную цель — загрузку с SD-карты.

**The goal:** replace the stock LK (Little Kernel) bootloader with U-Boot on the
Infinix Note 12 Pro (X676B, MediaTek MT6789 / Helio G99), to get a bootloader with
USB control and Android boot, and ultimately to boot from the SD card.

> Файл переписан 2026-10-13. Предыдущая версия описывала этап июля и была
> неактуальна: USB и дисплей тогда ещё не работали, дисплей был записан как
> неподдерживаемый.
>
> This file was rewritten on 2026-10-13. The previous version described the July
> stage and was outdated: USB and the display did not work yet, and the display
> was listed as unsupported.

---

## Статус / Status

### Работает / Working

| Подсистема | Детали |
|---|---|
| **Дисплей** | текст U-Boot на AMOLED 1080×2400. Свой драйвер `drivers/video/mediatek/mtk_disp_g99.c` (453 строки) перенастраивает тракт OVL0 → RDMA0 → DITHER0 → DSI0; панель ILI7835F и сам DSI инициализирует стоковый LK. Работает с v183/v187 |
| **USB fastboot** | телефон перечисляется на ПК по USB. Конфиг: `CONFIG_USB_FUNCTION_FASTBOOT=y`, PIO-режим |
| **Консоль по USB (CDC ACM)** | `usbacm` на stdin/stdout/stderr. UART-кабель не нужен. Включается пунктом меню, не автоматически |
| **UMS / fastboot block** | память телефона видна на ПК: `ums 0 scsi 2` — разделы идут через SCSI-слой UFS |
| **Кнопки** | Volume Up / Down. Свой драйвер `drivers/button/button-mtk-kp.c` (204 строки), узлы в DTS, Volume Up = Enter, Volume Down = скролл. Работает с v88/v89 |
| **Часы** | драйвер часов MT6789 переписан с нуля (709 → 191 строка). Без него не включаются ни дисплей, ни SD, ни USB |
| **UFS** | чтение и запись работают |

### Не работает / Not working

| Подсистема | Состояние |
|---|---|
| **SD-карта** | контроллер MSDC1 поднимается, карта не отвечает: `CMD8` → `INT=0x400`, `RSP=0`, CRCERR `0x480`. **Текущий блокер** |
| **Загрузка Android** | ядро стартует и паникует: `Attempted to kill init!` — не тот DTB. Работы не начаты |
| **Кнопки в U-Boot** | водитель работает, но в U-Boot нет полноценного меню на экране — только текст |

---

## Где что лежит / Repository layout

| Репозиторий | Содержимое |
|---|---|
| **[u-boot-mtk-g99](https://github.com/mnnoee/u-boot-mtk-g99)** | исходники U-Boot, все самописные драйверы, DTS, документация. Ветка `mt6789-stable`, 84 коммита над `ellyq` |
| **[u-boot-x676b](https://github.com/mnnoee/u-boot-x676b)** ← этот | прошиваемые образы, скрипты, это состояние проекта |
| **[u-boot-x676b_docs](https://github.com/mnnoee/u-boot-x676b_docs)** | сырые заметки по сессиям, живые дампы Android |
| **[x676b-tools](https://github.com/mnnoee/x676b-tools)** | скрипты анализа, гайды Ghidra, дизассемблированный LK (локально) |

---

## Ключевые файлы / Key files

| Файл | Роль |
|---|---|
| `configs/mt6789_infinix_x676b_defconfig` | конфигурация сборки |
| `arch/arm/dts/mt6789-infinix-x676b.dts` | device tree: узлы кнопок, переопределения совместимости |
| `arch/arm/dts/mt6789.dtsi` | общий файл форка: USB, T-PHY, SD-часы и пины |
| `drivers/video/mediatek/mtk_disp_g99.c` | **дисплей, самописный** |
| `drivers/button/button-mtk-kp.c` | **кнопки, самописный** |
| `drivers/clk/mediatek/clk-mt6789.c` | **часы, переписан** |
| `include/early_log.h` | буфер раннего лога в DRAM, самописный |
| `drivers/mmc/mtk-sd.c` | MSDC, здесь идёт работа над SD-картой |
| `drivers/usb/musb-new/mt85xx.c` | MUSB, PIO-режим |
| `board/mediatek/mtk-phone.env` | окружение, пункты меню загрузки |

---

## Что сделано по этапам / Work stages

| Период | Что |
|---|---|
| июль 2026 | разбор железа: совместимые строки, карта памяти, разделы, регистры дисплея из LK |
| | вывод U-Boot в U-Boot-совместимый вид, появление меню в UART |
| | USB: PHY, MUSB, fastboot, ACM. Дисплей: свой драйвер. Кнопки: свой драйвер |
| | часы: найдено, что драйвер в форке не собирается — переписан |
| август 2026 | UFS, UMS, отладка SD-карты: v161…v219, регистры сведены к живому Android 1:1, карта не отвечает |
| октябрь 2026 | оформление: документация, репозитории, релиз v219 |

---

## Прошивка / Flashing

Образ: `uboot-lk-x676b-v219.img` (2.6 МБ) —
[релиз v219](https://github.com/mnnoee/u-boot-mtk-g99/releases/tag/x676b-v219)

```bash
adb reboot bootloader
fastboot flash lk_a uboot-lk-x676b-v219.img
fastboot flash lk_b uboot-lk-x676b-v219.img
fastboot reboot
```

Если телефон не входит в fastboot:

```bash
cd mtkclient
python mtk w lk_a ../u-boot-x676b/uboot-lk-x676b-v219.img
```

> ⚠️ **Откат обязателен.** Стоковый LK — единственный способ вернуть телефон в
> рабочее состояние. Он используется и как база при упаковке U-Boot
> (`gimme-uboot.py`), поэтому нужен в любом случае.
>
> ⚠️ **Rollback is mandatory.** The stock LK is the only way back to a working
> phone, and it is also the packing base for U-Boot, so it is needed anyway.

---

## Где читать подробности / Where to read details

- **[docs/compatibility.md](https://github.com/mnnoee/u-boot-mtk-g99/blob/mt6789-stable/docs/compatibility.md)** — что реально стоит в телефоне, какая строка в DTS, какой драйвер на неё подхватился и почему между ними расхождение
- **[docs/hardware/sd-card-msdc1.md](https://github.com/mnnoee/u-boot-mtk-g99/blob/mt6789-stable/docs/hardware/sd-card-msdc1.md)** — все эксперименты с SD-картой v161…v219, что уже исключено, следующий шаг
- **[docs/decisions/](https://github.com/mnnoee/u-boot-mtk-g99/tree/mt6789-stable/docs/decisions)** — пять решений с обоснованием
- **[docs/hardware/](https://github.com/mnnoee/u-boot-mtk-g99/tree/mt6789-stable/docs/hardware)** — дисплей, USB, кнопки, часы, память

---

## Как продолжать / How to continue

Следующая задача — **SD-карта**. Статика регистров исчерпана: в v219 контроллер
настроен 1:1 как в живом Android, где карта работает, а ответа нет. Осталось
сравнить внутреннее состояние через отладочный мукс `MSDC_DBG_SEL` (`0xa0`) /
`MSDC_DBG_OUT` (`0xa4`) — команда `msdcbg` в U-Boot уже это делает, нужен такой
же дамп со снятия на живом Android.

The next task is the **SD card**. Static register values are exhausted: in v219 the
controller is configured 1:1 as in working Android, yet there is no response. What
is left is to compare internal state through the `MSDC_DBG_SEL` (`0xa0`) /
`MSDC_DBG_OUT` (`0xa4`) debug mux — the `msdcbg` command in U-Boot already does
this, the missing part is the same capture on live Android.

---

## Ограничения / Constraints

- Ответы и обсуждение — на русском и английском
- Флеш-команды выполняет пользователь, не агент
- `sudo pacman` не запускается
- Python — через venv mtkclient, без активации
- Файлы разбора складываются в `docs/AGENTS/`, выжимка — в `docs/` репозитория U-Boot