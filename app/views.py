import json

import requests
from flask import render_template, request, redirect, url_for, session, flash
from flask.ext.paginate import Pagination

from app import app, cfg, helper
from forms import LoginForm, RegisterForm, MailForm
from models import User, LoggedUser

api_url = cfg.ServerConfig['API_URL']
headers = cfg.ServerConfig['HEADERS']


@app.errorhandler(404)
def error_404(error):
    return _render_template('error_page.html', status_code=404, message='Page not found')


@app.errorhandler(401)
def error_401(error):
    return _render_template('error_page.html', status_code=401, message='Unauthorized access')


@app.errorhandler(400)
def error_400(error):
    return _render_template('error_page.html', status_code=400, message='Bad request')


@app.route('/')
def index():
    return _render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if request.method == 'POST':

        if not form.validate_on_submit():
            flash('Wrong username or password', 'danger')
            return _render_template('login.html', form=form)

        r = requests.get(api_url + '/token',
                         headers=headers,
                         auth=(form.username.data + '@' + cfg.AppConfig['MAIL_DOMAIN'], form.password.data))

        # Successfully authorization
        if r.status_code == 200:
            data = json.loads(r.text)
            session['user'] = User(id=data['id'], username=data['username'], token=data['token']).__dict__
            return redirect(url_for('get_all_mails'))

        # Server hotfix
        if r.status_code == 401:
            flash('Wrong username or password', 'danger')
            return _render_template('login.html', form=form)

        flash(json.loads(r.text)['error'], 'danger')
        return _render_template('login.html', form=form)

    else:
        return _render_template('login.html', form=form)


@app.route('/logout')
def logout():
    if session['user']:
        del session['user']

    return redirect(url_for('index'))


@app.route('/join', methods=['POST', 'GET'])
def register():
    form = RegisterForm()

    if request.method == 'POST':

        if not form.validate_on_submit():
            flash('Invalid name or/and password', 'danger')
            return _render_template('join.html', form=form)

        r = requests.put(api_url + '/user',
                         headers=headers,
                         data=json.dumps({'username': form.username.data,
                                          'password': form.password.data}))

        # Successfully registration
        if r.status_code == 201:
            r = requests.get(api_url + '/token',
                             headers=headers,
                             auth=(form.username.data + '@' + cfg.AppConfig['MAIL_DOMAIN'], form.password.data))
            data = json.loads(r.text)
            session['user'] = User(id=data['id'], username=data['username'], token=data['token']).__dict__
            return redirect(url_for('get_all_mails'))

        # Errors
        flash(json.loads(r.text)['error'], 'danger')
        return _render_template('join.html', form=form)

    else:
        return _render_template('join.html', form=form)


# Mails

sections = ('inbox', 'sent', 'draft')


@app.route('/mail/<string:section>/<int:mail_id>')
def get_mail(mail_id, section):
    if section not in sections:
        return _render_template('error_page.html', status_code=404, message='Page not found')

    r = requests.get(api_url + '/mail/' + str(mail_id),
                     headers=headers,
                     auth=(session['user']['token'], 'unused'))

    if r.status_code == 200:
        mail = json.loads(r.text)['mail']

        # Set the flag is_viewed as True
        if section == 'inbox':
            requests.put(api_url + '/mail/' + str(mail_id),
                         headers=headers,
                         auth=(session['user']['token'], 'unused'),
                         data=json.dumps({'recipient': None,
                                          'subject': None,
                                          'text': None,
                                          'status': None,
                                          'is_viewed': True}))

        # Fill form fields
        if section == 'draft':
            form = MailForm()
            form.recipient.data = mail['recipient']
            form.subject.data = mail['subject']
            form.text.data = mail['text']

            return _render_template('mail_form.html',
                                    section='draft',
                                    form=form,
                                    updated_id=mail_id,
                                    new_mails_count=new_mails_count(),
                                    draft_mails_count=draft_mails_count())

        return _render_template('mail.html',
                                section=section,
                                mail=format_mail(mail),
                                new_mails_count=new_mails_count(),
                                draft_mails_count=draft_mails_count())

    else:
        return _render_template('error_page.html', status_code=r.status_code)


@app.route('/delete/<string:section>/<mail_id>')
def delete_mail(section, mail_id):
    if section not in sections:
        return _render_template('error_page.html', status_code=400, message='Page not found')

    r1 = requests.delete(api_url + '/mail/' + mail_id,
                         headers=headers,
                         auth=(session['user']['token'], 'unused'))

    if r1.status_code == 200:
        flash('Message was successfully deleted', 'success')
        return redirect('/mailbox/' + section)
    else:
        return _render_template('error_page.html', status_code=r1.status_code)


@app.route('/mailbox')
@app.route('/mailbox/<string:section>')
@app.route('/mailbox/<string:section>/<int:page>')
def get_all_mails(section='inbox', page=1):
    if section not in sections:
        return _render_template('error_page.html', status_code=404, message='Page not found')

    mails = get_my_mails(section)
    total_count = len(mails)
    mails_per_page = cfg.AppConfig['MAIL_PER_PAGE']

    if total_count < 1:
        flash('In this category there is no mail', 'info')

    mails = mails[((page - 1) * mails_per_page):(page * mails_per_page)]

    pagination = Pagination(page=page,
                            per_page=mails_per_page,
                            total=total_count,
                            bs_version=3)

    return _render_template('mails.html',
                            data=format_mails(mails),
                            section=section,
                            pagination=pagination,
                            new_mails_count=new_mails_count(),
                            draft_mails_count=draft_mails_count())


@app.route('/mail_form/new', methods=['POST', 'GET'])
@app.route('/mail_form/draft/<mail_id>', methods=['POST', 'GET'])
def mail_form(mail_id=0):
    form = MailForm()

    if request.method == 'POST':

        recipient = form.recipient.data
        subject = form.subject.data
        text = form.text.data

        mail_status = None
        if request.form['submit'] == 'save':
            mail_status = 'draft'
        if request.form['submit'] == 'send':
            mail_status = 'sent'

        if mail_id == 0:
            r1 = requests.put(api_url + '/mail',
                              headers=headers,
                              auth=(session['user']['token'], 'unused'),
                              data=json.dumps({'recipient': recipient,
                                               'subject': subject,
                                               'text': text,
                                               'status': mail_status}))
        else:
            r1 = requests.put(api_url + '/mail/' + str(mail_id),
                              headers=headers,
                              auth=(session['user']['token'], 'unused'),
                              data=json.dumps({'recipient': recipient,
                                               'subject': subject,
                                               'text': text,
                                               'status': mail_status}))
        if r1.status_code == 400:
            flash(json.loads(r1.text)['error'], 'danger')
        elif r1.status_code == 201 or r1.status_code == 200:
            if request.form['submit'] == 'send':
                flash('Mail was successfully sent', 'success')
            if request.form['submit'] == 'save':
                flash('Mail was successfully saved', 'success')
        else:
            return _render_template('error_page.html', status_code=r1.status_code)

        return redirect(url_for('get_all_mails'))

    else:
        return _render_template('mail_form.html',
                                form=form,
                                section='new',
                                new_mails_count=new_mails_count(),
                                draft_mails_count=draft_mails_count())


def get_all_my_mails():
    r = requests.get(api_url + '/mail',
                     headers=headers,
                     auth=(session['user']['token'], 'unused'))

    if r.status_code == 200:
        return json.loads(r.text)['mails']

    return None


def get_my_mails(section):
    if section not in sections:
        return None

    mails = get_all_my_mails()

    if section == 'inbox':
        return list([mail for mail in mails
                     if mail['status'] == 'sent' and mail['recipient'] == session['user']['username']])
    if section == 'draft':
        return list([mail for mail in mails
                     if mail['status'] == 'draft' and mail['sender_id'] == session['user']['id']])
    if section == 'sent':
        return list([mail for mail in mails
                     if mail['status'] == 'sent' and mail['sender_id'] == session['user']['id']])
    return None


def new_mails_count():
    k = 0
    for mail in get_my_mails(section='inbox'):
        if not mail['is_viewed']:
            k += 1
    return k


def draft_mails_count():
    return len(get_my_mails('draft'))


def format_mails(mails):
    return list([format_mail(mail) for mail in mails])


def format_mail(mail):
    sender_name = get_username(mail['sender_id'])
    timestamp = helper.format_timestamp(mail['timestamp'])

    return {'id': mail['id'],
            'recipient_name': mail['recipient'],
            'sender_name': sender_name,
            'subject': mail['subject'],
            'text': mail['text'],
            'timestamp': timestamp,
            'is_viewed': mail['is_viewed']}


def get_username(user_id):
    r = requests.get(api_url + '/user/' + str(user_id),
                     headers=headers,
                     auth=(session['user']['token'], 'unused'))
    if r.status_code == 200:
        return json.loads(r.text)['username']
    return None


def _render_template(template, **kwargs):
    return render_template(template,
                           user=(LoggedUser(username=session['user']['username'])
                                 if 'user' in session.keys() else None), **kwargs)
