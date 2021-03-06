# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Main shell for parsing arguments directed toward Craton."""

from __future__ import print_function

import argparse
import six
import sys

from oslo_utils import encodeutils

from cratonclient import __version__
from cratonclient import session as craton

from cratonclient.common import cliutils
from cratonclient.shell.v1 import shell
from cratonclient.v1 import client


class CratonShell(object):
    """Class used to handle shell definition and parsing."""

    def get_base_parser(self):
        """Configure base craton arguments and parsing."""
        parser = argparse.ArgumentParser(
            prog='craton',
            description=__doc__.strip(),
            epilog='See "craton help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=argparse.HelpFormatter
        )

        parser.add_argument('-h', '--help',
                            action='store_true',
                            help=argparse.SUPPRESS,
                            )
        parser.add_argument('--version',
                            action='version',
                            version=__version__,
                            )
        parser.add_argument('--craton-url',
                            default=cliutils.env('CRATON_URL'),
                            help='Defaults to env[CRATON_URL]',
                            )
        parser.add_argument('--craton-project-id',
                            type=int,
                            default=1,
                            help='Defaults to 1',
                            )
        parser.add_argument('--os-username',
                            default=cliutils.env('OS_USERNAME'),
                            help='Defaults to env[OS_USERNAME]',
                            )
        parser.add_argument('--os-password',
                            default=cliutils.env('OS_PASSWORD'),
                            help='Defaults to env[OS_PASSWORD]',
                            )
        return parser

    # NOTE(cmspence): Credit for this get_subcommand_parser function
    # goes to the magnumclient developers and contributors.
    def get_subcommand_parser(self):
        """Get subcommands by parsing COMMAND_MODULES."""
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>',
                                           dest='subparser_name')
        command_modules = shell.COMMAND_MODULES
        for command_module in command_modules:
            self._find_subparsers(subparsers, command_module)
        self._find_subparsers(subparsers, self)
        return parser

    # NOTE(cmspence): Credit for this function goes to the
    # magnumclient developers and contributors.
    def _find_subparsers(self, subparsers, actions_module):
        """Find subparsers by looking at *_shell files."""
        help_formatter = argparse.HelpFormatter
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            action_help = desc.strip()
            arguments = getattr(callback, 'arguments', [])
            subparser = (subparsers.add_parser(command,
                                               help=action_help,
                                               description=desc,
                                               add_help=False,
                                               formatter_class=help_formatter)
                         )
            subparser.add_argument('-h', '--help',
                                   action='help',
                                   help=argparse.SUPPRESS)
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def main(self, argv):
        """Main entry-point for cratonclient shell argument parsing."""
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)
        subcommand_parser = (
            self.get_subcommand_parser()
        )
        self.parser = subcommand_parser

        if options.help or not argv:
            parser.print_help()
            return 0

        args = subcommand_parser.parse_args(argv)

        session = craton.Session(
            username=args.os_username,
            token=args.os_password,
            project_id=args.craton_project_id,
        )
        self.cc = client.Client(session, args.craton_url)

        args.func(self.cc, args)


def main():
    """Main entry-point for cratonclient's CLI."""
    try:
        CratonShell().main(map(encodeutils.safe_decode, sys.argv[1:]))
    except Exception as e:
        print("ERROR: %s" % encodeutils.safe_encode(six.text_type(e)),
              file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    main()
