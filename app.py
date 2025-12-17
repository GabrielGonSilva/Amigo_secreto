from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import random
from dateutil import parser
import resend
import secrets

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

resend.api_key = os.getenv('RESEND_API_KEY')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    grupos = db.relationship('MembroGrupo', back_populates='usuario')
    sugestoes = db.relationship('SugestaoPresente', back_populates='usuario')
    sorteios_feitos = db.relationship('SorteioIndividual', foreign_keys='SorteioIndividual.usuario_id',
                                      back_populates='usuario')
    sorteios_recebidos = db.relationship('SorteioIndividual', foreign_keys='SorteioIndividual.amigo_sorteado_id',
                                         back_populates='amigo')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    codigo_acesso = db.Column(db.String(10), unique=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_evento = db.Column(db.DateTime)
    local_evento = db.Column(db.String(200))
    valor_minimo = db.Column(db.Float)
    valor_maximo = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('User')
    membros = db.relationship('MembroGrupo', back_populates='grupo')
    sugestoes = db.relationship('SugestaoPresente', back_populates='grupo')
    sorteios_individual = db.relationship('SorteioIndividual', back_populates='grupo')

    @property
    def total_participantes(self):
        return len(self.membros)

    def usuario_ja_sorteou(self, usuario_id):
        return SorteioIndividual.query.filter_by(
            grupo_id=self.id,
            usuario_id=usuario_id
        ).first() is not None

    def amigo_do_usuario(self, usuario_id):
        sorteio = SorteioIndividual.query.filter_by(
            grupo_id=self.id,
            usuario_id=usuario_id
        ).first()
        return sorteio.amigo if sorteio else None

    def status_sorteio_membros(self):
        membros_status = []
        for membro in self.membros:
            sorteio = SorteioIndividual.query.filter_by(
                grupo_id=self.id,
                usuario_id=membro.usuario_id
            ).first()

            membros_status.append({
                'membro': membro,
                'ja_sorteou': sorteio is not None,
                'data_sorteio': sorteio.data_sorteio if sorteio else None,
                'amigo_sorteado': sorteio.amigo if sorteio else None
            })
        return membros_status


class MembroGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    data_ingresso = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('User', back_populates='grupos')
    grupo = db.relationship('Grupo', back_populates='membros')


class SorteioIndividual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    amigo_sorteado_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_sorteio = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_visualizacao = db.Column(db.DateTime)
    vezes_visualizado = db.Column(db.Integer, default=0)
    token_acesso = db.Column(db.String(100), unique=True, default=lambda: secrets.token_urlsafe(32))

    usuario = db.relationship('User', foreign_keys=[usuario_id])
    amigo = db.relationship('User', foreign_keys=[amigo_sorteado_id])
    grupo = db.relationship('Grupo', back_populates='sorteios_individual')

    def registrar_visualizacao(self):
        self.ultima_visualizacao = datetime.utcnow()
        self.vezes_visualizado += 1
        db.session.commit()


class SugestaoPresente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    grupo = db.relationship('Grupo', back_populates='sugestoes')
    usuario = db.relationship('User', back_populates='sugestoes')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def enviar_email(destinatario, assunto, corpo_html):
    try:
        params = {
            "from": "Amigo Secreto <no-reply@resend.dev>",
            "to": [destinatario],
            "subject": assunto,
            "html": corpo_html
        }
        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        nome = request.form['nome']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return redirect(url_for('register'))

        user = User(email=email, nome=nome)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Email ou senha inválidos!', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    membro_grupos = MembroGrupo.query.filter_by(usuario_id=current_user.id).all()
    grupos_ids = [mg.grupo_id for mg in membro_grupos]
    grupos = Grupo.query.filter(Grupo.id.in_(grupos_ids)).all()

    meus_grupos = Grupo.query.filter_by(admin_id=current_user.id).all()

    return render_template('dashboard.html', grupos=grupos, meus_grupos=meus_grupos)


@app.route('/grupo/criar', methods=['GET', 'POST'])
@login_required
def criar_grupo():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        data_evento = request.form.get('data_evento')
        local_evento = request.form.get('local_evento')
        valor_minimo = request.form.get('valor_minimo')
        valor_maximo = request.form.get('valor_maximo')

        import secrets
        codigo_acesso = secrets.token_hex(5)[:10].upper()

        grupo = Grupo(
            nome=nome,
            descricao=descricao,
            codigo_acesso=codigo_acesso,
            admin_id=current_user.id,
            data_evento=parser.parse(data_evento) if data_evento else None,
            local_evento=local_evento,
            valor_minimo=float(valor_minimo) if valor_minimo else None,
            valor_maximo=float(valor_maximo) if valor_maximo else None
        )

        db.session.add(grupo)
        db.session.commit()

        membro = MembroGrupo(usuario_id=current_user.id, grupo_id=grupo.id)
        db.session.add(membro)
        db.session.commit()

        flash('Grupo criado com sucesso!', 'success')
        return redirect(url_for('ver_grupo', grupo_id=grupo.id))

    return render_template('criar_grupo.html')


@app.route('/grupo/<int:grupo_id>')
@login_required
def ver_grupo(grupo_id):
    grupo = Grupo.query.get_or_404(grupo_id)

    membro = MembroGrupo.query.filter_by(
        usuario_id=current_user.id,
        grupo_id=grupo_id
    ).first()

    if not membro and grupo.admin_id != current_user.id:
        flash('Acesso negado!', 'error')
        return redirect(url_for('dashboard'))

    membros = MembroGrupo.query.filter_by(grupo_id=grupo_id).all()
    sugestoes = SugestaoPresente.query.filter_by(grupo_id=grupo_id).all()

    ja_sorteou = grupo.usuario_ja_sorteou(current_user.id)
    amigo_sorteado = grupo.amigo_do_usuario(current_user.id)

    status_membros = grupo.status_sorteio_membros() if grupo.admin_id == current_user.id else []

    return render_template('grupo.html',
                           grupo=grupo,
                           membros=membros,
                           sugestoes=sugestoes,
                           ja_sorteou=ja_sorteou,
                           amigo_sorteado=amigo_sorteado,
                           status_membros=status_membros)


@app.route('/grupo/entrar', methods=['POST'])
@login_required
def entrar_grupo():
    codigo = request.form['codigo'].strip().upper()
    grupo = Grupo.query.filter_by(codigo_acesso=codigo).first()

    if not grupo:
        flash('Código inválido!', 'error')
        return redirect(url_for('dashboard'))

    existente = MembroGrupo.query.filter_by(
        usuario_id=current_user.id,
        grupo_id=grupo.id
    ).first()

    if existente:
        flash('Você já é membro deste grupo!', 'warning')
        return redirect(url_for('ver_grupo', grupo_id=grupo.id))

    membro = MembroGrupo(usuario_id=current_user.id, grupo_id=grupo.id)
    db.session.add(membro)
    db.session.commit()

    flash('Você entrou no grupo com sucesso!', 'success')
    return redirect(url_for('ver_grupo', grupo_id=grupo.id))

@app.route('/grupo/<int:grupo_id>/sorteio')
@login_required
def tela_sorteio(grupo_id):
    grupo = Grupo.query.get_or_404(grupo_id)

    membro = MembroGrupo.query.filter_by(
        usuario_id=current_user.id,
        grupo_id=grupo_id
    ).first()

    if not membro:
        flash('Você não é membro deste grupo!', 'error')
        return redirect(url_for('dashboard'))

    sorteio_existente = SorteioIndividual.query.filter_by(
        usuario_id=current_user.id,
        grupo_id=grupo_id
    ).first()

    if sorteio_existente:
        return redirect(url_for('ver_meu_sorteio', token=sorteio_existente.token_acesso))

    membros = MembroGrupo.query.filter_by(grupo_id=grupo_id).all()
    participantes = [m.usuario for m in membros if m.usuario_id != current_user.id]

    if len(participantes) < 1:
        flash('Não há participantes suficientes para sortear!', 'error')
        return redirect(url_for('ver_grupo', grupo_id=grupo_id))

    return render_template('sorteio_tela.html',
                           grupo=grupo,
                           participantes=participantes)


@app.route('/grupo/<int:grupo_id>/realizar-sorteio', methods=['POST'])
@login_required
def realizar_sorteio_individual(grupo_id):
    grupo = Grupo.query.get_or_404(grupo_id)

    membro = MembroGrupo.query.filter_by(
        usuario_id=current_user.id,
        grupo_id=grupo_id
    ).first()

    if not membro:
        return jsonify({'error': 'Você não é membro deste grupo!'}), 403

    sorteio_existente = SorteioIndividual.query.filter_by(
        usuario_id=current_user.id,
        grupo_id=grupo_id
    ).first()

    if sorteio_existente:
        return jsonify({
            'error': 'Você já realizou o sorteio!',
            'redirect': url_for('ver_meu_sorteio', token=sorteio_existente.token_acesso)
        }), 400

    membros = MembroGrupo.query.filter_by(grupo_id=grupo_id).all()
    participantes = [m.usuario for m in membros if m.usuario_id != current_user.id]

    if len(participantes) < 1:
        return jsonify({'error': 'Não há participantes disponíveis!'}), 400

    amigo_sorteado = random.choice(participantes)

    sorteio = SorteioIndividual(
        usuario_id=current_user.id,
        grupo_id=grupo_id,
        amigo_sorteado_id=amigo_sorteado.id,
        token_acesso=secrets.token_urlsafe(32)
    )

    db.session.add(sorteio)
    db.session.commit()

    return jsonify({
        'success': True,
        'amigo': {
            'id': amigo_sorteado.id,
            'nome': amigo_sorteado.nome,
            'email': amigo_sorteado.email
        },
        'token': sorteio.token_acesso,
        'redirect': url_for('ver_meu_sorteio', token=sorteio.token_acesso)
    })


@app.route('/meu-sorteio/<string:token>')
@login_required
def ver_meu_sorteio(token):
    sorteio = SorteioIndividual.query.filter_by(token_acesso=token).first_or_404()

    if sorteio.usuario_id != current_user.id:
        flash('Acesso negado! Este sorteio não é seu.', 'error')
        return redirect(url_for('dashboard'))

    sorteio.registrar_visualizacao()

    grupo = Grupo.query.get(sorteio.grupo_id)
    sugestoes_amigo = SugestaoPresente.query.filter_by(
        grupo_id=grupo.id,
        usuario_id=sorteio.amigo_sorteado_id
    ).all()

    return render_template('ver_sorteio.html',
                           sorteio=sorteio,
                           grupo=grupo,
                           amigo=sorteio.amigo,
                           sugestoes_amigo=sugestoes_amigo)



@app.route('/grupo/<int:grupo_id>/sugestoes')
@login_required
def lista_sugestoes(grupo_id):
    grupo = Grupo.query.get_or_404(grupo_id)

    membro = MembroGrupo.query.filter_by(
        usuario_id=current_user.id,
        grupo_id=grupo_id
    ).first()

    if not membro:
        flash('Você não é membro deste grupo!', 'error')
        return redirect(url_for('dashboard'))

    sugestoes = SugestaoPresente.query.filter_by(grupo_id=grupo_id).all()

    sugestoes_por_usuario = {}
    for sugestao in sugestoes:
        if sugestao.usuario_id not in sugestoes_por_usuario:
            sugestoes_por_usuario[sugestao.usuario_id] = {
                'usuario': sugestao.usuario,
                'sugestoes': []
            }
        sugestoes_por_usuario[sugestao.usuario_id]['sugestoes'].append(sugestao)

    return render_template('lista_sugestoes.html',
                           grupo=grupo,
                           sugestoes_por_usuario=sugestoes_por_usuario)


@app.route('/grupo/<int:grupo_id>/sugestao/adicionar', methods=['POST'])
@login_required
def adicionar_sugestao(grupo_id):
    descricao = request.form['descricao']
    link = request.form.get('link', '')

    membro = MembroGrupo.query.filter_by(
        usuario_id=current_user.id,
        grupo_id=grupo_id
    ).first()

    if not membro:
        return jsonify({'error': 'Você não é membro deste grupo!'}), 403

    if not descricao.strip():
        return jsonify({'error': 'Descrição é obrigatória!'}), 400

    sugestao = SugestaoPresente(
        grupo_id=grupo_id,
        usuario_id=current_user.id,
        descricao=descricao.strip(),
        link=link.strip() if link else None
    )

    db.session.add(sugestao)
    db.session.commit()

    return jsonify({
        'success': True,
        'sugestao': {
            'id': sugestao.id,
            'descricao': sugestao.descricao,
            'link': sugestao.link,
            'usuario_nome': current_user.nome,
            'data': sugestao.created_at.strftime('%d/%m/%Y %H:%M')
        }
    })


@app.route('/sugestao/<int:sugestao_id>/editar', methods=['POST'])
@login_required
def editar_sugestao(sugestao_id):
    sugestao = SugestaoPresente.query.get_or_404(sugestao_id)

    if sugestao.usuario_id != current_user.id:
        return jsonify({'error': 'Você não pode editar esta sugestão!'}), 403

    descricao = request.form.get('descricao')
    link = request.form.get('link', '')

    if descricao:
        sugestao.descricao = descricao.strip()

    sugestao.link = link.strip() if link else None
    db.session.commit()

    return jsonify({
        'success': True,
        'sugestao': {
            'id': sugestao.id,
            'descricao': sugestao.descricao,
            'link': sugestao.link
        }
    })


@app.route('/sugestao/<int:sugestao_id>/remover', methods=['POST'])
@login_required
def remover_sugestao(sugestao_id):
    sugestao = SugestaoPresente.query.get_or_404(sugestao_id)

    if sugestao.usuario_id != current_user.id:
        return jsonify({'error': 'Você não pode remover esta sugestão!'}), 403

    db.session.delete(sugestao)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/grupo/<int:grupo_id>/status-sorteio')
@login_required
def api_status_sorteio(grupo_id):
    grupo = Grupo.query.get_or_404(grupo_id)

    if grupo.admin_id != current_user.id:
        return jsonify({'error': 'Acesso negado! Apenas o admin pode ver este status.'}), 403

    status_membros = grupo.status_sorteio_membros()

    return jsonify({
        'grupo': {
            'id': grupo.id,
            'nome': grupo.nome,
            'total_membros': len(status_membros)
        },
        'membros': [
            {
                'id': status['membro'].id,
                'usuario_id': status['membro'].usuario_id,
                'nome': status['membro'].usuario.nome,
                'email': status['membro'].usuario.email,
                'ja_sorteou': status['ja_sorteou'],
                'data_sorteio': status['data_sorteio'].isoformat() if status['data_sorteio'] else None,
                'amigo_sorteado': status['amigo_sorteado'].nome if status['amigo_sorteado'] else None
            }
            for status in status_membros
        ]
    })


if __name__ == '__main__':
    app.run(debug=True)
