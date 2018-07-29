# #!/usr/bin/env python3
# coding: utf-8

import csv
import sys
from re import compile
import logging

csvname = 'Compare.csv'

def parseHex(val):
    val = val[:-1] # cut off h
    if (val is not ''):
        return int(val, 16)
    return -1

with open(csvname, 'r', newline='') as f:
    csvr = csv.reader(f, dialect='excel')
    rows = []
    for ix, row in enumerate(csvr):
        if (0 == ix or not row):
            # skip first
            rows.append(row)
            continue
        if (not row):
            # skip empty
            continue
        addressA = parseHex(row[1])
        sizeA    = parseHex(row[2])
        addressB = parseHex(row[3])
        sizeB    = parseHex(row[4])
        if (sizeA != sizeB):
            logging.fatal('Unequal match lengths!')
            raise RuntimeError('Unequal match lengths!')
        if (sizeA <= 2 and sizeB <= 2):
            rows.append(row)
            continue
        while(sizeA > 0):
            new_row = []
            new_row.append(row[0])
            new_row.append('{0:X}h'.format(addressA))
            new_row.append('{0:X}h'.format(2 if sizeA >= 2 else 1))
            new_row.append('{0:X}h'.format(addressB))
            new_row.append('{0:X}h'.format(2 if sizeB >= 2 else 1))
            sizeA -= 2
            sizeB -= 2
            addressA += 2
            addressB += 2
            rows.append(new_row)

with open(csvname, 'w', newline='') as f:
    csvw = csv.writer(f, dialect='excel')
    for r in rows:
        csvw.writerow(r)