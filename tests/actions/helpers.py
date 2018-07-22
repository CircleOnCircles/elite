import os
from collections import namedtuple
from subprocess import CompletedProcess


CommandMapping = namedtuple(
    'CommandMapping', ['command', 'returncode', 'stdout_filename', 'stderr_filename'],
    defaults=(0, None, None)
)


def build_run(fixture_subpath, command_mappings):
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', fixture_subpath)

    # pylint: disable=unused-argument
    def run(self, command, ignore_fail=False, fail_error=None, **kwargs):
        for (
            expected_command, expected_returncode, stdout_filename, stderr_filename
        ) in command_mappings:

            if command != expected_command:
                continue

            expected_stdout = ''
            if stdout_filename:
                with open(os.path.join(fixture_path, stdout_filename), 'r') as f:
                    expected_stdout = f.read()

            expected_stderr = ''
            if stderr_filename:
                with open(os.path.join(fixture_path, stderr_filename), 'r') as f:
                    expected_stderr = f.read()

            return CompletedProcess(
                args=command, returncode=expected_returncode,
                stdout=expected_stdout, stderr=expected_stderr
            )

        raise Exception(f'unexpected command {command} encountered')

    return run
