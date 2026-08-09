# Georgie animation matrix

This file is the source of truth for Georgie's Codex v2 motion.

## Shared geometry

- Cell: `192x208` pixels.
- Atlas: 8 columns by 11 rows, `1536x2288` pixels.
- Master standing body height: 145 pixels at the neutral pose. Use the same row-level scale for every frame.
- Directional drag gait height: 130 pixels. The side profile has more visual mass than the standing pose, so both gait rows use this shared smaller scale.
- Grounded baseline: `y=203`, with at most 1 pixel of drift in frequent rows. Airborne frames move above it without changing body scale.
- Subtle-row height range: at most 3 pixels within a row.
- Lower-torso horizontal drift: at most 0.5 pixel in `review`. The `running` body is checked inside its fixed-body box because the tail intentionally changes the full silhouette.
- Full-silhouette horizontal drift: at most 1 pixel in `review`. The `running` row instead enforces its fixed-body pixel and silhouette budgets plus loop closure.
- In `running`, adjacent frames may change at most 6 percent of central body pixels and 2 percent of the central body silhouette. Tail motion is outside this fixed-body region.
- No frame may change Georgie's head size, muzzle length, ear length, eye spacing, markings, or coat style.
- No cast shadow, detached effect, motion line, blur, floor patch, text, prop, or scenery.

## State sequence

| Row | State | Frames | Trigger meaning | Sequence | Loop requirement |
| ---: | --- | ---: | --- | --- | --- |
| 0 | `idle` | 6 | Codex is resting | neutral, soft inhale, soft exhale, full blink, eyes open, neutral | Quiet breathing. No head turn. Last frame visually matches first. |
| 1 | `running-right` | 8 | User drags Georgie right | contact, down, passing, up, contact, down, passing, up | True right-facing gait at the shared 130 px directional scale, with an even cyclic cadence. |
| 2 | `running-left` | 8 | User drags Georgie left | contact, down, passing, up, contact, down, passing, up | True left-facing gait at the same 130 px scale. Mirror row 1 only if markings remain correct. |
| 3 | `waving` | 4 | Brief greeting or attention | tail at rest, small tail sweep, return through midpoint, tail at rest | One restrained tail greeting. Feet, torso, and head stay anchored. No paw lift. |
| 4 | `jumping` | 5 | Playful direct interaction | exact neutral, crouch, lift, peak, exact neutral | One compact hop. The first and last cells reuse the approved neutral whole pose, so the loop cannot pop at its boundary. |
| 5 | `failed` | 8 | A task failed or stopped | exact neutral, ears soften, sit, eyes lower, recover, rise, standing bridge, exact neutral | Gentle disappointment, not distress. The standing bridge removes the seated-to-neutral pop. |
| 6 | `waiting` | 6 | Codex needs input or approval | paw already held softly up, tiny toe flex, hold, blink, hold, held paw | Paw stays raised through the loop. No repeated lift-drop-lift cycle. |
| 7 | `running` | 6 | Codex is actively working | tail A, tail B, tail C, tail D, tail C, tail B | A continuous restrained tail wag built from one fixed whole body and four image-generated tail keys. The sequence is palindromic, so the three system repeats have no reset frame. Feet, torso, head, muzzle, drop ears, scale, and baseline stay locked. No lateral drift, nod, roll, slide, wink, or paw motion. |
| 8 | `review` | 6 | Codex is checking completed work | attentive, eyes lower slightly, full blink, eyes reopen, attentive, attentive | Most restrained loop. No head circle, side-eye snap, paw lift, tail gesture, or body translation. |
| 9 | look `000` to `157.5` | 8 | Pointer is above through lower-right | up, hold up-right, hold, hold, hold, down-right, hold, hold | The small-angle buckets hold a clear quadrant gaze. This prevents a head roll while the pointer crosses nearby angles. |
| 10 | look `180` to `337.5` | 8 | Pointer is below through upper-left | down, down-left, hold, hold, hold, up-left, hold, hold | Continue with clear quadrant gazes. The skull, dropped ears, torso, feet, scale, and baseline stay fixed. |

## Cross-state continuity

- `idle`, `running`, and `review` share the same grounded neutral silhouette at their quiet boundary.
- `waving`, `jumping`, and `failed` settle back to the grounded neutral silhouette.
- `waiting` is a held state. Its internal loop is seamless even though entering the state changes the paw pose once.
- Pointer looks preserve the complete body footprint and the `y=203` baseline. Generate intermediates in four-pose source families when a full row changes body geometry. Do not synthesize ear or head follow-through.
- Directional drag rows are independent cyclic gaits and do not borrow frames from stationary rows.

## Rejection conditions

Reject the complete row when any of these appear:

- the body slides inside the cell without state meaning;
- the first-to-last seam is more abrupt than an internal step;
- visible height, head size, or baseline pops;
- a paw, tail, ear, or head appears from an unrelated pose;
- a full-body pose is copied from another state;
- `running` or `review` becomes more expressive than `idle`;
- the `running` tail moves but the face, coat, legs, or central body flicker or redraw;
- the waiting paw repeatedly lifts because the row loops;
- a pointer-look cell changes full-body scale or registration;
- chroma fringe, clipping, detached pixels, or transparent holes remain.
