Multi-ROM menu for the Acorn Electron
=====================================

This repository contains code to display a title and menu for the Multi-ROM
cartridge for the Acorn Electron.


Building the menu
-----------------

The source code is provided in the form of 6502 assembly language suitable for
the Ophis 6502 assembler. Code is assembled to a ROM image that can be
flashed to an EEPROM or flash ROM.

The build script requires both Python and the Ophis 6502 assembler to be
installed. Enter the directory containing the `build.py` script and run it:

  ./build.py

If successful, the `title.rom` file should be created, and this can be used as
outlined above.

You will also need to flash the ROM images for the games shown in the
`images/title.png` picture and described in the `asm/menu-data.oph` file to
the appropriate pages of the ROM.


Running the menu
----------------

By default the menu will load when the Electron boots up. However, you can
run the menu from BASIC with the following command:

  *MULTIROM

Typing the command

  *HELP MULTIROM

will show a minimal help message.


License
-------

The source code is licensed under the GNU General Public License version 3 or
later. See the COPYING file for more information about this license. A short
version of the license is given below:

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
