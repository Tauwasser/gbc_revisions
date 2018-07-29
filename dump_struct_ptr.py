# #!/usr/bin/env python3
# coding: utf-8

romname = 'aka10_base.gbc'
outname = 'struct_info.txt'
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
    for entry in range(0,9):
        ptr = getByte(rom, 0x41AF + entry * 2 + 1)
        ptr <<= 8
        ptr |= getByte(rom, 0x41AF + entry * 2)
        
        print('Processing entry {0:02X} table 13:{1:04X}'.format(entry, ptr))
        elem0 = getByte(rom, ptr + 1)
        elem0 <<= 8
        elem0 |= getByte(rom, ptr)
        
        num_elems = (elem0 - ptr) // 2
        print('    Elements: {0:02X}'.format(num_elems))
        f.write('ptrtbl 13 13:{0:04X} 13:{1:04X}\n'.format(ptr, elem0))
        
        for e in range(0, num_elems):
            elem = getByte(rom, ptr + e * 2 + 1)
            elem <<= 8
            elem |= getByte(rom, ptr + e * 2)
            
            num_structs = getByte(rom, elem)
            
            print('    Processing element {0:02X} with {1:02X} structs at 13:{2:04X}'.format(e, num_structs, elem))
            elem += 1
            
            for s in range(0, num_structs):
            
                print('        Processing struct {0:02X} at 13:{1:04X}'.format(s, elem))
                this_elem = elem & 0x3FFF
                struct = rom[0x13][this_elem:this_elem + 6]
                print('            {0:s}'.format(' '.join(['{0:02X}'.format(b) for b in struct])))
                if (struct[2] == 0xFF):
                    f.write('ptrtbl 13 13:{0:04X} 13:{1:04X}\n'.format(elem + 3, elem + 5))
                elem += 6
