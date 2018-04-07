import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import plotly.plotly as py
import plotly.graph_objs as go

#classes for an Actor and a baby name. Probably not necessary to create for this
#, but man, I'm trying to demonstrate all the fun things I've learned!!!!
class Actor():
    def __init__(self, full_name, bio, details, rank):
        self.full_name = full_name
        self.first_name = full_name.split(" ")[0]
        self.bio = bio
        self.details = details
        self.rank = rank

    def __str__(self):
        return self.full_name

class BabyName():
    def __init__(self, year, name, rank):
        self.year = int(year)
        self.name = name
        self.rank = int(rank)

    def __str__(self):
        return self.name

#base urls for IMDB and baby scraping stuff
IMDB_URL = 'http://www.imdb.com/list/ls050274118/'
BABY_BASE_URL = 'https://www.babycenter.com/top-baby-names-'
#cache file name
CACHE_FNAME = 'url_cache.json'
#database details
DB_NAME = "jjwolver_final.sqlite"

try: #to check the cache file to see if it exists
    file_obj = open(CACHE_FNAME, 'r')
    cache_contents = file_obj.read()
    cache_file = json.loads(cache_contents)
    file_obj.close()
# if there was no file, no worries. There will be soon!
except:
    cache_file = {}

#function: to check the status of the database, to see if it needs to be
#          created or if we should use existing data
def check_db_status():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    try:
        statement = """
            SELECT COUNT(*) FROM Actors;
        """
        cur.execute(statement)
        actor_record_count = 0
        for row in cur:
            actor_record_count = row[0]
    except:
        actor_record_count = 0

    try:
        statement = """
            SELECT COUNT(*) FROM BabyNames;
        """
        cur.execute(statement)
        baby_record_count = 0
        for row in cur:
            baby_record_count = row[0]
    except:
        baby_record_count = 0

    conn.close()

    return (actor_record_count,baby_record_count)

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

def crawl_baby_name_pages():

    #crawl top 100 for every year since 1880
    for year in range(1880,2019):
        this_page = BABY_BASE_URL + str(year) + '.htm'
        this_scrape = scrape_baby_name_page(this_page,year)

        #add these to the baby table
        load_baby_name_data(this_scrape)

        #write cache file on every 10th scrape
        if year % 10 == 0:
            write_cache_file(cache_file)

    #write the cache file when its all done
    write_cache_file(cache_file)

#function: inserts data into baby name table
#inputs: list of BabyName class
#returns: nothing, nada, zip, zilch
def load_baby_name_data(baby_name_list):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    statement = """
        INSERT INTO BabyNames (
        Year, Name, Rank) VALUES (?,?,?)
    """

    record_count = 0
    for item in baby_name_list:
        record_count += 1
        parms = (item.year,item.name,item.rank)

        if item.rank > 0:
            cur.execute(statement,parms)
            conn.commit()

    conn.close()


#function: scrapes a baby name page
#inputs: page_url
#returns: list of boy names
def scrape_baby_name_page(url_path, year):
    baby_names = []

    if url_path not in cache_file:
        my_request = requests.get(url_path)
        html = my_request.text
        print_status("Adding html to cache for baby names in " + str(year) + "...")
        cache_file[url_path] = html
    else:
        print_status("Scraping baby names from cache for " + str(year) + "...")
        html = cache_file[url_path]

    soup = BeautifulSoup(html,'html.parser')

    #find all table rows
    all_tr = soup.find_all('tr')

    #find all table columns within each row
    for tr in all_tr:
        all_td = tr.find_all('td')
        col_pos = 0
        this_rank = 0
        this_boy_name = ''
        for td in all_td:
            col_pos += 1
            if col_pos == 1:
                this_rank = td.text.strip()
            if col_pos == 3:
                this_boy_name = td.a.text.strip()
        baby_boy = BabyName(year, this_boy_name, this_rank)
        baby_names.append(baby_boy)

    return baby_names





#function: to create the table to store baby name info
#inputs: none
#outputs: none
def create_baby_name_table():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    print_status("Preparing BabyNames table...")

    #drop the table if it exists
    statement = """
        DROP TABLE IF EXISTS BabyNames;
    """

    cur.execute(statement)
    conn.commit()

    #create the table if it does not exist
    statement = """
        CREATE TABLE IF NOT EXISTS BabyNames (
            Year INTEGER,
            [Rank] INTEGER,
            Name TEXT
        );
    """

    cur.execute(statement)
    conn.commit()

    #close the connection
    conn.close()












#function: scrapes the IMDB top 100 actors of all time page
#inputs: None
#returns: list of actor classes
def scrape_imdb():
    actors = []

    if IMDB_URL not in cache_file:
        print_status("Scraping IMDB from web...")
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

#function: to create the data table and structure to store the data about
#          the top 100 actors
# inputs: none
# outputs: none
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

#function: to insert the records for the top 100 male actors of all time
#          as voted on my IMDB community.
#inputs: a list of actors (scraped from IMDB)
#outputs: none
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


def plot_most_common_names():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    name_list = []
    count_list = []

    print_status("Gathering most popular baby " \
                 "name data (Most times appeared in top 10)")
    statement = """
        SELECT Name, COUNT(*) [Total]
        FROM BabyNames
        GROUP BY Name
        HAVING Rank <= 10
        ORDER BY COUNT(*) DESC;
    """

    cur.execute(statement)

    idx=0
    for row in cur:
        name_list.append(row[0])
        count_list.append(row[1])
        idx+=1

    conn.close()


    data = [go.Bar(
                x=name_list,
                y=count_list
        )]

    print_status("Loading plotly graph")
    py.plot(data, filename='Most-Common-Names')


def main_program_start():
    db_status = check_db_status()

    print_status("**********************ACTORS TABLE**************************")
    if db_status[0] > 0:
        print_status("Actors table detected with " + str(db_status[0]) + " records.")
        user_input_1 = "start"
        while user_input_1 not in 'yes no':
            user_input_1 = ""
            print_status("Would you like to rebuild the actors table? Y/N")
            user_input_1 = input().lower()

            if user_input_1 == 'y' or user_input_1 == 'yes':
                #scrape IMDB and create a list of actor classes
                top_100_actors = scrape_imdb()

                # create the actors table and load the data
                create_actor_table()
                load_actor_data(top_100_actors)

            elif user_input_1 == 'n' or user_input_1 == 'no':
                print_status("Using existing actors table")
            else:
                print_status("Invalid command. Y/N only please.")
    else: #no records detected for the actors, rebuild it all
        #scrape IMDB and create a list of actor classes
        top_100_actors = scrape_imdb()

        # create the actors table and load the data
        create_actor_table()
        load_actor_data(top_100_actors)

    print_status("**********************BABY NAMES TABLE**************************")
    if db_status[1] > 0:
        print_status("BabyNames table detected with " + str(db_status[1]) + " records.")
        user_input_1 = "start"
        while user_input_1 not in 'yes no':
            user_input_1 = ""
            print_status("Would you like to rebuild the baby names table? Y/N")
            user_input_1 = input().lower()

            if user_input_1 == 'y' or user_input_1 == 'yes':
                create_baby_name_table()
                crawl_baby_name_pages()

            elif user_input_1 == 'n' or user_input_1 == 'no':
                print_status("Using existing baby names table")
            else:
                print_status("Invalid command. Y/N only please.")
    else: #no records detected for the babynames, rebuild it all
        create_baby_name_table()
        crawl_baby_name_pages()



if __name__ == '__main__':

    plot_most_common_names()
