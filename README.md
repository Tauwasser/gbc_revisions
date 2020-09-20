[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)

This repository contains a few Python 3 scripts to analyze 
differences between Game Boy™ game revisions.

Currently supported:
- **Shin Megami Tensei: Aka no Sho**: Rev 1.0 and Rev 1.1
- **Shin Megami Tensei: Kuro no Sho**: Rev 1.0 and Rev 1.1
- **Mr. Driller (Japan)**: BMDJ Rev 1.0 and BV3J Rev 1.0
- **Laura (Europe)**: BLDP Rev 1.0 and Nintendo Gigaleak

## Results

Results can be found in the *<game>_results* folders:
- **Shin Megami Tensei: Aka no Sho**: 4049 differences trimmed to 12 principal changes
- **Shin Megami Tensei: Kuro no Sho**: 4083 differences trimmed to 12 principal changes (which match Aka)
- **Mr. Driller (Japan)**: 930 differences trimmed to 10
- **Laura (Europe)**: 1011 differences trimmed to 7

## Workflow

I use [010 Editor](https://www.sweetscape.com/010editor/)'s
binary compare feature to get a re-synchronized comparison.

Then I export this comparison as CSV to *<game>_compare.csv*.
Create empty *<game>_ramshift.csv* with the same header as the exported CSV.
Create empty *<game><version>_info.txt*.

From there, the main script will parse this CSV file and discard
differences that are solely due to insertions/deletions of code
that shift subsequent addresses.

To do that, I defined a few rules to filter the resultant diffs:

- track address shifts in calls
- track address shifts in load/store operations (direct and indirect via 16-bit register and shorthand 0xFF00 + N)
- track address shifts in pointer tables
- track address shifts in far calls (which are specific to Devil Children games and use rst $0)

This should trim the diff down significantly. After that, enter
shifted WRAM and HRAM addresses in *<game>_ramshift.csv*.
This file also supports remapped addresses, i.e. addresses that map from
source to destination and don't necessarily obey address shifts.

*<game><version>_info.txt* supplies the main script
with additional information regarding pointer tables and code locations.
For pointer tables, I would regularly have to redump them using
010 Editor's simple comparison mode and then split the exported CSV file,
because it would merge adjacent diffs into longer runs than the main
script can handle.

For the Devil Children games it turned out that rom bank 0x13 contained
some structures with internal pointers that aren't easily tracked by hand.
For that purpose, I wrote two additional scripts to parse
the structures and emit pointer table entries for the info text file.

## Main script diff_trim.py

*diff_trim.py* is the main script. It reads all the CSV and info
files as well as source and destination ROMs.

## Helper script diff_split.py

*diff_split.py* is the helper script that splits exported simple CSV
differences into runs of 1 or 2 byte differences so the main script can
track pointer table changes properly.

## Helper scripts dds_dump_struct{,2}_ptr.py

*dds_dump_struct_ptr.py* and *dds_dump_struct2_ptr.py* dump locations for
pointers internal to the structures in rom bank 0x13 in info text format.

I'm not exactly sure what the structs actually contain at this point.

## Legalese

I'm not affiliated with Nintendo in any way.

Game Boy™ and Game Boy Color™ are trademarks of Nintendo. Nintendo® is a registered trademark.
All other trademarks are property of their respective owner.
