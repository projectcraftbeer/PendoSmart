import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()
# SQL Server ODBC connection string from .env
SQLSERVER_CONN_STR = os.getenv("SQLSERVER_CONN_STR")
if not SQLSERVER_CONN_STR:
    raise RuntimeError("SQLSERVER_CONN_STR not set in .env file")

def init_sqlserver():
    with pyodbc.connect(SQLSERVER_CONN_STR) as conn:
        c = conn.cursor()
        # Table: strings
        c.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='strings' AND xtype='U')
        CREATE TABLE strings (
            id INT IDENTITY(1,1) PRIMARY KEY,
            source NVARCHAR(MAX) NOT NULL,
            japanese NVARCHAR(MAX) NOT NULL,
            confidence FLOAT,
            reason NVARCHAR(MAX),
            suggestion NVARCHAR(MAX)
        )''')
        # Table: smartling_keys
        c.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='smartling_keys' AND xtype='U')
        CREATE TABLE smartling_keys (
            id INT IDENTITY(1,1) PRIMARY KEY,
            user_id NVARCHAR(255) NOT NULL,
            secret NVARCHAR(255) NOT NULL,
            project_id NVARCHAR(255),
            job_id NVARCHAR(255),
            access_token NVARCHAR(MAX),
            refresh_token NVARCHAR(MAX),
            token_expires BIGINT,
            account_id NVARCHAR(255),
            locale NVARCHAR(32)
        )''')
        # Table: job_files
        c.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='job_files' AND xtype='U')
        CREATE TABLE job_files (
            id INT IDENTITY(1,1) PRIMARY KEY,
            job_id NVARCHAR(255) NOT NULL,
            file_uri NVARCHAR(MAX) NOT NULL,
            project_id NVARCHAR(255)
        )''')
        # Table: smartling_job_files
        c.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='smartling_job_files' AND xtype='U')
        CREATE TABLE smartling_job_files (
            id INT IDENTITY(1,1) PRIMARY KEY,
            job_id NVARCHAR(255) NOT NULL,
            file_uri NVARCHAR(MAX) NOT NULL,
            project_id NVARCHAR(255) NOT NULL
        )''')
        # Table: smartling_translations
        c.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='smartling_translations' AND xtype='U')
        CREATE TABLE smartling_translations (
            id INT IDENTITY(1,1) PRIMARY KEY,
            project_id NVARCHAR(255) NOT NULL,
            file_uri NVARCHAR(MAX) NOT NULL,
            locale NVARCHAR(32) NOT NULL,
            parsed_string_text NVARCHAR(MAX),
            translation NVARCHAR(MAX),
            status NVARCHAR(32) NOT NULL DEFAULT 'pending',
            confidence FLOAT,
            reason NVARCHAR(MAX),
            flag INT,
            hashcode NVARCHAR(255) UNIQUE
        )''')
        conn.commit()

if __name__ == "__main__":
    init_sqlserver()
