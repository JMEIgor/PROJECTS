create_table_queries = {
            'tb_analyst': """
            CREATE TABLE IF NOT EXISTS tb_analyst (
                id_analyst SERIAL PRIMARY KEY,
                lettel_agent VARCHAR(20) NOT NULL,
                name VARCHAR(40) NOT NULL,
                team VARCHAR(25) NOT NULL
            );
            """,
            'tb_gpt_output': """
            CREATE TABLE IF NOT EXISTS tb_gpt_output (
                id SERIAL PRIMARY KEY,
                uid_call VARCHAR(32) NOT NULL,
                dt_call DATE NOT NULL,
                id_speaker VARCHAR(8) NOT NULL,
                id_caller VARCHAR(30) NOT NULL,
                tx_response TEXT NOT NULL
            );
            """,
            'tb_info_call': """
            CREATE TABLE IF NOT EXISTS tb_info_call (
                id SERIAL PRIMARY KEY,
                callid VARCHAR(32) NOT NULL,
                caller_id VARCHAR(30) NOT NULL,
                transfer VARCHAR(30),
                status VARCHAR(30) NOT NULL,
                date DATE NOT NULL,
                queue VARCHAR(25) NOT NULL,
                position INT,
                original_position INT,
                holdtime INT,
                start_time INT NOT NULL,
                end_time INT NOT NULL,
                text VARCHAR(50000),
                duration INT NOT NULL,
                agente VARCHAR(30)
            );
            """,
            'tb_import_call': """
            CREATE TABLE IF NOT EXISTS tb_import_call (
                id SERIAL PRIMARY KEY,
                callid VARCHAR(32) NOT NULL,
                caller_id VARCHAR(30) NOT NULL,
                transfer VARCHAR(30),
                status VARCHAR(30) NOT NULL,
                date DATE NOT NULL,
                queue VARCHAR(25) NOT NULL,
                holdtime INT,
                start_time INT NOT NULL,
                end_time INT NOT NULL,
                text VARCHAR(10000),
                duration INT NOT NULL,
                agente VARCHAR(30)
            );
            """
        }