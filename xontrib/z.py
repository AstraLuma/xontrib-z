"""Tracks your most used directories, based on 'frecency'"""
import os as _os
import sys as _sys
import re as _re
import functools as _functools
import collections as _collections
import datetime as _datetime
import shutil as _shutil
import xonsh.lazyasd as _lazyasd
import xonsh.dirstack as _dirstack
import xonsh.built_ins as _built_ins

_old_cd = aliases['cd']

class _ZEntry(_collections.namedtuple('ZEntry', ['path', 'rank', 'time'])):
    @property
    def frecency(self):
        dx = _datetime.datetime.utcnow() - self.time
        if dx < _datetime.timedelta(hours=1):
            return self.rank * 4
        elif dx < _datetime.timedelta(days=1):
            return self.rank * 2
        elif dx < _datetime.timedelta(weeks=1):
            return self.rank / 2
        else:
            return self.rank / 4

class _ZHandler:
    """Tracks your most used directories, based on 'frecency'.

    After  a  short  learning  phase, z will take you to the most 'frecent'
    directory that matches ALL of the regexes given on the command line, in
    order.

    For example, z foo bar would match /foo/bar but not /bar/foo.
    """
    GROOM_THRESHOLD = 9000
    GROOM_LEVEL = 0.99

    def parser():
        from argparse import ArgumentParser
        parser = ArgumentParser(prog='avox', description=__doc__)

        parser.add_argument('patterns', metavar='REGEX', nargs='+',
                            help='Names to match')
   
        parser.add_argument('-c', default=False,
                            action='store_true', dest='subdir_only',
                            help='restrict matches to subdirectories of the current directory')

        actions = parser.add_mutually_exclusive_group()
        actions.add_argument('-e', const='echo', default='cd',
                           action='store_const', dest='action',
                           help="echo the best match, don't cd")
        actions.add_argument('-l', const='list', default='cd',
                           action='store_const', dest='action',
                           help='list only')
        actions.add_argument('-x', const='remove', default='cd',
                           action='store_const', dest='action',
                           help='remove the current directory from the datafile')
        # actions.add_argument('-h', const='help', default='cd',
        #                    action='store_const', dest='action',
        #                    help='show a brief help message')

        modes = parser.add_mutually_exclusive_group()
        modes.add_argument('-r', const='rank', default='frecency',
                           action='store_const', dest='mode',
                           help="match by rank only")
        modes.add_argument('-t', const='time', default='frecency',
                           action='store_const', dest='mode',
                           help="match by recent access only")

        return parser

    parser = _lazyasd.LazyObject(parser, locals(), 'parser')

    def __init__(self):
        self.Z_DATA = __xonsh_env__.get('_Z_DATA', _os.path.expanduser('~/.z'))
        self.Z_OWNER = __xonsh_env__.get('_Z_OWNER')
        self.Z_NO_RESOLVE_SYMLINKS = __xonsh_env__.get('_Z_NO_RESOLVE_SYMLINKS', False)
        self.Z_EXCLUDE_DIRS = __xonsh_env__.get('_Z_EXCLUDE_DIRS', [])

    # XXX: Is there a way to make this more transactional?
    def load_data(self):
        with open(self.Z_DATA, 'rt') as f:
            for l in f:
                l = l.strip()
                p, r, t = l.split('|')
                r = int(r)
                if r >= 1:
                    t = _datetime.datetime.utcfromtimestamp(int(t))
                    yield _ZEntry(p, r, t)

    def save_data(self, data):
        # Age data
        if hasattr(data, '__len__') and len(data) > self.GROOM_THRESHOLD:
            for i, e in enumerate(data):
                data[i] = _ZEntry(e.path, int(e.rank * self.GROOM_LEVEL), e.time)

        # Use a temporary file to minimize time the file is open and minimize clobbering
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile('wt', encoding=_sys.getfilesystemencoding()) as f:
            for e in data:
                f.write("{}|{}|{}\n".format(e.path, e.rank, int(e.time.timestamp())))

            if self.Z_OWNER:
                _shutil.chown(f.name, user=self.Z_OWNER)

            # On POSIX, rename() is atomic and will clobber
            # On Windows, neither of these is true, so remove first.
            from xonsh.platform import ON_WINDOWS
            if ON_WINDOWS and _os.path.exists(self.Z_DATA):
                _os.remove(self.Z_DATA)
            _shutil.copy(f.name, self.Z_DATA)

    def _doesitmatch(self, patterns, entry):
        """
        Checks that a series of patterns match against a path.

        Each one is checked in sequence. They must be in order and non-overlapping.
        """
        path = entry.path
        for p in patterns:
            m = p.search(path)
            if m is None: return False
            path = path[m.end():]
        else:
            return True


    def __call__(self, args, stdin=None):
        args = self.parser.parse_args(args)

        if args.action == 'help':
            self.parser.print_help()
            return
        elif args.action == 'remove':
            self.remove(self.pwd())
            return
        
        data = list(self.load_data())
        if args.subdir_only:
            pwd = self.getpwd()
            # XXX: Is there a better way to detect subpath relationship?
            data = [e for e in data if _os.path.commonpath((pwd, e.path)) == pwd]
        if args.mode == 'frecency':
            data.sort(reverse=True, key=lambda e: e.frecency)
        elif args.mode == 'rank':
            data.sort(reverse=True, key=lambda e: e.rank)
        elif args.mode == 'time':
            data.sort(reverse=True, key=lambda e: e.time)
        else:
            # argparse should prevent this from happening
            raise RuntimeError("Unknown sort mode: {}".format(args.mode))

        # Actually do search
        pats = list(map(_re.compile, args.patterns))  # Used repeatedly, pre-evaluate
        data = list(filter(_functools.partial(self._doesitmatch, pats), data))

        if args.action == 'cd':
            _built_ins.run_subproc([['cd', data[0].path]])
        elif args.action == 'echo':
            return data[0].path + '\n'
        elif args.action == 'list':
            # FIXME: Prefix with sort key
            return '\n'.join(e.path for e in data)+'\n'


    def getpwd(self):
        pwd = _os.getcwd()
        if not self.Z_NO_RESOLVE_SYMLINKS:
            pwd = _os.path.normpath(pwd)
        return pwd

    def add(self, path):
        now = _datetime.datetime.utcnow()
        data = list(self.load_data())
        for i, e in enumerate(data):
            if e.path == path:
                data[i] = _ZEntry(e.path, e.rank+1, now)
                break
        else:
            data.append(_ZEntry(path, 1, now))
        self.save_data(data)

    def remove(self, path):
        data = list(self.load_data())
        for i, e in enumerate(data):
            if e.path == path:
                del data[i]
                break
        self.save_data(data)


    @classmethod
    def handler(cls, args, stdin=None):
        return cls()(args, stdin)

# FIXME: This should be pre-command, not on `cd`
    @classmethod
    def cd_handler(cls, args, stdin=None):
        rtn = _old_cd(args, stdin)
        try:
            self = cls()
            self.add(self.getpwd())
        except Exception:
            import traceback
            traceback.print_exc()
        return rtn

aliases['z'] = _ZHandler.handler
aliases['cd'] = _ZHandler.cd_handler
