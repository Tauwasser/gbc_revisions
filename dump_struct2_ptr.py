# #!/usr/bin/env python3
# coding: utf-8


import argparse
import sys

banksize = 0x4000

def getBytes(rom, bank, offset, len):
    offset &= 0x3FFF
    return rom[bank][offset:offset+len]

def getByte(rom, bank, offset):
    offset &= 0x3FFF
    return rom[bank][offset]

def getPtr(rom, bank, offset):
    val = getByte(rom, bank, offset + 1)
    val <<= 8
    val |= getByte(rom, bank, offset)
    return val

address_map = {
    'aka10' : {'entries': 0x12, 'bank': 0x13, 'ptr': 0x6535},
    'aka11' : {'entries': 0x12, 'bank': 0x13, 'ptr': 0x654A},
    'kuro10': {'entries': 0x12, 'bank': 0x13, 'ptr': 0x6535},
    'kuro11': {'entries': 0x12, 'bank': 0x13, 'ptr': 0x654A},
    }

def main():

    ap = argparse.ArgumentParser(description='Dump RB 0x13 struct type 2',
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('romtype', help='ROM type: aka10, aka11, kuro10, kuro11')
    ap.add_argument('romfile', help='path to ROM')
    ap.add_argument('outfile', nargs='?', default='struct2_info.txt', help='path to output info file')

    args = ap.parse_args()
    romtype = args.romtype
    romname = args.romfile
    outname = args.outfile

    if (romtype not in address_map):
        return -1
    
    with open(romname, 'rb') as f:
        bank = 0
        rom = {}
        data = f.read(banksize)
        while (data):
            rom[bank] = data
            bank += 1
            data = f.read(banksize)

    num_entries = address_map[romtype]['entries']
    bank        = address_map[romtype]['bank']
    address     = address_map[romtype]['ptr']
    
    with open(outname, 'w') as f:
        for entry in range(0, num_entries):
            ptr = getPtr(rom, bank, address + entry * 2)
            
            print('Processing entry {0:02X} table 13:{1:04X}'.format(entry, ptr))
            
            for s in range(0, 256): # some limit
                print('        Processing struct {0:02X} at 13:{1:04X}'.format(s, ptr))
                struct = getBytes(rom, bank, ptr, 3)
                print('            {0:s}'.format(' '.join(['{0:02X}'.format(b) for b in struct])))
                if (struct[0] == 0xFF):
                    break
                f.write('ptrtbl 13 13:{0:04X} 13:{1:04X}\n'.format(ptr + 1, ptr + 3))
                ptr += 3
     
    return 0

if __name__ == '__main__':
    sys.exit(main())