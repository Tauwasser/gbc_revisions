This repository contains a few Python 3 scripts to analyze the 
differences between *Shin Megami Tensei: Aka no Sho* and
*Shin Megami Tensei: Kuro no Sho* revisions v1.0 and v1.1.

## Workflow

I used [010 Editor](https://www.sweetscape.com/010editor/)'s
binary compare feature to get a re-synchronized comparison.

This comparison was then exported as CSV to *aka_compare.csv*.
From there, I wrote a script that parsed this CSV file and began
tracking shifted data and code in the *Aka no Sho* ROM.
There are some 4049 differences between Aka no Sho v1.0 and Aka
no Sho v1.1, so I had to trim them down.

To do that, I defined a few rules to filter the resultant diffs:

- track address shifts in calls
- track address shifts in load/store operations (direct and indirect via 16-bit register)
- track address shifts in pointer tables
- track address shifts in far calls (which are specific to Devil Children games and use rst $0)

This trimmed the diff down significantly. After that, I defined
a CSV file *aka_ramshift.csv*
to track shifted WRAM addresses as well.

Then I introduced *aka10_info.txt*, which supplies the main script
with additional information regarding pointer tables and code locations.
For pointer tables, I would regularly have to redump them using
010 Editor's simple comparison mode and then split the exported CSV file,
because it would merge adjacent diffs into longer runs than the main
script can handle.

It turns out, rom bank 0x13 contains some structures with
internal pointers that aren't easily tracked by hand.
For that purpose, I wrote two additional scripts to parsed
the structures and emit pointer table entries for the info text file.

After that, only 12 siginificant changes plus insertions/deletions
remained.

## Main script diff_trim.py

*diff_trim.py* is the main script. It reads all the CSV and info
files as well as v1.0 and v1.1 ROMs.

## Helper script diff_split.py

*diff_split.py* is the helper script that splits exported simple CSV
differences into runs of 1 or 2 byte differences so the main script can
track pointer table changes properly.

## Helper scripts dump_struct{,2}_ptr.py

*dump_struct_ptr.py* and *dump_struct2_ptr.py* dump locations for
pointers internal to the structures in rom bank 0x13 in info text format.

I'm not exactly sure what the structs actually contain at this point.
