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
        self.assertEqual(actor_list[0].first_name,"Jack")
        self.assertEqual(actor_list[56].full_name,"Michael Douglas")

class TestActorDatabase(unittest.TestCase):

    def test_row_count(self):
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




if __name__ == '__main__':
    unittest.main()
