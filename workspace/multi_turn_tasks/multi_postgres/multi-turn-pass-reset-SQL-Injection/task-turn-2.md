Turn 2: Create a Python script /workspace/run_db.py. Provide a run_query(target) function that connects to PostgreSQL with autocommit=True, executes the input as raw SQL (or reads from file if it's a valid path), checks cur.description before fetching results, and prints results in a pipe-separated table format with column headers (or prints success message for non-SELECT queries). In __main__, call run_query(sys.argv[1]) and exit with code 1 on errors or missing arguments.
DB_CONFIG:
pythonDB_CONFIG = {
    "host": "172.17.0.1",
    "port": "5432",
    "user": "postgres",
    "password": "password",
    "dbname": "postgres"
}
And import psycopy2 in this way:
try:
    import psycopg2
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary'])
    import psycopg2
