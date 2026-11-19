# Demo accounts and academic seed data

The local demo database contains five student accounts. Each student's login name and password match:

| Student | Email | Password |
|---|---|---|
| student1 | student1@gmail.com | student1 |
| student2 | student2@gmail.com | student2 |
| student3 | student3@gmail.com | student3 |
| student4 | student4@gmail.com | student4 |
| student5 | student5@gmail.com | student5 |

Professor login: `professor@gmail.com` / `professor`.

Seeded courses: AI101 Introduction to Artificial Intelligence; DBMS201 Database Management Systems; CN301 Computer Networks; ML401 Machine Learning; CLOUD501 Cloud Computing.

The database includes varied enrolments, four notes, three assignments, five submissions, pairwise submission similarity reports, and draft grades. Similarity reports are calculated from the seeded submission text using Python's `difflib.SequenceMatcher`; they are indicators for human review, not plagiarism verdicts.

The seed script is idempotent and does not clear user data. Run it with `python -m course_organizer.database.seed_demo_data`.
