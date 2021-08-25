import os
import sqlite3 
from flask import Flask, g, request, render_template, Response, redirect, url_for
from flask.helpers import flash
import requests
import json

app = Flask(__name__)

app.config.update(dict(
    SECRET_KEY = 'jobinterview',
    DATABASE = os.path.join(app.root_path, 'db.sqlite'),
    SITE_NAME = 'Biblioteka książek'
))

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'db'):
        g.db = connect_db() 
    return g.db 

@app.teardown_request
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/db/books/new')
def dbBooksNew():
    return render_template('db_books_new.html') 

@app.route('/db/books/new/manual')
def dbBooksNewManual():
    flash('Książka została dodana do bazy danych', 'success')
    return render_template('db_books_new_manual.html') 

@app.route('/db/books/<id>')
def dbBooksSingle(id):
    db = get_db()
    query= 'SELECT * FROM books WHERE id=?'

    cur = db.execute(query, (id,))
    book = cur.fetchone()

    return render_template('db_books_single.html', book=book)

@app.route('/db/books/<id>/edit')
def dbBooksEdit(id):    
    db = get_db()
    query= 'SELECT * FROM books WHERE id=?'
    cur = db.execute(query, (id,))
    book = cur.fetchone()

    return render_template('db_books_edit.html', book=book)

@app.route('/db/books/<id>/update', methods = ['POST'])
def dbBooksPatch(id):
    try:    
        db = get_db() 
        cur = db.cursor()

        id = request.form['id']
        author = request.form['author']
        title = request.form['title']
        publication_date = request.form['publication_date']
        ISBN = request.form['ISBN']
        pages  = request.form['pages']
        cover = request.form['cover']
        lang = request.form['lang']

        if author != '': cur.execute("update books set author=? where id=?", (author, id,))
        if title != '': cur.execute("update books set title=? where id=?", (title, id,))
        if publication_date != '': cur.execute("update books set publication_date=? where id=?", (publication_date, id,))
        if ISBN != '': cur.execute("update books set ISBN=? where id=?", (ISBN, id,))
        if pages != '': cur.execute("update books set pages=? where id=?", (pages, id,))
        if cover != '': cur.execute("update books set cover=? where id=?", (cover, id,))
        if lang != '': cur.execute("update books set lang=? where id=?", (lang, id,))

        db.commit()

        flash('Dane książki zostały zaktualizowane', 'success')
    except:
        flash('Wystąpił błąd przy aktualizacji...', 'error')

    return redirect(url_for('dbBooks'))

@app.route('/db/books/<id>/delete')
def dbBooksDelete(id):
    db = get_db()
    sql = 'DELETE FROM books WHERE id=?'
    cur = db.cursor()
    cur.execute(sql, (id,))
    db.commit()

    flash('Książka została usunięta', 'success')
    return redirect(url_for('dbBooks'))

@app.route('/db/books', methods = ['POST'])
def dbBooksCreate():
    books = json.loads(request.form['api_books'])

    db = get_db()
    cur = db.cursor()

    for book in books:
        cur.execute("insert into books (author, title, publication_date, ISBN, pages, cover, lang) VALUES (?,?,?,?,?,?,?)",(book["author"], book["title"], book["publishedDate"], book["ISBN"], book["pageCount"], book["cover"], book["language"]))        
    
    db.commit()
    return redirect(url_for('dbBooks'))

@app.route('/db/books/single', methods = ['POST'])
def dbBooksCreateSingle():
    book = json.loads(request.form)
    db = get_db()
    cur = db.cursor()
    cur.execute("insert into books (author, title, publication_date, ISBN, pages, cover, lang) VALUES (?,?,?,?,?,?,?)",(book["author"], book["title"], book["publishedDate"], book["ISBN"], book["pageCount"], book["cover"], book["language"]))
    db.commit()

    return redirect(url_for('dbBooks'))

@app.route('/db/books/single/manual', methods = ['POST'])
def dbBooksCreateSingleManual():
    author = request.form['author']
    title = request.form['title']
    publication_date = request.form['publication_date']
    ISBN = request.form['ISBN']
    pages  = request.form['pages']
    cover = request.form['cover']
    lang = request.form['lang']

    db = get_db()
    cur = db.cursor()
    cur.execute("insert into books (author, title, publication_date, ISBN, pages, cover, lang) VALUES (?,?,?,?,?,?,?)",(author, title, publication_date, ISBN, pages, cover, lang))
    db.commit()

    return redirect(url_for('dbBooks'))

@app.route('/db/books')
def dbBooks():
    db = get_db()
    query = ''
    entries = []

    publication_date_from = request.args.get('publication_date_from')
    publication_date_to = request.args.get('publication_date_to') 

    try:
        if (publication_date_from == '') and (publication_date_to == ''): query= 'select id, title, author, publication_date, ISBN, pages, cover, lang from books where author like \'%' + str(request.args.get('author')) + '%\' and title like \'%' + str(request.args.get('title')) + '%\' and lang like \'%' + str(request.args.get('lang')) + '%\' order by id;'   
        elif (publication_date_from != '') and (publication_date_to == ''): query= 'select id, title, author, publication_date, ISBN, pages, cover, lang from books where author like \'%' + str(request.args.get('author')) + '%\' and title like \'%' + str(request.args.get('title')) + '%\' and lang like \'%' + str(request.args.get('lang')) + '%\' and CAST(strftime(\'%s\',publication_date) AS integer) >= CAST(strftime(\'%s\',\'' + request.args.get('publication_date_from') + '\') AS integer) order by id;'   
        elif (publication_date_to != '') and (publication_date_from == ''): query= 'select id, title, author, publication_date, ISBN, pages, cover, lang from books where author like \'%' + str(request.args.get('author')) + '%\' and title like \'%' + str(request.args.get('title')) + '%\' and lang like \'%' + str(request.args.get('lang')) + '%\' and CAST(strftime(\'%s\',publication_date) AS integer) <= CAST(strftime(\'%s\',\'' + request.args.get('publication_date_to') + '\') AS integer) order by id;'   
        else: query= 'select id, title, author, publication_date, ISBN, pages, cover, lang from books where author like \'%' + str(request.args.get('author')) + '%\' and title like \'%' + str(request.args.get('title')) + '%\' and lang like \'%' + str(request.args.get('lang')) + '%\' and CAST(strftime(\'%s\',publication_date) AS integer) >= CAST(strftime(\'%s\',\'' + request.args.get('publication_date_from') + '\') AS integer) and CAST(strftime(\'%s\',publication_date) AS integer) <= CAST(strftime(\'%s\',\'' + request.args.get('publication_date_to') + '\') AS integer) order by id;'
        
    except:
        query = "select * from books"

    cur = db.execute(query)
    entries = cur.fetchall()

    return render_template('db_books.html', entries=entries)

@app.route('/api/books')
def apiBooks():
    apiSearchQuery = request.args.get('api_search_query')
    apiSearchQueryTitle = request.args.get('api_search_query_title')
    apiSearchQueryAuthor = request.args.get('api_search_query_author')
    data = { " books": [], "stringifiedBooks": ""}

    print("1: ",(apiSearchQuery))
    print("2: ",apiSearchQueryTitle)
    print("3: ",apiSearchQueryAuthor)

    if apiSearchQueryAuthor:
        response = requests.get("https://www.googleapis.com/books/v1/volumes?q=inauthor:" + apiSearchQueryAuthor)
        responseDict = json.loads(response.text)
        books = None

        if 'items' in responseDict:
            books = mapApiBooks(responseDict['items'])
        
        else:
            flash('Nie znaleziono żadnej ksiażki', 'error')

        data = { "books": books, "stringifiedBooks": json.dumps(books)}

    if apiSearchQueryTitle:
        response = requests.get("https://www.googleapis.com/books/v1/volumes?q=intitle:" + apiSearchQueryTitle)
        responseDict = json.loads(response.text)
        books = None

        if 'items' in responseDict:
            books = mapApiBooks(responseDict['items'])
        
        else:
            flash('Nie znaleziono żadnej ksiażki', 'error')

        data = { "books": books, "stringifiedBooks": json.dumps(books)}

    if apiSearchQuery:
        response = requests.get("https://www.googleapis.com/books/v1/volumes?q=" + apiSearchQuery)
        responseDict = json.loads(response.text)
        books = None

        if 'items' in responseDict:
            books = mapApiBooks(responseDict['items'])
        
        else:
            flash('Nie znaleziono żadnej ksiażki', 'error')

        data = { "books": books, "stringifiedBooks": json.dumps(books)}

    return render_template('api_books.html', data=data)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(error):
    return Response(json.dumps({"Error": True}), status=500, mimetype='application/json')

def mapApiBooks(rawBooks):
    try:
        mappedBooks=[]
        
        for y in rawBooks:
            x = y['volumeInfo']
        
            if 'title' in x.keys():
                title=x['title']
            else:
                title=''

            if 'authors' in x.keys():
                author=str(x['authors']).replace('[','').replace(']','').replace('\'','')
            else:
                author=''

            if 'publishedDate' in x.keys():    
                publishedDate=x['publishedDate']
            else:
                publishedDate=''

            if 'industryIdentifiers' in x.keys():
                apiISBN1=[x['industryIdentifiers']][0][0]
                apiISBN2=apiISBN1['identifier']
            else:
                apiISBN2=''

            if 'pageCount' in x.keys():
                pageCount=x['pageCount']
            else:
                pageCount=''

            if 'imageLinks' in x.keys():
                cover=[x['imageLinks']][0]['thumbnail']
            else:
                cover=''

            if 'language' in x.keys():
                language=x['language']
            else:
                language=''
            
            bookFromApi={
                "title":title,
                "author":author,
                "publishedDate":publishedDate,
                "ISBN":apiISBN2,
                "pageCount":pageCount,
                "cover":cover,
                "language":language,
                "volumeInfo":y['volumeInfo']
            }
            mappedBooks.append(bookFromApi)
        
        return mappedBooks

    except:
        print("An error has occured")

if __name__ == '__main__':
    app.run(debug=True)