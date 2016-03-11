#! /usr/bin/env python2.7
from optparse import OptionParser
import re
import io

def genResult(note, dur, point, tie):
    durPrefix = ''
    durPostfix = ''
    tiePostfix = ''
    if point:
        pointOutput = '.'
    else:
        pointOutput = ''
    if dur == 4:
        durPrefix = ''
    if dur == 8:
        durPrefix = 'q'
    if dur == 16:
        durPrefix = 's'
    if dur == 2:
        if point:
            durPostfix = ' - -'
            pointOutput = ''
        else:
            durPostfix = ' -'
    if dur == 1:
        durPostfix = ' - - -'
    if tie:
        tiePostfix = ' ('
    return durPrefix + note + pointOutput + durPostfix + tiePostfix + " "

def getBody(lines, type):
    isCollect = False
    body = ""
    for l in lines:
        if l.startswith(type):
            isCollect = True
            continue
        if isCollect and l.startswith("."):
            break
        if isCollect:
            body += l + "\n"
    return body

class Note:
    def __init__(self):
        self.note = 0
        self.duration = 4
        self.point = False
        self.postfix = ''
        self.postfix2 = ''
        self.special = None
    def __unicode__(self):
        if self.special:
            return self.special
        value = self.note + str(self.duration)
        if self.point:
            value += "."
        return value + self.postfix2 + self.postfix

    def __str__(self, encoding='utf-8'):
        return self.__unicode__().encode(encoding)


class IllegalNoteException(Exception):
    pass


class JpwFile:
    def __init__(self):
        self.options = []
        self.fonts = []
        self.title = []
        self.voice = []
        self.words = []
        self.attachments = []
        self.page = []
        self.notes = []
        self.key = None
        self.sig = None
        self.song_title = None

        self.alternative_opened = False
        self.repeat = 0

    def __unicode__(self):
        output = []
        output.append(u".Options")
        output.append(u"\n".join(self.options))
        output.append(u"\n")
        output.append(u".Fonts")
        output.append(u"\n".join(self.fonts))
        output.append(u"\n")
        output.append(u".Title")
        output.append(u"\n".join(self.title))
        output.append(u"\n")
        output.append(u".Voice")
        output.append(u"\n".join(self.voice))
        output.append(u"\n")
        output.append(u".Words")
        output.append(u"\n".join(self.words))
        output.append(u"\n")
        output.append(u".Attachments")
        output.append(u"\n".join(self.attachments))
        output.append(u"\n")
        output.append(u".Page")
        output.append(u"\n".join(self.page))

        return u"\n".join(output)

    def __str__(self, encoding='utf-8'):
        return self.__unicode__().encode(encoding)

    def parse(self, from_file):
        try:
            input = io.open(from_file, 'r', encoding='utf-16').read()
        except UnicodeDecodeError:
            return None

        section_list = [
            'fonts',
            'options',
            'title',
            'voice',
            'words',
            'attachments',
            'page',
        ]
        lines = input.splitlines()
        section_name = ''
        for line in lines:
            if len(line.strip()) == 0:
                continue
            if line.startswith("."):
                section_name = line[1:].strip().lower()
                continue
            if section_name in section_list:
                getattr(self, section_name).append(line)

    def number_to_note(self, n):
        note = ''
        if n == '1':
            note = 'c\''
        elif n == '2':
            note = 'd\''
        elif n == '3':
            note = 'e\''
        elif n == '4':
            note = 'f\''
        elif n == '5':
            note = 'g\''
        elif n == '6':
            note = 'a\''
        elif n == '7':
            note = 'b\''
        elif n == '0':
            note = 'r'
        return note

    def key_to_offset(self):

        offset = 0
        if self.key:
            kv = self.key.split("=")
            if len(kv) == 2:

                if kv[0] == '1':
                    line.append('\\key %s \\major' % self.parse_note(kv[1]))
                elif kv[0] == '6':
                    line.append('\\key %s \\minor' % self.parse_note(kv[1]))
        return offset

    def parse_token(self, token):
        ret_value = []
        note = None
        end = ''
        skip = False
        skipped = ''
        postfix = ''
        postfix2 = ''
        offset = self.key_to_offset()
        for n in token:
            if end == n:
                if skipped == 'ZhongYin':
                    postfix2 += '\\accent'
                elif skipped == 'BoYin':
                    postfix2 += '\\prall'
                skip = False
                end = ''
                continue
            if skip:
                skipped += n
                continue
            if n == '(':
                postfix = '('
                continue
            if n == ')':
                note.postfix = ')'
                continue
            if n == '{':
                skip = True
                end = '}'
            if n.isdigit():
                if note:
                    ret_value.append(note)
                note = Note()
                note.note = self.number_to_note(n, offset)
                note.postfix = postfix
                note.postfix2 = postfix2
                postfix = ''
                postfix2 = ''
            if n == '\'':
                if len(note.note) == 0:
                    raise IllegalNoteException()
                note.note += '\''
            if n == '_':
                note.duration *= 2
            if n == '-':
                if note.duration == 4:
                    note.duration = 2
                elif note.duration == 2 and not note.point:
                    note.point = True
                elif note.duration == 2 and note.point:
                    note.point = False
                    note.duration = 1
                else:
                    raise IllegalNoteException()
            if n == '.':
                note.point = True
        if note:
            ret_value.append(note)
        return ret_value

    def parse_bars(self, token):
        if token == "|":
            return "|"
        elif token == '|]':
            if self.alternative_opened:
                self.alternative_opened = False
                return '} } \\bar "|."'
        elif token == ':|':
            return '\\bar ":|."'
        elif token.startswith('|[1.'):
            self.alternative_opened = True
            self.repeat += 1
            return '} \\alternative { {'
        elif token.startswith('||['):
            self.alternative_opened = True
            self.repeat += 1
            return '| } {'
        return '|'

    def parse_tempo(self, token):
        return '\\time ' + token

    def parse_voice(self):
        for line in self.voice:
            for token in line.split(" "):
                token = token.strip()
                # Skip empty token
                if len(token) == 0:
                    continue
                # Skip $(...)
                if token[0] == '$':
                    continue
                # Skip ( )
                if token == '(' or token == ')':
                    continue
                # Bars
                if token.find('|') != -1 or token == '[|]' != -1:
                    n = Note()
                    n.special = self.parse_bars(token)
                    self.notes.append(n)
                    continue

                # Tempo
                if token.find('/') != -1:
                    n = Note()
                    n.special = self.parse_tempo(token)
                    self.notes.append(n)
                    continue

                # Parse Note
                for n in self.parse_token(token):
                    self.notes.append(n)

    def parse_note(self, note):
        ret = note[-1].lower()
        if note[0] == '#':
            ret = ret + 'es'
        elif note[0] == 'b':
            ret = ret + 'is'
        return ret

    def to_lilypond(self):
        line = []
        line.append('\\version "2.18.2"')
        line.append('\\header {')
        if self.song_title:
            line.append('    title = "%s"' % self.song_title)
        line.append('}')
        #line.append('\\absolute ')
        line.append('{')
        line.append('\\clef "treble"')
        if self.sig:
            line.append('\\time ' + self.sig)
        if self.repeat > 0:
            line.append('\\repeat volta %d { ' % self.repeat)
        if self.key:
            kv = self.key.split("=")
            if len(kv) == 2:
                if kv[0] == '1':
                    line.append('\\key %s \\major' % self.parse_note(kv[1]))
                elif kv[0] == '6':
                    line.append('\\key %s \\minor' % self.parse_note(kv[1]))
            else:
                line.append('\\key c \\major')
        line.append(" ".join(str(n) for n in self.notes))
        line.append('}')
        return u"\n".join(line)

    def parse_key_and_meters(self):
        for t in self.title:
            kv = t.split("=", 1)
            if kv[0].strip().lower() == "keyandmeters":
                m = re.match("\{([1,6]=[A-G]),([0-9/]*)\}", kv[1].strip())
                if m:
                    self.key = m.group(1)
                    self.sig = m.group(2)
            elif kv[0].strip().lower() == "title":
                m = re.match("(\{)*([^}]*)(\})*", kv[1].strip())
                if m:
                    self.song_title = m.group(2)

def convert(from_file, to_file):
    input = JpwFile()
    input.parse(from_file)
    input.parse_key_and_meters()
    input.parse_voice()
    output = io.open(to_file, "w", encoding='utf-8')
    output.write(input.to_lilypond())

if __name__ == '__main__':
    usage = "usage: %prog [options] args"
    parser = OptionParser(usage=usage)
    parser.add_option("-f", "--from", action="store", type="string", dest="from_file",
                      help="input file name")
    parser.add_option("-t", "--to", action="store", type="string", dest="to_file",
                      help="output file name")
    (options, args) = parser.parse_args()
    if not options.from_file or not options.to_file:
        parser.print_help()
        parser.error('Arguments must be provided')
        exit(1)

    convert(options.from_file, options.to_file)