set shell := ["pwsh.exe", "-NoLogo", "-NoProfile", "-Command"]

pet_id := "georgie-phalene"
asset := "spritesheet.webp"

default:
  just --list

check:
  python skills/georgie-animation/scripts/check_motion.py {{asset}}; if ($LASTEXITCODE) { exit $LASTEXITCODE }; $root = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }; python (Join-Path $root 'skills\hatch-pet\scripts\validate_atlas.py') {{asset}} --require-v2 --chroma-key '#0000FF'

install: check
  $root = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }; $target = Join-Path $root 'pets\{{pet_id}}'; New-Item -ItemType Directory -Force -Path $target | Out-Null; Copy-Item -LiteralPath {{asset}} -Destination (Join-Path $target {{asset}}) -Force; Get-FileHash -Algorithm SHA256 -LiteralPath {{asset}},(Join-Path $target {{asset}})

status:
  $root = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }; $installed = Join-Path $root 'pets\{{pet_id}}\{{asset}}'; Get-FileHash -Algorithm SHA256 -LiteralPath {{asset}},$installed; git status --short

rig-running output_dir:
  python skills/georgie-animation/scripts/build_tail_wag.py skills/georgie-animation/assets/georgie-tail-rig.png {{output_dir}}

publish message:
  just check; git add -- {{asset}} README.md media/georgie-check-in.png pet.json Justfile .gitignore AGENTS.md skills; git commit -m {{message}}; git push
