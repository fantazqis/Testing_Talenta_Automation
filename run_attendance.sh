#!/bin/bash
# run_attendance.sh
# Script ini dijalankan di dalam Android Emulator runner

set -e  # Stop jika ada error

# Tentukan aksi berdasarkan environment variable dari workflow
ACTION="${ATTENDANCE_ACTION}"

echo "================================"
echo "Talenta Auto Attendance"
echo "Aksi: $ACTION"
echo "Waktu: $(date)"
echo "================================"

# Tunggu emulator benar-benar siap
echo "Menunggu emulator siap..."
adb wait-for-device
adb shell input keyevent 82
sleep 3

# Install APK Talenta ke emulator
echo "Menginstall APK Talenta..."
adb install -r talenta.apk
echo "APK berhasil diinstall!"
sleep 5

# Cek activity name yang benar dari APK
echo "=== INFO APK TALENTA ==="
adb shell pm dump co.talenta | grep -A 5 "Activity"
echo "=== MAIN ACTIVITY ==="
adb shell cmd package resolve-activity --brief co.talenta
echo "========================"

# Jalankan Appium server di background
echo "Menjalankan Appium server..."
appium &
APPIUM_PID=$!

# Tunggu Appium benar-benar siap menerima koneksi
echo "Menunggu Appium siap..."
for i in $(seq 1 30); do
  if curl -s http://localhost:4723/status > /dev/null 2>&1; then
    echo "Appium siap!"
    break
  fi
  echo "Menunggu... ($i/30)"
  sleep 2
done

# Jalankan script Python
echo "Menjalankan script Python..."
python talenta_clockin.py "$ACTION"
EXIT_CODE=$?

# Matikan Appium
kill $APPIUM_PID 2>/dev/null || true

# Keluar dengan exit code dari Python script
exit $EXIT_CODE
