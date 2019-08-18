CREATE TABLE IF NOT EXISTS inverter(
    updated   TIMESTAMP,
    power     FLOAT             NOT NULL,
    U_ac      FLOAT             NOT NULL,
    U_dc      FLOAT             NOT NULL,
    I_dc      FLOAT             NOT NULL,
    E_day     FLOAT             NOT NULL,
    E_total   FLOAT             NOT NULL,
    temp      FLOAT             NOT NULL,
    PRIMARY KEY (updated));

CREATE TABLE IF NOT EXISTS optimizer(
    serial    CHAR(11)          NOT NULL,
    updated   TIMESTAMP,
    reported  TIMESTAMP,
    power     FLOAT             NOT NULL,
    U_out     FLOAT             NOT NULL,
    U_in      FLOAT             NOT NULL,
    E_day     FLOAT             NOT NULL,
    E_total   FLOAT             NOT NULL,
    temp      FLOAT             NOT NULL,
    PRIMARY KEY (serial, updated));

CREATE TABLE IF NOT EXISTS layout(
    serial       CHAR(11)        NOT NULL,
    pvo_systemid INTEGER         NOT NULL,
    orientation  SMALLINT        DEFAULT 0,
    inclination  SMALLINT        DEFAULT 0,
    PRIMARY KEY (serial));
