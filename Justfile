set shell := ["pwsh.exe", "-NoLogo", "-NoProfile", "-Command"]

pet_id := "georgie-phalene"
asset := "spritesheet.webp"

default:
  just --list

check:
  $python = 'C:\Users\joryp\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'; & $python "$env:USERPROFILE\.codex\skills\hatch-pet\scripts\validate_atlas.py" {{asset}} --require-v2 --chroma-key '#00FF00'

install: check
  $root = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }; $target = Join-Path $root 'pets\{{pet_id}}'; New-Item -ItemType Directory -Force -Path $target | Out-Null; Copy-Item -LiteralPath {{asset}} -Destination (Join-Path $target {{asset}}) -Force; Get-FileHash -Algorithm SHA256 -LiteralPath {{asset}},(Join-Path $target {{asset}})

status:
  $root = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }; $installed = Join-Path $root 'pets\{{pet_id}}\{{asset}}'; Get-FileHash -Algorithm SHA256 -LiteralPath {{asset}},$installed; git status --short

publish message:
  just check; git add {{asset}} README.md pet.json Justfile; git commit -m {{message}}; git push
