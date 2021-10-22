import sqlite3

con = sqlite3.connect("C:/Users/USER/PycharmProjects/my_window/get_data/day.db")
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
table_list = [code[0] for code in cur.fetchall()]
print(table_list)

for i, table in enumerate(table_list[4:7]):
    con.execute(f"SELECT * FROM '{table}'")
    print(f'dump중 {table} /{len(table_list)}')
    with open('day_dump.sql', 'w') as f:
        for line in con.iterdump():
            f.write('%s\n' % line)


'''
dump한 sql파일을 다시 읽어들이는 방법
다음은 가져오기를 수행할 새 데이터베이스 newdb.sqlite3을 만든다. 새 데이터베이스이므로 저장된 것이 아무것도 없는 상태이다.

sqlite3 newdb.sqlite3
$ sqlite3 newdb.sqlite3
SQLite version 3.19.3 2017-06-27 16:48:08
Enter ".help" for usage hints.
sqlite> 
그러면 .read 명령을 사용하여 파일을 가져온다.

.read ./dump.txt
sqlite> .read ./dump.txt
sqlite> 
가져오기를 수행하면 파일에 작성된 SQL 문이 순서대로 실행된다. 이번 경우에는 테이블이 2개 만들어 지고, 두개의 테이블에 데이터가 저장된다.

테이블이 작성되었는지 여부를 확인해 보면, 두 개의 테이블이 생성되어있는 것을 알 수 있다.

.tables
sqlite> .table
color  user 
sqlite> 
다음은 테이블에 데이터가 저장되어 있는지 확인한다. 두 개의 테이블에 가져오기를 한 파일에 작성된 대로 데이터가 저장되어 있다.

select * from user;
sqlite> select * from user;
devkuma|28|Seoul
kimkc|22|Busan
araikuma|32|Seoul
happykuma|23|Seoul
mykuma|23|Daejeon
sqlite> 
select * from color;
sqlite> select * from color;
1|Red
2|Blue
3|White
sqlite> 
이와 같이 데이터베이스를 덤프한 파일을 새 데이터베이스에서 가져오기를 하면 데이터베이스를 다시 구축할 수 있다.

'''
