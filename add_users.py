from views import db, models

u = models.User(nickname='john',email='john@gmail.com',role=models.ROLE_USER)
db.session.add(u)
db.session.commit()