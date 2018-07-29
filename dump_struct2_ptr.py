# #!/usr/bin/env python3
# coding: utf-8

romname = 'aka10_base.gbc'
outname = 'struct2_info.txt'
banksize = 0x4000

def getByte(rom, offset):
    offset &= 0x3FFF
    return rom[0x13][offset]

with open(romname, 'rb') as f:
    bank = 0
    rom = {}
    data = f.read(banksize)
    while (data):
        rom[bank] = data
        bank += 1
        data = f.read(banksize)

with open(outname, 'w') as f:
    for entry in range(0,0x12):
        ptr = getByte(rom, 0x6535 + entry * 2 + 1)
        ptr <<= 8
        ptr |= getByte(rom, 0x6535 + entry * 2)
        
        print('Processing entry {0:02X} table 13:{1:04X}'.format(entry, ptr))
        
        for s in range(0, 256): # some limit
            print('        Processing struct {0:02X} at 13:{1:04X}'.format(s, ptr))
            this_ptr = ptr & 0x3FFF
            struct = rom[0x13][this_ptr:this_ptr + 3]
            print('            {0:s}'.format(' '.join(['{0:02X}'.format(b) for b in struct])))
            if (struct[0] == 0xFF):
                break
            f.write('ptrtbl 13 13:{0:04X} 13:{1:04X}\n'.format(ptr + 1, ptr + 3))
            ptr += 3
 