import json
import sqlite3
from pathlib import Path
from scripts.seed_fbs_and_florida import build_canonical_record, DB_PATH, SEED_FILE, NOW_STR

MORE_FBS = [
    # SEC
    {"id": "176035", "name": "Mississippi State University", "alias": "Mississippi State, Bulldogs, Hail State", "control": "public", "city": "Mississippi State", "state": "MS", "undergrad_size": 18000, "acceptance_rate": 0.75, "median_earnings_10yr": 54100, "net_price_average": 16400, "sat_math_25": 530, "sat_math_75": 650, "sat_reading_25": 540, "sat_reading_75": 660, "faculty_to_student_ratio": "16:1"},
    {"id": "106397", "name": "University of Arkansas", "alias": "Arkansas, Razorbacks, Hogs, Woo Pig", "control": "public", "city": "Fayetteville", "state": "AR", "undergrad_size": 25000, "acceptance_rate": 0.79, "median_earnings_10yr": 58900, "net_price_average": 16700, "sat_math_25": 550, "sat_math_75": 670, "sat_reading_25": 560, "sat_reading_75": 680, "faculty_to_student_ratio": "18:1"},
    {"id": "218663", "name": "University of South Carolina", "alias": "South Carolina, Gamecocks, USC Columbia", "control": "public", "city": "Columbia", "state": "SC", "undergrad_size": 27000, "acceptance_rate": 0.64, "median_earnings_10yr": 61200, "net_price_average": 21800, "sat_math_25": 580, "sat_math_75": 680, "sat_reading_25": 600, "sat_reading_75": 690, "faculty_to_student_ratio": "17:1"},
    {"id": "157085", "name": "University of Kentucky", "alias": "Kentucky, UK, Wildcats, Big Blue Nation", "control": "public", "city": "Lexington", "state": "KY", "undergrad_size": 22000, "acceptance_rate": 0.94, "median_earnings_10yr": 57900, "net_price_average": 19800, "sat_math_25": 540, "sat_math_75": 660, "sat_reading_25": 550, "sat_reading_75": 670, "faculty_to_student_ratio": "16:1"},
    {"id": "178396", "name": "University of Missouri-Columbia", "alias": "Missouri, Mizzou, Tigers", "control": "public", "city": "Columbia", "state": "MO", "undergrad_size": 23000, "acceptance_rate": 0.77, "median_earnings_10yr": 62400, "net_price_average": 16900, "sat_math_25": 560, "sat_math_75": 670, "sat_reading_25": 570, "sat_reading_75": 680, "faculty_to_student_ratio": "17:1"},

    # Big 12
    {"id": "104179", "name": "University of Arizona", "alias": "Arizona, U of A, Wildcats, Bear Down", "control": "public", "city": "Tucson", "state": "AZ", "undergrad_size": 39000, "acceptance_rate": 0.87, "median_earnings_10yr": 62000, "net_price_average": 15600, "sat_math_25": 560, "sat_math_75": 680, "sat_reading_25": 570, "sat_reading_75": 680, "faculty_to_student_ratio": "15:1"},
    {"id": "155317", "name": "University of Kansas", "alias": "Kansas, KU, Jayhawks, Rock Chalk", "control": "public", "city": "Lawrence", "state": "KS", "undergrad_size": 19000, "acceptance_rate": 0.88, "median_earnings_10yr": 61500, "net_price_average": 18900, "sat_math_25": 550, "sat_math_75": 670, "sat_reading_25": 560, "sat_reading_75": 680, "faculty_to_student_ratio": "17:1"},
    {"id": "155399", "name": "Kansas State University", "alias": "Kansas State, K-State, Wildcats", "control": "public", "city": "Manhattan", "state": "KS", "undergrad_size": 15000, "acceptance_rate": 0.95, "median_earnings_10yr": 58200, "net_price_average": 18500, "sat_math_25": 540, "sat_math_75": 660, "sat_reading_25": 530, "sat_reading_75": 660, "faculty_to_student_ratio": "18:1"},
    {"id": "153603", "name": "Iowa State University", "alias": "Iowa State, ISU, Cyclones", "control": "public", "city": "Ames", "state": "IA", "undergrad_size": 25000, "acceptance_rate": 0.90, "median_earnings_10yr": 63400, "net_price_average": 16200, "sat_math_25": 560, "sat_math_75": 690, "sat_reading_25": 550, "sat_reading_75": 670, "faculty_to_student_ratio": "19:1"},
    {"id": "207388", "name": "Oklahoma State University-Main Campus", "alias": "Oklahoma State, OSU, Cowboys, Pokes", "control": "public", "city": "Stillwater", "state": "OK", "undergrad_size": 20000, "acceptance_rate": 0.71, "median_earnings_10yr": 57900, "net_price_average": 14700, "sat_math_25": 530, "sat_math_75": 660, "sat_reading_25": 540, "sat_reading_75": 660, "faculty_to_student_ratio": "18:1"},
    {"id": "228875", "name": "Texas Christian University", "alias": "TCU, Horned Frogs", "control": "private_nonprofit", "city": "Fort Worth", "state": "TX", "undergrad_size": 10500, "acceptance_rate": 0.56, "median_earnings_10yr": 73200, "net_price_average": 36100, "sat_math_25": 580, "sat_math_75": 680, "sat_reading_25": 600, "sat_reading_75": 690, "faculty_to_student_ratio": "13:1"},
    {"id": "223234", "name": "Baylor University", "alias": "Baylor, Bears, Sic 'em", "control": "private_nonprofit", "city": "Waco", "state": "TX", "undergrad_size": 15000, "acceptance_rate": 0.46, "median_earnings_10yr": 66500, "net_price_average": 38400, "sat_math_25": 590, "sat_math_75": 690, "sat_reading_25": 610, "sat_reading_75": 710, "faculty_to_student_ratio": "15:1"},
    {"id": "229115", "name": "Texas Tech University", "alias": "Texas Tech, TTU, Red Raiders, Wreck 'em", "control": "public", "city": "Lubbock", "state": "TX", "undergrad_size": 33000, "acceptance_rate": 0.67, "median_earnings_10yr": 63800, "net_price_average": 17900, "sat_math_25": 560, "sat_math_75": 660, "sat_reading_25": 560, "sat_reading_75": 660, "faculty_to_student_ratio": "21:1"},
    {"id": "225511", "name": "University of Houston", "alias": "Houston, UH, Cougars, Coogs", "control": "public", "city": "Houston", "state": "TX", "undergrad_size": 37000, "acceptance_rate": 0.66, "median_earnings_10yr": 64800, "net_price_average": 14400, "sat_math_25": 580, "sat_math_75": 680, "sat_reading_25": 580, "sat_reading_75": 670, "faculty_to_student_ratio": "22:1"},
    {"id": "201885", "name": "University of Cincinnati-Main Campus", "alias": "Cincinnati, UC, Bearcats", "control": "public", "city": "Cincinnati", "state": "OH", "undergrad_size": 30000, "acceptance_rate": 0.85, "median_earnings_10yr": 61900, "net_price_average": 20400, "sat_math_25": 580, "sat_math_75": 690, "sat_reading_25": 580, "sat_reading_75": 680, "faculty_to_student_ratio": "16:1"},
    {"id": "238032", "name": "West Virginia University", "alias": "West Virginia, WVU, Mountaineers, Country Roads", "control": "public", "city": "Morgantown", "state": "WV", "undergrad_size": 20000, "acceptance_rate": 0.89, "median_earnings_10yr": 57400, "net_price_average": 13100, "sat_math_25": 510, "sat_math_75": 620, "sat_reading_25": 520, "sat_reading_75": 630, "faculty_to_student_ratio": "17:1"},

    # ACC
    {"id": "157289", "name": "University of Louisville", "alias": "Louisville, UofL, Cardinals, Cards", "control": "public", "city": "Louisville", "state": "KY", "undergrad_size": 16000, "acceptance_rate": 0.80, "median_earnings_10yr": 57900, "net_price_average": 19300, "sat_math_25": 540, "sat_math_75": 660, "sat_reading_25": 550, "sat_reading_75": 670, "faculty_to_student_ratio": "14:1"},
    {"id": "215293", "name": "University of Pittsburgh-Pittsburgh Campus", "alias": "Pittsburgh, Pitt, Panthers, Hail to Pitt", "control": "public", "city": "Pittsburgh", "state": "PA", "undergrad_size": 19000, "acceptance_rate": 0.49, "median_earnings_10yr": 73200, "net_price_average": 24200, "sat_math_25": 640, "sat_math_75": 740, "sat_reading_25": 640, "sat_reading_75": 730, "faculty_to_student_ratio": "14:1"},
    {"id": "196413", "name": "Syracuse University", "alias": "Syracuse, Orange, 'Cuse", "control": "private_nonprofit", "city": "Syracuse", "state": "NY", "undergrad_size": 15000, "acceptance_rate": 0.52, "median_earnings_10yr": 75800, "net_price_average": 43500, "sat_math_25": 620, "sat_math_75": 720, "sat_reading_25": 630, "sat_reading_75": 710, "faculty_to_student_ratio": "15:1"},
    {"id": "164924", "name": "Boston College", "alias": "Boston College, BC, Eagles", "control": "private_nonprofit", "city": "Chestnut Hill", "state": "MA", "undergrad_size": 9800, "acceptance_rate": 0.15, "median_earnings_10yr": 98200, "net_price_average": 31200, "sat_math_25": 710, "sat_math_75": 780, "sat_reading_25": 690, "sat_reading_75": 750, "faculty_to_student_ratio": "10:1"},
    {"id": "199847", "name": "Wake Forest University", "alias": "Wake Forest, WFU, Demon Deacons", "control": "private_nonprofit", "city": "Winston-Salem", "state": "NC", "undergrad_size": 5400, "acceptance_rate": 0.20, "median_earnings_10yr": 88400, "net_price_average": 27200, "sat_math_25": 690, "sat_math_75": 770, "sat_reading_25": 680, "sat_reading_75": 750, "faculty_to_student_ratio": "10:1"},
    {"id": "228246", "name": "Southern Methodist University", "alias": "SMU, Mustangs, Pony Up", "control": "private_nonprofit", "city": "Dallas", "state": "TX", "undergrad_size": 7100, "acceptance_rate": 0.52, "median_earnings_10yr": 83400, "net_price_average": 40500, "sat_math_25": 680, "sat_math_75": 770, "sat_reading_25": 670, "sat_reading_75": 750, "faculty_to_student_ratio": "11:1"},

    # Independents & Service Academies & Pac-12
    {"id": "197036", "name": "United States Military Academy", "alias": "West Point, Army, Black Knights", "control": "public", "city": "West Point", "state": "NY", "undergrad_size": 4500, "acceptance_rate": 0.11, "median_earnings_10yr": 115000, "net_price_average": 0, "sat_math_25": 630, "sat_math_75": 740, "sat_reading_25": 630, "sat_reading_75": 730, "faculty_to_student_ratio": "7:1", "tuition_in_state": 0, "tuition_out_of_state": 0},
    {"id": "164155", "name": "United States Naval Academy", "alias": "Navy, Midshipmen, Annapolis", "control": "public", "city": "Annapolis", "state": "MD", "undergrad_size": 4500, "acceptance_rate": 0.08, "median_earnings_10yr": 120000, "net_price_average": 0, "sat_math_25": 640, "sat_math_75": 750, "sat_reading_25": 640, "sat_reading_75": 740, "faculty_to_student_ratio": "8:1", "tuition_in_state": 0, "tuition_out_of_state": 0},
    {"id": "126182", "name": "United States Air Force Academy", "alias": "Air Force, Falcons, USAFA", "control": "public", "city": "USAF Academy", "state": "CO", "undergrad_size": 4300, "acceptance_rate": 0.12, "median_earnings_10yr": 118000, "net_price_average": 0, "sat_math_25": 660, "sat_math_75": 760, "sat_reading_25": 640, "sat_reading_75": 730, "faculty_to_student_ratio": "8:1", "tuition_in_state": 0, "tuition_out_of_state": 0},
    {"id": "209542", "name": "Oregon State University", "alias": "Oregon State, OSU, Beavers", "control": "public", "city": "Corvallis", "state": "OR", "undergrad_size": 27000, "acceptance_rate": 0.83, "median_earnings_10yr": 63400, "net_price_average": 21400, "sat_math_25": 550, "sat_math_75": 670, "sat_reading_25": 560, "sat_reading_75": 680, "faculty_to_student_ratio": "18:1"},
    {"id": "236939", "name": "Washington State University", "alias": "Washington State, WSU, Cougars, Cougs", "control": "public", "city": "Pullman", "state": "WA", "undergrad_size": 24000, "acceptance_rate": 0.85, "median_earnings_10yr": 62800, "net_price_average": 17800, "sat_math_25": 530, "sat_math_75": 650, "sat_reading_25": 540, "sat_reading_75": 660, "faculty_to_student_ratio": "15:1"},
    {"id": "129020", "name": "University of Connecticut", "alias": "UConn, Huskies, Connecticut", "control": "public", "city": "Storrs", "state": "CT", "undergrad_size": 19000, "acceptance_rate": 0.55, "median_earnings_10yr": 73400, "net_price_average": 23900, "sat_math_25": 620, "sat_math_75": 720, "sat_reading_25": 620, "sat_reading_75": 710, "faculty_to_student_ratio": "16:1"},

    # Top Group of 5 FBS & Mid-Majors
    {"id": "220862", "name": "University of Memphis", "alias": "Memphis, Tigers", "control": "public", "city": "Memphis", "state": "TN", "undergrad_size": 17000, "acceptance_rate": 0.88, "median_earnings_10yr": 48200, "net_price_average": 13900, "sat_math_25": 500, "sat_math_75": 620, "sat_reading_25": 510, "sat_reading_75": 630, "faculty_to_student_ratio": "16:1"},
    {"id": "229027", "name": "The University of Texas at San Antonio", "alias": "UTSA, Roadrunners, Birds Up", "control": "public", "city": "San Antonio", "state": "TX", "undergrad_size": 29000, "acceptance_rate": 0.87, "median_earnings_10yr": 56900, "net_price_average": 12800, "sat_math_25": 520, "sat_math_75": 630, "sat_reading_25": 530, "sat_reading_75": 640, "faculty_to_student_ratio": "25:1"},
    {"id": "198464", "name": "East Carolina University", "alias": "ECU, East Carolina, Pirates", "control": "public", "city": "Greenville", "state": "NC", "undergrad_size": 22000, "acceptance_rate": 0.92, "median_earnings_10yr": 54200, "net_price_average": 15400, "sat_math_25": 530, "sat_math_75": 630, "sat_reading_25": 540, "sat_reading_75": 640, "faculty_to_student_ratio": "18:1"},
    {"id": "110538", "name": "California State University-Fresno", "alias": "Fresno State, Bulldogs", "control": "public", "city": "Fresno", "state": "CA", "undergrad_size": 22000, "acceptance_rate": 0.95, "median_earnings_10yr": 55100, "net_price_average": 7200, "sat_math_25": 480, "sat_math_75": 590, "sat_reading_25": 490, "sat_reading_75": 600, "faculty_to_student_ratio": "23:1"},
    {"id": "182281", "name": "University of Nevada-Las Vegas", "alias": "UNLV, Rebels, Runnin' Rebels", "control": "public", "city": "Las Vegas", "state": "NV", "undergrad_size": 25000, "acceptance_rate": 0.85, "median_earnings_10yr": 54800, "net_price_average": 13800, "sat_math_25": 510, "sat_math_75": 620, "sat_reading_25": 520, "sat_reading_75": 630, "faculty_to_student_ratio": "20:1"},
    {"id": "126818", "name": "Colorado State University-Fort Collins", "alias": "Colorado State, CSU, Rams", "control": "public", "city": "Fort Collins", "state": "CO", "undergrad_size": 25000, "acceptance_rate": 0.90, "median_earnings_10yr": 61200, "net_price_average": 19500, "sat_math_25": 560, "sat_math_75": 670, "sat_reading_25": 570, "sat_reading_75": 680, "faculty_to_student_ratio": "16:1"},
    {"id": "217633", "name": "Coastal Carolina University", "alias": "Coastal Carolina, Chanticleers, Chants", "control": "public", "city": "Conway", "state": "SC", "undergrad_size": 10000, "acceptance_rate": 0.79, "median_earnings_10yr": 50800, "net_price_average": 15400, "sat_math_25": 520, "sat_math_75": 610, "sat_reading_25": 530, "sat_reading_75": 630, "faculty_to_student_ratio": "16:1"},
    {"id": "102368", "name": "Troy University", "alias": "Troy, Trojans", "control": "public", "city": "Troy", "state": "AL", "undergrad_size": 11000, "acceptance_rate": 0.94, "median_earnings_10yr": 47200, "net_price_average": 14100, "sat_math_25": 500, "sat_math_75": 600, "sat_reading_25": 510, "sat_reading_75": 620, "faculty_to_student_ratio": "16:1"},
    {"id": "237525", "name": "Marshall University", "alias": "Marshall, Thundering Herd, We Are Marshall", "control": "public", "city": "Huntington", "state": "WV", "undergrad_size": 8500, "acceptance_rate": 0.97, "median_earnings_10yr": 48200, "net_price_average": 9600, "sat_math_25": 500, "sat_math_75": 600, "sat_reading_25": 510, "sat_reading_75": 620, "faculty_to_student_ratio": "17:1"},
    {"id": "206084", "name": "University of Toledo", "alias": "Toledo, Rockets", "control": "public", "city": "Toledo", "state": "OH", "undergrad_size": 12000, "acceptance_rate": 0.96, "median_earnings_10yr": 56400, "net_price_average": 17800, "sat_math_25": 510, "sat_math_75": 630, "sat_reading_25": 520, "sat_reading_75": 640, "faculty_to_student_ratio": "14:1"},
    {"id": "232557", "name": "Liberty University", "alias": "Liberty, Flames", "control": "private_nonprofit", "city": "Lynchburg", "state": "VA", "undergrad_size": 47000, "acceptance_rate": 0.99, "median_earnings_10yr": 48900, "net_price_average": 28400, "sat_math_25": 520, "sat_math_75": 630, "sat_reading_25": 540, "sat_reading_75": 650, "faculty_to_student_ratio": "18:1"}
]

def append_all():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    existing_seeds = []
    if SEED_FILE.exists():
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            existing_seeds = json.load(f)

    seed_map = {str(c["id"]): c for c in existing_seeds}
    added = 0
    updated = 0

    for c in MORE_FBS:
        cid = str(c["id"])
        record = build_canonical_record(c)
        seed_map[cid] = record

        cursor.execute("SELECT id FROM colleges WHERE id = ?", (cid,))
        exists = cursor.fetchone()

        cursor.execute(
            """
            INSERT OR REPLACE INTO colleges (
                id, unitid, name, alias, control, city, state, location_type,
                acceptance_rate, net_price_average, median_earnings_10yr, undergrad_size,
                data_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid,
                record["unitid"],
                record["name"],
                record["alias"],
                record["control"],
                record["location"]["city"],
                record["location"]["state"],
                record["location"]["location_type"],
                record["admissions"]["acceptance_rate"]["value"],
                record["costs"]["net_price_average"]["value"],
                record["outcomes"]["median_earnings_10yr"]["value"],
                record["undergrad_size"]["value"],
                json.dumps(record),
                NOW_STR
            )
        )
        if exists:
            updated += 1
        else:
            added += 1

    conn.commit()
    conn.close()

    updated_seeds = list(seed_map.values())
    with open(SEED_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_seeds, f, indent=2)

    print(f"More FBS Appended: {added} new, {updated} updated. Total in JSON: {len(updated_seeds)}")

if __name__ == "__main__":
    append_all()
