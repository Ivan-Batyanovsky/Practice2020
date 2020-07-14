import numpy as np
import pandas as pd
import pymysql

conn = pymysql.connect(host="127.0.0.1", user="root", passwd="Eszqsc1234", db="mysql", use_unicode=True, charset="utf8")
cur = conn.cursor()
cur.execute("USE scraping")

results = pd.read_sql_query("SELECT * FROM protNews", conn)
results.to_csv("output_with_sport.csv", index=False, index_label="id")