# #!/usr/bin/env python3
# coding: utf-8

import argparse
import csv
import sys
from re import compile
import logging

banksize = 0x4000

def getBank(address):
    return address // banksize
    
def getPointer(address):
    
    bank = getBank(address)
    pnt = address % banksize
    if (0 == bank):
        return pnt
    return pnt | 0x4000

def readRom(path):
    rom = {}
    with open(path, 'rb') as f:
        bank = 0
        data = f.read(banksize)
        while (data):
            rom[bank] = data
            bank += 1
            data = f.read(banksize)
    return rom
    
def parseHex(val):
    val = val[:-1] # cut off h
    if (val is not ''):
        return int(val, 16)
    return -1

def sumShifts(shifts, bank, ptr):
    
    loc_bank = bank if ptr >= 0x4000 else 0x00
    shift = 0
    for s in shifts:
        if (s['bankA'] > loc_bank) or \
           (s['bankA'] == loc_bank and s['ptrA'] > ptr):
            break
        
        shift += s['shift']

    return shift

def sumRamShifts(shifts, bank, ptr):
    
    shift = 0
    for s in shifts:
        if (s['bank'] > bank) or \
           (s['bank'] == bank and s['ptr'] > ptr):
            break

        shift += s['shift']

    return shift

def isRamSwitch(switches, ptrA, ptrB):
    
    for s in switches:
        if (ptrA == s['ptrA'] and ptrB == s['ptrB']):
            return True
    
    return False
    
def getInfo(info, bank, ptr):
    
    for i in info:
        if i['bank'] != bank:
            continue
        if i['ptr'] > ptr or i['ptr'] + i['len'] < ptr:
            continue
        return i
    
    return {'type': None}

def getByte(rom, bank, ptr, offset):
    ptr &= 0x3FFF
    if (0 > (ptr + offset)):
        logging.debug('1')
        return None
    if (0x4000 <= (ptr + offset)):
        logging.debug('2')
        return None
    return rom[bank][ptr + offset]

def getBytes(romA, romB, record, offset):
    
    return getByte(romA, record['bankA'], record['ptrA'], offset), \
           getByte(romB, record['bankB'], record['ptrB'], offset)

def main():

    ap = argparse.ArgumentParser(description='Filter out bogus diffs from revision comparisons by tracking address shifts',
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--debug', dest='debug', default=False, help='print debug output', action='store_true')
    ap.add_argument('romtype', help='ROM type: aka, kuro')
    ap.add_argument('versionA', help='ROM A version string')
    ap.add_argument('versionB', help='ROM B version string')
    ap.add_argument('outfile', nargs='?', help='path to trimmed output diff file')

    args = ap.parse_args()
    debug = args.debug
    romtype = args.romtype
    outname = args.outfile
    versionA = args.versionA
    versionB = args.versionB
    
    if outname is None:
        outname = '{0:s}{2:s}v{3:s}_trimmed{1:s}.log'.format(romtype, '-debug' if debug else '', versionA, versionB)
    
    romnameA = '{0:s}{1:s}.gbc'.format(romtype, versionA)
    romnameB = '{0:s}{1:s}.gbc'.format(romtype, versionB)
    csvname = '{0:s}_compare.csv'.format(romtype)
    infoname = '{0:s}{1:s}_info.txt'.format(romtype, versionA)
    ramshiftname = '{0:s}_ramshift.csv'.format(romtype)

    loglevel = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='[%(levelname)-8s] %(message)s', level=loglevel, filename=outname, filemode='w')

    romA = readRom(romnameA)
    romB = readRom(romnameB)

    info_regex = compile('^([a-z]+) +([0-9A-Fa-f]{2}) ([0-9A-Fa-f]{2}):([0-9A-Fa-f]{4}) ([0-9A-Fa-f]{2}):([0-9A-Fa-f]{4})$')
    info = []
    with open(infoname, 'r') as f:
        for line in f:
            m = info_regex.match(line)
            if m is None:
                continue
            type = m.group(1)
            bank = int(m.group(2), 16)
            start = int(m.group(3), 16) * banksize + (int(m.group(4), 16) & 0x3FFF)
            end = int(m.group(5), 16) * banksize + (int(m.group(6), 16) & 0x3FFF)
            info.append({
                'type':    type,
                'bank':    getBank(start),
                'ptr' :    getPointer(start),
                'refBank': bank,
                'len' :    end - start
                }
            )

    with open(csvname, 'r', newline='') as csvfile:
        csvr = csv.reader(csvfile, dialect='excel')
        records = []
        shifts  = []
        insertions = []
        deletions = []
        cur_addrA = 0
        cur_addrB = 0
        for ix, row in enumerate(csvr):
            if (0 == ix or not row):
                # skip first and empty rows
                continue
            addressA = parseHex(row[1])
            sizeA    = parseHex(row[2])
            addressB = parseHex(row[3])
            sizeB    = parseHex(row[4])
            if row[0] == 'Match':
                # ignore matches
                cur_addrA = addressA + sizeA
                cur_addrB = addressB + sizeB
                continue
            elif row[0] == 'Difference':
                records.append({
                    'bankA': getBank(addressA),
                    'ptrA' : getPointer(addressA),
                    'bankB': getBank(addressB),
                    'ptrB' : getPointer(addressB),
                    'lenA' : sizeA,
                    'lenB' : sizeB,
                    }
                )
                if (sizeA != sizeB):
                    oldAddressA = addressA + sizeA
                    newAddressB = addressB + sizeB
                    shifts.append({
                        'bankA': getBank(oldAddressA),
                        'ptrA' : getPointer(oldAddressA),
                        'bankB': getBank(newAddressB),
                        'ptrB' : getPointer(newAddressB),
                        'shift': sizeB - sizeA
                        }
                    )
                if (sizeA > sizeB):
                    # mark whole section deleted
                    deletions.append({
                        'bankA': getBank(addressA),
                        'ptrA' : getPointer(addressA),
                        'bankB': getBank(addressB),
                        'ptrB' : getPointer(addressB),
                        'len': sizeA
                        }
                    )
                if (sizeA < sizeB):
                    # mark whole section inserted
                    insertions.append({
                        'bankA': getBank(addressA),
                        'ptrA' : getPointer(addressA),
                        'bankB': getBank(addressB),
                        'ptrB' : getPointer(addressB),
                        'len': sizeB
                        }
                    )
            elif row[0] == 'Only in B':
                shifts.append({
                    'bankA': getBank(cur_addrA),
                    'ptrA' : getPointer(cur_addrA),
                    'bankB': getBank(addressB),
                    'ptrB' : getPointer(addressB),
                    'shift': sizeB
                    }
                )
                insertions.append({
                    'bankA': getBank(cur_addrA),
                    'ptrA' : getPointer(cur_addrA),
                    'bankB': getBank(addressB),
                    'ptrB' : getPointer(addressB),
                    'len': sizeB
                    }
                )
            elif row[0] == 'Only in A':
                oldAddressA = addressA + sizeA
                shifts.append({
                    'bankA': getBank(oldAddressA),
                    'ptrA' : getPointer(oldAddressA),
                    'bankB': getBank(cur_addrB),
                    'ptrB' : getPointer(cur_addrB),
                    'shift': -sizeA
                    }
                )
                deletions.append({
                    'bankA': getBank(addressA),
                    'ptrA' : getPointer(addressA),
                    'bankB': getBank(cur_addrB),
                    'ptrB' : getPointer(cur_addrB),
                    'len': sizeA
                    }
                )
            else:
                logging.warning('Unknown comparison type \'{0:s}\'!'.format(row[0]))

    with open(ramshiftname, 'r', newline='') as csvfile:
        csvr = csv.reader(csvfile, dialect='excel')
        ram_shifts  = []
        ram_deletions = []
        ram_switches = []
        cur_addr = 0
        for ix, row in enumerate(csvr):
            if (0 == ix or not row):
                # skip first and empty rows
                continue
            addressA = parseHex(row[1])
            sizeA    = parseHex(row[2])
            addressB = parseHex(row[3])
            sizeB    = parseHex(row[4])
            if row[0] == 'Match':
                # ignore matches
                cur_addr = addressA + sizeA
                continue
            elif row[0] == 'Only in B':
                ram_shifts.append({
                    'bank' : 0,
                    'ptr'  : cur_addr,
                    'shift': sizeB
                    }
                )
            elif row[0] == 'Only in A':
                oldAddressA = addressA + sizeA
                ram_shifts.append({
                    'bank' : 0,
                    'ptr'  : oldAddressA,
                    'shift': -sizeA
                    }
                )
                ram_deletions.append({
                    'addr' : addressA,
                    'len': sizeA
                    }
                )
            elif row[0] == 'Switch':
                ram_switches.append({
                    'ptrA' : addressA,
                    'lenA' : sizeA,
                    'ptrB' : addressB,
                    'lenB' : sizeB,
                    }
                )
            else:
                logging.warning('Unknown comparison type \'{0:s}\'!'.format(row[0]))

    # print shifts:
    shift = 0
    for s in shifts:
        logging.debug('Shift: {0:02X}:{1:04X} -- {2:d} --> {3:d}'.format(s['bankA'], s['ptrA'], shift, shift + s['shift']))
        shift += s['shift']

    for i in insertions:
        logging.debug('Insertion: {0:02X}:{1:04X} -- -{2:d}'.format(i['bankA'], i['ptrA'], i['len']))
        
    for d in deletions:
        logging.debug('Deletion: {0:02X}:{1:04X} -- -{2:d}'.format(d['bankA'], d['ptrA'], d['len']))

    shift = 0
    for s in ram_shifts:
        logging.debug('RAM Shift: {0:02X}:{1:04X} -- {2:d} --> {3:d}'.format(s['bank'], s['ptr'], shift, shift + s['shift']))
        shift += s['shift']

    for d in ram_deletions:
        logging.debug('RAM Deletion: {0:02X}:{1:04X} -- -{2:d}'.format(d['bank'], d['ptr'], d['len']))

    # print infos:
    for i in info:
        logging.debug('Info: {0:02X}:{1:04X} -- {2:d} bytes ref bank {3:02X}'.format(i['bank'], i['ptr'], i['len'], i['refBank']))

    records_filtered = []
    for ix, r in enumerate(records):
        
        logging.info('Checking record {0:02X}:{1:04X}...'.format(r['bankA'], r['ptrA']))
        
        pre2A, pre2B = getBytes(romA, romB, r, -2)
        preA, preB = getBytes(romA, romB, r, -1)
        curA, curB = getBytes(romA, romB, r, 0)
        nextA, nextB = getBytes(romA, romB, r, +1)
        r_info = getInfo(info, r['bankA'], r['ptrA'])
        
        logging.debug('    Infotype: {0!s}'.format(r_info['type']))
        
        # check if call 0xCD
        # check if call nc 0xD4
        # check if call c 0xDC
        # check if call nz 0xC4
        # check if call z 0xCC
        # check if jp 0xC3
        # check if jp nc 0xD2
        # check if jp c 0xDA
        # check if jp nz 0xC2
        # check if jp z 0xCA
        if ( \
            ( \
                (0xCD == preA and 0xCD == preB) or \
                (0xD4 == preA and 0xD4 == preB) or \
                (0xDC == preA and 0xDC == preB) or \
                (0xC4 == preA and 0xC4 == preB) or \
                (0xCC == preA and 0xCC == preB) or \
                (0xC3 == preA and 0xC3 == preB) or \
                (0xD2 == preA and 0xD2 == preB) or \
                (0xDA == preA and 0xDA == preB) or \
                (0xC2 == preA and 0xC2 == preB) or \
                (0xCA == preA and 0xCA == preB) \
            ) \
            and \
            (r['lenA'] <= 2 and r['lenB'] <= 2)
           ):
            if (nextA is not None and nextB is not None):
                called_addrA = (nextA << 8) | curA
                called_addrB = (nextB << 8) | curB
                logging.debug('    call: {0:04X} -- {1:04X}'.format(called_addrA, called_addrB))
                bank = r['bankA']
                if (r_info['type'] != 'code'):
                    if (0 == r['bankA'] and called_addrA >= 0x4000):
                        logging.warning('    call: out of bank call rom A.')
                        continue
                    if (0 == r['bankB'] and called_addrB >= 0x4000):
                        logging.warning('    call: out of bank call rom B but not rom A!')
                        continue
                else:
                    bank = r_info['refBank']
                shift = sumShifts(shifts, bank, called_addrA)
                logging.debug('    call: shift {0:04X}'.format(shift))
                if (called_addrA + shift == called_addrB):
                    continue
        
        # check if long call rst $0 0xC7 (DDS-specific)
        if (romtype == 'aka' or romtype == 'kuro'):
            if (0xC7 == pre2A and 0xC7 == pre2B):
                if (preA == preB and nextA is not None and nextB is not None):
                    called_addrA = (nextA << 8) | curA
                    called_addrB = (nextB << 8) | curB
                    logging.debug('    longcall: {0:02X}:{1:04X} -- {2:02X}:{3:04X}'.format(preA, called_addrA, preB, called_addrB))
                    
                    shift = sumShifts(shifts, preA, called_addrA)
                    logging.debug('    longcall: shift {0:04X}'.format(shift))
                    if (called_addrA + shift == called_addrB):
                        continue
        
        # check if ld [$NNNN], a
        # check if ld a, [$NNNN]
        # check if ld hl, $NNNN
        # check if ld de, $NNNN
        # check if ld bc, $NNNN
        if ( \
            ( \
                (0xEA == preA and 0xEA == preB) or \
                (0xFA == preA and 0xFA == preB) or \
                (0x21 == preA and 0x21 == preB) or \
                (0x11 == preA and 0x11 == preB) or \
                (0x01 == preA and 0x01 == preB) \
            ) \
            and \
            (r['lenA'] <= 2 and r['lenB'] <= 2)
           ):
            if (nextA is not None and nextB is not None):
                loaded_addrA = (nextA << 8) | curA
                loaded_addrB = (nextB << 8) | curB
                logging.debug('    loadstore: {0:04X} -- {1:04X}'.format(loaded_addrA, loaded_addrB))
                if ( \
                    (loaded_addrA < 0x8000 and loaded_addrB >= 0x8000) or \
                    (loaded_addrA < 0x8000 and loaded_addrB >= 0x8000) \
                   ):
                    logging.warning('    loadstore: rom A/B perform access to different ROM/RAM target...')
                else:
                    target = 'rom'
                    if (loaded_addrA >= 0x8000):
                        target = 'ram'
                    bank = r['bankA']
                    if (r_info['type'] != 'code' and target == 'rom'):
                        if (0 == r['bankA'] and loaded_addrA >= 0x4000):
                            logging.warning('    loadstore: out of bank access rom A.')
                            continue
                        if (0 == r['bankB'] and loaded_addrB >= 0x4000):
                            logging.warning('    loadstore: out of bank access rom B but not rom A!')
                            continue
                    elif (r_info['type'] == 'code'):
                        bank = r_info['refBank']
                    
                    if (target == 'rom'):
                        shift = sumShifts(shifts, bank, loaded_addrA)
                    else:
                        # target == 'ram'
                        shift = sumRamShifts(ram_shifts, 0, loaded_addrA)
                        if (isRamSwitch(ram_switches, loaded_addrA, loaded_addrB)):
                            continue
                    logging.debug('    loadstore: {1:s} shift {0:04X}'.format(shift, target))
                    if (loaded_addrA + shift == loaded_addrB):
                        continue
        
        # check if ld a,[$FF00 + $N]
        # check if ld [$FF00 + $N], a
        if ( \
            ( \
                (0xF0 == preA and 0xF0 == preB) or \
                (0xE0 == preA and 0xE0 == preB) \
            ) \
            and \
            (r['lenA'] <= 1 and r['lenB'] <= 1)
           ):
            if (nextA is not None and nextB is not None):
                loaded_addrA = 0xFF00 | curA
                loaded_addrB = 0xFF00 | curB
                logging.debug('    loadstore: {0:04X} -- {1:04X}'.format(loaded_addrA, loaded_addrB))
                shift = sumRamShifts(ram_shifts, 0, loaded_addrA)
                if (isRamSwitch(ram_switches, loaded_addrA, loaded_addrB)):
                    continue
                logging.debug('    loadstore: {1:s} shift {0:04X}'.format(shift, 'ram'))
                if (loaded_addrA + shift == loaded_addrB):
                    continue
        
        # check if ptr-table
        if (r_info['type'] == 'ptrtbl'):
            banks = r['bankA'] - r_info['bank']
            diff = r['ptrA'] - r_info['ptr']
            offset = banks * banksize + diff
            if ((offset & 1) == 0):
                ptrAddrA = (nextA << 8) | curA
                ptrAddrB = (nextB << 8) | curB
            else:
                ptrAddrA = (curA << 8) | preA
                ptrAddrB = (curB << 8) | preB
            logging.debug('    ptrtbl: {0:04X} -- {1:04X}'.format(ptrAddrA, ptrAddrB))
            shift = sumShifts(shifts, r_info['refBank'], ptrAddrA)
            logging.debug('    ptrtbl: shift {0:04X}'.format(shift))
            if (ptrAddrA + shift == ptrAddrB):
                continue
        
        logging.info('    Interesting...')
        records_filtered.append(r)

    logging.info('------------------------------------------------------------------------')
    logging.info('filtered/unfiltered {0:d}/{1:d}'.format(len(records_filtered), len(records)))

    # mix everything together
    # insertions, deletions, filtered records

    for e in insertions:
        e['type'] = 'Insertion'
    for e in deletions:
        e['type'] = 'Deletion'
    for e in records_filtered:
        e['type'] = 'Difference'

    all_records = insertions + deletions + records_filtered

    all_records = sorted(all_records, key=lambda entry: entry['bankA'] * banksize | (entry['ptrA'] & 0x3FFF))

    for r in all_records:
        lenA = r['len'] if 'len' in r else r['lenA']
        lenB = r['len'] if 'len' in r else r['lenB']
        logging.info('{0:12s} at A {1:02X}:{2:04X} - {3:2d} -- B: {4:02X}:{5:04X} - {6:2d}'.format(
            r['type'],
            r['bankA'],
            r['ptrA'],
            lenA,
            r['bankB'],
            r['ptrB'],
            lenB
            )
        )

    logging.info('------------------------------------------------------------------------')
    return 0

if __name__ == '__main__':
    sys.exit(main())