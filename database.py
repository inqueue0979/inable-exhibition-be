import os
import json
from datetime import datetime
from typing import List, Dict, Optional

try:
    import psycopg2
    import psycopg2.extras
    USE_POSTGRES = True
except ImportError:
    import sqlite3
    USE_POSTGRES = False

class DatabaseManager:
    def __init__(self, db_path: str = "alt_text_evaluations.db"):
        self.db_path = db_path
        self.use_postgres = USE_POSTGRES and os.getenv('DATABASE_URL')
        self.init_database()

    def get_connection(self):
        if self.use_postgres:
            return psycopg2.connect(os.getenv('DATABASE_URL'))
        else:
            return sqlite3.connect(self.db_path)

    def init_database(self):
        if self.use_postgres:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluations (
                        id SERIAL PRIMARY KEY,
                        alt_text TEXT NOT NULL,
                        image_data TEXT,
                        image_type TEXT,
                        grade TEXT,
                        reason TEXT,
                        improvement TEXT,
                        compliant INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # PostgreSQL에서 컬럼 존재 확인 및 추가
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name='evaluations' AND column_name='image_data'
                """)
                if not cursor.fetchone():
                    cursor.execute('ALTER TABLE evaluations ADD COLUMN image_data TEXT')
                conn.commit()
        else:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alt_text TEXT NOT NULL,
                        image_data TEXT,
                        image_type TEXT,
                        grade TEXT,
                        reason TEXT,
                        improvement TEXT,
                        compliant INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 기존 테이블에 image_data 컬럼이 없는 경우 추가
                cursor.execute("PRAGMA table_info(evaluations)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'image_data' not in columns:
                    cursor.execute('ALTER TABLE evaluations ADD COLUMN image_data TEXT')
                conn.commit()

    def save_evaluation(self, alt_text: str, result: Dict, image_data: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO evaluations
                    (alt_text, image_data, image_type, grade, reason, improvement, compliant)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (
                    alt_text,
                    image_data,
                    result.get('type'),
                    result.get('grade'),
                    result.get('reason'),
                    result.get('improvement'),
                    result.get('compliant')
                ))
                evaluation_id = cursor.fetchone()[0]
            else:
                cursor.execute('''
                    INSERT INTO evaluations
                    (alt_text, image_data, image_type, grade, reason, improvement, compliant)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alt_text,
                    image_data,
                    result.get('type'),
                    result.get('grade'),
                    result.get('reason'),
                    result.get('improvement'),
                    result.get('compliant')
                ))
                evaluation_id = cursor.lastrowid
            conn.commit()
            return evaluation_id

    def get_history(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        with self.get_connection() as conn:
            if self.use_postgres:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute('''
                    SELECT * FROM evaluations
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                ''', (limit, offset))
            else:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM evaluations
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_evaluation_by_id(self, evaluation_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            if self.use_postgres:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute('''
                    SELECT * FROM evaluations WHERE id = %s
                ''', (evaluation_id,))
            else:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM evaluations WHERE id = ?
                ''', (evaluation_id,))

            row = cursor.fetchone()
            return dict(row) if row else None

    def get_statistics(self) -> Dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 전체 평가 수
            cursor.execute('SELECT COUNT(*) FROM evaluations')
            total_count = cursor.fetchone()[0]

            # 이미지 유형별 통계
            cursor.execute('''
                SELECT image_type, COUNT(*) as count
                FROM evaluations
                GROUP BY image_type
            ''')
            type_stats = dict(cursor.fetchall())

            # 준수 등급별 통계
            cursor.execute('''
                SELECT grade, COUNT(*) as count
                FROM evaluations
                GROUP BY grade
            ''')
            grade_stats = dict(cursor.fetchall())

            # 준수도별 통계
            cursor.execute('''
                SELECT compliant, COUNT(*) as count
                FROM evaluations
                GROUP BY compliant
            ''')
            compliant_stats = dict(cursor.fetchall())

            return {
                'total_evaluations': total_count,
                'type_distribution': type_stats,
                'grade_distribution': grade_stats,
                'compliant_distribution': compliant_stats
            }