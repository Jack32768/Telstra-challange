__author__ = 'Jack'

import sqlite3

def main ():
    try:
        db = sqlite3.connect('M2M.db')
        cursor = db.cursor()

        id = cursor.execute('SELECT id FROM records')
        index = id.fetchall()
        print type(index)
        print index
        print len(index)
        for i in range(len(index)):
            cursor.execute("DELETE FROM records WHERE id=?", index[i])
        print "DB cleared!"
    except:
        print "Database already empty or something wrong"


db.commit()
db.close()