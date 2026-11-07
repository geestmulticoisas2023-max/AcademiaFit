import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave-local-de-desenvolvimento')
DB_PATH = os.environ.get('ACADEMIA_DB', os.path.join(os.path.dirname(__file__), 'academia.db'))

def connection():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    return db

def init_db():
    with connection() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            telefone TEXT NOT NULL,
            criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS mensalidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER NOT NULL REFERENCES alunos(id),
            competencia TEXT NOT NULL,
            valor REAL NOT NULL CHECK (valor > 0),
            status TEXT NOT NULL CHECK (status IN ('Pendente','Pago')),
            UNIQUE(aluno_id, competencia)
        );
        ''')

@app.route('/')
def index():
    with connection() as db:
        alunos = db.execute('SELECT COUNT(*) n FROM alunos').fetchone()['n']
        pendentes = db.execute("SELECT COUNT(*) n FROM mensalidades WHERE status='Pendente'").fetchone()['n']
    return render_template('index.html', alunos=alunos, pendentes=pendentes)

@app.route('/alunos', methods=['GET', 'POST'])
def alunos():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        telefone = request.form.get('telefone', '').strip()
        if not nome or not email or not telefone or '@' not in email:
            flash('Preencha nome, e-mail válido e telefone.', 'erro')
        else:
            try:
                with connection() as db:
                    db.execute('INSERT INTO alunos(nome,email,telefone) VALUES (?,?,?)', (nome,email,telefone))
                flash('Aluno cadastrado com sucesso!', 'ok')
                return redirect(url_for('alunos'))
            except sqlite3.IntegrityError:
                flash('Este e-mail já está cadastrado.', 'erro')
    with connection() as db:
        registros = db.execute('SELECT * FROM alunos ORDER BY id DESC').fetchall()
    return render_template('alunos.html', registros=registros)

@app.route('/mensalidades', methods=['GET', 'POST'])
def mensalidades():
    if request.method == 'POST':
        try:
            aluno_id = int(request.form['aluno_id'])
            competencia = request.form['competencia'].strip()
            valor = float(request.form['valor'].replace(',', '.'))
            if not competencia or valor <= 0:
                raise ValueError
            with connection() as db:
                db.execute("INSERT INTO mensalidades(aluno_id,competencia,valor,status) VALUES (?,?,?,'Pendente')", (aluno_id,competencia,valor))
            flash('Mensalidade registrada!', 'ok')
            return redirect(url_for('mensalidades'))
        except (ValueError, KeyError, sqlite3.IntegrityError):
            flash('Dados inválidos ou mensalidade já existente para o período.', 'erro')
    with connection() as db:
        lista_alunos = db.execute('SELECT id,nome FROM alunos ORDER BY nome').fetchall()
        registros = db.execute('''SELECT m.*, a.nome FROM mensalidades m JOIN alunos a ON a.id=m.aluno_id ORDER BY m.id DESC''').fetchall()
    return render_template('mensalidades.html', alunos=lista_alunos, registros=registros)

@app.post('/mensalidades/<int:mensalidade_id>/pagar')
def pagar(mensalidade_id):
    with connection() as db:
        db.execute("UPDATE mensalidades SET status='Pago' WHERE id=?", (mensalidade_id,))
    flash('Pagamento registrado.', 'ok')
    return redirect(url_for('mensalidades'))

@app.route('/pendencias')
def pendencias():
    with connection() as db:
        registros = db.execute("""SELECT m.*, a.nome FROM mensalidades m JOIN alunos a ON a.id=m.aluno_id WHERE m.status='Pendente' ORDER BY a.nome""").fetchall()
    return render_template('pendencias.html', registros=registros)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
