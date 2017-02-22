from pygments.lexer import RegexLexer
from pygments.token import *

__all__ = ['gcodeLexer']

class GcodeLexer(RegexLexer):
    name = 'g-code'
    aliases = ['gcode']
    filenames = ['*.gcode']

    tokens = {
        'root': [
            (r'^;.*$', Comment),
            (r'\(.*\)', Comment),
            (r'\s;.*', Comment.Multiline, 'blockcomment'),
            (r'^[gmtGMT]\d{1,4}\s',Name.Builtin), # M or G commands
            (r'[^gGmM][+-]?\d*[.]?\d+', Keyword),
            (r'\s', Text.Whitespace),
            (r'.*\n', Text),
        ],
        'blockcomment': [
            (r'.*;.*$', Comment.Multiline, '#pop'),
            (r'^.*\n', Comment.Multiline),
            (r'.', Comment.Multiline),
        ]
    }
