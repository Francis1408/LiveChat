CREATE TABLE IF NOT EXISTS users (
    id serial PRIMARY KEY,
	fullname VARCHAR ( 100 ) NOT NULL, 
	username VARCHAR ( 50 ) NOT NULL,
	password VARCHAR ( 255 ) NOT NULL,
	email VARCHAR ( 50 ) NOT NULL
);

CREATE TABLE IF NOT EXISTS room (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,   
    name VARCHAR(100),                  
    owner_id INTEGER NOT NULL,          
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_owner
        FOREIGN KEY (owner_id)
            REFERENCES users(id)
            ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS room_members (
    room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY(room_id, user_id),

    CONSTRAINT fk_room
        FOREIGN KEY(room_id) REFERENCES room(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_msg_room
        FOREIGN KEY(room_id) REFERENCES room (id) ON DELETE CASCADE,

    CONSTRAINT fk_msg_user
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);