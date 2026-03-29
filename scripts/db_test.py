"""
ReviewBot - Database Test Script
Connects to PostgreSQL, creates schema tables, inserts sample data, and queries results.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# ─── Connection ────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "127.0.0.1",
    "port":     5435,
    "dbname":   "reviews_db",
    "user":     "review_user",
    "password": "review_password_change_me",
}

def connect():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn


# ─── Schema ────────────────────────────────────────────────────────────────────
CREATE_TABLES_SQL = """
-- Users
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    full_name   VARCHAR(255) NOT NULL,
    role        VARCHAR(50)  DEFAULT 'reviewer',
    is_active   BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMP    DEFAULT NOW()
);

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    domain      VARCHAR(100),
    description TEXT,
    status      VARCHAR(50)  DEFAULT 'active',
    owner_id    INTEGER REFERENCES users(id),
    created_at  TIMESTAMP    DEFAULT NOW()
);

-- Checklists
CREATE TABLE IF NOT EXISTS checklists (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    type        VARCHAR(50)  NOT NULL,
    version     VARCHAR(20)  DEFAULT '1.0',
    project_id  INTEGER REFERENCES projects(id),
    is_global   BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMP    DEFAULT NOW()
);

-- Checklist Items
CREATE TABLE IF NOT EXISTS checklist_items (
    id                  SERIAL PRIMARY KEY,
    checklist_id        INTEGER REFERENCES checklists(id) ON DELETE CASCADE,
    item_code           VARCHAR(20),
    area                VARCHAR(255),
    question            TEXT NOT NULL,
    weight              NUMERIC(3,1) DEFAULT 1.0,
    is_review_mandatory         BOOLEAN      DEFAULT TRUE,
    "order"         INTEGER      DEFAULT 0
);

-- Reviews
CREATE TABLE IF NOT EXISTS reviews (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER REFERENCES projects(id),
    checklist_id    INTEGER REFERENCES checklists(id),
    title           VARCHAR(255),
    status          VARCHAR(50)  DEFAULT 'draft',
    conducted_by    INTEGER REFERENCES users(id),
    review_date     TIMESTAMP    DEFAULT NOW(),
    created_at      TIMESTAMP    DEFAULT NOW()
);

-- Review Responses
CREATE TABLE IF NOT EXISTS review_responses (
    id                  SERIAL PRIMARY KEY,
    review_id           INTEGER REFERENCES reviews(id) ON DELETE CASCADE,
    checklist_item_id   INTEGER REFERENCES checklist_items(id),
    answer              VARCHAR(50),
    comments            TEXT,
    rag_status          VARCHAR(10)  DEFAULT 'na',
    created_at          TIMESTAMP    DEFAULT NOW()
);

-- Reports
CREATE TABLE IF NOT EXISTS reports (
    id                  SERIAL PRIMARY KEY,
    review_id           INTEGER REFERENCES reviews(id),
    compliance_score    NUMERIC(5,2),
    overall_rag_status  VARCHAR(10),
    approval_status     VARCHAR(50)  DEFAULT 'pending',
    summary             TEXT,
    created_at          TIMESTAMP    DEFAULT NOW()
);
"""


# ─── Sample Data ───────────────────────────────────────────────────────────────
def insert_sample_data(conn):
    cur = conn.cursor()

    # Users  (hashed_password = bcrypt hash of "Password123!")
    HASHED_PW = "$2b$12$1YEK5YKoxFGQcYTmG0.XiuWCC5B1an1sOocu8ivfnAohRPv9e9jyG"
    cur.execute("""
        INSERT INTO users (email, full_name, hashed_password, role) VALUES
            ('admin@reviewbot.com',    'Admin User',     %s, 'admin'),
            ('manager@reviewbot.com',  'Project Manager',%s, 'manager'),
            ('reviewer@reviewbot.com', 'Tech Reviewer',  %s, 'reviewer')
        ON CONFLICT (email) DO NOTHING
        RETURNING id, email, role;
    """, (HASHED_PW, HASHED_PW, HASHED_PW))
    users = cur.fetchall()
    print(f"  Inserted {len(users)} user(s)")

    # Get admin id
    cur.execute("SELECT id FROM users WHERE email = 'admin@reviewbot.com'")
    admin_id = cur.fetchone()[0]

    # Projects
    cur.execute("""
        INSERT INTO projects (name, domain, description, status, owner_id) VALUES
            ('NeUMoney Platform',   'fintech',    'Digital banking platform review',      'active',    %s),
            ('HealthTrack App',     'healthcare', 'Patient data management system',       'active',    %s),
            ('ShopEase Commerce',   'ecommerce',  'E-commerce platform delivery review',  'completed', %s)
        ON CONFLICT DO NOTHING
        RETURNING id, name, domain;
    """, (admin_id, admin_id, admin_id))
    projects = cur.fetchall()
    print(f"  Inserted {len(projects)} project(s)")

    # Get NeUMoney project id
    cur.execute("SELECT id FROM projects WHERE name = 'NeUMoney Platform'")
    proj_id = cur.fetchone()[0]

    # Checklist
    cur.execute("""
        INSERT INTO checklists (name, type, version, project_id, is_global) VALUES
            ('Standard Delivery Checklist', 'delivery',  '1.0', NULL,    TRUE),
            ('Standard Technical Checklist','technical', '1.0', NULL,    TRUE),
            ('NeUMoney Delivery Review',    'delivery',  '1.0', %s,      FALSE)
        ON CONFLICT DO NOTHING
        RETURNING id, name, type;
    """, (proj_id,))
    checklists = cur.fetchall()
    print(f"  Inserted {len(checklists)} checklist(s)")

    # Get delivery checklist id
    cur.execute("SELECT id FROM checklists WHERE name = 'Standard Delivery Checklist'")
    cl_id = cur.fetchone()[0]

    # Checklist Items
    cur.execute("""
        INSERT INTO checklist_items (checklist_id, item_code, area, question, weight, "order") VALUES
            (%s, '1.1', 'Scope & Planning',    'Is the project scope clearly defined and signed off?',        1.5, 1),
            (%s, '1.2', 'Scope & Planning',    'Are all stakeholders identified and onboarded?',              1.0, 2),
            (%s, '2.1', 'Security',            'Has a security review been completed?',                       2.0, 3),
            (%s, '2.2', 'Security',            'Are API endpoints protected with authentication?',             2.0, 4),
            (%s, '3.1', 'Testing',             'Is test coverage above 80%%?',                                1.5, 5),
            (%s, '3.2', 'Testing',             'Have performance tests been executed?',                       1.0, 6),
            (%s, '4.1', 'Deployment',          'Is CI/CD pipeline configured and tested?',                    1.5, 7),
            (%s, '4.2', 'Deployment',          'Is a rollback plan documented and tested?',                   1.0, 8)
        ON CONFLICT DO NOTHING
        RETURNING id;
    """, (cl_id,) * 8)
    items = cur.fetchall()
    print(f"  Inserted {len(items)} checklist item(s)")

    # Review
    cur.execute("SELECT id FROM users WHERE email = 'reviewer@reviewbot.com'")
    reviewer_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO reviews (project_id, checklist_id, title, status, conducted_by)
        VALUES (%s, %s, 'Q1 2026 Delivery Review', 'completed', %s)
        ON CONFLICT DO NOTHING
        RETURNING id;
    """, (proj_id, cl_id, reviewer_id))
    row = cur.fetchone()
    if row:
        review_id = row[0]
    else:
        cur.execute("SELECT id FROM reviews WHERE title = 'Q1 2026 Delivery Review'")
        review_id = cur.fetchone()[0]
    print(f"  Inserted review id={review_id}")

    # Review Responses
    cur.execute('SELECT id FROM checklist_items WHERE checklist_id = %s ORDER BY "order"', (cl_id,))
    item_ids = [r[0] for r in cur.fetchall()]

    responses = [
        (review_id, item_ids[0], 'yes',     'Scope doc approved by all stakeholders', 'green'),
        (review_id, item_ids[1], 'yes',     'Stakeholder matrix updated',              'green'),
        (review_id, item_ids[2], 'partial', 'Security review in progress, 80% done',  'amber'),
        (review_id, item_ids[3], 'yes',     'OAuth2 implemented on all endpoints',     'green'),
        (review_id, item_ids[4], 'no',      'Coverage at 65%, need to improve',        'red'),
        (review_id, item_ids[5], 'no',      'Performance tests not yet run',           'red'),
        (review_id, item_ids[6], 'yes',     'GitHub Actions pipeline active',          'green'),
        (review_id, item_ids[7], 'partial', 'Rollback plan drafted, not tested',       'amber'),
    ]

    cur.executemany("""
        INSERT INTO review_responses (review_id, checklist_item_id, answer, comments, rag_status)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, responses)
    print(f"  Inserted {len(responses)} review response(s)")

    # Report
    cur.execute("""
        INSERT INTO reports (review_id, compliance_score, overall_rag_status, approval_status, summary)
        VALUES (%s, 62.50, 'amber', 'pending',
                'Review completed. 4 items green, 2 amber, 2 red. Testing gaps need urgent attention.')
        ON CONFLICT DO NOTHING
        RETURNING id;
    """, (review_id,))
    print(f"  Inserted report")

    conn.commit()
    cur.close()


# ─── Queries ───────────────────────────────────────────────────────────────────
def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def query_data(conn):
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print_section("USERS")
    cur.execute("SELECT id, email, full_name, role, is_active FROM users ORDER BY id")
    for row in cur.fetchall():
        print(f"  [{row['id']}] {row['full_name']} <{row['email']}> | role={row['role']}")

    print_section("PROJECTS")
    cur.execute("""
        SELECT p.id, p.name, p.domain, p.status, u.full_name AS owner
        FROM projects p LEFT JOIN users u ON u.id = p.owner_id
        ORDER BY p.id
    """)
    for row in cur.fetchall():
        print(f"  [{row['id']}] {row['name']} | domain={row['domain']} | status={row['status']} | owner={row['owner']}")

    print_section("CHECKLISTS")
    cur.execute("SELECT id, name, type, version, is_global FROM checklists ORDER BY id")
    for row in cur.fetchall():
        scope = "GLOBAL" if row['is_global'] else "PROJECT"
        print(f"  [{row['id']}] {row['name']} | type={row['type']} | v{row['version']} | {scope}")

    print_section("CHECKLIST ITEMS  (Standard Delivery)")
    cur.execute("""
        SELECT ci.item_code, ci.area, ci.question, ci.weight
        FROM checklist_items ci
        JOIN checklists c ON c.id = ci.checklist_id
        WHERE c.name = 'Standard Delivery Checklist'
        ORDER BY ci."order"
    """)
    for row in cur.fetchall():
        print(f"  {row['item_code']}  [{row['area']}]  {row['question'][:60]}  (weight={row['weight']})")

    print_section("REVIEW RESPONSES  (Q1 2026 Delivery Review)")
    cur.execute("""
        SELECT ci.item_code, ci.area, rr.answer, rr.rag_status, rr.comments
        FROM review_responses rr
        JOIN checklist_items ci ON ci.id = rr.checklist_item_id
        JOIN reviews r ON r.id = rr.review_id
        WHERE r.title = 'Q1 2026 Delivery Review'
        ORDER BY ci."order"
    """)
    rag_icon = {'green': 'GREEN', 'amber': 'AMBER', 'red': 'RED  ', 'na': 'N/A  '}
    for row in cur.fetchall():
        icon = rag_icon.get(row['rag_status'], '?????')
        print(f"  [{icon}] {row['item_code']}  {row['answer']:7}  {row['comments'][:55]}")

    print_section("REPORT SUMMARY")
    cur.execute("""
        SELECT rp.id, rp.compliance_score, rp.overall_rag_status, rp.approval_status,
               r.title AS review_title, p.name AS project_name, rp.summary
        FROM reports rp
        JOIN reviews r ON r.id = rp.review_id
        JOIN projects p ON p.id = r.project_id
        ORDER BY rp.id
    """)
    for row in cur.fetchall():
        print(f"  Project       : {row['project_name']}")
        print(f"  Review        : {row['review_title']}")
        print(f"  Score         : {row['compliance_score']}%")
        print(f"  Overall RAG   : {row['overall_rag_status'].upper()}")
        print(f"  Approval      : {row['approval_status']}")
        print(f"  Summary       : {row['summary']}")

    print_section("RAG STATUS BREAKDOWN")
    cur.execute("""
        SELECT rag_status, COUNT(*) AS count,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
        FROM review_responses
        GROUP BY rag_status
        ORDER BY rag_status
    """)
    for row in cur.fetchall():
        bar = '#' * int(row['pct'] // 5)
        print(f"  {row['rag_status']:6}  {str(row['count']):3} items  {row['pct']:5}%  {bar}")

    cur.close()


# ─── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  ReviewBot - Database Setup & Query Test")
    print("=" * 60)

    print(f"\nConnecting to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']} ...")
    conn = connect()
    print("  Connected successfully!")

    print("\n[1/3] Creating schema tables ...")
    cur = conn.cursor()
    cur.execute(CREATE_TABLES_SQL)
    conn.commit()
    cur.close()
    print("  Tables created (or already exist)")

    print("\n[2/3] Inserting sample data ...")
    insert_sample_data(conn)

    print("\n[3/3] Querying data ...")
    query_data(conn)

    conn.close()
    print("\n" + "=" * 60)
    print("  Done!")
    print("=" * 60)

