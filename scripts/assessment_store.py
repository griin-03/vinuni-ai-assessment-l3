"""Additive storage for authored papers, immutable releases and scheduled rooms."""


def migrate(db, now):
    db.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY,name TEXT NOT NULL,applied_at TEXT NOT NULL)')
    if db.execute('SELECT 1 FROM schema_migrations WHERE version=2').fetchone():
        return
    if not db.in_transaction:
        db.execute('BEGIN IMMEDIATE')
    if db.execute('SELECT 1 FROM schema_migrations WHERE version=2').fetchone():
        return
    statements = [
        '''CREATE TABLE assessment_papers(id INTEGER PRIMARY KEY,owner_id INTEGER NOT NULL REFERENCES users(id),title TEXT NOT NULL,description TEXT NOT NULL,subject TEXT NOT NULL,grade INTEGER NOT NULL,items TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'draft',created_at TEXT NOT NULL,updated_at TEXT NOT NULL)''',
        '''CREATE TABLE assessment_releases(id INTEGER PRIMARY KEY,paper_id INTEGER NOT NULL UNIQUE REFERENCES assessment_papers(id),owner_id INTEGER NOT NULL REFERENCES users(id),title TEXT NOT NULL,description TEXT NOT NULL,subject TEXT NOT NULL,grade INTEGER NOT NULL,items TEXT NOT NULL,content_hash TEXT NOT NULL,created_at TEXT NOT NULL)''',
        "CREATE TRIGGER assessment_release_immutable BEFORE UPDATE ON assessment_releases BEGIN SELECT RAISE(ABORT,'Released papers are immutable'); END",
        "CREATE TRIGGER assessment_release_no_delete BEFORE DELETE ON assessment_releases BEGIN SELECT RAISE(ABORT,'Released papers cannot be deleted'); END",
        "ALTER TABLE exams ADD COLUMN release_id INTEGER REFERENCES assessment_releases(id)",
        "ALTER TABLE exams ADD COLUMN owner_id INTEGER REFERENCES users(id)",
        "ALTER TABLE exams ADD COLUMN starts_at REAL NOT NULL DEFAULT 0",
        "ALTER TABLE exams ADD COLUMN result_policy TEXT NOT NULL DEFAULT 'immediate'",
        "ALTER TABLE exams ADD COLUMN request_key TEXT",
        "ALTER TABLE exams ADD COLUMN request_hash TEXT",
        "CREATE UNIQUE INDEX assessment_room_request ON exams(owner_id,request_key) WHERE request_key IS NOT NULL",
        "ALTER TABLE attempts ADD COLUMN revision INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE attempts ADD COLUMN pass_score_snapshot INTEGER",
        "ALTER TABLE attempts ADD COLUMN title_snapshot TEXT",
        "ALTER TABLE attempts ADD COLUMN submission_reason TEXT",
        "CREATE INDEX assessment_paper_owner ON assessment_papers(owner_id)",
        "CREATE INDEX assessment_room_owner ON exams(owner_id,release_id)",
        "CREATE INDEX attempt_expiry ON attempts(deadline) WHERE submitted_at IS NULL",
        "UPDATE attempts SET pass_score_snapshot=(SELECT pass_score FROM exams WHERE exams.id=attempts.exam_id),title_snapshot=(SELECT title FROM exams WHERE exams.id=attempts.exam_id)",
    ]
    for statement in statements:
        db.execute(statement)
    db.execute('INSERT INTO schema_migrations VALUES(2,?,?)', ('assessment-papers-and-rooms', now))
