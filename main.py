#! /usr/bin/env python2.7
from optparse import OptionParser
import re

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



def convert(fromFile, toFile):
    input = open(fromFile).read()
    output = open(toFile, "w")


    lines = input.splitlines()

    # Find title and meta
    title = getBody(lines, ".Title")
    for t in title.splitlines():
        if t.startswith("T:"):
            title = t.split(",")[0].split(":")[1]
            output.write("title=%s\n" % title)
            m = re.match(".*,.*,.*\{([1,6]=[A-G]), ([0-9/]*)\}", t)
            if m:
                key = m.group(1)
                sig = m.group(2)
                output.write(key + "\n")
                output.write(sig + "\n")
            break

    # Find Voice
    voice = getBody(lines, ".Voice")

    note = ''
    dur = 4
    point = False
    skip = False
    tie = False
    for c in voice:
        if c == '{':
            skip = True
            continue
        elif c == '}':
            skip = False
            continue
        if skip:
            continue
        if c.isdigit():
            if note != '':
                output.write(genResult(note, dur, point, tie))
                dur = 4
                point = False
                tie = False
            note = c
        elif c == ',':
            note = note + ","
        elif c == '\'':
            note = note + "'"
        elif c == '_':
            dur = dur * 2
        elif c == '-':
            dur = dur / 2
        elif c == '.':
            point = True
        elif c == '(':
            tie = True
        elif c == ')':
            if note != '':
                output.write(genResult(note, dur, point, tie))
                dur = 4
                point = False
                note = ''
                tie = False
            output.write(c + " ")
        else:
            if note != '':
                output.write(genResult(note, dur, point, tie))
                dur = 4
                point = False
                note = ''
                tie = False
    output.close()

if __name__ == '__main__':
    usage = "usage: %prog [options] args"
    parser = OptionParser(usage=usage)
    parser.add_option("-f", "--from", action="store", type="string", dest="fromFile",
                      help="input file name")
    parser.add_option("-t", "--to", action="store", type="string", dest="toFile",
                      help="output file name")
    (options, args) = parser.parse_args()
    if not options.fromFile or not options.toFile:
        parser.print_help()
        parser.error('Arguments must be provided')
        exit(1)

    convert(options.fromFile, options.toFile)