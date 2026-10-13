# Infinix X676B — рабочий каталог / Working directory

Здесь лежат **прошиваемые образы**, история состояния проекта и вспомогательные
скрипты. Сам исходный код U-Boot — в отдельном репозитории.

This holds the **flashable images**, the project history and helper scripts.
The U-Boot source code itself lives in a separate repository.

---

## Где что лежит / What is where

| | |
|---|---|
| **Исходники U-Boot** | **[github.com/mnnoee/u-boot-mtk-g99](https://github.com/mnnoee/u-boot-mtk-g99)** — форк `ellyq`, ветка `mt6789-stable` |
| **Документация** | `docs/` в репозитории U-Boot; сырые заметки — в репозитории `docs` (`docs/AGENTS/`) |
| **Состояние проекта** | [`PROJECT_STATE.md`](PROJECT_STATE.md) — подробный разбор |

---

## Статус / Status

**Работает / Working**
- 🔌 USB fastboot
- 🖥 USB ACM — консоль U-Boot по USB, без кабеля
- 💾 UMS / fastboot block по UFS
- 📺 текст U-Boot на AMOLED
- 🔘 кнопки Volume Up / Down в меню загрузки

**Не работает / Not working**
- ❌ SD-карта — текущий блокер
- ❌ загрузка Android — паника `Attempted to kill init`

> ⚠️ Часть `PROJECT_STATE.md` относится к раннему этапу и уже неактуальна
> (там USB и дисплей записаны как неработающие — с тех пор это исправлено).
> Актуальные документы: `docs/` в репозитории U-Boot.
>
> ⚠️ Parts of `PROJECT_STATE.md` describe an early stage and are outdated
> (USB and display are listed as broken — fixed since). Current docs live in
> `docs/` of the U-Boot repository.

---

## Образы / Images

| Файл | Описание |
|---|---|
| `uboot-lk-x676b-v219.img` | **последняя рабочая версия** (2.6 МБ) |
| `uboot-lk-x676b-v4-msdc1-fix.img` | ранняя экспериментальная версия |

Все прочие версии (v4…v218) исключены из git — они патчат один и тот же бинарник,
и в истории только раздували размер. Пересобрать можно в любой момент.

All other versions (v4…v218) are excluded from git — they patch the same binary and
only bloated the history. Any of them can be rebuilt.

---

## Сборка / Build

```bash
git clone https://github.com/mnnoee/u-boot-mtk-g99.git
cd u-boot-mtk-g99

make CROSS_COMPILE=aarch64-linux-gnu- mt6789_infinix_x676b_defconfig
make CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc)
```

Упаковка в формат LK:

```bash
python3 gimme-uboot.py lk_a_dump.img u-boot.bin uboot-lk-x676b.img
```

Подробнее: **[README в репозитории U-Boot](https://github.com/mnnoee/u-boot-mtk-g99/blob/mt6789-stable/README.md)**

---

## Прошивка / Flashing

```bash
adb reboot bootloader
fastboot flash lk_a uboot-lk-x676b-v219.img
fastboot flash lk_b uboot-lk-x676b-v219.img
fastboot reboot
```

> ⚠️ **Откат обязателен.** Стоковый LK — единственный способ вернуть телефон
> в рабочее состояние. Прошивка идёт в обе A/B-части.
>
> ⚠️ **Rollback is mandatory.** The stock LK is the only way back to a working
> phone. The image is flashed to both A/B slots.

---

## Скрипты и патчи / Scripts and patches

| Файл | Назначение |
|---|---|
| `compare_dbgmux.py` | сравнение значений отладочного мукса MSDC1 |
| `dump_dbgmux.sh` | снятие дампа отладочного мукса |
| `patches/0001-*.patch` | принудительный источник 26 МГц для MSDC1 |
| `patches/0002-*.patch` | ранний этап (10.07.2026): правки USB PHY, MUSB, bootm |
| `patches/0003-*.patch` | ранний этап: новые файлы — DTS X676B и defconfig |

Патчи `0002`/`0003` — это снимок работы от 10 июля 2026, **предшественник**
текущего состояния. Они не применяются поверх HEAD (уже влиты), но сохранены,
чтобы история не потерялась.

Patches `0002`/`0003` are a snapshot of the 10 July 2026 work, the **precursor**
to the current state. They no longer apply on top of HEAD but are kept so the
history is not lost.