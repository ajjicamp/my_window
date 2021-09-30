import sqlite3
# DB 생성 (오토 커밋)
conn = sqlite3.connect("test.db", isolation_level=None)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS table1 \
    (id integer PRIMARY KEY, name text, birthday text)")

test_tuple = (
    (3, 'PARK', '1991-00-00'),
    (4, 'CHOI', '1999-00-00'),
    (5, 'JUNG', '1989-00-00')
)
# c.executemany("INSERT INTO table1(id, name, birthday) VALUES(?,?,?)", test_tuple)

c.execute("SELECT * FROM table1")
print(c.fetchone())
print(c.fetchone())
print(c.fetchall())

c.execute("SELECT * FROM table1")
print(c.fetchall())

# 방법 1
c.execute("SELECT * FROM table1")
for row in c.fetchall():
    print(row)

# 방법 2
for row in c.execute("SELECT * FROM table1 ORDER BY id ASC"):
    print(row)

param1='3'
c.execute("SELECT * FROM table1 WHERE id=?", param1)
print('where', c.fetchall())

param2='4'
# c.execute("SELECT * FROM table1 WHERE id='%s'" % param2)
c.execute("SELECT * FROM table1 WHERE id=:ID", {"ID":5})
print('where', c.fetchall())

c.execute("UPDATE table1 SET name=? WHERE id=?", ('NEW1', 4))
# 방법 2
c.execute("UPDATE table1 SET name=:name WHERE id=:id", {"name": 'NEW2', 'id': 3})
# 방법 3
c.execute("UPDATE table1 SET name='%s' WHERE id='%s'" % ('NEW3', 5))
# 확인
for row in c.execute('SELECT * FROM table1'):
    print(row)
c.execute("SELECT * FROM table1")
print('all', c.fetchall())
