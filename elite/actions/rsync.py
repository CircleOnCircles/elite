import ast
import os
import shutil

from . import Action, ActionError


class Rsync(Action):
    __action_name__ = 'rsync'

    def __init__(self, path, source, executable=None, archive=True, options=None):
        self.path = path
        self.source = source
        self.executable = executable
        self.archive = archive
        self.options = options

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)
        source = os.path.expanduser(self.source)

        # Determine the rsync executable
        if not self.executable:
            executable = shutil.which('rsync')
            if not executable:
                raise ActionError('unable to find rsync executable to use')

        # Create a list to store our rsync options
        options_list = []

        if self.archive:
            options_list.append('--archive')

        # Add any additional user provided options
        options_list.extend(self.options if self.options else [])

        # The output we want from rsync is a tuple containing the operation and filename of
        # each affected file
        options_list.append("--out-format=('%o', '%n')")

        # Run rsync to sync the files requested
        rsync_proc = self.run(
            [executable] + options_list + [source, path], stdout=True,
            fail_error='rsync failed to sync the requested source to path'
        )

        # Obtain rsync output and check to see if any changes were made
        rsync_output = rsync_proc.stdout.strip()
        if not rsync_output:
            return self.ok()

        # Changes were found and must be reported to the user
        changes = [ast.literal_eval(c) for c in rsync_output.split('\n')]
        return self.changed(changes=changes)
