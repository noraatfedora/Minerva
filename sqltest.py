from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
engine = create_engine('sqlite:///src/instance/college.db', echo=True)
meta = MetaData()

students = Table(
   'students', meta, 
   Column('id', Integer, primary_key = True), 
   Column('name', String), 
   Column('lastname', String) 
)

meta.create_all(engine)
engine.execute(students.insert().values(name = "n4rew", lastname="Kapoor"))
print("sddf" + str(engine.execute(students.select()).fetchall()))

meta.create_all(engine)