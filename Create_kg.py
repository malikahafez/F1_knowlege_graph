import dotenv
import csv
import os
import neo4j
from neo4j import GraphDatabase
from neo4j.time import Date

# from neo4j.debug import watch

# watch("neo4j")

load_status = dotenv.load_dotenv("config.txt", override=True)
if load_status is False:
    raise RuntimeError('Environment variables not loaded.')

URI = os.getenv("URI")
USER = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
if not URI or not USER or not PASSWORD:
    raise ValueError("Missing URI, USERNAME, or PASSWORD in config.txt")
DATABASE = os.getenv("DATABASE", None)
AUTH = (USER, PASSWORD)

print(URI)
print(AUTH)

def clean_int(val):
    # if \N, omit will omit by checking if it is None
    if val is None or val == '\\N' or str(val).strip() == '':
        return None
    return int(val)

def clean_float(val):
    # if \N, omit will omit by checking if it is None
    if val is None or val == '\\N' or str(val).strip() == '':
        return None
    return float(val)

def clean_str(val):
    # if \N, omit will omit by checking if it is None
    if val is None or val == '\\N' or str(val).strip() == '':
        return None
    return str(val).strip()

def clean_date(val):
    # if \N, omit will omit by checking if it is None
    # convert date strings to Neo4j date objects
    # Neo4j python driver handles datetime.date or Neo4j Date objects
    s = clean_str(val)
    if not s:
        return None
    try:
        # YYYY-MM-DD format in F1 dataset
        parts = s.split('-')
        return Date(int(parts[0]), int(parts[1]), int(parts[2])) # neo4j date
    except Exception:
        return s
    
def filter_properties(props_dict):
    #Removes keys with None values (missing values or \N) so they are omitted from the node/relationship.'''
    return {k: v for k, v in props_dict.items() if v is not None}

def create_knowledge_graph_nodes(driver):
    with driver.session(database=DATABASE) as session:
        print("Creating constraints...")
        constraints = [
            "CREATE CONSTRAINT driver_id_uniq IF NOT EXISTS FOR (d:Driver) REQUIRE d.driverId IS UNIQUE",
            "CREATE CONSTRAINT constructor_id_uniq IF NOT EXISTS FOR (c:Constructor) REQUIRE c.constructorId IS UNIQUE",
            "CREATE CONSTRAINT circuit_id_uniq IF NOT EXISTS FOR (ci:Circuit) REQUIRE ci.circuitId IS UNIQUE",
            "CREATE CONSTRAINT season_year_uniq IF NOT EXISTS FOR (s:Season) REQUIRE s.year IS UNIQUE",
            "CREATE CONSTRAINT status_id_uniq IF NOT EXISTS FOR (st:Status) REQUIRE st.statusId IS UNIQUE",
            "CREATE CONSTRAINT race_id_uniq IF NOT EXISTS FOR (r:Race) REQUIRE r.raceId IS UNIQUE",
            "CREATE CONSTRAINT result_id_uniq IF NOT EXISTS FOR (res:Result) REQUIRE res.resultId IS UNIQUE",
            "CREATE CONSTRAINT qualify_id_uniq IF NOT EXISTS FOR (q:Qualifying) REQUIRE q.qualifyId IS UNIQUE",
            "CREATE CONSTRAINT pitstop_id_uniq IF NOT EXISTS FOR (p:PitStop) REQUIRE p.eventId IS UNIQUE"
        ]
        for query in constraints:
            session.run(query)

        # --- DRIVERS (Entity Nodes) ---
        print("Importing Driver Nodes...")
        with open("drivers.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                props = filter_properties({
                    "driverId": clean_int(row["driverId"]),
                    "driverRef": clean_str(row["driverRef"]),
                    "number": clean_int(row["number"]),
                    "code": clean_str(row["code"]),
                    "forename": clean_str(row["forename"]),
                    "surname": clean_str(row["surname"]),
                    "dob": clean_date(row["dob"]),
                    "nationality": clean_str(row["nationality"])
                })
                session.run("""
                    MERGE (d:Driver {driverId: $driverId})
                    SET d += $props
                """, driverId=props["driverId"], props=props)   

        # --- CONSTRUCTORS (Entity Nodes) ---
        print("Importing Constructor Nodes...")
        with open("constructors.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                props = filter_properties({
                    "constructorId": clean_int(row["constructorId"]),
                    "constructorRef": clean_str(row["constructorRef"]),
                    "constructor_name": clean_str(row["name"]),
                    "constructor_nationality": clean_str(row["nationality"])
                })
                session.run("""
                    MERGE (con:Constructor {constructorId: $constructorId})
                    SET con += $props
                """, constructorId=props["constructorId"], props=props)  

        # --- CIRCUITS (Entity Nodes) ---
        print("Importing Circuit Nodes...")
        with open("circuits.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                props = filter_properties({
                    "circuitId": clean_int(row["circuitId"]),
                    "circuitRef": clean_str(row["circuitRef"]),
                    "circuit_name": clean_str(row["name"]),
                    "circuit_loc": clean_str(row["location"]),
                    "circuit_country": clean_str(row["country"]),
                    "lat": clean_float(row["lat"]),
                    "lng": clean_float(row["lng"]),
                    "alt": clean_int(row["alt"])
                })
                session.run("""
                    MERGE (c:Circuit {circuitId: $circuitId})
                    SET c += $props
                """, circuitId=props["circuitId"], props=props)     

        # --- SEASONS (Entity Nodes) ---
        print("Importing Season Nodes...")
        with open("seasons.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                props = filter_properties({
                    "year": clean_int(row["year"])
                })
                query = "MERGE (s:Season {year: $year})"
                session.run(query, **props) # Unpacks dict into keyword arguments (year=...)

        # --- STATUS (Entity Nodes) ---
        print("Importing Status Nodes...")
        with open("status.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                props = filter_properties({
                    "statusId": clean_int(row["statusId"]),
                    "status": clean_str(row["status"])
                })
                session.run("""
                    MERGE (st:Status {statusId: $statusId})
                    SET st += $props
                """, statusId=props["statusId"], props=props)

        # --- RACES (Entity Nodes - Need to create relationships later) ---
        print("Importing Race Nodes...")
        with open("races.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                props = filter_properties({
                    "raceId": clean_int(row["raceId"]),
                    "year": clean_int(row["year"]),
                    "round": clean_int(row["round"]),
                    "name": clean_str(row["name"]),
                    "date": clean_date(row["date"]),
                    "time": clean_str(row["time"])
                })
                session.run("""
                    MERGE (r:Race {raceId: $raceId})
                    SET r += $props
                """, raceId=props["raceId"], props=props)

        # --- RESULTS (Fact Nodes - Need to create relationships later) ---
        print("Importing Result Fact Nodes...")
        with open("results.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                props = filter_properties({
                    "resultId": clean_int(row["resultId"]),
                    "number": clean_int(row["number"]),
                    "grid": clean_int(row["grid"]),
                    "position": clean_int(row["position"]),
                    "positionText": clean_str(row["positionText"]),
                    "positionOrder": clean_int(row["positionOrder"]),
                    "points": clean_float(row["points"]),
                    "laps": clean_int(row["laps"]),
                    "time": clean_str(row["time"]),
                    "milliseconds": clean_int(row["milliseconds"]),
                    "fastestLap": clean_int(row["fastestLap"]),
                    "rank": clean_int(row["rank"]),
                    "fastestLapTime": clean_str(row["fastestLapTime"]),
                    "fastestLapSpeed": clean_float(row["fastestLapSpeed"])
                })
                session.run("""
                    MERGE (res:Result {resultId: $resultId})
                    SET res += $props
                """, resultId=props["resultId"], props=props)

        # --- QUALIFYING (Fact Nodes - Need to create relationships later) ---
        print("Importing Qualifying Fact Nodes...")
        with open("qualifying.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                props = filter_properties({
                    "qualifyId": clean_int(row["qualifyId"]),
                    "number": clean_int(row["number"]),
                    "position": clean_int(row["position"]),
                    "q1": clean_str(row["q1"]),
                    "q2": clean_str(row["q2"]),
                    "q3": clean_str(row["q3"])
                })
                session.run("""
                    MERGE (q:Qualifying {qualifyId: $qualifyId})
                    SET q += $props
                """, qualifyId=props["qualifyId"], props=props)

        # --- PIT STOPS (Fact Nodes - Need to create relationships later) ---
        print("Importing PitStop Fact Nodes...")
        with open("pit_stops.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                race_id = row["raceId"]
                driver_id = row["driverId"]
                stop_num = row["stop"]
                event_id = f"{race_id}:{driver_id}:{stop_num}"

                props = filter_properties({
                    "eventId": event_id,
                    "stop": clean_int(row["stop"]),
                    "lap": clean_int(row["lap"]),
                    "time": clean_str(row["time"]),
                    "duration": clean_str(row["duration"]),
                    "milliseconds": clean_int(row["milliseconds"])
                })
                session.run("""
                    MERGE (p:PitStop {eventId: $eventId})
                    SET p += $props
                """, eventId=event_id, props=props)

    print("Knowledge Graph node creation completed successfully!")

    def resetDatabase():
        #reset the database if something went wrong'''
        with driver.session(database=DATABASE) as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared successfully!")

if __name__ == "__main__":
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connection established. Building Knowledge Graph nodes...")
        create_knowledge_graph_nodes(driver)


# with GraphDatabase.driver(URI, auth=AUTH) as driver:
#     driver.verify_connectivity()
#     print("Connection established.")