from app.core.firebase import db

doc_ref = db.collection('data').document()
doc_ref.set({'date': '2020-03-31', 'value': 1732064000000, 'memo': 'test'})
print("write success:", doc_ref.id)

doc = doc_ref.get()
print("read success:", doc.to_dict())