from jjwolver_final import *
import unittest

class TestActorClass(unittest.TestCase):

    def test_class_creation(self):
        actor_class = Actor("Will Smith","A good actor","He was in Independence Day",100)
        self.assertEqual(actor_class.first_name,"Will")
        self.assertEqual(actor_class.rank,100)
        self.assertEqual(actor_class.bio,"A good actor")
        self.assertEqual(actor_class.details,"He was in Independence Day")

    def test_list_length(self):
        actor_list = scrape_imdb()
        self.assertEqual(len(actor_list), 100)

    def test_specific_actors_from_list(self):
        actor_list = scrape_imdb()
        #this tests that the first name of the top most actor in the list is
        #jack (Jack Nicholson)
        self.assertEqual(actor_list[0].first_name,"Jack")

        #this tests that the full name of the 57th most popular actor is in
        #fact Michael Douglas
        self.assertEqual(actor_list[56].full_name,"Michael Douglas")

class TestActorDatabase(unittest.TestCase):

    def test_row_count_actor(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        statement = """
            SELECT COUNT(*) FROM Actors;
        """

        cur.execute(statement)
        for row in cur:
            row_count = row[0]
        conn.close()

        self.assertEqual(row_count,100)

class TestBabyNameClass(unittest.TestCase):
    def test_class_creation(self):
        baby_class = BabyName(2018, 'Jeremy', 1)

        self.assertEqual(baby_class.year,2018)
        self.assertEqual(baby_class.rank,1)
        self.assertEqual(baby_class.name,"Jeremy")

class TestBabyDatabase(unittest.TestCase):

    def test_row_count_baby(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        statement = """
            SELECT COUNT(*) FROM BabyNames;
        """

        cur.execute(statement)
        for row in cur:
            row_count = row[0]
        conn.close()

        #test that there is more than 5000 rows
        self.assertGreater(row_count,5000)



if __name__ == '__main__':
    unittest.main()
