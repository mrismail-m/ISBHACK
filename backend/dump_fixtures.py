import os
import json
from sqlmodel import Session, select
from app.db import engine
from app.models.core import User, Assessment
from app.schemas.core import UserSchema, AssessmentSchema

def dump():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        assessments = session.exec(select(Assessment)).all()
        
        user_schemas = [UserSchema.model_validate(u, from_attributes=True) for u in users]
        assessment_schemas = [AssessmentSchema.model_validate(a, from_attributes=True) for a in assessments]
        
        os.makedirs("../fixtures/api", exist_ok=True)
        
        with open("../fixtures/api/users.json", "w") as f:
            f.write(json.dumps([u.model_dump(mode='json') for u in user_schemas], indent=2))
            
        with open("../fixtures/api/assessments.json", "w") as f:
            f.write(json.dumps([a.model_dump(mode='json') for a in assessment_schemas], indent=2))

if __name__ == "__main__":
    dump()
