param(
  [string]$Spec = "ytd.spec"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $Spec)) {
  throw "Spec file not found: $Spec"
}

if (!(Test-Path ".\\ffmpeg.exe")) {
  throw "Missing .\\ffmpeg.exe (place it next to $Spec)"
}

if (!(Test-Path ".\\yt-dlp.exe")) {
  throw "Missing .\\yt-dlp.exe (place it next to $Spec)"
}

pyinstaller --noconfirm --clean $Spec

