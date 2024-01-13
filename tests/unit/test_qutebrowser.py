# SPDX-FileCopyrightText: Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for qutebrowser.qutebrowser.

(Mainly commandline flag parsing)
"""

import re

import pytest

from qutebrowser import qutebrowser


@pytest.fixture
def parser():
    return qutebrowser.get_argparser()


class TestDebugFlag:

    def test_valid(self, parser):
        args = parser.parse_args(['--debug-flag', 'chromium',
                                  '--debug-flag', 'stack'])
        assert args.debug_flags == ['chromium', 'stack']

    def test_invalid(self, parser, capsys):
        with pytest.raises(SystemExit):
            parser.parse_args(['--debug-flag', 'invalid'])

        _out, err = capsys.readouterr()
        assert 'Invalid debug flag - valid flags:' in err


class TestLogFilter:

    def test_valid(self, parser):
        args = parser.parse_args(['--logfilter', 'misc'])
        assert args.logfilter == 'misc'

    def test_invalid(self, parser, capsys):
        with pytest.raises(SystemExit):
            parser.parse_args(['--logfilter', 'invalid'])

        _out, err = capsys.readouterr()
        print(err)
        assert 'Invalid log category invalid - valid categories' in err


class TestJsonArgs:

    def test_partial(self, parser):
        """Make sure we can provide a subset of all arguments.

        This ensures that it's possible to restart into an older version of qutebrowser
        when a new argument was added.
        """
        args = parser.parse_args(['--json-args', '{"debug": true}'])
        args = qutebrowser._unpack_json_args(args)
        # pylint: disable=no-member
        assert args.debug
        assert not args.temp_basedir


class TestValidateUntrustedArgs:

    @pytest.mark.parametrize('args', [
        [],
        [':nop'],
        [':nop', '--untrusted-args'],
        [':nop', '--debug', '--untrusted-args'],
        [':nop', '--untrusted-args', 'foo'],
        ['--debug', '--untrusted-args', 'foo'],
        ['foo', '--untrusted-args', 'bar'],
    ])
    def test_valid(self, args):
        qutebrowser._validate_untrusted_args(args)

    @pytest.mark.parametrize('args, message', [
        (
            ['--untrusted-args', '--debug'],
            "Found --debug after --untrusted-args, aborting.",
        ),
        (
            ['--untrusted-args', ':nop'],
            "Found :nop after --untrusted-args, aborting.",
        ),
        (
            ['--debug', '--untrusted-args', '--debug'],
            "Found --debug after --untrusted-args, aborting.",
        ),
        (
            [':nop', '--untrusted-args', '--debug'],
            "Found --debug after --untrusted-args, aborting.",
        ),
        (
            [':nop', '--untrusted-args', ':nop'],
            "Found :nop after --untrusted-args, aborting.",
        ),
        (
            [
                ':nop',
                '--untrusted-args',
                ':nop',
                '--untrusted-args',
                'https://www.example.org',
            ],
            (
                "Found multiple arguments (:nop --untrusted-args "
                "https://www.example.org) after --untrusted-args, aborting."
            )
        ),
        (
            ['--untrusted-args', 'okay1', 'okay2'],
            "Found multiple arguments (okay1 okay2) after --untrusted-args, aborting.",
        ),
    ])
    def test_invalid(self, args, message):
        with pytest.raises(SystemExit, match=re.escape(message)):
            qutebrowser._validate_untrusted_args(args)
