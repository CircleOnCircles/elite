from functools import wraps

import yaml

from .elite import Elite, EliteError
from .config import load_config
from .printer import Printer
from .utils import build_absolute_path
from . import ansi


def main(config_path, config_order, action_search_paths=[]):
    def decorator(main):
        @wraps(main)
        def decorated_function():
            try:
                # Setup Elite and our configuration
                action_search_paths_abs = [build_absolute_path(msp) for msp in action_search_paths]

                # Create our objects
                printer = Printer()
                elite = Elite(printer=printer, action_search_paths=action_search_paths_abs)
                config = load_config(build_absolute_path(config_path), config_order)

                # Header
                printer.header()

                # Run the main Elite entrypoint
                main(elite, config, printer)

                # Summary
                printer.heading('Summary')
                elite.summary()

            # A config issue was encountered
            except yaml.YAMLError as e:
                print()
                print(
                    f'{ansi.RED}Config Error: {e}{ansi.ENDC}'
                )

            # A task failed to run
            except EliteError:
                # Summary
                printer.heading('Summary')
                elite.summary()

            # User has hit Ctrl+C
            except KeyboardInterrupt:
                print()
                print()
                print(
                    f'{ansi.RED}Processing aborted as requested by keyboard interrupt.{ansi.ENDC}'
                )

            # Footer
            finally:
                printer.footer()

        return decorated_function

    return decorator
