import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import plotly.plotly as py
import plotly.graph_objs as go
from time import sleep

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
    def __init__(self, year, name, rank, uri):
        self.year = int(year)
        self.name = name
        self.rank = int(rank)
        self.uri = uri

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.year == other.year and self.name == other.name and \
            self.rank == other.rank

    def __ne__(self, other):
        return self.year != other.year or self.name != other.name or \
            self.rank != other.rank

#base urls for IMDB and baby scraping stuff
IMDB_URL = 'http://www.imdb.com/list/ls050274118/'
BABY_BASE_URL = 'https://www.babycenter.com/top-baby-names-'
BABY_BASE_ORIGIN_URL = 'https://www.babycenter.com/'

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

#function: to clear the cache file
#inputs: none
#outputs: none
def clear_cache():
    try:
        cache_file = {}
        write_cache_file(cache_file)
        print_status("Cache file has been cleared")
    except:
        print_status("There has been an error when attempting "\
                     "to clear the cache")


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

#function: prints a message if the program is run from __main__
#purpose: to ignore any print statements when test code is run
def print_status(message):
    if __name__ == '__main__':
        print(message)

## writes out the contents of the cache file for later use
## param: the contents of the cache file
## returns: nothing
def write_cache_file(file_contents):
    try:
        with open(CACHE_FNAME,'w') as fileobj:
            json.dump(file_contents,fileobj, indent=4)
    except:
        print("Error writing cache file contents. Permission Denied")

#function: crawls all the baby name pages
#inputs: none
#outputs: none
def crawl_baby_name_pages():

    #crawl top 100 for every year since 1880
    for year in range(1880,2019):

        this_page = BABY_BASE_URL + str(year) + '.htm'

        this_scrape = None
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
        Year, Name, Rank, URI) VALUES (?,?,?,?)
    """

    record_count = 0
    for item in baby_name_list:
        record_count += 1
        parms = (item.year,item.name,item.rank, item.uri)

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
    total_this_page = 0
    for tr in all_tr:

        all_td = tr.find_all('td')
        col_pos = 0
        this_rank = 0
        this_boy_name = ''
        uri = ''
        for td in all_td:
            col_pos += 1
            if col_pos == 1:
                this_rank = td.text.strip()
            if col_pos == 3:
                this_boy_name = td.a.text.strip()
                uri = td.a['href']

        #only take the top 100, some pages show the next years top 100 and it
        # was causing duplicate records in the same year.
        total_this_page += 1
        if total_this_page <= 101:
            baby_boy = BabyName(year, this_boy_name, this_rank, uri)
            baby_names.append(baby_boy)

    return baby_names


#function: a distinct list of URIs are scraped to get the meaning and origin
#          of each baby name
#inputs: none
#outputs: none - writes to the database
def crawl_baby_name_meaning_pages():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    #used for the insert statement during cursor loop
    insert = conn.cursor()

    statement = """
        SELECT DISTINCT Name, URI
        FROM BabyNames
    """

    cur.execute(statement)

    row_counter = 0
    for row in cur:
        row_counter += 1

        #write cache file on every 30th scrape
        if row_counter % 30 == 0:
            write_cache_file(cache_file)

        baby_name_items = scrape_baby_name_meaning_page(row[0],\
                        BABY_BASE_ORIGIN_URL + row[1])


        statement = """
            INSERT INTO BabyNameOrigin (Name, Meaning, Origin) VALUES (?,?,?);
        """
        insert.execute(statement,baby_name_items)
        conn.commit()

    conn.close()

    #write the cache file when its all done
    #sleep 3 seconds first before you write the cache.. cache file is VERY large
    sleep(2)
    write_cache_file(cache_file)

def scrape_baby_name_meaning_page(name, url):

    if url not in cache_file:
        print_status("Scraping " + name + " meaning from web...")
        my_request = requests.get(url)
        html = my_request.text
        print_status("Adding html to cache...")
        cache_file[url] = html
    else:
        print_status("Scraping " + name + " meaning from cache...")
        html = cache_file[url]

    soup = BeautifulSoup(html,'html.parser')

    try:
        paragraph_tags = soup.find_all(class_='row')
        counter = 0
        name_meaning = ''
        name_origin = ''
        for item in paragraph_tags:
            p = item.find_all('p')
            for this_p in p:
                counter+=1
                if counter == 11:
                    name_meaning = this_p.text.strip()
                if counter == 12:
                    name_origin = this_p.find('a').text.strip()

        return (name,name_meaning,name_origin)
    except:
        return (name,'','')




#function: to create the table to store baby name info
#inputs: none
#outputs: none
def create_baby_name_tables():
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
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Year INTEGER,
            [Rank] INTEGER,
            Name TEXT,
            URI TEXT
        );
    """

    cur.execute(statement)
    conn.commit()


    #drop the table if it exists
    statement = """
        DROP TABLE IF EXISTS BabyNameOrigin;
    """

    cur.execute(statement)
    conn.commit()

    #create the table if it does not exist
    statement = """
        CREATE TABLE IF NOT EXISTS BabyNameOrigin (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name Text,
            Meaning Text,
            Origin Text
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

#function: produces a bar chart showing the 25 most common names that appear
# in the Top 10. The y axis is how many years it appeared in the top 10. There
# is mouseover details showing the highest rank, the average rank, the meaning
# and the origin of the name.
def bar_most_common_names():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    name_list = []
    count_list = []
    text_list = []

    statement = """
        SELECT a.Name, COUNT(*) [Total]
        , ROUND(AVG(a.Rank),1) [AvgRank]
        , MIN(a.Rank) [BestRank]
        , (SELECT z.Origin FROM BabyNameOrigin z WHERE z.Name = a.Name) [Origin]
        , (SELECT z.Meaning FROM BabyNameOrigin z WHERE z.Name = a.Name) [Meaning]
        FROM BabyNames a
        WHERE a.Rank <= 10
        GROUP BY a.Name
        ORDER BY COUNT(*) DESC ,AVG(a.Rank) ASC LIMIT 25;
    """

    cur.execute(statement)

    idx=0
    for row in cur:
        name_list.append(row[0])
        count_list.append(row[1])

        #this piece of code puts a line break in for every 10th word
        #to help with spacing
        meaning_split = row[5].split(" ")
        meaning_with_breaks = ''
        break_counter = 0
        for word in meaning_split:
            break_counter += 1
            if break_counter % 10 == 0:
                meaning_with_breaks += "<br>"
            else:
                meaning_with_breaks += word + ' '

        text_list.append('Avg Rank: ' + str(row[2]) + "<br>" +\
                         'Highest Rank: ' + str(row[3]) + "<br>" + \
                         'Origin: ' + str(row[4]) + "<br>" + \
                         'Meaning: ' + meaning_with_breaks  )
        idx+=1

    conn.close()


    data = [go.Bar(
                x=name_list,
                y=count_list,
                text=text_list,
                name="Names appearing in top 10 the most"
        )]

    layout = dict(title = 'Names appearing in the Top 10 the Most',
                  autosize = False,
                  width = 900,
                  height = 750,
                  xaxis = dict(title = 'Name'),
                  yaxis = dict(title = 'Number of Years in the Top 10'),
                  )

    fig = dict(data=data,layout=layout)
    py.plot(fig, filename='Most-Common-Names')

    print_status("Generating graph of most common names. " \
                 "This is defined as the name that appears in the top 10 " \
                 "the most.")


def line_name_trend(name_passed):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    name_proper = name_passed[:1].upper() + \
                  name_passed[1:].lower()

    year_list = []
    rank_list = []

    statement = """
        SELECT Year, Rank
        FROM BabyNames
        WHERE LOWER(Name) = ?
        ORDER BY Year ASC;
    """
    params = (name_passed.lower(),)
    cur.execute(statement,params)

    idx=0
    for row in cur:
        year_list.append(row[0])
        rank_list.append(row[1])
        idx+=1

    conn.close()

    trace0 = go.Scatter(
                x = year_list,
                y = rank_list,
                mode = 'lines',
                name = 'Name Trend for: ' + name_proper
            )

    data = [trace0]

    layout = dict(title = 'Name Trend for: ' + name_proper,
                  autosize = False,
                  width = 500,
                  height = 500,
                  xaxis = dict(title = 'Year'),
                  yaxis = dict(title = 'Rank Achieved',
                               autorange='reversed'),
                  )

    fig = dict(data=data,layout=layout)
    py.plot(fig, filename='Name-trend')

    print_status("Generating trend graph of the name " + name_proper + ". " \
                 "I'll also provide a list of actors that have that name." \
                 "Two separate browser windows will be opened.")



def table_actor_names(name_passed):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    statement = """
        SELECT FullName, Bio, Rank
        FROM Actors a
        WHERE LOWER(FirstName) = ?
    """

    params = (name_passed,)
    cur.execute(statement,params)
    actor_name = []
    rank = []
    bio = []
    for row in cur:
        actor_name.append(row[0])
        bio.append(row[2])
        rank.append(row[1])

    conn.close()

    values = [[actor_name],
            [rank],
            [bio]]

    trace0 = go.Table(
      type = 'table',
      columnorder = [1,2,3],
      columnwidth = [80,400,80],
      header = dict(
        values = [['<b>Actor Name</b>'],
                      ['<b>Bio</b>'],
                      ['<b>Rank</b>']],
        line = dict(color = '#506784'),
        fill = dict(color = '#119DFF'),
        align = ['left','left','left'],
        font = dict(color = 'white', size = 12),
        height = 40
      ),
      cells = dict(
        values = values,
        line = dict(color = '#506784'),
        fill = dict(color = ['#25FEFD', 'white']),
        align = ['left', 'left', 'left'],
        font = dict(color = '#506784', size = 12),
        height = 30
        ))

    data = [trace0]

    py.plot(data, filename = "Famous Actors")

def bubble_baby_names():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    name_list = []
    count_list = []
    highest_rank_list = []
    actors = []
    color_list = []
    statement = """
        SELECT a.Name, COUNT(*)
        , (SELECT z.FullName FROM Actors z WHERE z.FirstName = a.Name) [Actors]
        , MIN(Rank)
        FROM BabyNames a
        WHERE a.Rank <= 25
        GROUP BY a.Name
        ORDER BY COUNT(*) DESC LIMIT 50
    """

    cur.execute(statement)
    for row in cur:
        name_list.append(row[0])
        count_list.append(row[1])
        actors.append(row[2])
        highest_rank_list.append(row[3])
        if row[2] != None:
            color_list.append("Blue")
        else:
            color_list.append("Black")

    conn.close()

    #normalize the count array for sizing
    count_list = [(float(i)/max(count_list))*50 for i in count_list]

    trace0 = go.Scatter(
                x=name_list,
                y=highest_rank_list,
                text=actors,
                mode='markers',
                marker=dict(
                    color=color_list,
                    size=count_list,
                )
            )

    data = [trace0]

    layout = dict(title = 'Bubble Plot of Top 50 Names',
                  autosize = False,
                  width = 900,
                  height = 750,
                  xaxis = dict(title = 'Name'),
                  yaxis = dict(title = 'Rank Achieved',
                               autorange='reversed'),
                  )

    fig = dict(data=data,layout=layout)
    py.plot(fig, filename='Bubble')

    print_status("Generating bubble plot of top 50 names. " \
                 "Names that are shared by a Top 100 Actor will be colored blue.")


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
                create_baby_name_tables()
                crawl_baby_name_pages()
                #after all the names are written to the DB a unique list is
                #used to get the meaning and origin of each name
                crawl_baby_name_meaning_pages()

            elif user_input_1 == 'n' or user_input_1 == 'no':
                print_status("Using existing baby names table")
            else:
                print_status("Invalid command. Y/N only please.")
    else: #no records detected for the babynames, rebuild it all
        create_baby_name_tables()
        crawl_baby_name_pages()
        #after all the names are written to the DB a unique list is
        #used to get the meaning and origin of each name
        crawl_baby_name_meaning_pages()

def print_options():
    print_status("")
    print_status("Welcome to the baby name / actor name popularity final project!")
    print_status("")
    print_status("-"*25)
    print_status("COMMAND".ljust(14) + "DESCRIPTION")
    print_status("- - - - - - - - - - - - - - - - - ")
    print_status("common".ljust(14) + "Shows a bar chart of the most common names of all time")
    print_status("name".ljust(14) + "Prints line graph of all years and when the name was most popular")
    print_status("actor".ljust(14) + "Prints bubble plot of top 25 names and actors with those names")
    print_status("- - - - - - - - - - - - - - - - - ")
    print_status("clear-cache".ljust(14) + "Clears the cache file.")
    print_status("rebuild".ljust(14) + "Rebuilds all databases, and rescrapes the data.")
    print_status("help".ljust(14) + "Prints this list of commands")
    print_status("- - - - - - - - - - - - - - - - - ")

if __name__ == '__main__':

    main_program_start()

    #list of allowable commands
    quit_commands = "exit quit stop"
    available_commands = "common name actor clear-cache rebuild help"
    print_options()

    user_input_2 = 'start'
    while user_input_2 not in quit_commands:
        print_status("Enter command")
        user_input_2 = input().lower()

        user_input_list = user_input_2.split(" ")

        if user_input_list[0] in quit_commands:
            print_status("Bye!")
            exit()

        if user_input_list[0] in available_commands:
            if user_input_list[0] == 'help':
                print_options()

            if user_input_list[0] == 'clear-cache':
                clear_cache()

            if user_input_list[0] == 'rebuild':
                main_program_start()

            if user_input_list[0] == 'common':
                bar_most_common_names()

            if user_input_list[0] == 'name':
                if len(user_input_list) > 1:
                    line_name_trend(user_input_list[1])
                    table_actor_names(user_input_list[1])
                else:
                    print_status("Must supply a name after the name parameter")

            if user_input_list[0] == 'actor':
                bubble_baby_names()
        else:
            print_status("Command not found: " + user_input_list[0])
