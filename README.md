# SI507 Final Project

SI507 Final Project for Jeremy Wolverton (jjwolver).

## Prerequisites

Refer to the requirements.txt file for python package installation.

## UnitTest

This application uses UnitTest. jjwolver_final_test.py runs 8 separate tests
with various assertions to verify that aspects of the application are
built properly.

## Running the main program

1. Initial run will automatically create 3 database tables and begin scraping
   the web for the top 100 actors from IMDB. And then the top 100 baby names
   by year since 1880. And finally a unique list of names and their origin/meaning
   a. Subsequent runs will detect that the tables already exist. And will
      prompt the user if they would like to recreate the database or use the
      existing data.
2. After several minutes of scraping (if initial run or rebuild), the user
   will be taken to a menu with 3 choices.
3. The user can type "common" to produce a graph of the most common baby names.
   The user can type "name [sampleName]" to produce a line graph showing the
   popularity of that name over time. The x axis will be the year, and the
   line value will be the ranks of that corresponding year.
   The user can type "actor" to produce a bubble chart of the top 50 names.
   The size of the bubble represents the number of years the name was in the top
   50.
4. System commands (help, quit, rebuild, clear-cache)
5. Application commands (common, name <name>, actor)

## Data Sources - All through open HTTP web scraping
1. IMDB
2. BabyCenter [Top 100 names since 1880]
NOTE: All urls visited and scraped will be cached in url_cache.json

## Code Structure
1. [Import Statements for Packages used]
2. [Class Definitions]
3. [Functions]
4. [Program Start]
5. [User Interaction]

## Versioning

1.0   Initial Release

## Authors

* **Jeremy Wolverton** - *Initial work* - [jjwolver](https://github.com/jjwolver)

## Acknowledgments

* Thank you SI507 W18 teaching team! You guys worked hard all term!
