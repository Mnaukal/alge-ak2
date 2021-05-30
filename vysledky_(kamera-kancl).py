#!/usr/bin/env python3

#####################################################
# Skript pro převod formátu OPTIcXNet (nová kamera) do starého OPTIc (stará kamera), který se dá importovat do AK2
# Autor: Michal Töpfer, AC Mladá Boleslav
#
# Skirpt pracuje přímo ve složce, ve které je spuštěn, a pro každý '*.heatresultxml' soubor vytvoří '*.txt' soubor,
# který se dá importovat do AK2.
# Pokud vše pracuje správně, jsou ID závodů nastavená podle ID ze závodní kanceláře.
#####################################################

import sys
from pathlib import Path
import xml.etree.ElementTree as etree
import csv

GENERATE_CSV = False
WIND = True


def try_parse_int(s):
    try:
        return int(s)
    except ValueError:
        return 999999


def attempt_to_find_missing_lane(competitor, f):
    filename = "p" + f.stem + ".txt"
    with open(f.parent / filename) as p_file:
        reader = csv.reader(p_file, delimiter='\t', dialect=csv.excel)
        for row in reader:
            if row[3] == competitor["Firstname"] and row[4] == competitor["Lastname"]:
                return row[2]
    return None


def process_competitor(competitor, f):
    c = competitor.attrib

    if "Lane" not in c and "Bib" not in c:
        lane = attempt_to_find_missing_lane(c, f)
        if lane is not None:
            c["Lane"] = lane
        else:
            raise Exception(f"V souboru není určena dráha ani Bib závodníka/závodníků ({c.get('Firstname', '')} {c.get('Lastname', '')}).")

    result = [
        c.get("Rank", ""),
        c.get("Bib", ""),
        c.get("Lane", ""),
        c.get("Firstname", ""),
        c.get("Lastname", ""),
        c.get("Club", ""),
        "00"  # birth year - unused
    ]

    if "Runtime" in c:
        result.append(c["Runtime"])
    elif "State" in c:  # DQ, DNS, ...
        if c["State"] == "DSQ":
            result.append("disqualified")
        elif c["State"] == "DNS":
            result.append("did not start")
        elif c["State"] == "DNF":
            result.append("did not finish")
        else:
            result.append("")
    else:
        result.append("")

    #result.append("1067")  # something
    #result.append("591800")  # time in ms
    #result.append("1")  # camera picture
    #result.append("3")  # something
    #result.append("")  # something
    #result.append("")  # something
    #result.append("")  # something
    #
    #if "DifferenceToWinner" in c:  # DQ, DNS, ...
    #    if c["DifferenceToWinner"] == "Winner":
    #        result.append("winner")
    #    else:
    #        result.append("+" + c["DifferenceToWinner"])
    #
    #result.append("591800")  # time in ms

    #if "Rank" in c and c["Rank"] == "1":
    #    result.append("winner")
    #else:
    #    result.append("")  # something
    #
    #result.append("")  # something
    #result.append("")  # something
    #result.append("")  # something

    return result


def process_competitor_csv(competitor):
    c = competitor.attrib
    lane = c.get("Lane")
    if "Runtime" in c:
        return [lane, c["Runtime"]]
    if "State" in c:
        return [lane, c["State"]]
    else:
        raise Exception(f"Chybějíci výsledek pro dráhu {lane}.")


def process_heatresult(f):
    heat_result = etree.parse(f).getroot()
    results = heat_result[0]
    heat_number = heat_result.attrib["Nr"]
    filename = f.parent / (heat_number + ".txt")
    try:
        with open(filename, "w", newline="") as out_file:
            writer = csv.writer(out_file, delimiter="\t")
            for competitor in results:
                writer.writerow(process_competitor(competitor, f))

        if GENERATE_CSV:
            filename = f.parent / (heat_number + ".csv")
            with open(filename, "w", newline="") as out_file:
                writer = csv.writer(out_file, delimiter=";")
                writer.writerow(["Track", "BestResult"])
                for competitor in results:
                    writer.writerow(process_competitor_csv(competitor))

        if "Wind" in heat_result.attrib:
            wind = float(heat_result.attrib['Wind'])
            # print(f"  vítr: {wind} m/s")
            filename = f.parent / (heat_number + ".sav")
            with open(filename, "w", newline="") as out_file:
                print(f"[RaceInfo]\nWind={wind:+.1f} m/s\n", file=out_file)
        else:
            distance = int(heat_result.attrib.get("DistanceMeters", '0'))
            if distance <= 200:
                print(f"VAROVÁNÍ: chybí měření větru pro #{heat_number} ({heat_result.attrib['Name']})")

        print(f"#{heat_number} úspěšně zpracováno ({heat_result.attrib['Name']})")

    except Exception as e:
        print(f"CHYBA: {f.stem} ({heat_result.attrib['Name']})")
        print(" ", e)


path = Path(".")
if len(sys.argv) == 2:
    path = Path("./" + sys.argv[1])  # used mainly for debug purposes

files = path.glob("*.heatresultxml")
files = sorted(files, key=lambda x: try_parse_int(x.stem))

for f in files:
    try:
        process_heatresult(f)
    except:
        print(f"CHYBA při zpracování souboru '{f}'. Soubor je pravděpodobně poškozen.")

print()
input("Stiskněte Enter pro ukončení programu...")
