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
    """Removes keys with None values (missing values or \N) so they are omitted from the node/relationship."""
    return {k: v for k, v in props_dict.items() if v is not None}

integers = {
    "driverId",      # Driver entity node
    "number",        # Driver, Result, and Qualifying nodes
    "constructorId", # Constructor entity node
    "circuitId",     # Circuit entity node
    "alt",           # Circuit entity node
    "year",          # Season and Race entity nodes
    "round",         # Race entity node
    "statusId",      # Status entity node
    "raceId",        # Race entity node
    "resultId",      # Result fact node
    "grid",          # Result fact node
    "position",      # Result and Qualifying fact nodes
    "positionOrder", # Result fact node
    "laps",          # Result fact node
    "milliseconds",  # Result and PitStop fact nodes
    "fastestLap",    # Result fact node
    "rank",          # Result fact node
    "qualifyId",     # Qualifying fact node
    "stop",          # PitStop fact node
    "lap"            # PitStop fact node
}

floats = {
    "points",           # Result fact node
    "lat",              # Circuit entity node
    "lng",              # Circuit entity node
    "fastestLapSpeed"   # Result fact node
}

strings = {
    # Driver entity node
    "driverRef",
    "code",
    "forename",
    "surname",
    "nationality",
    
    # Constructor entity node
    "constructorRef",
    "constructor_name",
    "constructor_nationality",
    
    # Circuit entity node
    "circuitRef",
    "circuit_name",
    "circuit_loc",
    "circuit_country",
    
    # Status entity node
    "status",
    
    # Race entity node
    "name",
    "time",         # Also used in Result and PitStop
    
    # Result fact node
    "positionText",
    "fastestLapTime",
    
    # Qualifying fact node
    "q1",
    "q2",
    "q3",
    
    # PitStop fact node
    "eventId",
    "duration"
}

dates = {
    "dob",   # Driver entity node
    "date"   # Race entity node
}




with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Connection established.")