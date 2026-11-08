"""Versioned, additive migration for the grounded question authoring slice."""
import json
from pathlib import Path
from rag_domain import chunk_text, digest

ROOT = Path(__file__).resolve().parents[1]

SCHEMA = [
    'CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY,name TEXT NOT NULL,applied_at TEXT NOT NULL)',
    '''CREATE TABLE knowledge_documents(id INTEGER PRIMARY KEY,title TEXT NOT NULL,category TEXT NOT NULL,department_id INTEGER REFERENCES departments(id),owner_id INTEGER REFERENCES users(id),status TEXT NOT NULL DEFAULT 'active',current_version_id INTEGER,sample_key TEXT UNIQUE,created_at TEXT NOT NULL)''',
    '''CREATE TABLE knowledge_versions(id INTEGER PRIMARY KEY,document_id INTEGER REFERENCES knowledge_documents(id),version INTEGER NOT NULL,content TEXT NOT NULL,content_hash TEXT NOT NULL,effective_from TEXT NOT NULL,confirmed_by INTEGER REFERENCES users(id),created_at TEXT NOT NULL,UNIQUE(document_id,version))''',
    '''CREATE TABLE knowledge_chunks(id INTEGER PRIMARY KEY,version_id INTEGER REFERENCES knowledge_versions(id),start INTEGER NOT NULL,end INTEGER NOT NULL,text TEXT NOT NULL,heading TEXT NOT NULL,line_start INTEGER NOT NULL,line_end INTEGER NOT NULL,risk_flags TEXT NOT NULL)''',
    '''CREATE VIRTUAL TABLE knowledge_fts USING fts5(text,tokenize='unicode61 remove_diacritics 2')''',
    '''CREATE TABLE ai_jobs(id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),request_key TEXT NOT NULL,request_hash TEXT NOT NULL,request TEXT NOT NULL,status TEXT NOT NULL,decision TEXT NOT NULL DEFAULT '',message TEXT NOT NULL DEFAULT '',sources TEXT NOT NULL DEFAULT '[]',provider TEXT NOT NULL,model TEXT NOT NULL DEFAULT '',prompt_version TEXT NOT NULL,usage TEXT NOT NULL DEFAULT '{}',lease_token TEXT,lease_until REAL,run_count INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,finished_at TEXT,UNIQUE(user_id,request_key))''',
    '''CREATE TABLE ai_items(id INTEGER PRIMARY KEY,job_id INTEGER REFERENCES ai_jobs(id),ordinal INTEGER NOT NULL,question TEXT NOT NULL,options TEXT NOT NULL,correct INTEGER,category TEXT NOT NULL,citations TEXT NOT NULL,validation TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'needs_review',revision INTEGER NOT NULL DEFAULT 0,reviewer_id INTEGER REFERENCES users(id),review_comment TEXT NOT NULL DEFAULT '',question_id INTEGER REFERENCES questions(id),reviewed_at TEXT,UNIQUE(job_id,ordinal))''',
    'CREATE INDEX knowledge_chunk_version ON knowledge_chunks(version_id)',
    'CREATE INDEX ai_job_queue ON ai_jobs(status,lease_until)',
    'CREATE INDEX ai_item_job ON ai_items(job_id)',
    "CREATE TRIGGER knowledge_version_immutable BEFORE UPDATE ON knowledge_versions BEGIN SELECT RAISE(ABORT,'Source versions are immutable'); END",
    "CREATE TRIGGER knowledge_version_no_delete BEFORE DELETE ON knowledge_versions BEGIN SELECT RAISE(ABORT,'Source versions cannot be deleted'); END",
    "CREATE TRIGGER knowledge_chunk_immutable BEFORE UPDATE ON knowledge_chunks BEGIN SELECT RAISE(ABORT,'Source chunks are immutable'); END",
    "CREATE TRIGGER knowledge_chunk_no_delete BEFORE DELETE ON knowledge_chunks BEGIN SELECT RAISE(ABORT,'Source chunks cannot be deleted'); END",
]


def add_version(db, document_id, content, effective_from, actor_id, now):
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    version = db.execute('SELECT COALESCE(MAX(version),0)+1 FROM knowledge_versions WHERE document_id=?', (document_id,)).fetchone()[0]
    cur = db.execute('INSERT INTO knowledge_versions(document_id,version,content,content_hash,effective_from,confirmed_by,created_at) VALUES(?,?,?,?,?,?,?)', (document_id, version, content, digest(content), effective_from, actor_id, now))
    vid = cur.lastrowid
    for chunk in chunk_text(content):
        row = db.execute('INSERT INTO knowledge_chunks(version_id,start,end,text,heading,line_start,line_end,risk_flags) VALUES(?,?,?,?,?,?,?,?)', (vid, chunk['start'], chunk['end'], chunk['text'], chunk['heading'], chunk['line_start'], chunk['line_end'], json.dumps(chunk['risk_flags'])))
        db.execute('INSERT INTO knowledge_fts(rowid,text) VALUES(?,?)', (row.lastrowid, chunk['text']))
    db.execute('UPDATE knowledge_documents SET current_version_id=?,status="active" WHERE id=?', (vid, document_id))
    return vid


def migrate(db, now):
    db.execute(SCHEMA[0])
    if db.execute('SELECT 1 FROM schema_migrations WHERE version=1').fetchone(): return
    if not db.in_transaction: db.execute('BEGIN IMMEDIATE')
    if db.execute('SELECT 1 FROM schema_migrations WHERE version=1').fetchone(): return
    for statement in SCHEMA[1:]: db.execute(statement)
    columns = {r['name'] for r in db.execute('PRAGMA table_info(questions)')}
    if 'source_ai_item_id' not in columns: db.execute('ALTER TABLE questions ADD COLUMN source_ai_item_id INTEGER')
    if 'provenance' not in columns: db.execute("ALTER TABLE questions ADD COLUMN provenance TEXT NOT NULL DEFAULT '{}' ")
    db.execute('CREATE UNIQUE INDEX question_ai_item_unique ON questions(source_ai_item_id) WHERE source_ai_item_id IS NOT NULL')
    demo = db.execute('SELECT value FROM settings WHERE key="demo"').fetchone()
    if demo and demo[0] == '1':
        actor = db.execute('SELECT id FROM users WHERE role="training" ORDER BY id LIMIT 1').fetchone()
        actor_id = actor[0] if actor else db.execute('SELECT id FROM users ORDER BY id LIMIT 1').fetchone()[0]
        for document in json.loads((ROOT / 'content/rag-demo.json').read_text())['documents']:
            cur = db.execute('INSERT INTO knowledge_documents(title,category,department_id,owner_id,sample_key,created_at) VALUES(?,?,?,?,?,?)', (document['title'], document['category'], document['department_id'], actor_id, document['key'], now))
            add_version(db, cur.lastrowid, document['content'], now[:10], actor_id, now)
    db.execute('INSERT INTO schema_migrations VALUES(1,?,?)', ('grounded-question-authoring', now))
