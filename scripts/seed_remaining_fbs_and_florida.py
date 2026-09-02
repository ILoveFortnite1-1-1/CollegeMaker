import json
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from scripts.seed_fbs_and_florida import build_canonical_record, DB_PATH, SEED_FILE, NOW_STR

REMAINING = [
    # Top Priority Florida
    {
        "id": "132903", "unitid": 132903, "name": "University of Central Florida", "alias": "UCF, Central Florida, Knights, Charge On",
        "control": "public", "city": "Orlando", "state": "FL", "zip": "32816", "location_type": "Suburban",
        "undergrad_size": 60000, "acceptance_rate": 0.360,
        "sat_reading_25": 600, "sat_reading_75": 680, "sat_math_25": 580, "sat_math_75": 680, "act_25": 25, "act_75": 30,
        "tuition_in_state": 6368, "tuition_out_of_state": 22467, "room_and_board": 11500, "net_price_average": 11100,
        "completion_rate_4yr": 0.48, "completion_rate_6yr": 0.74, "retention_rate_ft": 0.92, "median_earnings_10yr": 62400,
        "faculty_to_student_ratio": "30:1",
        "popular_programs": ["Computer Science", "Mechanical Engineering", "Biomedical Sciences", "Psychology", "Hospitality Management (Rosen)", "Finance"],
        "strengths": ["Largest university undergraduate enrollment in Florida and #2 nationally", "Rosen College of Hospitality Management ranked top 2 in the world", "Big 12 athletic conference competitor and Bounce House stadium atmosphere", "Extraordinary space and defense contracting pipeline to Cape Canaveral"]
    },
    {
        "id": "133881", "unitid": 133881, "name": "Florida Institute of Technology", "alias": "Florida Tech, FIT, Panthers",
        "control": "private_nonprofit", "city": "Melbourne", "state": "FL", "zip": "32901", "location_type": "City: Small",
        "undergrad_size": 3600, "acceptance_rate": 0.650,
        "sat_reading_25": 580, "sat_reading_75": 670, "sat_math_25": 580, "sat_math_75": 690, "act_25": 24, "act_75": 30,
        "tuition_in_state": 44360, "tuition_out_of_state": 44360, "room_and_board": 12800, "net_price_average": 32800,
        "completion_rate_4yr": 0.45, "completion_rate_6yr": 0.60, "retention_rate_ft": 0.79, "median_earnings_10yr": 73800,
        "faculty_to_student_ratio": "14:1",
        "popular_programs": ["Aerospace Engineering", "Aeronautical Science", "Mechanical Engineering", "Ocean Engineering", "Computer Science"],
        "strengths": ["Florida's STEM University located in the heart of the Space Coast", "Direct hiring pipelines with NASA, SpaceX, Northrop Grumman, L3Harris", "Premier aviation flight training"]
    },
    {
        "id": "135081", "unitid": 135081, "name": "Jacksonville University", "alias": "JU, Dolphins",
        "control": "private_nonprofit", "city": "Jacksonville", "state": "FL", "zip": "32211", "location_type": "Urban",
        "undergrad_size": 2800, "acceptance_rate": 0.770,
        "sat_reading_25": 540, "sat_reading_75": 640, "sat_math_25": 520, "sat_math_75": 630, "act_25": 22, "act_75": 28,
        "tuition_in_state": 43520, "tuition_out_of_state": 43520, "room_and_board": 15400, "net_price_average": 26900,
        "completion_rate_4yr": 0.42, "completion_rate_6yr": 0.54, "retention_rate_ft": 0.76, "median_earnings_10yr": 61200,
        "faculty_to_student_ratio": "11:1",
        "popular_programs": ["Nursing", "Aviation", "Business Administration", "Kinesiology", "Marine Science"],
        "strengths": ["St. Johns River waterfront campus with private university marina", "Brooks Rehabilitation College of Healthcare Sciences", "Davis College of Business & Aviation"]
    },
    {
        "id": "133465", "unitid": 133465, "name": "Eckerd College", "alias": "Eckerd, Tritons",
        "control": "private_nonprofit", "city": "St. Petersburg", "state": "FL", "zip": "33711", "location_type": "Urban",
        "undergrad_size": 2000, "acceptance_rate": 0.690,
        "sat_reading_25": 570, "sat_reading_75": 680, "sat_math_25": 530, "sat_math_75": 650, "act_25": 24, "act_75": 30,
        "tuition_in_state": 49800, "tuition_out_of_state": 49800, "room_and_board": 14200, "net_price_average": 33900,
        "completion_rate_4yr": 0.60, "completion_rate_6yr": 0.67, "retention_rate_ft": 0.82, "median_earnings_10yr": 52400,
        "faculty_to_student_ratio": "12:1",
        "popular_programs": ["Marine Science", "Environmental Studies", "Biology", "Psychology", "International Business"],
        "strengths": ["Waterfront campus on Tampa Bay with on-campus marina and student boat rentals", "Nationally renowned Marine Science program and turtle research", "Pet-friendly campus culture"]
    },
    {
        "id": "133526", "unitid": 133526, "name": "Flagler College", "alias": "Flagler, Saints",
        "control": "private_nonprofit", "city": "St. Augustine", "state": "FL", "zip": "32084", "location_type": "Town",
        "undergrad_size": 2600, "acceptance_rate": 0.790,
        "sat_reading_25": 540, "sat_reading_75": 630, "sat_math_25": 500, "sat_math_75": 590, "act_25": 20, "act_75": 26,
        "tuition_in_state": 23440, "tuition_out_of_state": 23440, "room_and_board": 13200, "net_price_average": 25800,
        "completion_rate_4yr": 0.52, "completion_rate_6yr": 0.61, "retention_rate_ft": 0.77, "median_earnings_10yr": 49800,
        "faculty_to_student_ratio": "16:1",
        "popular_programs": ["Business Administration", "Strategic Communication", "Psychology", "Hospitality & Tourism", "Education"],
        "strengths": ["Centerpiece is Henry Flagler's iconic 1888 Gilded Age Hotel Ponce de Leon", "Located in historic downtown St. Augustine, America's oldest city", "Minutes from the Atlantic Ocean beaches"]
    },

    # All Remaining FBS Football Universities
    {"id": "227757", "name": "Rice University", "alias": "Rice, Owls", "control": "private_nonprofit", "city": "Houston", "state": "TX", "undergrad_size": 4200, "acceptance_rate": 0.08, "median_earnings_10yr": 93200, "net_price_average": 19200, "sat_math_25": 750, "sat_math_75": 800, "sat_reading_25": 720, "sat_reading_75": 770, "act_25": 34, "act_75": 36, "faculty_to_student_ratio": "6:1", "tuition_in_state": 54960, "tuition_out_of_state": 54960},
    {"id": "216339", "name": "Temple University", "alias": "Temple, Owls", "control": "public", "city": "Philadelphia", "state": "PA", "undergrad_size": 25000, "acceptance_rate": 0.79, "median_earnings_10yr": 62800, "net_price_average": 23900, "sat_math_25": 560, "sat_math_75": 660, "sat_reading_25": 580, "sat_reading_75": 680, "faculty_to_student_ratio": "13:1"},
    {"id": "207962", "name": "University of Tulsa", "alias": "Tulsa, TU, Golden Hurricane", "control": "private_nonprofit", "city": "Tulsa", "state": "OK", "undergrad_size": 2700, "acceptance_rate": 0.69, "median_earnings_10yr": 68400, "net_price_average": 25900, "sat_math_25": 580, "sat_math_75": 700, "sat_reading_25": 590, "sat_reading_75": 710, "faculty_to_student_ratio": "9:1", "tuition_in_state": 45400, "tuition_out_of_state": 45400},
    {"id": "100663", "name": "University of Alabama at Birmingham", "alias": "UAB, Blazers", "control": "public", "city": "Birmingham", "state": "AL", "undergrad_size": 13500, "acceptance_rate": 0.88, "median_earnings_10yr": 56800, "net_price_average": 17200, "sat_math_25": 530, "sat_math_75": 660, "sat_reading_25": 540, "sat_reading_75": 670, "faculty_to_student_ratio": "18:1"},
    {"id": "198543", "name": "University of North Carolina at Charlotte", "alias": "Charlotte, 49ers, UNCC", "control": "public", "city": "Charlotte", "state": "NC", "undergrad_size": 24000, "acceptance_rate": 0.79, "median_earnings_10yr": 58900, "net_price_average": 15800, "sat_math_25": 540, "sat_math_75": 640, "sat_reading_25": 550, "sat_reading_75": 650, "faculty_to_student_ratio": "19:1"},
    {"id": "227216", "name": "University of North Texas", "alias": "UNT, Mean Green, North Texas", "control": "public", "city": "Denton", "state": "TX", "undergrad_size": 33000, "acceptance_rate": 0.81, "median_earnings_10yr": 56400, "net_price_average": 14200, "sat_math_25": 520, "sat_math_75": 630, "sat_reading_25": 540, "sat_reading_75": 640, "faculty_to_student_ratio": "23:1"},
    {"id": "240727", "name": "University of Wyoming", "alias": "Wyoming, UW, Cowboys, Cowgirls", "control": "public", "city": "Laramie", "state": "WY", "undergrad_size": 9500, "acceptance_rate": 0.96, "median_earnings_10yr": 57900, "net_price_average": 12800, "sat_math_25": 520, "sat_math_75": 630, "sat_reading_25": 530, "sat_reading_75": 640, "faculty_to_student_ratio": "14:1"},
    {"id": "230728", "name": "Utah State University", "alias": "Utah State, USU, Aggies", "control": "public", "city": "Logan", "state": "UT", "undergrad_size": 24000, "acceptance_rate": 0.93, "median_earnings_10yr": 57200, "net_price_average": 13900, "sat_math_25": 530, "sat_math_75": 650, "sat_reading_25": 540, "sat_reading_75": 660, "faculty_to_student_ratio": "19:1"},
    {"id": "182290", "name": "University of Nevada-Reno", "alias": "Nevada, UNR, Wolf Pack", "control": "public", "city": "Reno", "state": "NV", "undergrad_size": 17000, "acceptance_rate": 0.86, "median_earnings_10yr": 59400, "net_price_average": 16900, "sat_math_25": 520, "sat_math_75": 630, "sat_reading_25": 530, "sat_reading_75": 640, "faculty_to_student_ratio": "18:1"},
    {"id": "193930", "name": "University of New Mexico-Main Campus", "alias": "New Mexico, UNM, Lobos", "control": "public", "city": "Albuquerque", "state": "NM", "undergrad_size": 16000, "acceptance_rate": 0.97, "median_earnings_10yr": 50800, "net_price_average": 13400, "sat_math_25": 500, "sat_math_75": 610, "sat_reading_25": 510, "sat_reading_75": 630, "faculty_to_student_ratio": "16:1"},
    {"id": "122755", "name": "San Jose State University", "alias": "San Jose State, SJSU, Spartans", "control": "public", "city": "San Jose", "state": "CA", "undergrad_size": 27000, "acceptance_rate": 0.84, "median_earnings_10yr": 78200, "net_price_average": 16200, "sat_math_25": 540, "sat_math_75": 670, "sat_reading_25": 530, "sat_reading_75": 650, "faculty_to_student_ratio": "25:1"},
    {"id": "141574", "name": "University of Hawaii at Manoa", "alias": "Hawaii, UH Manoa, Rainbow Warriors", "control": "public", "city": "Honolulu", "state": "HI", "undergrad_size": 14000, "acceptance_rate": 0.83, "median_earnings_10yr": 57900, "net_price_average": 15900, "sat_math_25": 540, "sat_math_75": 650, "sat_reading_25": 550, "sat_reading_75": 660, "faculty_to_student_ratio": "13:1"},
    {"id": "139931", "name": "Georgia Southern University", "alias": "Georgia Southern, GSU, Eagles", "control": "public", "city": "Statesboro", "state": "GA", "undergrad_size": 22000, "acceptance_rate": 0.89, "median_earnings_10yr": 51200, "net_price_average": 15800, "sat_math_25": 500, "sat_math_75": 600, "sat_reading_25": 510, "sat_reading_75": 620, "faculty_to_student_ratio": "21:1"},
    {"id": "159647", "name": "University of Louisiana at Lafayette", "alias": "Louisiana, UL Lafayette, Ragin' Cajuns", "control": "public", "city": "Lafayette", "state": "LA", "undergrad_size": 14000, "acceptance_rate": 0.78, "median_earnings_10yr": 51900, "net_price_average": 12800, "sat_math_25": 510, "sat_math_75": 610, "sat_reading_25": 520, "sat_reading_75": 630, "faculty_to_student_ratio": "18:1"},
    {"id": "228459", "name": "Texas State University", "alias": "Texas State, Bobcats", "control": "public", "city": "San Marcos", "state": "TX", "undergrad_size": 33000, "acceptance_rate": 0.88, "median_earnings_10yr": 54600, "net_price_average": 16900, "sat_math_25": 510, "sat_math_75": 600, "sat_reading_25": 520, "sat_reading_75": 620, "faculty_to_student_ratio": "21:1"},
    {"id": "102094", "name": "University of South Alabama", "alias": "South Alabama, USA, Jaguars", "control": "public", "city": "Mobile", "state": "AL", "undergrad_size": 9500, "acceptance_rate": 0.71, "median_earnings_10yr": 49800, "net_price_average": 15400, "sat_math_25": 500, "sat_math_75": 610, "sat_reading_25": 510, "sat_reading_75": 630, "faculty_to_student_ratio": "17:1"},
    {"id": "139940", "name": "Georgia State University", "alias": "Georgia State, Panthers", "control": "public", "city": "Atlanta", "state": "GA", "undergrad_size": 28000, "acceptance_rate": 0.69, "median_earnings_10yr": 53800, "net_price_average": 17200, "sat_math_25": 500, "sat_math_75": 610, "sat_reading_25": 520, "sat_reading_75": 630, "faculty_to_student_ratio": "26:1"},
    {"id": "232982", "name": "Old Dominion University", "alias": "Old Dominion, ODU, Monarchs", "control": "public", "city": "Norfolk", "state": "VA", "undergrad_size": 19000, "acceptance_rate": 0.96, "median_earnings_10yr": 55800, "net_price_average": 17500, "sat_math_25": 510, "sat_math_75": 610, "sat_reading_25": 520, "sat_reading_75": 630, "faculty_to_student_ratio": "17:1"},
    {"id": "176372", "name": "University of Southern Mississippi", "alias": "Southern Miss, USM, Golden Eagles", "control": "public", "city": "Hattiesburg", "state": "MS", "undergrad_size": 10500, "acceptance_rate": 0.98, "median_earnings_10yr": 46200, "net_price_average": 14800, "sat_math_25": 490, "sat_math_75": 590, "sat_reading_25": 500, "sat_reading_75": 610, "faculty_to_student_ratio": "16:1"},
    {"id": "106458", "name": "Arkansas State University", "alias": "Arkansas State, Red Wolves", "control": "public", "city": "Jonesboro", "state": "AR", "undergrad_size": 8500, "acceptance_rate": 0.70, "median_earnings_10yr": 44800, "net_price_average": 13900, "sat_math_25": 490, "sat_math_75": 600, "sat_reading_25": 500, "sat_reading_75": 610, "faculty_to_student_ratio": "14:1"},
    {"id": "159656", "name": "University of Louisiana at Monroe", "alias": "ULM, Warhawks", "control": "public", "city": "Monroe", "state": "LA", "undergrad_size": 6500, "acceptance_rate": 0.70, "median_earnings_10yr": 47200, "net_price_average": 11800, "sat_math_25": 490, "sat_math_75": 590, "sat_reading_25": 500, "sat_reading_75": 600, "faculty_to_student_ratio": "18:1"},
    {"id": "204024", "name": "Miami University-Oxford", "alias": "Miami University, Miami of Ohio, RedHawks", "control": "public", "city": "Oxford", "state": "OH", "undergrad_size": 17000, "acceptance_rate": 0.88, "median_earnings_10yr": 66800, "net_price_average": 24200, "sat_math_25": 590, "sat_math_75": 690, "sat_reading_25": 590, "sat_reading_75": 690, "faculty_to_student_ratio": "15:1"},
    {"id": "204857", "name": "Ohio University-Main Campus", "alias": "Ohio University, OU, Bobcats", "control": "public", "city": "Athens", "state": "OH", "undergrad_size": 20000, "acceptance_rate": 0.87, "median_earnings_10yr": 56800, "net_price_average": 22100, "sat_math_25": 530, "sat_math_75": 640, "sat_reading_25": 540, "sat_reading_75": 650, "faculty_to_student_ratio": "16:1"},
    {"id": "201441", "name": "Bowling Green State University-Main Campus", "alias": "Bowling Green, BGSU, Falcons", "control": "public", "city": "Bowling Green", "state": "OH", "undergrad_size": 14500, "acceptance_rate": 0.79, "median_earnings_10yr": 52800, "net_price_average": 18900, "sat_math_25": 500, "sat_math_75": 610, "sat_reading_25": 510, "sat_reading_75": 620, "faculty_to_student_ratio": "18:1"},
    {"id": "172699", "name": "Western Michigan University", "alias": "Western Michigan, WMU, Broncos", "control": "public", "city": "Kalamazoo", "state": "MI", "undergrad_size": 14000, "acceptance_rate": 0.85, "median_earnings_10yr": 54800, "net_price_average": 19400, "sat_math_25": 510, "sat_math_75": 620, "sat_reading_25": 510, "sat_reading_75": 620, "faculty_to_student_ratio": "15:1"},
    {"id": "169248", "name": "Central Michigan University", "alias": "Central Michigan, CMU, Chippewas", "control": "public", "city": "Mount Pleasant", "state": "MI", "undergrad_size": 11000, "acceptance_rate": 0.77, "median_earnings_10yr": 53400, "net_price_average": 16400, "sat_math_25": 490, "sat_math_75": 600, "sat_reading_25": 500, "sat_reading_75": 610, "faculty_to_student_ratio": "17:1"},
    {"id": "169798", "name": "Eastern Michigan University", "alias": "Eastern Michigan, EMU, Eagles", "control": "public", "city": "Ypsilanti", "state": "MI", "undergrad_size": 12000, "acceptance_rate": 0.85, "median_earnings_10yr": 49800, "net_price_average": 15800, "sat_math_25": 480, "sat_math_75": 590, "sat_reading_25": 490, "sat_reading_75": 600, "faculty_to_student_ratio": "14:1"},
    {"id": "147703", "name": "Northern Illinois University", "alias": "Northern Illinois, NIU, Huskies", "control": "public", "city": "Dekalb", "state": "IL", "undergrad_size": 11500, "acceptance_rate": 0.70, "median_earnings_10yr": 58900, "net_price_average": 14800, "sat_math_25": 490, "sat_math_75": 600, "sat_reading_25": 500, "sat_reading_75": 610, "faculty_to_student_ratio": "15:1"},
    {"id": "150136", "name": "Ball State University", "alias": "Ball State, BSU, Cardinals, Chirp Chirp", "control": "public", "city": "Muncie", "state": "IN", "undergrad_size": 14000, "acceptance_rate": 0.69, "median_earnings_10yr": 52800, "net_price_average": 15400, "sat_math_25": 520, "sat_math_75": 620, "sat_reading_25": 530, "sat_reading_75": 630, "faculty_to_student_ratio": "14:1"},
    {"id": "196088", "name": "University at Buffalo", "alias": "Buffalo, UB, Bulls, SUNY Buffalo", "control": "public", "city": "Buffalo", "state": "NY", "undergrad_size": 21000, "acceptance_rate": 0.68, "median_earnings_10yr": 68400, "net_price_average": 18200, "sat_math_25": 610, "sat_math_75": 710, "sat_reading_25": 590, "sat_reading_75": 680, "faculty_to_student_ratio": "13:1"},
    {"id": "200800", "name": "University of Akron Main Campus", "alias": "Akron, Zips", "control": "public", "city": "Akron", "state": "OH", "undergrad_size": 11000, "acceptance_rate": 0.84, "median_earnings_10yr": 51200, "net_price_average": 17800, "sat_math_25": 500, "sat_math_75": 610, "sat_reading_25": 500, "sat_reading_75": 620, "faculty_to_student_ratio": "17:1"},
    {"id": "203517", "name": "Kent State University at Kent", "alias": "Kent State, Golden Flashes", "control": "public", "city": "Kent", "state": "OH", "undergrad_size": 21000, "acceptance_rate": 0.88, "median_earnings_10yr": 49800, "net_price_average": 19200, "sat_math_25": 510, "sat_math_75": 610, "sat_reading_25": 520, "sat_reading_75": 630, "faculty_to_student_ratio": "19:1"},
    {"id": "157951", "name": "Western Kentucky University", "alias": "Western Kentucky, WKU, Hilltoppers, Big Red", "control": "public", "city": "Bowling Green", "state": "KY", "undergrad_size": 13500, "acceptance_rate": 0.98, "median_earnings_10yr": 48400, "net_price_average": 13900, "sat_math_25": 500, "sat_math_75": 600, "sat_reading_25": 510, "sat_reading_75": 620, "faculty_to_student_ratio": "17:1"},
    {"id": "101480", "name": "Jacksonville State University", "alias": "Jacksonville State, JSU, Gamecocks", "control": "public", "city": "Jacksonville", "state": "AL", "undergrad_size": 7500, "acceptance_rate": 0.78, "median_earnings_10yr": 45600, "net_price_average": 14200, "sat_math_25": 490, "sat_math_75": 590, "sat_reading_25": 500, "sat_reading_75": 610, "faculty_to_student_ratio": "18:1"},
    {"id": "193888", "name": "New Mexico State University-Main Campus", "alias": "New Mexico State, NMSU, Aggies", "control": "public", "city": "Las Cruces", "state": "NM", "undergrad_size": 11000, "acceptance_rate": 0.78, "median_earnings_10yr": 47200, "net_price_average": 11800, "sat_math_25": 480, "sat_math_75": 590, "sat_reading_25": 490, "sat_reading_75": 600, "faculty_to_student_ratio": "16:1"},
    {"id": "220978", "name": "Middle Tennessee State University", "alias": "Middle Tennessee, MTSU, Blue Raiders", "control": "public", "city": "Murfreesboro", "state": "TN", "undergrad_size": 17000, "acceptance_rate": 0.72, "median_earnings_10yr": 51200, "net_price_average": 13200, "sat_math_25": 500, "sat_math_75": 610, "sat_reading_25": 510, "sat_reading_75": 620, "faculty_to_student_ratio": "16:1"},
    {"id": "229063", "name": "The University of Texas at El Paso", "alias": "UTEP, Miners, Picks Up", "control": "public", "city": "El Paso", "state": "TX", "undergrad_size": 20000, "acceptance_rate": 1.00, "median_earnings_10yr": 50800, "net_price_average": 9800, "sat_math_25": 480, "sat_math_75": 580, "sat_reading_25": 490, "sat_reading_75": 590, "faculty_to_student_ratio": "20:1"},
    {"id": "159658", "unitid": 159658, "name": "Louisiana Tech University", "alias": "Louisiana Tech, LA Tech, Bulldogs", "control": "public", "city": "Ruston", "state": "LA", "undergrad_size": 9000, "acceptance_rate": 0.66, "median_earnings_10yr": 58200, "net_price_average": 12400, "sat_math_25": 530, "sat_math_75": 650, "sat_reading_25": 530, "sat_reading_75": 650, "faculty_to_student_ratio": "19:1"},
    {"id": "227881", "name": "Sam Houston State University", "alias": "Sam Houston State, SHSU, Bearkats", "control": "public", "city": "Huntsville", "state": "TX", "undergrad_size": 18000, "acceptance_rate": 0.85, "median_earnings_10yr": 53400, "net_price_average": 14200, "sat_math_25": 490, "sat_math_75": 590, "sat_reading_25": 500, "sat_reading_75": 600, "faculty_to_student_ratio": "22:1"},
    {"id": "139995", "name": "Kennesaw State University", "alias": "Kennesaw State, KSU, Owls", "control": "public", "city": "Kennesaw", "state": "GA", "undergrad_size": 38000, "acceptance_rate": 0.68, "median_earnings_10yr": 56800, "net_price_average": 16200, "sat_math_25": 520, "sat_math_75": 620, "sat_reading_25": 540, "sat_reading_75": 640, "faculty_to_student_ratio": "21:1"}
]

def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    existing_seeds = []
    if SEED_FILE.exists():
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            existing_seeds = json.load(f)

    seed_map = {str(c["id"]): c for c in existing_seeds}
    added = 0
    updated = 0

    for c in REMAINING:
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

    print(f"Remaining FBS & Florida added: {added} new, {updated} updated.")
    print(f"Total colleges in seed JSON: {len(updated_seeds)}")

if __name__ == "__main__":
    run()
