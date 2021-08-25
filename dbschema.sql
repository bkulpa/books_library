
create table if not exists books (
    id integer primary key autoincrement, 
    author text not null, 
    title text not null, 
    publication_date datetime not null, 
    ISBN text not null,
    pages integer not null,
    cover text not null,
    lang text not null
);
