#!/usr/bin/env python3

#####################################################
# Skript pro převod formátu OPTIc (stará kamera, AK2) do OPTIcXNet (nová kamera)
# Autor: Michal Töpfer, AC Mladá Boleslav
#
# Skirpt pracuje přímo ve složce, ve které je spuštěn, a pro každý '*.rac' soubor (a odpovídající 'p*.txt') vytvoří
# '*.heatxml', který se dá importovat do OPTIc3Net.
# Pokud vše pracuje správně, jsou ID závodů nastavená podle ID ze závodní kanceláře.
#####################################################

import sys
from pathlib import Path
import xml.etree.ElementTree as etree
import csv
import io


def try_parse_int(s):
    try:
        return int(s)
    except ValueError:
        return 999999


def convert_wind_mode(w):
    if w == "6":
        return "5Seconds"
    if w == "5":
        return "10Seconds"
    if w == "4":
        return "13Seconds"
    if w == "3":
        return "10SecondsWith10SecondsDelay"
    return "None"


def read_rac(f):
    heat_args = {}
    with open(f, "rt") as rac:
        for line in rac:
            tokens = line.strip().split("=")
            if len(tokens) == 2:
                if tokens[0] == "CompType":
                    heat_args["Name"] = tokens[1]
                if tokens[0] == "RaceNo":
                    heat_args["Id"] = tokens[1]
                    heat_args["Nr"] = tokens[1]
                if tokens[0] == "WindMode":
                    heat_args["WindMeasurement"] = convert_wind_mode(tokens[1])
                if tokens[0] == "Distance":
                    heat_args["Distance"] = ''.join(c for c in tokens[1] if c.isdigit())
    return heat_args


def read_competitors(f):
    filename = "p" + f.stem + ".txt"
    with open(f.parent / filename) as p_file:
        reader = csv.reader(p_file, delimiter='\t', dialect=csv.excel)
        for row in reader:
            yield {
                "Bib": row[1],
                "Lane": row[2],
                "Firstname": row[3],
                "Lastname": row[4],
                "Club": row[5],
            }


def process_heat(f):
    heat_args = read_rac(f)
    heat = etree.Element("Heat", attrib=heat_args)
    for c_attr in read_competitors(f):
        etree.SubElement(heat, "Competitor", c_attr)
    filename = f.stem + ".heatxml"
    with io.open(f.parent / filename, "w", encoding='utf8') as out_file:
        out_file.write(etree.tostring(heat, encoding="unicode"))
    print(f"#{f.stem} úspěšně zpracováno ({heat_args.get('Name', '')})")


path = Path(".")
if len(sys.argv) == 2:
    path = Path("./" + sys.argv[1])

files = path.glob("*.rac")
files = sorted(files, key=lambda x: try_parse_int(x.stem))

for f in files:
    try:
        process_heat(f)
    except Exception as e:
        print(f"CHYBA při zpracování souboru '{f}'.")
        print(" ", e)

print()
input("Stiskněte Enter pro ukončení programu...")
