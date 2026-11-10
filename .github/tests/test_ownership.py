"""Unsigned synthetic host: actual dispatcher, all wrappers, complete unchanged SDK."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get("OWNERSHIP_SOURCE_ROOT", ROOT)).resolve()
SDK = {
    "4DPluginAPI.c": "478081f0238f6bc5393222f574bc2656f010b67b",
    "4DPluginAPI.h": "9054b45ffc7ff6f5b8d57529a3788a55d977b314",
    "EntryPoints.h": "730f2f77ff2713fb2fe4b7d6562baeedf5f664cb",
    "Flags.h": "10a83185333dac06a62dda61b9f9428243d1e2ee",
    "PrivateTypes.h": "77053dc0c0a3718d2d3b6f158371a6af78c6ae66",
    "PublicTypes.h": "2bb392e73e9c556c274fe0a75b3a6b83e310b77c",
    "4DPluginAPI.def": "996ecc4ab11ad165de9192eba2e7478db141c757",
    "licence.txt": "e6af14f72d6e5e9bde3eab35d18f5f23823e46a2",
}
WRAPPERS = (
    "ARRAY_BOOLEAN", "ARRAY_DATE", "ARRAY_INTEGER", "ARRAY_LONGINT", "ARRAY_REAL",
    "ARRAY_TEXT", "ARRAY_TIME", "C_BLOB", "C_DATE", "C_INTEGER", "C_LONGINT",
    "C_PICTURE", "C_POINTER", "C_REAL", "C_TEXT", "C_TIME",
)


@unittest.skipUnless(sys.platform == "darwin", "macOS synthetic host")
class OwnershipTests(unittest.TestCase):
    results = []

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="split-pictures-ownership-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.binary = Path(cls.temp.name) / "ownership"
        api = SOURCE / "4D Plugin API"
        for name, expected in SDK.items():
            contents = (api / name).read_bytes()
            blob = hashlib.sha1(f"blob {len(contents)}\0".encode() + contents).hexdigest()
            if blob != expected:
                raise AssertionError(f"Re-audit changed SDK: {name}: {blob}")
        wrappers = sorted((api / "Classes").glob("*.cpp"))
        if [path.stem for path in wrappers] != list(WRAPPERS):
            raise AssertionError("Re-audit changed wrapper inventory")
        command = [
            "clang++", "-std=c++14", "-x", "objective-c++",
            "-include", str(ROOT / ".github/tests/ownership_platform.h"),
            "-I", str(api), "-I", str(api / "Classes"), "-I", str(SOURCE),
            "-fsanitize=address,undefined", "-fno-sanitize=alignment",
            "-fno-omit-frame-pointer", "-g",
            "-Wno-deprecated-declarations", "-Wno-return-type-c-linkage",
            "-Wno-ignored-attributes", "-Wno-writable-strings",
            str(api / "4DPluginAPI.c"), *map(str, wrappers),
            str(SOURCE / "4DPlugin.cpp"), str(ROOT / ".github/tests/ownership_host.mm"),
            "-framework", "Cocoa", "-framework", "Carbon", "-o", str(cls.binary),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        imports = subprocess.check_output(["nm", "-u", str(cls.binary)], text=True)
        forbidden = {
            "_system", "_popen", "_execve", "_posix_spawn", "_kill", "_getenv",
            "_setenv", "_OBJC_CLASS_$_NSURL", "_OBJC_CLASS_$_NSImage",
            "_OBJC_CLASS_$_NSProcessInfo", "_OBJC_CLASS_$_NSWorkspace",
            "_OBJC_CLASS_$_NSFileManager", "_OBJC_CLASS_$_NSAppleScript",
            "_CFURLCreateWithFileSystemPath", "_CFURLCopyFileSystemPath",
            "_CGImageSourceCreateWithData", "_CGImageDestinationCreateWithData",
            "_AESend", "_AESendMessage", "_OSAExecute",
        }
        linked = {line.split()[-1] for line in imports.splitlines() if line.split()}
        if forbidden & linked:
            raise AssertionError(f"Real platform boundary linked: {forbidden & linked}")

    @classmethod
    def tearDownClass(cls):
        passed = sum(result["returncode"] == 0 for result in cls.results)
        print(f"LEAF runs={len(cls.results)} passed={passed} "
              f"failed={len(cls.results) - passed}", file=sys.stderr)
        if os.environ.get("OWNERSHIP_LOG"):
            Path(os.environ["OWNERSHIP_LOG"]).write_text(json.dumps(cls.results, indent=2))

    def run_case(self, case, text="", empty="allocated", *args):
        result = subprocess.run(
            [str(self.binary), case, text, empty, *map(str, args)],
            env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0",
                 "UBSAN_OPTIONS": "halt_on_error=1"},
            capture_output=True, text=True,
        )
        type(self).results.append({
            "case": case, "text": text, "empty": empty, "args": args,
            "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
        })
        self.assertEqual(result.returncode, 0, f"{case}: {result.stdout}{result.stderr}")
        self.assertIn("strings=0 pictures=0 handles=0 objects=n/a collections=n/a", result.stdout)

    def test_paths_and_copy_exact_text_and_empty_owners(self):
        for case in ("path", "copy"):
            for text in ("ASCII", "\u65e5", "\U0001f600", ""):
                for empty in ("allocated", "null"):
                    with self.subTest(case=case, text=text, empty=empty):
                        self.run_case(case, text, empty)

    def test_picture_creation_borrowing_and_owned_returns(self):
        for case in ("bytes", "gray", "size", "thumbnail"):
            with self.subTest(case=case):
                self.run_case(case)

    def test_array_transfers_copy_churn_replacement_shrink_clear_rejection(self):
        for empty in ("allocated", "null"):
            with self.subTest(empty=empty):
                self.run_case("arrays", "", empty)

    def test_scalar_content_setter_lifetimes(self):
        for text in ("ASCII", "\u65e5", "\U0001f600", ""):
            for empty in ("allocated", "null"):
                with self.subTest(text=text, empty=empty):
                    self.run_case("scalar", text, empty)

    def test_failed_unspecified_command_returns_preserve_existing_behavior(self):
        for case in ("path", "copy", "gray", "size", "thumbnail"):
            for failure in ("handle", "command"):
                with self.subTest(case=case, failure=failure):
                    self.run_case(f"{case}:{failure}")

    def test_sdk_failure_predicates_not_oom_safety(self):
        self.run_case("sdk-failures")

    def test_successful_command_return_owners(self):
        for case in ("path", "copy", "gray", "size", "thumbnail"):
            for kind in range(3):
                with self.subTest(case=case, kind=kind):
                    self.run_case("command-returns", "", "allocated", kind, case)

    def test_pointer_references(self):
        for case in ("pointer", "pointer-field"):
            with self.subTest(case=case):
                self.run_case(case, "ASCII")

    def test_heap_owning_wrapper_copy_capabilities_and_runtime_probes(self):
        for name in ("C_TEXT", "ARRAY_TEXT", "CPicture", "C_PICTURE", "C_BLOB",
                     "ARRAY_BOOLEAN", "ARRAY_DATE", "ARRAY_INTEGER", "ARRAY_LONGINT",
                     "ARRAY_REAL", "ARRAY_TIME", "values"):
            for case in ("traits", "copy-probe"):
                with self.subTest(wrapper=name, case=case):
                    self.run_case(case, name)

    def test_actual_dispatcher_terminal_enumeration_is_offline(self):
        for empty in ("allocated", "null"):
            with self.subTest(empty=empty):
                self.run_case("dispatch", "", empty)


if __name__ == "__main__":
    unittest.main()
