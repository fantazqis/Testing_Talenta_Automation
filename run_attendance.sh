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

# Jalankan Appium server di background
echo "Menjalankan Appium server..."
appium --allow-insecure chromedriver_autodownload &
APPIUM_PID=$!
sleep 8

# Jalankan script Python
echo "Menjalankan script Python..."
python talenta_clockin.py "$ACTION"
EXIT_CODE=$?

# Matikan Appium
kill $APPIUM_PID 2>/dev/null || true

# Keluar dengan exit code dari Python script
exit $EXIT_CODE
