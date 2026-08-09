# Georgie repository instructions

## Visual source of truth

Before changing `spritesheet.webp`, read:

- `skills/georgie-animation/SKILL.md`
- `skills/georgie-animation/references/animation-matrix.md`

Use the `georgie-animation`, `hatch-pet`, and `imagegen` skills for pet work.

## Required workflow

- Change complete source rows, not packaged cells.
- Extract complete poses with one row scale and one body anchor. Never scale frames separately.
- Reject a source strip when a pose crosses an equal slot and no six-pixel empty gap separates complete poses.
- Preserve approved rows during a targeted repair.
- Render and inspect every changed row as an animation before assembly.
- Run the motion validator and Codex v2 atlas validator before installation.
- Install the same validated WebP that is committed to the repository.
- Confirm repository and installed SHA-256 hashes match.

## Forbidden repairs

- No per-cell shifts, scaling, cropping, rotation, splicing, or repainting.
- No region replacement for heads, tails, eyes, ears, bodies, or paws.
- Do not reuse expressive poses across states unless the animation matrix names the complete source family and its new sequence. An exact neutral boundary pose may be reused as a loop anchor.
- If an eight-pose pointer strip moves the skull, ears, feet, scale, or baseline, generate four-pose gaze families. Assemble only complete approved poses. Do not blend or patch body regions.
- No direct edits to the installed pet followed by a reverse copy into the repository.
- No publishing when the animation has only been checked as a contact sheet.

## Release gate

Do not commit, push, or install a visual change unless:

1. The changed row follows the animation matrix.
2. Its GIF has no drift, scale pop, abrupt seam, overlap, or identity change.
3. `python skills/georgie-animation/scripts/check_motion.py spritesheet.webp` passes.
4. The hatch-pet v2 atlas validator passes without warnings.
5. The final extended contact sheet passes visual QA.

Documentation-only changes do not require pet QA.
