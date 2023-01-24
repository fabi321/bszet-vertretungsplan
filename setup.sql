PRAGMA foreign_keys = ON;

create table if not exists credentials (
    yid int primary key,
    username text not null,
    password text not null
);

create table if not exists class (
    gid text primary key
);

create table if not exists user (
    uid int primary key,
    gid text references class on delete cascade,
    trusted int not null default 0,
    last_update int not null default (strftime('%s', 'now'))
);

create table if not exists substitution (
    sid integer primary key,
    gid text not null references class on delete cascade,
    day int not null,
    lesson int not null,
    teacher text not null,
    subject text not null,
    room text not null,
    notes text,
    last_update int not null default (strftime('%s', 'now')),
    unique (day, lesson, gid)
);
