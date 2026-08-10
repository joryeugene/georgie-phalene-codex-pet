---
name: georgie-animation
description: Create, rebuild, repair, validate, install, or publish Georgie the Phalene as a cohesive Codex v2 animated pet. Use for changes to Georgie's spritesheet, action rows, timing, scale, registration, pointer looks, motion previews, animation QA, pet packaging, or any request about making Georgie's movement seamless.
---

# Georgie Animation

Build Georgie from coherent source rows. Never repair the packaged atlas one cell at a time.

## Required context

1. Read `references/animation-matrix.md` before changing visual assets.
2. Read the repository `AGENTS.md` before editing or publishing.
3. Use the installed `hatch-pet` and `imagegen` skills for visual generation and Codex v2 packaging.

## Source lock

- Treat one approved full-body Georgie image as the identity reference for every row.
- Preserve his Phalene drop ears, chestnut-and-white markings, face, proportions, coat, eye shape, and quiet expression.
- Keep one shared cell geometry: `192x208`, common grounded baseline, common visible body height, and common torso anchor.
- Generate each animation row as one coherent strip. Never assemble a row from unrelated poses. Pointer rows may use ordered four-pose source families when an eight-pose strip cannot keep the body locked.

## Workflow

1. Write or update the complete state sequence in `references/animation-matrix.md`.
2. Generate the smallest failing unit, normally one complete row, from the canonical identity reference and the row layout guide. For a stationary articulated appendage loop, an image-generated body-and-key component kit may be used with `scripts/build_tail_wag.py`.
3. Run `scripts/extract_row.py` on the complete strip. It accepts equal slots or certified empty gaps, applies one row scale, and registers complete poses to one body anchor.
4. Run `scripts/render_row.py` and inspect the complete loop at app size before assembly.
5. Reject the complete row for drift, scale pop, baseline jump, identity change, broken loop closure, or incorrect state meaning.
6. Assemble the v2 atlas only from approved complete rows.
7. Run `scripts/check_motion.py`, the `hatch-pet` atlas validator, chroma cleanup, and final visual QA.
8. Install and publish only after every gate passes.

Rebuild the deterministic running frames with:

```powershell
just rig-running <output-directory>
```

The command uses `assets/georgie-tail-rig.png`, which contains the approved image-generated body and four tail keys.

Rebuild the stable first pointer row from the approved second row with:

```powershell
just rig-pointer <row-10-frames-directory> <output-directory>
```

The command keeps one registered body family and mirrors only the two eye masks. It repeats the nearest up-gaze pose for the two top buckets instead of introducing a different body silhouette.

## Hard rules

- Do not shift, crop, rotate, scale, splice, inpaint, or copy individual packaged cells to hide a bad transition.
- Do not scale frames separately. Deterministic full-pose registration to the shared body anchor is allowed during source extraction.
- Reject the full strip when a pose crosses its equal slot and no empty gap of at least six pixels separates the complete poses.
- Do not replace body regions inside final cells to hide a failed generated row. A declared appendage rig is allowed only when every visual component comes from one coherent image-generated kit, the appendage is composited behind one unchanged whole body, and the completed loop passes deterministic and visual QA.
- A pointer gaze rig may mirror only the two declared eye masks from one approved whole-body look family. Every pixel outside those masks must stay on the same registered body.
- Do not reuse another state's row as a substitute.
- An exact neutral whole-pose frame may anchor state boundaries when the matrix requires a pixel-stable entry or exit.
- Do not publish a row that has not been watched as a complete loop at app size.
- Do not install a candidate before final QA passes.
- Regenerate the complete row when its source motion is wrong.
- Preserve unrelated approved rows during a targeted repair.

## Motion gates

- Make the first-to-last loop seam as deliberate as every internal transition.
- Keep grounded rows on the same baseline.
- Keep subtle rows within the drift and scale budgets in the matrix.
- Keep the `running` and `review` rows restrained because Codex repeats them often.
- Keep `waiting` attentive through the eyes and ears. Do not use a paw lift in a looping row.
- Do not use paw motion in `waiting`, `running`, or `review`.
- Keep pointer-look motion separate from state animation and preserve the same full-body scale.
- Keep pointer looks on the same `y=203` baseline as the grounded rows. Do not pass a cell through a helper that vertically centers it before look registration.
- If two eye-only look generations still move the head or body, stop regenerating the eight-pose sweep. Generate the intermediates as ordered four-pose gaze families, then assemble the approved whole poses in clockwise order.

## Validation

Run:

```powershell
python skills/georgie-animation/scripts/check_motion.py spritesheet.webp
```

The command must exit successfully. Treat every reported error as a release blocker. Review warnings against the rendered GIFs instead of suppressing them.
