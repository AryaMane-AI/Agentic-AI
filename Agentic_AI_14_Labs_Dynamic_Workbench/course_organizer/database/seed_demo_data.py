"""Idempotently seed realistic local viva/demo records.

Safe to run repeatedly: records are matched by stable email/code/title keys.
Does not delete or reset existing user data.
"""
from __future__ import annotations
import hashlib, secrets, sqlite3
from difflib import SequenceMatcher
from pathlib import Path

DB = Path(__file__).resolve().parent / "course_organizer.db"

def _hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return salt.hex() + "$" + digest.hex()

def seed_demo_data():
    if not DB.exists():
        raise FileNotFoundError(f"Database not found: {DB}. Run database initialization first.")
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        # Ensure authentication column exists (main.py normally adds it).
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        if "password_hash" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

        def user(name, email, role, password):
            row = conn.execute("SELECT id,password_hash FROM users WHERE email=?", (email,)).fetchone()
            if row:
                uid = row["id"]
                if not row["password_hash"]:
                    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (_hash(password), uid))
            else:
                cur = conn.execute("INSERT INTO users(name,email,role,password_hash) VALUES(?,?,?,?)",
                                   (name,email,role,_hash(password)))
                uid = cur.lastrowid
            return uid

        professor_id = user("professor", "professor@gmail.com", "professor", "professor")
        students = [user(f"student{i}", f"student{i}@gmail.com", "student", f"student{i}") for i in range(1,6)]

        courses = [
            ("AI101", "Introduction to Artificial Intelligence", "Foundations of intelligent systems, search and knowledge representation."),
            ("DBMS201", "Database Management Systems", "Relational modelling, SQL, normalization and transactions."),
            ("CN301", "Computer Networks", "Network models, routing, transport and application protocols."),
            ("ML401", "Machine Learning", "Supervised learning, model evaluation and feature engineering."),
            ("CLOUD501", "Cloud Computing", "Virtualization, cloud services, deployment and monitoring."),
        ]
        course_ids = {}
        for code, name, desc in courses:
            row = conn.execute("SELECT id FROM courses WHERE course_code=?", (code,)).fetchone()
            if row:
                cid = row[0]
            else:
                cur = conn.execute("INSERT INTO courses(course_code,name,semester,description,created_by) VALUES(?,?,?,?,?)",
                                   (code,name,7,desc,professor_id))
                cid = cur.lastrowid
            course_ids[code] = cid

        # Varied enrolments across the five actual courses.
        enrolments = {"AI101": students, "DBMS201": students[:4], "CN301": students[1:],
                      "ML401": [students[0],students[2],students[4]], "CLOUD501": [students[1],students[3],students[4]]}
        for code, ids in enrolments.items():
            for sid in ids:
                conn.execute("INSERT OR IGNORE INTO course_enrollments(course_id,student_id) VALUES(?,?)", (course_ids[code],sid))

        notes = [
            ("AI101", "AI Search Algorithms", "Search strategies include breadth-first search, depth-first search, uniform-cost search and A* search. A* combines path cost with a heuristic."),
            ("DBMS201", "SQL and Normalization", "SQL supports data definition and manipulation. Normalization reduces redundancy. First, second and third normal forms address progressively stronger dependency constraints."),
            ("CN301", "TCP IP Model", "The TCP/IP model contains application, transport, internet and network-access layers. TCP provides reliable delivery; UDP provides low-overhead datagrams."),
            ("ML401", "Model Evaluation Metrics", "Classification metrics include accuracy, precision, recall and F1-score. A confusion matrix summarizes true and false predictions."),
        ]
        note_ids = {}
        for code,title,content in notes:
            row=conn.execute("SELECT id FROM notes WHERE course_id=? AND title=?",(course_ids[code],title)).fetchone()
            if row: nid=row[0]
            else:
                cur=conn.execute("INSERT INTO notes(course_id,title,current_version,created_by) VALUES(?,?,1,?)",(course_ids[code],title,professor_id)); nid=cur.lastrowid
                conn.execute("INSERT INTO note_versions(note_id,version_number,content,created_by) VALUES(?,?,?,?)",(nid,1,content,professor_id))
            note_ids[title]=nid

        assignments = [
            ("AI101", "AI Search Strategy Assignment", "Compare BFS, DFS and A* with a worked example.", 100),
            ("DBMS201", "Library Database Design", "Design a normalized relational schema for a library.", 50),
            ("ML401", "Classification Metrics Exercise", "Explain precision, recall and F1-score with a confusion matrix.", 50),
        ]
        assignment_ids={}
        for code,title,desc,marks in assignments:
            row=conn.execute("SELECT id FROM assignments WHERE course_id=? AND title=?",(course_ids[code],title)).fetchone()
            if row: aid=row[0]
            else:
                cur=conn.execute("INSERT INTO assignments(course_id,title,description,deadline,max_marks,created_by) VALUES(?,?,?,?,?,?)",
                                 (course_ids[code],title,desc,"2030-12-31T23:59:00",marks,professor_id)); aid=cur.lastrowid
            assignment_ids[code]=aid

        # Five submissions for the AI assignment, including a deliberately similar pair.
        texts = [
            "Breadth first search explores nodes level by level using a queue. Depth first search follows a branch using a stack. A star selects nodes using path cost plus heuristic estimate.",
            "Breadth first search explores nodes level by level using a queue. Depth first search follows one branch using a stack. A star uses path cost and a heuristic estimate to select nodes.",
            "BFS uses a queue and visits vertices by increasing distance. DFS explores deeply before backtracking. A* ranks paths using g(n) plus h(n).",
            "Search algorithms solve state-space problems. Uniform cost search expands the lowest accumulated path cost, while greedy search uses a heuristic.",
            "A* is an informed search technique. It evaluates f(n) as g(n) plus h(n), where g is the cost so far and h estimates the remaining cost.",
        ]
        submission_ids=[]
        for sid, content in zip(students,texts):
            row=conn.execute("SELECT id FROM submissions WHERE assignment_id=? AND student_id=?",(assignment_ids["AI101"],sid)).fetchone()
            if row: subid=row[0]
            else:
                cur=conn.execute("INSERT INTO submissions(assignment_id,student_id,content,status) VALUES(?,?,?,'submitted')",(assignment_ids["AI101"],sid,content)); subid=cur.lastrowid
            submission_ids.append(subid)

        # Similarity scores are calculated from the actual seeded submission text.
        for i in range(len(submission_ids)):
            for j in range(i+1,len(submission_ids)):
                a=conn.execute("SELECT content FROM submissions WHERE id=?",(submission_ids[i],)).fetchone()[0]
                b=conn.execute("SELECT content FROM submissions WHERE id=?",(submission_ids[j],)).fetchone()[0]
                score=round(SequenceMatcher(None,a.lower(),b.lower()).ratio()*100,2)
                exists=conn.execute("SELECT id FROM similarity_reports WHERE submission_id=? AND compared_submission_id=?",(submission_ids[i],submission_ids[j])).fetchone()
                if not exists:
                    conn.execute("INSERT INTO similarity_reports(submission_id,compared_submission_id,similarity_score,details) VALUES(?,?,?,?)",
                                 (submission_ids[i],submission_ids[j],score,"Seeded demo comparison; score computed from normalized submission text."))

        # Draft grades let the professor demonstrate the grade -> approve -> publish workflow.
        for sid, subid, marks in zip(students[:3], submission_ids[:3], [88,84,92]):
            row=conn.execute("SELECT id FROM grades WHERE submission_id=?",(subid,)).fetchone()
            if not row:
                conn.execute("INSERT INTO grades(submission_id,marks,feedback,status,graded_by) VALUES(?,?,?,'draft',?)",
                             (subid,marks,"Demo draft grade; review before approval and publication.",professor_id))

        conn.commit()
        return {"students":len(students),"courses":len(courses),"notes":len(notes),"assignments":len(assignments),
                "submissions":len(submission_ids),"similarity_pairs":10,"professor":"professor@gmail.com"}
    finally:
        conn.close()

if __name__ == "__main__":
    print(seed_demo_data())
