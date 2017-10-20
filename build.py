#!/usr/bin/env python

"""
Copyright (C) 2017 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, stat, struct, sys
import Image

from compressors.distance_pair import compress
from palette import get_entries, black, red, green, yellow, blue, magenta, \
                    cyan, white

version = "0.1"

def system(command):

    if os.system(command):
        sys.exit(1)

palette = {"\x00\x00\x00": 0,
           "\xff\x00\x00": 1,
           "\xff\xff\x00": 2,
           "\x00\x80\x00": 3,
           "\xff\xff\xff": 3}

def read_png(path):

    im = Image.open(path).convert("RGB")
    s = im.tostring()
    
    data = []
    a = 0
    
    i = 0
    while i < im.size[1]:
    
        line = []
        
        j = 0
        while j < im.size[0]:
        
            line.append(palette[s[a:a+3]])
            a += 3
            j += 1
        
        i += 1
        data.append(line)
    
    return data

def read_sprite(lines):

    data = ""
    
    # Read 8 rows at a time.
    for row in range(0, len(lines), 8):
    
        width = len(lines[0])
        
        # Read 4 columns at a time.
        for column in range(0, width, 4):
        
            # Read the rows.
            for line in lines[row:row + 8]:
            
                shift = 3
                byte = 0
                for pixel in line[column:column + 4]:
                
                    if pixel == 1:
                        byte = byte | (0x01 << shift)
                    elif pixel == 2:
                        byte = byte | (0x10 << shift)
                    elif pixel == 3:
                        byte = byte | (0x11 << shift)
                    
                    shift -= 1
                
                data += chr(byte)
    
    return data

rainbow_colours = [red, yellow, green, cyan, blue, magenta]

def rainbow(i, colours, s):

    # Each physical colour is used in two adjacent rows.
    c1 = colours[(i/s) % len(colours)]
    c2 = colours[(((i+1)/s) + 1) % len(colours)]
    return [black, c1, c2, white]

def format_data(data):

    s = ""
    i = 0
    while i < len(data):
        s += ".byte " + ",".join(map(lambda c: "$%02x" % ord(c), data[i:i+24])) + "\n"
        i += 24
    
    return s

def title_palette(full = True):

    # Special title palette processing
    
    fe08_data = []
    fe09_data = []
    
    blank = get_entries(4, [black, black, black, black])
    standard = get_entries(4, [black, red, yellow, green])
    
    s1, s2 = 4, 34
    
    for i in range(256):
    
        if i >= 128 + s1 and i < 128 + s2:
            fe08, fe09 = get_entries(4, rainbow(i, rainbow_colours, 3))
        else:
            fe08, fe09 = standard
        
        fe08_data.append(fe08)
        fe09_data.append(fe09)
    
    return fe08_data, fe09_data


if __name__ == "__main__":

    if len(sys.argv) != 1:
    
        sys.stderr.write("Usage: %s\n" % sys.argv[0])
        sys.exit(1)
    
    # Memory map
    code_start = 0x0e00
    
    files = []
    
    # Special title image and code processing
    
    # Convert the PNG to screen data and compress it with the palette data.
    title_sprite = read_sprite(read_png("images/title.png"))
    fe08_data, fe09_data = title_palette(full = True)
    data_list = "".join(map(chr, compress(fe08_data + fe09_data + map(ord, title_sprite))))
    
    # Read the code and append the formatted title data to it.
    code_temp = open("asm/code.oph").read()
    code_temp += "\n" + "title_data:\n" + format_data(data_list)
    
    # Write "temporary" files containing the code and compressed title data.
    # The title.oph file will include the decompression code.
    # This file can be included in a UEF2ROM project that provides its own
    # decompression code, or the dp_decode.oph sources can be appended to it.
    open("asm/code-temp.oph", "w").write(code_temp)
    
    # Assemble the files.
    assemble = [("asm/title.oph", "title.rom")]
    
    code_data = {}
    
    for name, output in assemble:
        if name.endswith(".oph"):
            system("ophis " + name + " -o " + output)
            code = open(output).read()
        elif name.endswith(".dat"):
            code = open(name).read()
        elif name.endswith(".png"):
            code = read_sprite(read_png(name))
        else:
            code = open(name).read().replace("\n", "\r")
        
        code_data[output] = code
    
    # Create a full title ROM.
    title = open("title.rom").read()
    padding = 16384 - len(title)
    if padding > 0:
        title += "\x00" * padding
    
    open("title.rom", "w").write(title)
    
    # General ROM processing
    
    for src, obj in assemble:
        if not obj.endswith(".rom"):
            files.append((obj, code_start, code_start, code_data[obj]))
    
    # Remove the executable files.
    keep = []
    
    for name, output in assemble:
        if name.endswith(".oph") and os.path.exists(output):
            if not output.endswith(".rom") and output not in keep:
                os.remove(output)
    
    remove = ["asm/code-temp.oph"]
    
    for name in remove:
        os.remove(name)
    
    # Exit
    sys.exit()
