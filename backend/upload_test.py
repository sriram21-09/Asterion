from app.database.session import SessionLocal
from app.services.import_service import CDRImportService

db = SessionLocal()
with open('/app/datasets/sample/Import - 9714499703_Airtel.csv', 'rb') as f:
    res = CDRImportService().process_upload(
        'Import - 9714499703_Airtel.csv', 
        f.read(), 
        None, 
        'auto', 
        db
    )
print(res['summary'])
