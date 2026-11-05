import dotenv
import os
import neo4j
from neo4j import GraphDatabase

# from neo4j.debug import watch

# watch("neo4j")

load_status = dotenv.load_dotenv("config.txt", override=True)
if load_status is False:
    raise RuntimeError('Environment variables not loaded.')

URI = os.getenv("URI")
AUTH = (os.getenv("USERNAME"), os.getenv("PASSWORD"))
print(URI)
print(AUTH)

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Connection established.")