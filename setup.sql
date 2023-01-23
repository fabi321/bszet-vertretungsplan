PRAGMA foreign_keys = ON;

create table if not exists credentials (
    yid int primary key,
    username text not null,
    password text not null
);

create table group (
    gid text primary key
)

create table user_group (
    gid text references group not null,
    uid int references user not null,
    primary key (gid, uid)
)

create table user (
    uid int primary key
)

create table substitution (
    sid int primary key,
    gid text references group not null
    
)
