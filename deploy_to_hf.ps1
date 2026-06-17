# deploy_to_hf.ps1
# Script untuk mengotomatiskan deployment pembaruan kode ke Hugging Face Spaces

$ErrorActionPreference = "Stop"

# Tentukan path folder
$sourceDir = "SkillBridgeAI"
$deployDir = "..\deploy-api" # Berada sejajar dengan kelompok-6

Write-Host "=== SkillBridge AI Auto-Deployer to Hugging Face ===" -ForegroundColor Cyan

# 1. Validasi folder sumber
if (-not (Test-Path $sourceDir)) {
    Write-Error "Folder sumber '$sourceDir' tidak ditemukan. Pastikan Anda menjalankan script ini dari folder root proyek (kelompok-6)."
}

# 2. Sinkronisasi file ke folder deploy-api (menghapus file lama & menyalin yang baru, kecuali folder .git)
Write-Host "Syncing files to deployment directory..." -ForegroundColor Yellow
if (-not (Test-Path $deployDir)) {
    New-Item -ItemType Directory -Path $deployDir | Out-Null
}

# Hapus seluruh isi deploy-api kecuali folder .git agar tetap bersih
Get-ChildItem -Path $deployDir -Exclude ".git" | Remove-Item -Recurse -Force

# Salin isi SkillBridgeAI ke deploy-api
Copy-Item -Path "$sourceDir\*" -Destination $deployDir -Recurse -Force

# Pastikan tidak ada file biner .npy yang tidak sengaja terbawa di folder tujuan
$forbiddenNpy = Join-Path $deployDir "data/embeddings/career_embeddings.npy"
if (Test-Path $forbiddenNpy) {
    Remove-Item -Force $forbiddenNpy
    Write-Host "Menghapus file biner .npy dari direktori deploy untuk mencegah penolakan server..." -ForegroundColor Yellow
}

# 3. Lakukan Commit dan Push di folder deploy-api
cd $deployDir

Write-Host "Adding files and committing..." -ForegroundColor Yellow
git init | Out-Null
git add .

# Cek apakah ada perubahan yang perlu dicommit
$status = git status --porcelain
if ($status) {
    git commit -m "Update deployment: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
} else {
    Write-Host "Tidak ada perubahan kode baru yang terdeteksi." -ForegroundColor Green
}

Write-Host "Pushing updates to Hugging Face Spaces..." -ForegroundColor Yellow
Write-Host "Silakan masukkan token Hugging Face Anda jika diminta." -ForegroundColor Cyan
git push -f origin master:main

Write-Host "=== Deployment Selesai! ===" -ForegroundColor Green
Write-Host "Tunggu 2-3 menit hingga proses build di Hugging Face selesai." -ForegroundColor Green
