import requests
from bs4 import BeautifulSoup
import json
import sqlite3

#classes
class Actor():
    def __init__(self, full_name, bio, details, rank):
        self.full_name = full_name
        self.first_name = full_name.split(" ")[0]
        self.bio = bio
        self.details = details
        self.rank = rank

    def __str__(self):
        return self.full_name


#base urls
IMDB_URL = 'http://www.imdb.com/list/ls050274118/'
BABY_BASE_URL = 'https://www.babycenter.com/top-baby-names-'

#cache file check
CACHE_FNAME = 'url_cache.json'

#database details
DB_NAME = "jjwolver_final.sqlite"

try:
    file_obj = open(CACHE_FNAME, 'r')
    cache_contents = file_obj.read()
    cache_file = json.loads(cache_contents)
    file_obj.close()
# if there was no file, no worries. There will be soon!
except:
    cache_file = {}

#function: prints a message if the program is run from __main_
def print_status(message):
    if __name__ == '__main__':
        print(message)

## writes out the contents of the cache file for later use
## param: the contents of the cache file
## returns: nothing
def write_cache_file(file_contents):
    with open(CACHE_FNAME,'w') as fileobj:
        json.dump(file_contents,fileobj, indent=4)

#function: scrapes the IMDB top 100 actors of all time page
#inputs: None
#returns: list of actor classes
def scrape_imdb():
    actors = []

    if IMDB_URL not in cache_file:
        print("Scraping IMDB from web...")
        my_request = requests.get(IMDB_URL)
        html = my_request.text
        print_status("Adding html to cache...")
        cache_file[IMDB_URL] = html
        write_cache_file(cache_file)
    else:
        print_status("Scraping IMDB from cache...")
        html = cache_file[IMDB_URL]

    soup = BeautifulSoup(html,'html.parser')

    actor_content = soup.find_all(class_='lister-item-content')
    ability_content = soup.find_all(class_='list-description')

    x=0 #storing actor ability first
    ability_content_list = []
    for item in ability_content:
        #skip first p tag
        if x > 0:
            ability_details = ''
            p = item.find('p')
            ability_details = p.text.strip()
            ability_content_list.append(ability_details)

        x+=1

    x=0
    for item in actor_content:

        #actors full name and first name
        a = item.find('a')
        full_name = a.text.strip()
        first_name = full_name.split(" ")[0]

        #get bio (second paragraph tag)
        bio = ''
        all_p = item.find_all('p')
        p_count = 0
        for p in all_p:
            p_count += 1
            if p_count == 2:
                bio = p.text.strip()

        #create the actor class
        new_actor = Actor(full_name, bio, ability_content_list[x], str(x+1))

        #increment index
        x+=1

        actors.append(new_actor)

    return actors

def create_actor_table():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    print_status("Preparing Actors table...")

    #drop the table if it exists
    statement = """
        DROP TABLE IF EXISTS Actors;
    """

    cur.execute(statement)
    conn.commit()

    #create the table if it does not exist
    statement = """
        CREATE TABLE IF NOT EXISTS Actors (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            FullName TEXT,
            FirstName TEXT,
            Bio TEXT,
            Details TEXT,
            [Rank] INTEGER
        );
    """

    cur.execute(statement)
    conn.commit()

    #close the connection
    conn.close()

def load_actor_data(actor_list):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    print_status("Populating Actors table...")

    statement = """
        INSERT INTO Actors (
        FullName, FirstName, Bio, Details, Rank) VALUES (?,?,?,?,?)
    """

    actor_count = 0
    for item in actor_list:
        actor_count += 1
        parms = (item.full_name,item.first_name,\
                 item.bio, item.details,item.rank)
        cur.execute(statement,parms)
        conn.commit()

    conn.close()

    print_status("Added " + str(actor_count) + " actors to database...")

if __name__ == '__main__':

    #scrape IMDB and create a list of actor classes
    top_100_actors = scrape_imdb()

    #create the actors table and load the data
    create_actor_table()
    load_actor_data(top_100_actors)
