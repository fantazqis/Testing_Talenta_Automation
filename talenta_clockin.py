"""
Talenta Auto Clock In/Out
Flow: Buka App → Halaman Utama → Tap Clock In/Out → Kamera → Inject Foto → Submit

Requirements:
    pip install Appium-Python-Client

Setup Appium:
    npm install -g appium
    appium driver install uiautomator2
    appium  ← jalankan di terminal terpisah

Setup Emulator:
    1. Install LDPlayer
    2. Enable ADB: Settings → Others → ADB Debugging ON
    3. Cek device: adb devices
"""

import os
import sys
import time
import base64
import datetime
import logging

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ================================
# KONFIGURASI
# ================================

CONFIG = {
    # Credentials — simpan di environment variable, jangan hardcode!
    # Di terminal: set TALENTA_USER=email@kamu.com (Windows)
    #              export TALENTA_USER=email@kamu.com (Linux/Mac)
    "username": os.environ.get("TALENTA_USER", "email@kamu.com"),
    "password": os.environ.get("TALENTA_PASS", "passwordkamu"),

    # Path foto selfie di LOCAL (laptop/PC kamu)
    # Taruh file selfie.jpg di folder yang sama dengan script ini
    "selfie_local_path": "selfie.jpg",

    # Path tujuan di dalam emulator
    "selfie_device_path": "/sdcard/Pictures/selfie.jpg",

    # Appium server (default)
    "appium_host": "http://localhost:4723",

    # App Talenta
    "app_package": "co.talenta",
    "app_activity": "co.talenta.modul.main.MainActivity",

    # Nama device emulator — cek via: adb devices
    # Biasanya LDPlayer: emulator-5554
    "device_name": os.environ.get("DEVICE_NAME", "emulator-5554"),

    # Versi Android di emulator (GitHub Actions pakai Android 10)
    "platform_version": "10",
}

DESIRED_CAPS = {
    "platformName": "Android",
    "appium:platformVersion": CONFIG["platform_version"],
    "appium:deviceName": CONFIG["device_name"],
    "appium:appPackage": CONFIG["app_package"],
    "appium:appActivity": CONFIG["app_activity"],
    "appium:automationName": "UiAutomator2",
    "appium:noReset": True,
    "appium:fullReset": False,
    "appium:newCommandTimeout": 120,
    "appium:autoGrantPermissions": True,
}

# ================================
# LOGGING
# ================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("talenta.log"),
    ]
)
log = logging.getLogger(__name__)


# ================================
# HELPERS
# ================================

def wait_element(driver, xpath, timeout=20):
    """Tunggu elemen muncul, return element atau None."""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((AppiumBy.XPATH, xpath))
        )
        return el
    except TimeoutException:
        return None


def tap(driver, xpath, label="elemen", timeout=20):
    """Tunggu dan tap elemen. Return True jika berhasil."""
    el = wait_element(driver, xpath, timeout)
    if el:
        el.click()
        log.info(f"✓ Tap: {label}")
        time.sleep(1.5)
        return True
    log.warning(f"✗ Tidak ketemu: {label}")
    return False


def inject_selfie(driver):
    """
    Push foto selfie dari laptop ke emulator,
    lalu set sebagai virtual camera image.
    """
    try:
        # Baca foto dari local
        with open(CONFIG["selfie_local_path"], "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Push ke emulator
        driver.push_file(CONFIG["selfie_device_path"], img_b64)
        log.info(f"✓ Foto selfie berhasil dipush ke emulator")

        # Set virtual camera (khusus emulator Android)
        # Ini membuat kamera emulator menampilkan foto kita
        os.system(
            f'adb -s {CONFIG["device_name"]} shell '
            f'am broadcast -a com.android.emulator.camera.action.CHANGE_PHOTO '
            f'--es image_path {CONFIG["selfie_device_path"]}'
        )
        time.sleep(1)
        return True

    except FileNotFoundError:
        log.error(f"✗ File selfie tidak ditemukan: {CONFIG['selfie_local_path']}")
        log.error("  Pastikan selfie.jpg ada di folder yang sama dengan script ini!")
        return False
    except Exception as e:
        log.error(f"✗ Gagal inject foto: {e}")
        return False


def capture_photo(driver):
    """
    Ambil foto saat kamera terbuka.
    Mencoba beberapa selector tombol shutter yang umum.
    """
    shutter_selectors = [
        '//*[@content-desc="Shutter"]',
        '//*[@content-desc="Take photo"]',
        '//*[@content-desc="Capture"]',
        '//*[contains(@resource-id, "shutter")]',
        '//*[contains(@resource-id, "capture")]',
        '//*[contains(@resource-id, "btn_capture")]',
    ]

    for selector in shutter_selectors:
        try:
            el = driver.find_element(AppiumBy.XPATH, selector)
            el.click()
            log.info("✓ Tombol shutter ditemukan dan ditap")
            time.sleep(2)
            return True
        except NoSuchElementException:
            continue

    # Fallback: tap koordinat tengah-bawah layar
    log.warning("Tombol shutter tidak ditemukan via selector, mencoba tap koordinat...")
    size = driver.get_window_size()
    x = size["width"] // 2
    y = int(size["height"] * 0.85)  # 85% dari atas layar
    driver.tap([(x, y)])
    log.info(f"✓ Tap koordinat shutter: ({x}, {y})")
    time.sleep(2)
    return True


def confirm_photo(driver):
    """Konfirmasi foto setelah diambil."""
    confirm_selectors = [
        '//*[contains(@text, "OK")]',
        '//*[contains(@text, "Konfirmasi")]',
        '//*[contains(@text, "Gunakan")]',
        '//*[contains(@text, "Use Photo")]',
        '//*[contains(@text, "Submit")]',
        '//*[contains(@text, "Simpan")]',
        '//*[contains(@resource-id, "confirm")]',
        '//*[contains(@resource-id, "btn_ok")]',
    ]

    for selector in confirm_selectors:
        try:
            el = driver.find_element(AppiumBy.XPATH, selector)
            el.click()
            log.info("✓ Foto dikonfirmasi")
            time.sleep(2)
            return True
        except NoSuchElementException:
            continue

    log.warning("Tombol konfirmasi tidak ditemukan")
    return False


# ================================
# MAIN FLOW
# ================================

def do_clock_action(driver, action="clock_in"):
    """Jalankan clock in atau clock out."""

    log.info("Menunggu halaman utama Talenta...")
    time.sleep(4)  # Tunggu app loading

    # Selector berdasarkan resource-id dari XML dump HP asli
    if action == "clock_in":
        label = "Clock In"
    else:
        label = "Clock Out"

    # Tunggu halaman utama load dengan cek container clock buttons
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((AppiumBy.ID, "co.talenta:id/linClockButtons"))
        )
        log.info("✓ Halaman utama terdeteksi")
    except TimeoutException:
        log.error("✗ Halaman utama tidak muncul!")
        return False

    # Tap Clock In atau Clock Out
    # linClockIn tidak clickable, jadi tap linClockButtons (sisi kiri = Clock In, sisi kanan = Clock Out)
    if action == "clock_in":
        # Coba tap langsung linClockIn dulu
        try:
            el = driver.find_element(AppiumBy.ID, "co.talenta:id/linClockIn")
            # Tap di tengah elemen linClockIn
            bounds_el = driver.find_element(AppiumBy.ID, "co.talenta:id/tvClockIn")
            bounds_el.click()
            log.info("✓ Tap: Clock In via tvClockIn")
            time.sleep(2)
            tapped = True
        except Exception:
            # Fallback: tap koordinat sisi kiri linClockButtons
            container = driver.find_element(AppiumBy.ID, "co.talenta:id/linClockButtons")
            size = container.size
            loc = container.location
            # Tap 1/4 dari kiri container
            x = loc['x'] + size['width'] // 4
            y = loc['y'] + size['height'] // 2
            driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
            log.info(f"✓ Tap: Clock In via koordinat ({x}, {y})")
            time.sleep(2)
            tapped = True
    else:
        # Clock Out = linClockOut yang sudah clickable
        try:
            el = driver.find_element(AppiumBy.ID, "co.talenta:id/linClockOut")
            el.click()
            log.info("✓ Tap: Clock Out via linClockOut")
            time.sleep(2)
            tapped = True
        except Exception as e:
            log.error(f"✗ Tombol Clock Out tidak ditemukan: {e}")
            tapped = False

    if not tapped:
        log.error(f"✗ Tombol {label} tidak ditemukan!")
        return False

    # Inject foto ke virtual camera
    log.info("Kamera terbuka, menginjek foto selfie...")
    time.sleep(3)
    inject_selfie(driver)
    time.sleep(2)

    # Tap tombol Kirim (btnSubmit — confirmed dari XML dump)
    try:
        submit_btn = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((AppiumBy.ID, "co.talenta:id/btnSubmit"))
        )
        submit_btn.click()
        log.info("✓ Tap: Kirim (btnSubmit)")
        time.sleep(3)
    except TimeoutException:
        log.error("✗ Tombol Kirim (btnSubmit) tidak ditemukan!")
        return False

    # Cek apakah berhasil
    try:
        success_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                AppiumBy.XPATH,
                '//*[contains(@text, "Berhasil") or contains(@text, "berhasil") or contains(@text, "Success")]'
            ))
        )
        log.info(f"✅ {label} BERHASIL! Notifikasi: {success_el.text}")
        return True
    except TimeoutException:
        log.info(f"✅ {label} kemungkinan berhasil (tidak ada error terdeteksi)")
        return True


def main():
    now = datetime.datetime.now()

    # Tentukan aksi: clock_in atau clock_out
    # Bisa override via argument: python talenta_clockin.py clock_out
    if len(sys.argv) > 1 and sys.argv[1] in ["clock_in", "clock_out"]:
        action = sys.argv[1]
    else:
        # Auto: pagi = clock in, sore = clock out
        action = "clock_in" if now.hour < 12 else "clock_out"

    log.info("=" * 40)
    log.info("Talenta Auto Attendance")
    log.info(f"Waktu  : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"Aksi   : {action.upper()}")
    log.info(f"Device : {CONFIG['device_name']}")
    log.info("=" * 40)

    driver = None
    try:
        # Connect ke Appium menggunakan UiAutomator2Options (Appium Python Client v3)
        log.info("Menghubungkan ke Appium...")
        from appium.options.android.uiautomator2.base import UiAutomator2Options
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.platform_version = CONFIG["platform_version"]
        options.device_name = CONFIG["device_name"]
        options.app_package = CONFIG["app_package"]
        options.app_activity = CONFIG["app_activity"]
        options.no_reset = True
        options.full_reset = False
        options.new_command_timeout = 120
        options.auto_grant_permissions = True

        driver = webdriver.Remote(CONFIG["appium_host"], options=options)
        driver.implicitly_wait(5)
        log.info("✓ Terhubung ke Appium!")

        # Screenshot untuk debug — lihat app tampil apa
        time.sleep(5)
        screenshot_path = "screen_after_launch.png"
        driver.save_screenshot(screenshot_path)
        log.info(f"✓ Screenshot disimpan: {screenshot_path}")

        # Dump UI hierarchy untuk debug
        page_source = driver.page_source
        with open("page_source.xml", "w") as f:
            f.write(page_source)
        log.info("✓ UI hierarchy disimpan: page_source.xml")

        success = do_clock_action(driver, action)

        if success:
            log.info(f"✅ SELESAI: {action.upper()} berhasil!")
            sys.exit(0)
        else:
            log.error(f"❌ GAGAL: {action.upper()} tidak berhasil!")
            sys.exit(1)

    except Exception as e:
        log.error(f"❌ Error: {e}")
        sys.exit(1)

    finally:
        if driver:
            driver.quit()
            log.info("Driver ditutup.")


if __name__ == "__main__":
    main()
