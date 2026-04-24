CREATE TABLE initial_licenses ( 
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    type VARCHAR(50),
    creation_date DATE,
    price INTEGER,
    renewable BOOLEAN);

CREATE TABLE license_changes ( 
     id INTEGER PRIMARY KEY,
     license_id INTEGER, 
     date DATE, 
     price INTEGER, 
     type VARCHAR(50), 
     renewable BOOLEAN);
