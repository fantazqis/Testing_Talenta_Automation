# Talenta Auto Attendance

Otomasi clock in/out Mekari Talenta menggunakan GitHub Actions + Appium.

## Struktur Folder

```
talenta-automation/
├── .github/
│   └── workflows/
│       └── talenta-attendance.yml   ← jadwal otomatis
├── talenta_clockin.py               ← script utama
├── talenta.apk                      ← download & taruh disini
├── selfie.jpg                       ← foto selfie kamu
├── requirements.txt                 ← dependencies Python
└── README.md                        ← file ini
```

## Setup

### 1. Buat Repo Private di GitHub
- Buka github.com → New Repository
- Centang **Private** (wajib!)
- Upload semua file ini ke repo

### 2. Tambah GitHub Secrets
- Buka repo → Settings → Secrets and variables → Actions
- Klik "New repository secret"
- Tambahkan:
  - `TALENTA_USER` → email login Talenta kamu
  - `TALENTA_PASS` → password Talenta kamu

### 3. Siapkan File Tambahan (tidak ada di folder ini)
- `selfie.jpg` → foto selfie kamu, taruh di root folder
- `talenta.apk` → download dari APKPure/APKMirror, rename jadi talenta.apk

### 4. Upload ke GitHub & Test
- Push semua file ke repo
- Buka tab Actions → pilih workflow → Run workflow → pilih clock_in
- Lihat apakah berhasil

## Jadwal Otomatis
- **Clock In**  : 08:00 WIB, Senin-Jumat
- **Clock Out** : 17:00 WIB, Senin-Jumat

Ubah jadwal di file `.github/workflows/talenta-attendance.yml` bagian `cron`.

## Jalankan Manual
Buka tab Actions di GitHub → pilih workflow → Run workflow → pilih aksi.

## Catatan
- Log tersimpan otomatis di tab Actions tiap run (7 hari)
- Jangan share repo ini ke siapapun karena ada foto selfie
