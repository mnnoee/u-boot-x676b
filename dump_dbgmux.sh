#!/system/bin/sh
# Dump MSDC1 debug-mux on live Android (root) while controller is busy.
# Usage: sh dump_dbgmux.sh  (output on stdout)
dd if=/dev/block/mmcblk0 of=/dev/null bs=4096 count=65536 &
DD=$!
sleep 0.1
s=0
while [ $s -le 99 ]; do
  devmem 0x112400a0 32 $s >/dev/null 2>&1
  echo "$(printf '%03x' $s) $(devmem 0x112400a4 32 2>/dev/null)"
  s=$((s+1))
done
kill $DD 2>/dev/null
# sel 0x27 block (EMMC50_CFG4 mode) too
s=0
while [ $s -le 11 ]; do
  devmem 0x112400a0 32 $((0x27 + s)) >/dev/null 2>&1
  printf "x%02x:%02x %s\n" $((0x27 + s)) $s "$(devmem 0x112400a4 32 2>/dev/null)"
  s=$((s+1))
done
