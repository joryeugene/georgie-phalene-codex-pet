set shell := ["pwsh.exe", "-NoLogo", "-NoProfile", "-Command"]

pet_id := "georgie-phalene"
asset := "spritesheet.webp"
python := env_var_or_default("PYTHON", "python")

default:
    just --list

check:
    & '{{ python }}' skills/georgie-animation/scripts/check_motion.py {{ asset }}; if ($LASTEXITCODE) { exit $LASTEXITCODE }; $codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }; & '{{ python }}' (Join-Path $codexRoot 'skills\hatch-pet\scripts\validate_atlas.py') {{ asset }} --require-v2 --chroma-key '#00FF00'; if ($LASTEXITCODE) { exit $LASTEXITCODE }

install: check
    $codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }; $target = Join-Path $codexRoot 'pets\{{ pet_id }}'; New-Item -ItemType Directory -Force -Path $target | Out-Null; Copy-Item -LiteralPath {{ asset }},pet.json -Destination $target -Force; Get-FileHash -Algorithm SHA256 -LiteralPath {{ asset }},(Join-Path $target {{ asset }}); Get-FileHash -Algorithm SHA256 -LiteralPath pet.json,(Join-Path $target 'pet.json')

status:
    $codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }; $installed = Join-Path $codexRoot 'pets\{{ pet_id }}'; Get-FileHash -Algorithm SHA256 -LiteralPath {{ asset }},(Join-Path $installed {{ asset }}); Get-FileHash -Algorithm SHA256 -LiteralPath pet.json,(Join-Path $installed 'pet.json'); git status --short

rig-running output_dir:
    & '{{ python }}' skills/georgie-animation/scripts/build_tail_wag.py skills/georgie-animation/assets/georgie-tail-rig.png {{ output_dir }}

rig-pointer row_10_dir output_dir:
    & '{{ python }}' skills/georgie-animation/scripts/build_pointer_row.py {{ row_10_dir }} {{ output_dir }}

release-check: check
    git diff --check; if ($LASTEXITCODE) { exit $LASTEXITCODE }; git status --short
