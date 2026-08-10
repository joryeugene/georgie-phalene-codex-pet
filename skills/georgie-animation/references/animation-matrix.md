# Georgie animation matrix

This file is the source of truth for Georgie's Codex v2 motion.

## Shared geometry

- Cell: `192x208` pixels.
- Atlas: 8 columns by 11 rows, `1536x2288` pixels.
- Master standing body height: 176 pixels at the neutral pose. Use the same row-level scale for every frame.
- Directional drag gait height: 140 pixels. The side profile has more visual mass than the standing pose, so both gait rows use this shared smaller scale.
- Grounded baseline: `y=203`, with at most 1 pixel of drift in frequent rows. Airborne frames move above it without changing body scale.
- Subtle-row height range: at most 3 pixels within a row.
- Lower-torso horizontal drift: at most 0.75 pixel in `review`. The `waving` and `running` bodies are checked inside a fixed-body box because the tail intentionally changes the full silhouette.
- Full-silhouette horizontal drift: at most 1 pixel in `review`. The tail rows instead enforce fixed-body pixel and silhouette budgets plus loop closure.
- In `waving` and `running`, adjacent frames may change at most 6 percent of central body pixels and 2 percent of the central body silhouette. Tail motion is outside this fixed-body region.
- No frame may change Georgie's head size, muzzle length, ear length, eye spacing, markings, or coat style.
- No cast shadow, detached effect, motion line, blur, floor patch, text, prop, or scenery.

## State sequence

| Row | State | Frames | Trigger meaning | Sequence | Loop requirement |
| ---: | --- | ---: | --- | --- | --- |
| 0 | `idle` | 6 | Codex is resting | neutral, soft inhale, soft exhale, full blink, eyes open, neutral | Quiet breathing. No head turn. Last frame visually matches first. |
| 1 | `running-right` | 8 | User drags Georgie right | contact, down, passing, up, contact, down, passing, up | True right-facing gait at the shared 140 px directional scale, with an even cyclic cadence. |
| 2 | `running-left` | 8 | User drags Georgie left | contact, down, passing, up, contact, down, passing, up | True left-facing gait at the same 140 px scale. Mirror row 1 only if markings remain correct. |
| 3 | `waving` | 4 | Brief greeting or attention | tail A, tail B, tail C, tail B | One restrained palindromic tail greeting. Feet, torso, and head stay anchored. No paw lift. |
| 4 | `jumping` | 5 | Playful direct interaction | exact neutral, crouch, lift, peak, exact neutral | One compact hop. The first and last cells reuse the approved neutral whole pose, so the loop cannot pop at its boundary. |
| 5 | `failed` | 8 | A task failed or stopped | exact neutral, ears soften, lower, prone, lower, ears soften, standing bridge, exact neutral | Gentle disappointment, not distress. The descent reverses before one standing bridge and one neutral settle. |
| 6 | `waiting` | 6 | Codex needs input or approval | attentive, ears forward, hold, blink, eyes open, attentive | A patient expectant hold. No paw lift, head turn, or repeated gesture. |
| 7 | `running` | 6 | Codex is actively working | tail A, tail B, tail C, tail D, tail C, tail B | A continuous restrained tail wag built from one fixed whole body and four image-generated tail keys. The sequence is palindromic, so the three system repeats have no reset frame. Feet, torso, head, muzzle, drop ears, scale, and baseline stay locked. No lateral drift, nod, roll, slide, wink, or paw motion. |
| 8 | `review` | 6 | Codex is checking completed work | attentive, eyes lower slightly, full blink, eyes reopen, attentive, attentive | Most restrained loop. No head circle, side-eye snap, paw lift, tail gesture, or body translation. |
| 9 | look `000` to `157.5` | 8 | Pointer is above through lower-right | up-right, hold up-right, hold, hold, right, down-right, hold, hold | Mirror only the eye masks from row 10. The two top buckets share the nearest approved up-gaze pose. The body and tail do not flip or move. |
| 10 | look `180` to `337.5` | 8 | Pointer is below through upper-left | down, down-left, hold, hold, hold, up-left, hold, hold | Continue with clear quadrant gazes. The skull, dropped ears, torso, feet, scale, and baseline stay fixed. |

## Cross-state continuity

- Standing states share the 176 px body scale and the `y=203` grounded baseline at their quiet boundary.
- `waving`, `jumping`, and `failed` settle back to a standing boundary before the loop restarts.
- `waiting` is a held attentive state. It stays distinct from idle through the alert eyes and ears, not through a limb gesture.
- Pointer looks preserve the complete body footprint and the `y=203` baseline. Generate intermediates in four-pose source families when a full row changes body geometry. Do not synthesize ear or head follow-through.
- Directional drag rows are independent cyclic gaits and do not borrow frames from stationary rows.

## Rejection conditions

Reject the complete row when any of these appear:

- the body slides inside the cell without state meaning;
- the first-to-last seam is more abrupt than an internal step;
- visible height, head size, or baseline pops;
- a paw, tail, ear, or head appears from an unrelated pose;
- a full-body pose is copied from another state outside an explicit shared neutral boundary or fixed-body tail rig;
- `running` or `review` becomes more expressive than `idle`;
- the `running` tail moves but the face, coat, legs, or central body flicker or redraw;
- `waiting` introduces a paw lift, head turn, or repeated gesture;
- a pointer-look cell changes full-body scale or registration;
- chroma fringe, clipping, detached pixels, or transparent holes remain.
