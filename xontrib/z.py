"""Tracks your most used directories, based on 'frecency'"""
import os as _os
import sys as _sys
import xonsh.lazyasd as _lazyasd

_old_cd = aliases['cd']

class _ZHandler:
    """Tracks your most used directories, based on 'frecency'.

   After  a  short  learning  phase, z will take you to the most 'frecent'
   directory that matches ALL of the regexes given on the command line, in
   order.

   For example, z foo bar would match /foo/bar but not /bar/foo.
   """
    def parser():
        from argparse import ArgumentParser
        parser = ArgumentParser(prog='avox', description=__doc__)
   
        parse.add_argument('-c', default=False,
                            action='store_true', dest='subdir_only',
                            help='restrict matches to subdirectories of the current directory')

        actions = create.add_mutually_exclusive_group()
        actions.add_argument('-e', const='echo', default='cd',
                           action='store_const', dest='action',
                           help="echo the best match, don't cd")
        actions.add_argument('-l', const='list', default='cd',
                           action='store_const', dest='action',
                           help='list only')
        actions.add_argument('-x', const='remove', default='cd',
                           action='store_const', dest='action',
                           help='remove the current directory from the datafile')
        actions.add_argument('-h', const='help', default='cd',
                           action='store_const', dest='action',
                           help='show a brief help message')

        modes = create.add_mutually_exclusive_group()
        modes.add_argument('-r', const='rank', default='frecency',
                           action='store_const', dest='mode',
                           help="match by rank only")
        modes.add_argument('-t', const='rank', default='frecency',
                           action='store_const', dest='mode',
                           help="match by recent access only")

        return parser

    parser = _lazyasd.LazyObject(parser, locals(), 'parser')

    @classmethod
    def handler(cls, args, stdin=None):
        return cls()(args, stdin)

    def __call__(self, args, stdin=None):
        args = self.parser.parse_args(args)
        cmd = self.aliases.get(args.command, args.command)
        if cmd is None:
            self.parser.print_usage()
        else:
            getattr(self, 'cmd_'+cmd)(args, stdin)


    @classmethod
    def cd_handler(cls, args, stdin=None):
        self = cls()
        oldve = self.vox.active()
        rtn = _old_cd(args, stdin)
        newve = self.env()
        if oldve != newve:
            if newve is None:
                self.vox.deactivate()
            else:
                self.vox.activate(newve)
        return rtn

aliases['z'] = _ZHandler.handler
aliases['cd'] = _ZHandler.cd_handler
