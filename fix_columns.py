
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('ALTER TABLE tags ADD COLUMN price VARCHAR(20)')
cur.execute('ALTER TABLE tags ADD COLUMN source VARCHAR(50)')
conn.commit()
print('Columns added!')
conn.close()

