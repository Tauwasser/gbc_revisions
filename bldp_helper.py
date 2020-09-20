# #!/usr/bin/env python3
# coding: utf-8

import argparse
import logging
import sys

class MultiLineFormatter(logging.Formatter):
    def format(self, record):
        str = logging.Formatter.format(self, record)
        header, footer = str.split(record.message)
        str = str.replace('\n', '\n' + ' '*len(header))
        return str

banksize = 0x4000

def setMultiLineFormatterLogging():
    # Set up Logger
    l = logging.getLogger()
    h = logging.StreamHandler()
    h.setFormatter(MultiLineFormatter(fmt='[%(asctime)s][%(levelname)-8s] %(message)s', datefmt='%d %b %Y %H:%M:%S'))
    l.addHandler(h)
    return l

def cacheRomBanks(romfile, banks):
    
    cached_banks = {}
    
    with open(romfile, 'rb') as f:
        # cache banks
        for bank in banks:
            
            # seek to correct offset
            f.seek(bank * banksize, 0)
            
            cached_banks[bank] = f.read(banksize)
            
            if (len(cached_banks[bank]) < banksize):
                logging.fatal(f'Bank 0x{bank:02X} could not be fully read.')
                return -2
    
    return cached_banks

def searchFarCalls(banks):

    for bank, data in banks.items():
        
        offset = 0
        
        while (offset < banksize):
            
            # find RST $8
            if (data[offset] == 0xCF):
                offset += 1
                count = 0
                firstPtr = None
                start = offset
                # read pointers
                while (offset < banksize - 2):
                    l, h, b = data[offset], data[offset + 1], data[offset + 2]
                    offset += 3
                    # make sure it's a pointer
                    if ((b == 0x00 and h >= 0x40) or (b != 0x00 and not (0x40 <= h < 0x80))):
                        break
                    firstPtr = firstPtr or (b * banksize + ((h << 8) | l) & 0x3FFF)
                    count += 1
                    # stop when encountering address of first entry anyway
                    if (offset >= firstPtr & 0x3FFF):
                        break
                
                if (count):
                    base = 0x4000 if (bank) else 0x0000
                    start += base
                    end = start + 3*count
                    print(f'ptrtbl lhb {bank:02X} {bank:02X}:{start:04X} {bank:02X}:{end:04X}')
                
                continue
            
            offset += 1

def parseGfxStructs(banks):
    
    data = banks[1]
    
    # 2byte ptr table at 4AEE until 4C00
    start = 0x4AEE
    end = 0x4C00
    
    ptrs = [((data[o+1] << 8) | data[o+0]) for o in range(start & 0x3FFF, end & 0x3FFF, 2)]
    # if bit 7 of second byte is set, it's actually a reference to another entry (stored in low byte)
    ptrs = list(filter(lambda ptr: ptr < 0x8000, ptrs))
    
    for ptr in ptrs:
        
        offset = ptr & 0x3FFF
        
        # if first byte <> 0xFF: structure [WRAM bank][VRAM bank][control]...
        # then depending on control:
        # 76543210
        # |||||||\- decompress gfx/RNC file relative/absolute
        # ||||||\-- unused
        # |||||\--- call 1:6EB0 before restarting (palette calculation)
        # ||||\---- decompress gfx/RNC file
        # |||\----- copy two bytes from 1:hl to de
        # ||\------ unused
        # |\------- unused
        # \-------- unused
        # payload: [e][d][l][h] --> copy from 9:hl to de
        while (data[offset] != 0xFF):
            # WRAM VRAM Control
            control = data[offset+2]
            offset += 3
            ptr += 3
            # skip payload
            offset += 4
            ptr += 4
        
        # if first byte 0xFF: structure 0xFF l h b
        # --> output offset+1:offset+4 as ptrtbl lhb
        # up to 0x20 bytes follow this command as a variable payload for function b:hl,
        # which is called with a pointer to the (copied) payload in hl
        if (data[offset] == 0xFF):
            bank = 0x01
            start = ptr + 1
            end = ptr + 4
            print(f'ptrtbl lhb {bank:02X} {bank:02X}:{start:04X} {bank:02X}:{end:04X}')

def main():

    logLevelMap = {
        'debug':   logging.DEBUG,
        'info':    logging.INFO,
        'warning': logging.WARNING,
        'error':   logging.ERROR,
        }
    
    l = setMultiLineFormatterLogging()
    l.setLevel(logging.INFO)
    
    parser = argparse.ArgumentParser(description='Find BLDP-style 3-byte pointer tables in ROM banks',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--loglevel', help='Loglevel, one of \'DEBUG\', \'INFO\' (default), \'WARNING\', \'ERROR\'.', type=str, default='INFO')
    parser.add_argument('romfile', help='path to ROM file')
    subparsers = parser.add_subparsers(dest='sub_command', help='sub-command')
    
    parser_far_call = subparsers.add_parser('far-call', help='Search rst $8 far-calls in ROM banks')
    parser_far_call.add_argument('bank', type=int, nargs='+', help='ROM banks to process')
    
    parser_gfx_struct = subparsers.add_parser('gfx-struct', help='Process GFX structs in RB 0x01')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set User Loglevel
    logLevel = logLevelMap.get(args.loglevel.lower(), None)
    if (logLevel is None):
        logging.error('Invalid loglevel \'{0:s}\' passed. Exiting...'.format(args.loglevel))
        return -1
    l.setLevel(logLevel)
    
    romfile = args.romfile
    
    banks = []
    if (args.sub_command == 'far-call'):
        banks = args.bank
    elif (args.sub_command == 'gfx-struct'):
        banks = [1]
    
    banks = cacheRomBanks(romfile, banks)
    
    if (args.sub_command == 'far-call'):
        searchFarCalls(banks)
    elif (args.sub_command == 'gfx-struct'):
        parseGfxStructs(banks)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())