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
            """,
            'tb_teams': """
            CREATE TABLE IF NOT EXISTS tb_teams (
            id INT PRIMARY KEY NOT NULL,
            team VARCHAR(32) NOT NULL,
            );
            """,
            'tb_analyst': """ 
            CREATE TABLE IF NOT EXISTS tb_analyst (
            id SERIAL PRIMARY KEY NOT NULL,
            name VARCHAR(40) NOT NULL,
            team VARCHAR(5) NOT NULL,
            lettel_agent VARCHAR(20)
            );
            """
        }

#tb_analyst = {"""
#   insert into tb_analyst (id,	name, team,	lettel_agent)
#    values (113,'Hecktor','442','113'),
#	    (116,'Igor','444','116'),
#	    (117,'Carlos F.','444','117'),
#	    (118,'Luis Fernando','443','118'),
#	    (119,'Walter','444','118'),
#	    (124,'Gustavo','444','124'),
#	    (127,'Karita','442','127'),
#	    (128,'Jean','445','128'),
#	    (129,'Gabriel','443','129'),
#	    (130,'Weverton','443','130'),
#	    (133,'Alex','443','133'),
#	    (134,'Fernando B.','445','134'),
#	    (137,'Henrique V.','443','137'),
#	    (138,'Jezon','443','138'),
#	    (139,'Carlos K.','444','139'),
#	    (142,'João M.','442','142'),
#	    (143,'Renan','442','143'),
#	    (152,'Diogo','443','152'),
#	    (153,'Henrique C.','442','153')
#	on conflict do nothing
#"""
#}

#tb_teams = {"""
#    insert into tb_teams (id,team)
#	values (442,'PDV ou Sitef'),
#		(443, 'Comercial ou Logística'),
#		(444, 'Fiscal ou Financeiro'),
#		(445, 'Mobile ou Pricing')
#"""
#}