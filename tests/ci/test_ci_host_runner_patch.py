import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[2]


def job(workflow, name):
    match = re.search(rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  \w+:|\Z)", workflow)
    if match is None:
        raise AssertionError(f"Missing job: {name}")
    return match.group(1)


def step(job_text, name):
    match = re.search(
        rf"(?ms)^      - name: {re.escape(name)}\n(.*?)(?=^      - name: |\Z)",
        job_text,
    )
    if match is None:
        raise AssertionError(f"Missing step: {name}")
    return match.group(1)


def script(step_text):
    match = re.search(r"(?ms)^        run: \|\n(.*)", step_text)
    if match is None:
        raise AssertionError("Missing shell script")
    return textwrap.dedent(match.group(1))


class HostRunnerPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.checkout = Path(temporary.name)
        workflow_path = Path(".github/workflows/build.yml")
        (cls.checkout / workflow_path.parent).mkdir(parents=True)
        shutil.copy2(ROOT / workflow_path, cls.checkout / workflow_path)
        shutil.copy2(ROOT / "ci-ccache-apt-fixes.diff", cls.checkout)
        cls.apply = subprocess.run(
            ["git", "apply", str(ROOT / "ci-host-runner.patch")],
            cwd=cls.checkout,
            text=True,
            capture_output=True,
            check=False,
        )
        if cls.apply.returncode == 0:
            cls.workflow = (cls.checkout / workflow_path).read_text()

    def test_patch_applies_and_replaces_previous_patch(self):
        self.assertEqual(self.apply.returncode, 0, self.apply.stderr)
        self.assertFalse((self.checkout / "ci-ccache-apt-fixes.diff").exists())
        self.assertIn("Show twister build errors", self.workflow)
        self.assertIn("Run cppcheck MISRA analysis", self.workflow)

    def test_build_installs_required_host_tools_and_arm_sdk(self):
        if self.apply.returncode:
            self.skipTest(self.apply.stderr)
        build = job(self.workflow, "build")
        install = script(step(build, "Install build dependencies"))
        for package in (
            "ccache", "cmake", "device-tree-compiler", "g++-multilib",
            "gcc-multilib", "gperf", "ninja-build", "protobuf-compiler",
            "wget", "xz-utils",
        ):
            with self.subTest(package=package):
                self.assertRegex(install, rf"(?m)^  {re.escape(package)}(?: \\)?$")
        initialize = script(step(build, "Initialize"))
        self.assertIn("-r ../zephyr/scripts/requirements.txt", initialize)
        self.assertIn("west sdk install -d /opt/toolchains -t arm-zephyr-eabi", initialize)
        self.assertIn("sudo chown", install)

    def test_twister_diagnostics_are_failure_only_and_optional(self):
        if self.apply.returncode:
            self.skipTest(self.apply.stderr)
        build = job(self.workflow, "build")
        for name in ("Show twister build errors", "Upload twister logs"):
            with self.subTest(step=name):
                self.assertIn("if: failure()", step(build, name))
        upload = step(build, "Upload twister logs")
        self.assertIn("actions/upload-artifact@v4", upload)
        self.assertIn("cerebri/twister-out/**/*.log", upload)
        self.assertIn("cerebri/twister-out/twister.json", upload)
        self.assertIn("if-no-files-found: ignore", upload)

    def test_twister_diagnostics_print_only_first_eight_relevant_lines(self):
        if self.apply.returncode:
            self.skipTest(self.apply.stderr)
        command = script(step(job(self.workflow, "build"), "Show twister build errors"))
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            failed = workspace / "twister-out" / "failed"
            failed.mkdir(parents=True)
            (failed / "build.log").write_text(
                "ordinary output\n"
                + "".join(f"error: failure {number}\n" for number in range(10))
            )
            (workspace / "twister-out" / "passing").mkdir()
            (workspace / "twister-out" / "passing" / "build.log").write_text(
                "build succeeded\n"
            )
            result = subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", command],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("::group::twister-out/failed/build.log", result.stdout)
        self.assertIn("::endgroup::", result.stdout)
        self.assertEqual(result.stdout.count("error: failure"), 8)
        self.assertNotIn("error: failure 8", result.stdout)
        self.assertNotIn("passing/build.log", result.stdout)

    def test_twister_diagnostics_recognize_other_failure_formats(self):
        if self.apply.returncode:
            self.skipTest(self.apply.stderr)
        command = script(step(job(self.workflow, "build"), "Show twister build errors"))
        for message in ("CMake Error at CMakeLists.txt", "Error 2", "Error: failed", "FAILED: target"):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                logs = workspace / "twister-out"
                logs.mkdir()
                (logs / "build.log").write_text(f"harmless output\n{message}\n")
                result = subprocess.run(
                    ["bash", "-e", "-o", "pipefail", "-c", command],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(message, result.stdout)
                self.assertNotIn("harmless output", result.stdout)

    def test_twister_diagnostics_allow_empty_log_directory(self):
        if self.apply.returncode:
            self.skipTest(self.apply.stderr)
        command = script(step(job(self.workflow, "build"), "Show twister build errors"))
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / "twister-out").mkdir()
            result = subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", command],
                cwd=temporary,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_twister_diagnostics_allow_missing_twister_output(self):
        if self.apply.returncode:
            self.skipTest(self.apply.stderr)
        command = script(step(job(self.workflow, "build"), "Show twister build errors"))
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", command],
                cwd=temporary,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_misra_bootstrap_builds_compile_database_on_host(self):
        if self.apply.returncode:
            self.skipTest(self.apply.stderr)
        misra = job(self.workflow, "misra")
        install = script(step(misra, "Install build dependencies"))
        self.assertIn("cppcheck", install)
        self.assertIn("protobuf-compiler", install)
        initialize = script(step(misra, "Initialize"))
        for command in (
            "python3 -m pip install --user --break-system-packages poetry west",
            "command -v west", "west init -l .", "west update",
            "./scripts/cyecca_install", "-r ../zephyr/scripts/requirements.txt",
            "west sdk install -d /opt/toolchains -t arm-zephyr-eabi",
        ):
            with self.subTest(command=command):
                self.assertIn(command, initialize)
        build = step(misra, "Build compile_commands.json (mr_canhubk3/s32k344, app/b3rb)")
        self.assertIn("working-directory: cerebri", build)
        self.assertIn("-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", script(build))
        self.assertNotIn("docker run", misra)

    def test_misra_scopes_cppcheck_and_summarizes_findings(self):
        if self.apply.returncode:
            self.skipTest(self.apply.stderr)
        misra = job(self.workflow, "misra")
        analysis = step(misra, "Run cppcheck MISRA analysis")
        self.assertIn("working-directory: cerebri", analysis)
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            bin_dir = workspace / "bin"
            bin_dir.mkdir()
            checker = bin_dir / "cppcheck"
            checker.write_text(
                "#!/bin/sh\n"
                'printf "%s\\n" "$@" > "$CPPCHECK_ARGS_FILE"\n'
                "printf '%s\\n' '<results><error id=\"misra-c2012-2.1\"/>' "
                "'<error id=\"misra-c2012-2.1\"/>' "
                "'<error id=\"style\"/></results>' >&2\n"
            )
            checker.chmod(0o755)
            arguments = workspace / "arguments.txt"
            summary = workspace / "summary.txt"
            environment = os.environ.copy()
            environment.update(
                PATH=f"{bin_dir}:{environment['PATH']}",
                CPPCHECK_ARGS_FILE=str(arguments),
                GITHUB_STEP_SUMMARY=str(summary),
            )
            result = subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", script(analysis)],
                cwd=workspace,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            options = arguments.read_text().splitlines()
            for option in (
                "--project=build/compile_commands.json",
                "--cppcheck-build-dir=build/cppcheck",
                "--addon=misra", "--inline-suppr",
                "--suppressions-list=tools/misra/suppressions.txt",
                "--error-exitcode=0", "--xml", "--xml-version=2",
            ):
                with self.subTest(option=option):
                    self.assertIn(option, options)
            for source in ("app", "lib", "drivers"):
                self.assertIn(f"--file-filter={workspace}/{source}/*", options)
            self.assertTrue((workspace / "build" / "cppcheck").is_dir())
            self.assertIn('id="misra-c2012-2.1"', (workspace / "misra-report.xml").read_text())
            self.assertRegex(summary.read_text(), r'(?m)^\s*2 id="misra-c2012-2.1"$')
            self.assertRegex(summary.read_text(), r'(?m)^\s*1 id="style"$')

    def test_misra_report_upload_tolerates_missing_file(self):
        if self.apply.returncode:
            self.skipTest(self.apply.stderr)
        upload = step(job(self.workflow, "misra"), "Upload report")
        self.assertIn("if: always()", upload)
        self.assertIn("path: cerebri/misra-report.xml", upload)
        self.assertIn("if-no-files-found: ignore", upload)


if __name__ == "__main__":
    unittest.main()
