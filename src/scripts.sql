CREATE TABLE IF NOT EXISTS prompts_roles
(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role        TEXT,
    instruction TEXT
);


CREATE TABLE IF NOT EXISTS llm_results
(
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    created           DATETIME,
    model             TEXT,
    total_tokens      INT,
    prompt_tokens     INT,
    completion_tokens INT,
    prompt            TEXT,
    answer            TEXT
);





