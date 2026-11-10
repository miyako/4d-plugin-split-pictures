# Native ownership audit

## Provenance and inventory

Baseline: `83ab626f7c0eccd8f81fb1bfb2519d5afcea2da6`.
Canonical guidance: `miyako/skills`,
`4d-skills/skills/4dplugin/SKILL.md` at immutable
`e6b492fcb81e5e1a7f7db723594b420e63bf6eb9`, retrieved through the contents API.
Harness prior art: `miyako/4d-plugin-script` at immutable
`c13f12088f8c88b2f0fa6f5e79104759707ec7e2`; adapted to this repository,
not reused as evidence of this repository's behavior.

The bundled API header identifies itself as **v13**, not a verified upstream
release identifier. The runner verifies these exact unchanged Git blobs before
compilation, against both archived baseline and fixed source:

| SDK file | Git blob |
|---|---|
| 4DPluginAPI.c | `478081f0238f6bc5393222f574bc2656f010b67b` |
| 4DPluginAPI.h | `9054b45ffc7ff6f5b8d57529a3788a55d977b314` |
| EntryPoints.h | `730f2f77ff2713fb2fe4b7d6562baeedf5f664cb` |
| Flags.h | `10a83185333dac06a62dda61b9f9428243d1e2ee` |
| PrivateTypes.h | `77053dc0c0a3718d2d3b6f158371a6af78c6ae66` |
| PublicTypes.h | `2bb392e73e9c556c274fe0a75b3a6b83e310b77c` |
| 4DPluginAPI.def | `996ecc4ab11ad165de9192eba2e7478db141c757` |
| licence.txt | `e6af14f72d6e5e9bde3eab35d18f5f23823e46a2` |

All tracked native source is the complete SDK, `4DPlugin.cpp`/`.h`,
`4D Plugin_Prefix.pch`, and `4D Plugin API/Classes` (baseline tree
`efbc15b39c362057536caa8050cc81b692aef48d`). There is no second native source
copy hidden under the tracked build outputs or bundled sample plugin.
All **16** `.cpp` wrapper implementations and corresponding headers are included
in both Xcode's source phase and the Visual Studio compile inventory:

| Wrappers/helpers | Ownership surface |
|---|---|
| ARRAY_BOOLEAN, ARRAY_DATE, ARRAY_INTEGER, ARRAY_LONGINT, ARRAY_REAL, ARRAY_TIME | Six heap-owned vector wrappers; value element conversions; implicit wrapper copying was unsafe |
| ARRAY_TEXT | Seventh heap-owned vector wrapper; copies borrowed input text before replacement; creates independent output text and transfers at index zero and above |
| C_TEXT | Heap-owned UTF-16 string; content setters for scalar output/return; already explicitly noncopyable at baseline |
| C_BLOB / CBytes | Outer heap-owned helper; inner vector is independently copyable by value; hex/base64 helpers pass through C_TEXT |
| C_PICTURE / CPicture | Outer owned helper, inner picture reference and owned CBytes; command arguments, output handoffs, format conversion and metadata enumeration |
| C_POINTER | Borrowed pointer; constructs command references, not an owning fetched value |
| C_DATE, C_INTEGER, C_LONGINT, C_REAL, C_TIME | Value-only wrappers, no owned string aliases; remain copyable |
| C_TYPES.h | UTF-8/UTF-16 value string and vector aliases; platform imports |
| 4DPlugin.cpp / PluginMain / CommandDispatcher / SPLIT_PICTURES | Actual sole export dispatcher and picture/text-array command; no wrapper copies or CPicture calls |

Root and prebuilt-bundle `manifest.json` both declare only
`SPLIT PICTURES(&P;&Y;&Y)`: picture input, text-array and picture-array outputs,
no scalar return. All wrappers were audited regardless of that manifest.
CPicture and C_POINTER defects are library/helper defects, not evidence that
the current exported dispatcher reaches them. The ten newly noncopyable types
have no copy call in current production consumers. The test deliberately
instantiates such copies on the baseline to demonstrate the latent defect.

## Exact contracts and surgical changes

`PA_SetStringInArray` (SDK baseline lines 4444-4460) disposes the old element
and shallow-transfers the descriptor only for Unicode-array kind, non-null
data handle, `0 <= index <= fNbElements`, and non-null descriptor pointer.
Rejection retains the caller's ownership. `PA_GetStringInArray` (4266-4283)
is explicitly borrowed. ARRAY_TEXT and successful SPLIT_PICTURES insertion
already avoid post-transfer disposal; that behavior is unchanged.

`PA_SetStringVariable` (3826-3831) shallow-assigns without clearing the previous
owner. `PA_CreateVariable(eVK_Unistring)` creates an initial empty string;
emptiness does not prove the absence of an allocation. CPicture path/conversion
arguments now initialize Undefined before assignment. Path cleanup occurs
once, through its argument variable, not also through the local alias.

`PA_SetPictureVariable` (3852-3857) also shallow-assigns, while
`PA_CreateVariable(eVK_Picture)` creates an empty owned picture. Input slots
that are immediately overwritten now initialize Undefined. Output-only slots
retain their valid empty picture initialization. `fromFileAtPath` retains the
output into the wrapper before clearing the output argument. `setBytes`
releases the successful creation reference after `setPicture` retains it;
creation error is captured immediately, and no new disposal is applied to an
unspecified failed creation return.

`PA_ConvertCharsetToCharset` (4776-4793) explicitly returns **bytes** and forwards
byte capacity. `createCopy` now divides the returned byte count by
`sizeof(PA_Unichar)` for the `CUTF16String` constructor's **code units**.
The synthetic engine preserves those units rather than returning a convenient
unit count. Nonempty ASCII catches the original temporary-buffer overread;
BMP/supplementary and empty inputs verify callback content and termination too.

All five CPicture command helpers now clear successful owning return variables.
The shared helper captures `PA_GetLastError()` immediately after execution,
before any inspection or cleanup. On failure it does not inspect, normalize,
adopt or clear the unspecified return descriptor. The bundled
`PA_ExecuteCommandByID` (5257-5290) returns raw kind zero on handle-allocation
failure; `PA_GetVariableKind` normalizes zero as text, so kind inspection cannot
replace error checking.

C_POINTER now calls the exact SDK's `PA_SetVariableOrFieldReference`
(3923-3945), which derives kind/scope/tag/index/name from the pointer. It does
not fetch an owning value and reinterpret its union as reference metadata.
The SDK table has four entries; invalid scopes are not passed to it.
Existing field-reference behavior is preserved.

The seven array classes, C_BLOB, CPicture and C_PICTURE now declare private
copy construction/assignment. Each previously copied a raw owned pointer,
with both destructors deleting it. C_TEXT already provides noncopy prior art.
CBytes, numeric/date/time values and borrowed C_POINTER remain copyable.
All actual consumers compile with these restrictions.

## Reproducible isolated evidence

Run on macOS, without an Xcode/MSBuild project build:

```sh
python3 -B .github/tests/test_ownership.py -v
```

The runner compiles the **entire unchanged SDK**, all **16 actual wrappers**
and **actual 4DPlugin.cpp**, not extracted SDK functions or replacements.
The forced platform header is applied before every translation unit, redirecting
image/URL/filesystem entry points to denied synthetic stubs. The SDK's real
`gCall4D` boundary is a strict selector allowlist with synthetic in-memory
strings, handles, pictures, commands and codec results. Unknown selectors abort.
The linked-import gate rejects real image/file/AppleScript/process boundaries.
No native image decode, platform file read, UI, private sample data, settings,
network, signing or packaging is executed by the harness. A synthetic path
string reaches only the synthetic command callback, never a real file command.

Clang uses ASan and UBSan, with alignment checks disabled for the legacy packed
SDK ABI; this is not full ABI/alignment validation. macOS LeakSanitizer is
disabled; explicit allocation maps require **strings=0, pictures=0, handles=0**
on each successful leaf, including picture retain counts. Object/collection
API types do not exist in this SDK and are reported n/a, not simulated.

The same final harness is run with `OWNERSHIP_SOURCE_ROOT` pointing first at
an immutable `git archive` of the baseline native source and then at fixed
actual source. No baseline SDK/wrapper rewriting is used. Each leaf is its own
process, so a baseline sanitizer failure does not hide remaining cases.

| Group | Leaves | Baseline pass / fail | Fixed pass / fail |
|---|---:|---:|---:|
| Path and conversion: ASCII, BMP, supplementary, empty; allocated/null empty strings | 16 | 0 / 16 | 16 / 0 |
| Picture bytes repeated 20 times, gray, size, thumbnail | 4 | 0 / 4 | 4 / 0 |
| Array copy/churn/replacement/shrink/clear/rejections, both empties | 2 | 2 / 0 | 2 / 0 |
| Scalar content setter/return independence, four fixtures and both empties | 8 | 8 / 0 | 8 / 0 |
| Five commands: failed parameter-handle allocation and poisoned failed return | 10 | 0 / 10 | 10 / 0 |
| Successful command returns: Undefined, owned text, owned picture; five commands | 15 | 0 / 15 | 15 / 0 |
| Pointer variable scopes and field metadata | 2 | 1 / 1 | 2 / 0 |
| Eleven owning type traits plus value controls, and corresponding runtime copy probes | 24 | 4 / 20 | 24 / 0 |
| Actual dispatcher terminal-enumeration/null/unknown-selector controls, both empties | 2 | 2 / 0 | 2 / 0 |
| SDK failure-predicate control | 1 | 1 / 0 | 1 / 0 |
| **Total** | **84** | **18 / 66** | **84 / 0** |

Named baseline diagnostics: `copy` ASCII/allocated and ASCII/null report ASan
`heap-buffer-overflow`; nine runtime copy probes report ASan
`heap-use-after-free` (ARRAY_BOOLEAN/DATE/INTEGER/LONGINT/REAL/TEXT/TIME,
C_BLOB, C_PICTURE); CPicture's runtime copy probe reports duplicate/unowned
picture disposal. Path cases expose duplicate/unowned string disposal and
reference imbalance; other picture cases expose string/picture owner imbalance.
C_POINTER reports `reference construction fetched an owning value`.
The original C_TEXT noncopy restriction, value-copy controls, scalar setters,
array transfer/rejection, field metadata and terminal dispatcher all pass on
the baseline, demonstrating that these controls are not invented fixes.

## Deferred contracts and limits

The v13 SDK does **not** specify whether successful `PA_GetPictureData` metadata
is borrowed or independently owned, nor whether handle-filled calls return
distinct metadata. The dispatcher transfers the query descriptor into an array;
CPicture enumerates metadata; both also have data-read calls. Adding disposal
without that contract could create a use-after-free. These paths are unchanged.
The dispatcher test exercises terminal failure with a poisoned, unread return,
not successful metadata extraction; no metadata-lifetime safety is certified.

`PA_ResizeArray` updates logical count even when `PA_SetHandleSize` fails.
The SDK-predicate case demonstrates physical allocation preservation and logical
count divergence, repairs only the synthetic descriptor for cleanup, and does
not dispatch into the inconsistent array. OOM/resize safety in production is
deferred; success tests and rejected setter controls are not evidence of it.
Likewise native conversion/picture creation failure contracts are not established
by successful synthetic codecs. Existing helper failure behavior is retained:
argument processing/cleanup can overwrite API errors, zero size outputs and
unchanged/empty picture returns remain possible. No new throw, status channel
or success-shaped recovery policy is introduced; these remain diagnostic gaps.

No actual 4D host, Windows SDK branch/native ABI, real image codec, file import,
Objective-C UI/image adapter, signing or release is tested. This is not a
Windows 4D crash reproduction.

Before validation/push, both existing workflows and all scripts/build phases
were read: Bump version and Build are manual-only. Xcode's Deployment phase
signs, packages and notarizes; its outputs can overwrite the tracked sample
bundle. Neither project build was run. Existing workflows/projects/manifests/
binaries are unchanged. The new read-only unsigned workflow is push/path-filtered
only to `master` and `miyako-split-pictures-ownership`; it has no release,
artifact upload, manual dispatch or deployment job.
