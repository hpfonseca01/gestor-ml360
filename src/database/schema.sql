-- Schema do banco de dados gestor-ml360

CREATE TABLE IF NOT EXISTS jogadores_jogo (
    sofifa_id       VARCHAR PRIMARY KEY,
    nome            VARCHAR NOT NULL,
    idade           INTEGER,
    overall         INTEGER,
    potencial       INTEGER,
    posicao         VARCHAR,
    posicoes_alt    VARCHAR,
    time            VARCHAR,
    liga            VARCHAR,
    nacionalidade   VARCHAR,
    valor_eur       BIGINT,
    salario_eur     INTEGER,
    -- Atributos físicos
    altura_cm       INTEGER,
    peso_kg         INTEGER,
    pe_preferido    VARCHAR,
    skill_moves     INTEGER,
    weak_foot       INTEGER,
    -- Atributos técnicos
    ritmo           INTEGER,
    finalizacao     INTEGER,
    passe           INTEGER,
    drible          INTEGER,
    defesa          INTEGER,
    fisico          INTEGER,
    -- Controle
    versao_jogo     VARCHAR,
    data_coleta     TIMESTAMP DEFAULT current_timestamp,
    patch_versao    VARCHAR
);

CREATE TABLE IF NOT EXISTS historico_ratings (
    id              INTEGER PRIMARY KEY,
    sofifa_id       VARCHAR NOT NULL,
    overall         INTEGER,
    potencial       INTEGER,
    versao_jogo     VARCHAR,
    data_registro   TIMESTAMP DEFAULT current_timestamp,
    variacao        INTEGER  -- diferença em relação ao registro anterior
);

CREATE TABLE IF NOT EXISTS jogadores_reais (
    id              INTEGER PRIMARY KEY,
    nome            VARCHAR NOT NULL,
    time            VARCHAR,
    liga            VARCHAR,
    temporada       VARCHAR,
    -- Stats padrão
    partidas        INTEGER,
    minutos         INTEGER,
    gols            INTEGER,
    assistencias    INTEGER,
    -- xG / xA
    xg              DOUBLE,
    xa              DOUBLE,
    xg_por_90       DOUBLE,
    xa_por_90       DOUBLE,
    -- Progressão
    progressive_carries INTEGER,
    progressive_passes  INTEGER,
    -- Controle
    data_coleta     TIMESTAMP DEFAULT current_timestamp,
    fonte           VARCHAR DEFAULT 'fbref'
);

CREATE TABLE IF NOT EXISTS mapeamento_jogadores (
    sofifa_id       VARCHAR PRIMARY KEY,
    nome_jogo       VARCHAR,
    nome_real       VARCHAR,
    fbref_id        VARCHAR,
    similaridade    DOUBLE,
    verificado      BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS analises_scouting (
    id              INTEGER PRIMARY KEY,
    sofifa_id       VARCHAR,
    tipo_analise    VARCHAR,  -- 'promessa', 'subvalorizado', 'upgrade_esperado'
    score           DOUBLE,
    justificativa   VARCHAR,
    data_analise    TIMESTAMP DEFAULT current_timestamp
);
