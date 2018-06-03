import csv, sqlite3

con = sqlite3.connect("weather")
cur = con.cursor()
cur.execute("CREATE IF NOT EXISTS TABLE W0750 (lat, long, windSpeed, windDirection);")

with open("ws_0_750.csv","r") as f:
    dr = csv.DictReader(f, delimiter=" ")
    to_db_s = [(i['Latitude'], i['Longitude'], i['Value']) for i in dr]
with open("wdir_0_750.csv","r") as f:
    dr = csv.DictReader(f, delimiter=" ")
    to_db_dir = [(i['Latitude'], i['Longitude'], i['Value']) for i in dr]

to_db = [(to_db_s[i][0], to_db_s[i][1], to_db_s[i][2], to_db_dir[i][2]) for i in range(len(to_db_s))]

cur.executemany("INSERT INTO W0750 (long, lat, windSpeed, windDirection) VALUES (?,?,?,?);", to_db)
con.commit()
con.close()
