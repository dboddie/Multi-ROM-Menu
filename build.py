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

standard_colours = {
    "black": (0, 0, 0), "red": (255, 0, 0), "green": (0, 255, 0),
    "yellow": (255, 255, 0), "blue": (0, 0, 255), "magenta": (255, 0, 255),
    "cyan": (0, 255, 255), "white": (255, 255, 255)
    }

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

def title_palette(spans, default, full = True):

    # Special title palette processing
    
    fe08_data = []
    fe09_data = []
    
    blank = get_entries(4, [black, black, black, black])
    
    for i in range(256):
    
        for (s1, s2), fn in spans:
        
            if i >= s1 and i < s2:
                fe08, fe09 = fn(i)
                break
        else:
            # The last item in the list should be the fallback.
            fe08, fe09 = default(i)
        
        fe08_data.append(fe08)
        fe09_data.append(fe09)
    
    return fe08_data, fe09_data


def read_menu_cfg(file_name):

    lines = open(file_name).readlines()
    
    # Discard the headings.
    lines.pop(0)
    
    info = []
    
    i = 0
    while i < len(lines):
    
        line = lines[i]
        i += 1
        
        l = line.strip()
        if not l:
            break
        
        pieces = l.split()
        page = int(pieces[0])
        command = pieces[1]
        files = pieces[2:]
        info.append((page, command, files))
    
    # Read the spans.
    i += 1
    spans = []
    
    while i < len(lines):
    
        line = lines[i]
        i += 1
        
        l = line.strip()
        if not l:
            break
        
        pieces = l.split()
        begin = int(pieces[0])
        end = int(pieces[1])
        
        if pieces[2] == "rainbow":
            spans.append(((begin, end), lambda i: get_entries(4, rainbow(i, rainbow_colours, 3))))
        
        elif len(pieces) == 6:
            colours = []
            for c in pieces[2:]:
                colours.append(standard_colours[c])
            
            spans.append(((begin, end), lambda i: get_entries(4, colours)))
        
        else:
            sys.stderr.write("Invalid palette description '%s' in %s.\n" % (l, file_name))
            sys.exit(1)
    
    return info, spans


def generate_menu(info):

    s = ""
    
    key_codes = [0x30, 0x31, 0x11, 0x12, 0x13, 0x34, 0x24, 0x15, 0x26]
    
    s += "key_codes:\n"
    s += ".byte " + ",".join(map(lambda x: "$%x" % x, key_codes[:len(info)]))
    s += "\nkey_codes_end:\n\n"

    s += "bank_numbers:   ; These specify the banks occupied by the menu choices:\n"
    
    for page, command, files in info:
        s += ".byte %i\n" % page
    
    s += "\nboot_command_text:\n\n"
    
    i = 1
    
    for page, command, files in info:
    
        s += "game%i:\n" % i
        
        if command != "-":
            if page == 0:
                s += '.byte "%s", 13\n' % command
            else:
                s += '.byte "KEY 10 *%s|M", 13\n' % command
        else:
            s += '.byte 0\n'
        
        i += 1
    
    s += "\ncommand_names:\n"
    
    for i in range(len(info)):
        s += ".byte [game%i - boot_command_text]\n" % (i + 1)
    
    return s

def show_rom_order(info):

    low = [None] * 4
    low[0] = "title.rom"
    high = [None] * 4
    
    for page, command, files in info:
    
        if len(files) == 2:
            low[page] = files[0]
            high[page] = files[1]
        elif page != 0:
            low[page] = high[page] = files[0]
        else:
            high[page] = files[0]
    
    low = map(str, low)
    high = map(str, high)
    
    print
    print "# To make separate ROM sets for Elkulator:"
    print "cat " + " ".join(low) + " > roms1"
    print "cat " + " ".join(high) + " > roms2"
    print
    print "# ROM order for flashing:"
    i = 0
    for r1, r2 in zip(low, high):
        print "%x %s" % (i, r1)
        print "%x %s" % (i + 0x4000, r2)
        i += 0x8000
    print


if __name__ == "__main__":

    if len(sys.argv) != 3:
    
        sys.stderr.write("Usage: %s <menu configuration file> <title image>\n" % sys.argv[0])
        sys.exit(1)
    
    menu_cfg_file = sys.argv[1]
    title_image_file = sys.argv[2]
    
    # Special title image and code processing
    menu_info, spans = read_menu_cfg(menu_cfg_file)
    default = lambda i: get_entries(4, [black, red, yellow, white])
    
    # Convert the PNG to screen data and compress it with the palette data.
    title_sprite = read_sprite(read_png(title_image_file))
    fe08_data, fe09_data = title_palette(spans, default, full = True)
    data_list = "".join(map(chr, compress(fe08_data + fe09_data + map(ord, title_sprite))))
    
    # Prepend the menu data to a generated file.
    code_temp = generate_menu(menu_info)
    
    # Read the code and append the formatted title data to it.
    title_dest_end = 0x2e00 + len(title_sprite) + len(fe08_data) + len(fe09_data)
    code_temp += ".alias title_dest_end $%x\n" % title_dest_end
    code_temp += ".alias title_palette_start %i\n" % spans[0][0][0]
    code_temp += ".alias title_palette_finish %i\n\n" % spans[0][0][1]

    code_temp += open("asm/code.oph").read()
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
    
    # Remove the executable files.
    keep = []
    
    for name, output in assemble:
        if name.endswith(".oph") and os.path.exists(output):
            if not output.endswith(".rom") and output not in keep:
                os.remove(output)
    
    remove = ["asm/code-temp.oph"]
    
    for name in remove:
        os.remove(name)
    
    show_rom_order(menu_info)
    
    # Exit
    sys.exit()
