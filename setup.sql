PRAGMA foreign_keys = ON;

create table if not exists credentials (
    yid int primary key,
    username text not null,
    password text not null
);

create table group (
    gid text primary key
)

create table user (
    uid int primary key,
    gid text references group on delete cascade,
    trusted int not null default 0
)

create table substitution (
    sid int primary key,
    gid text not null references group on delete cascade
    day int not null,
    lesson int not null,
    teacher text not null,
    subject text not null,
    room text not null,
    notes text,
    unique (day, lesson, gid)
)
