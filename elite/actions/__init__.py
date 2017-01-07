import json
import keyword
import os
import shlex
import subprocess
import sys


# A list of reserved argument names that may not be used by actions
FORBIDDEN_ARGS = ['sudo', 'ok', 'changed']


class Argument(object):
    def __init__(self, name, optional=False, default=None, choices=None):
        self.name = name
        self.optional = optional
        self.default = default
        self.choices = choices

    def __repr__(self):
        args = [f'name={self.name!r}']
        if not self.optional:
            args.append(f'optional={self.optional!r}')
        if self.default is not None:
            args.append(f'default={self.default!r}')
        if self.choices is not None:
            args.append(f'choices={self.choices!r}')
        return f"{type(self).__name__}({', '.join(args)})"


class Action(object):
    def __init__(self, *arg_specs):
        for arg_spec in arg_specs:
            # Check for forbidden arguments used be elite
            if arg_spec.name in FORBIDDEN_ARGS:
                self.fail(f'module uses argument {arg_spec.name} which is forbidden')

            # Check for arguments that override Python keywords
            if arg_spec.name in keyword.kwlist:
                self.fail(f'module uses argument {arg_spec.name} which is a Python keyword')

            # Check for arguments that override Python builtins
            if arg_spec.name in dir(__builtins__):
                self.fail(f'module uses argument {arg_spec.name} which is a Python builtin')

        self.arg_specs = arg_specs

        # Parse and validate arguments in JSON via stdin
        try:
            self.args = json.load(sys.stdin)
        except KeyboardInterrupt:
            exit(2)
        except json.decoder.JSONDecodeError:
            self.fail('the json input provided could not be parsed')
        self.validate_args()

        # Open /dev/null for our run method
        self.devnull = open(os.devnull, 'w')

    def invoke(self):
        """Run the main process function for the action with the appropriate args."""
        self.process(**self.args)

    def validate_args(self):
        # Check that only supported arguments were provided
        arg_spec_names = [a.name for a in self.arg_specs]
        for arg_name in self.args.keys():
            if arg_name not in arg_spec_names:
                self.fail(f"provided argument '{arg_name}' is not supported by this action")

        # Validate our argument specification
        for arg_spec in self.arg_specs:
            # Check that each of the arguments are provided or set the default if optional
            if arg_spec.name not in self.args:
                if arg_spec.optional:
                    self.args[arg_spec.name] = arg_spec.default
                    continue
                else:
                    self.fail(f"mandatory argument '{arg_spec.name}' was not provided")

            # Verify that the provided value is one of the choices
            if (
                arg_spec.choices and
                self.args[arg_spec.name] not in arg_spec.choices
            ):
                self.fail(f"argument '{arg_spec.name}' must be one of {arg_spec.choices}")

    def ok(self, **data):
        print(json.dumps({'changed': False, 'ok': True, **data}, indent=2))
        exit(0)

    def changed(self, message, **data):
        print(json.dumps({'changed': True, 'message': message, 'ok': True, **data}, indent=2))
        exit(0)

    def fail(self, message, **data):
        print(json.dumps({'message': message, 'ok': False, **data}, indent=2))
        exit(1)

    def run(
        self, command, cwd=None, stdout=False, stderr=False, ignore_fail=False, fail_error=None
    ):
        # Allow for the user to send in a string instead of a list for the command
        if isinstance(command, str):
            command = shlex.split(command)

        # Determine if we need to capture stdout and stderr
        kwargs = {
            'stdout': subprocess.PIPE if stdout else self.devnull
        }
        if stderr or (not ignore_fail and not fail_error):
            kwargs['stderr'] = subprocess.PIPE
        else:
            kwargs['stderr'] = self.devnull

        # Run the command
        try:
            proc = subprocess.run(command, cwd=cwd, encoding='utf-8', **kwargs)
        except FileNotFoundError:
            self.fail(f'unable to find executable for command {command}')

        # Fail if the command returned a non-zero returrn code
        if proc.returncode and not ignore_fail:
            if proc.stderr:
                self.fail(proc.stderr.strip())
            elif fail_error:
                self.fail(fail_error)
            else:
                self.fail(f'unable to execute command {command}')

        return proc
