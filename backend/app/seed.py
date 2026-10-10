import argparse
from datetime import UTC, datetime

from sqlmodel import Session, SQLModel

from app.db import create_db_and_tables, engine
from app.models.core import Assessment, Classroom, User


def seed_db():
    create_db_and_tables()
    with Session(engine) as session:
        # Create users
        teacher = User(id="u_teacher_1", name="Mr. Smith", role="teacher", classroom_id="cl_1")
        session.add(teacher)
        
        # 12 students
        for i in range(1, 13):
            student = User(id=f"u_student_{i}", name=f"Student {i}", role="student", classroom_id="cl_1")
            session.add(student)
            
        classroom = Classroom(id="cl_1", name="CS101", teacher_id="u_teacher_1")
        session.add(classroom)
        
        # Assessments
        rubric = {
            "criteria": [
                {
                    "id": "c1",
                    "name": "Concept accuracy",
                    "description": "Explains what a collision is and why it happens, correctly.",
                    "max_marks": 5,
                    "topic": "hashing",
                    "levels": ["Absent or wrong", "Mentions the idea, mostly inaccurate", "Partly correct with clear gaps", "Mostly correct, minor gaps", "Correct, complete and precise"]
                },
                {
                    "id": "c2",
                    "name": "Resolution strategies",
                    "description": "Describes chaining and open addressing.",
                    "max_marks": 5,
                    "topic": "collisions",
                    "levels": ["Absent or wrong", "Mentions one strategy vaguely", "Describes one well, or both vaguely", "Describes both mostly correctly", "Describes both accurately and clearly"]
                },
                {
                    "id": "c3",
                    "name": "Complexity analysis",
                    "description": "Analyzes time complexity correctly.",
                    "max_marks": 5,
                    "topic": "complexity",
                    "levels": ["Absent or wrong", "Mentions O(1) without context", "Partly explains average vs worst case", "Good explanation with minor gaps", "Clear distinction between average and worst case"]
                },
                {
                    "id": "c4",
                    "name": "Communication",
                    "description": "Writing is clear and structured.",
                    "max_marks": 5,
                    "topic": "communication",
                    "levels": ["Unreadable", "Hard to follow", "Readable but poorly structured", "Clear and mostly well structured", "Excellent structure and clarity"]
                }
            ]
        }
        
        a1 = Assessment(
            id="a_1",
            classroom_id="cl_1",
            kind="assignment",
            title="A1: Hash table collisions",
            instructions_md="Explain how a hash table handles collisions in about 300 words.",
            max_marks=20.0,
            pass_mark_pct=50.0,
            rubric=rubric,
            model_answer_md=None,
            strictness="normal",
            viva_enabled=True,
            viva_weight=0.3,
            viva_question_count=3,
            viva_time_limit_s=90,
            feedback_mode="full",
            release_mode="after_approval",
            ai_policy="allowed_with_disclosure",
            paste_flag_chars=500,
            topics=["hashing", "collisions", "complexity", "communication"],
            status="open",
            due_at=datetime(2026, 10, 12, 18, 0, 0, tzinfo=UTC),
            created_at=datetime(2026, 10, 10, 5, 0, 0, tzinfo=UTC)
        )
        session.add(a1)
        
        # 3 completed earlier assessments
        for i in range(2, 5):
            past_a = Assessment(
                id=f"a_{i}",
                classroom_id="cl_1",
                kind="assignment",
                title=f"Past Assignment {i}",
                instructions_md="Instructions",
                max_marks=20.0,
                pass_mark_pct=50.0,
                rubric=rubric,
                strictness="normal",
                viva_enabled=True,
                viva_weight=0.3,
                viva_question_count=3,
                viva_time_limit_s=90,
                feedback_mode="full",
                release_mode="after_approval",
                ai_policy="allowed_with_disclosure",
                paste_flag_chars=500,
                topics=["hashing"],
                status="closed",
                due_at=datetime(2026, 9, 10 + i, 18, 0, 0, tzinfo=UTC),
                created_at=datetime(2026, 9, 1 + i, 5, 0, 0, tzinfo=UTC)
            )
            session.add(past_a)
            
        session.commit()
        print("Database seeded successfully.")

def reset_db():
    SQLModel.metadata.drop_all(engine)
    seed_db()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset database before seeding")
    args = parser.parse_args()
    
    if args.reset:
        reset_db()
    else:
        seed_db()
