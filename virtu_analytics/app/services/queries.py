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
                callid VARCHAR(32) NOT NULL,
                descricao_problema TEXT, 
                descricao_solucao TEXT,
                tipo_problema TEXT, 
                tempo_gasto_etapas TEXT,
                sugestao_feedback TEXT, 
                problema_resolvido TEXT
            );
            """,
            'tb_info_call': """
            CREATE TABLE tb_info_call (
                 id SERIAL PRIMARY KEY,
                callid VARCHAR(32) NOT NULL,
                caller_id VARCHAR(30) NOT NULL,
                transfer VARCHAR(30),
                status VARCHAR(30) NOT NULL,
                date DATE NOT NULL,
                queue VARCHAR(25) NOT NULL,
                position INTEGER,
                original_position INTEGER,
                holdtime INTEGER,
                start_time INTEGER NOT NULL,
                end_time INTEGER NOT NULL,
                text TEXT,
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
                duration INT NOT NULL,
                agente VARCHAR(30),
                speaker CHAR(1),
                start_time INT NOT NULL,
                end_time INT NOT NULL,
                text TEXT
            );
            """
        }