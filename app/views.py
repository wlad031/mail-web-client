import json

import requests
from flask import render_template, request, redirect, url_for, session, flash
from flask.ext.paginate import Pagination

from app import app, cfg
from forms import LoginForm, RegisterForm, MailForm
from models import User, LoggedUser

api_url = cfg.ServerConfig['API_URL']

headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}


@app.errorhandler(404)
def error_404():
    return _render_template('error_page.html', status_code=404, message='Page not found')


@app.errorhandler(401)
def error_401():
    return _render_template('error_page.html', status_code=401, message='Unauthorized access')


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

        r = requests.get(api_url + '/token', headers=headers, auth=(form.username.data, form.password.data))

        # Successfully authorization
        if r.status_code == 200:
            data = json.loads(r.text)
            session['user'] = User(id=data['id'], username=data['username'], token=data['token']).__dict__
            return redirect(url_for('index'))

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

        r = requests.post(api_url + '/user', headers=headers,
                          data=json.dumps({'username': form.username.data, 'password': form.password.data}))

        # Successfully registration
        if r.status_code == 201:
            r = requests.get(api_url + '/token', headers=headers, auth=(form.username.data, form.password.data))
            data = json.loads(r.text)
            session['user'] = User(username=data['username'], token=data['token']).__dict__
            return redirect(url_for('index'))

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

    r = requests.get(api_url + '/mail/' + mail_id, headers=headers, auth=(session['user']['token'], 'unused'))

    if r.status_code == 200:
        mail = json.loads(r.text)['mail']

        if section == 'inbox':
            requests.put(api_url + '/mail/' + mail_id, headers=headers, auth=(session['user']['token'], 'unused'),
                         data=json.dumps({'is_viewed': True}))

        if section == 'draft':
            form = MailForm()
            # form.recipient.data = mail.recipient.username
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
                                mail=add_names_to_mail(mail),
                                new_mails_count=new_mails_count(),
                                draft_mails_count=draft_mails_count())

    else:
        return _render_template('error_page.html', status_code=r.status_code)


@app.route('/delete/<string:section>/<mail_id>')
def delete_mail(section, mail_id):
    if section not in sections:
        return _render_template('error_page.html', status_code=400, message='Page not found')

    r = requests.get(api_url + '/mail/' + mail_id, headers=headers, auth=(session['user']['token'], 'unused'))

    if r.status_code == 200:
        r1 = requests.delete(api_url + '/mail/' + mail_id, headers=headers, auth=(session['user']['token'], 'unused'))

        if r1.status_code == 200:
            flash('Message was successfully deleted', 'success')
            return redirect('/mailbox/' + section)

    else:
        return _render_template('error_page.html', status_code=r.status_code)


@app.route('/mailbox')
@app.route('/mailbox/<string:section>')
@app.route('/mailbox/<string:section>/<int:page>')
def get_all_mails(section='inbox', page=1):
    if section not in sections:
        return _render_template('error_page.html', status_code=404, message='Page not found')

    total_count = len(get_my_mails(section))

    if total_count < 1:
        flash('In this category there is no mail', 'info')

    mails = get_my_mails(section)

    pagination = Pagination(page=page,
                            per_page=cfg.AppConfig['MAIL_PER_PAGE'],
                            total=total_count,
                            bs_version=3)

    return _render_template('mails.html',
                            data=add_names_to_mails(mails),
                            section=section,
                            pagination=pagination,
                            new_mails_count=new_mails_count(),
                            draft_mails_count=draft_mails_count())


@app.route('/mail_form/new', methods=['POST', 'GET'])
@app.route('/mail_form/draft/<mail_id>', methods=['POST', 'GET'])
def mail_form(mail_id=0):
    form = MailForm()

    if request.method == 'POST':

        recipient = form.subject.data
        subject = form.subject.data
        text = form.text.data

        if request.form['submit'] == 'save':
            mail_status = 'draft'
        if request.form['submit'] == 'send':
            mail_status = 'sent'

        if mail_id == 0:
            requests.put(api_url + '/mail', headers=headers, auth=(session['user']['token'], 'unused'),
                         data={'recipient_id': recipient,
                               'subject': subject,
                               'text': text,
                               'status': mail_status})

            if request.form['submit'] == 'send':
                flash('Mail was successfully sent', 'success')
            if request.form['submit'] == 'save':
                flash('Mail was successfully saved', 'success')

            return redirect(url_for('get_all_mails'))

        if mail_id != 0:
            requests.put(api_url + '/mail/' + str(mail_id), headers=headers, auth=(session['user']['token'], 'unused'),
                         data={'recipient_id': recipient,
                               'subject': subject,
                               'text': text,
                               'status': mail_status})

            if request.form['submit'] == 'send':
                flash('Mail was successfully sent', 'success')
            if request.form['submit'] == 'save':
                flash('Mail was successfully saved', 'success')

            return redirect('/mailbox/draft')

    else:
        return _render_template('mail_form.html',
                                form=form,
                                section='new',
                                new_mails_count=new_mails_count(),
                                draft_mails_count=draft_mails_count())


def get_all_my_mails():
    print session
    r = requests.get(api_url + '/mail', headers=headers, auth=(session['user']['token'], 'unused'))
    if r.status_code == 200:
        return json.loads(r.text)['mails']
    return None


def get_my_mails(section):
    if section not in sections:
        return None

    mails = get_all_my_mails()

    if section == 'inbox':
        return list([mail for mail in mails
                     if mail['status'] == 'sent' and mail['recipient_id'] == session['user']['id']])
    if section == 'draft':
        return list([mail for mail in mails
                     if mail['status'] == 'draft' and mail['sender_id'] == session['user']['id']])
    if section == 'sent':
        return list([mail for mail in mails
                     if mail['status'] == 'sent' and mail['sender_id'] == session['user']['id']])
    return None


def new_mails_count():
    k = 0
    for mail in get_my_mails('inbox'):
        if mail['is_viewed']:
            k += 1
    return k


def draft_mails_count():
    return len(get_my_mails('draft'))


def add_names_to_mails(mails, single=False):
    return list([add_names_to_mail(mail) for mail in mails])


def add_names_to_mail(mail):
    rr = requests.get(api_url + '/user/' + mail['recipient_id'],
                      headers=headers, auth=(session['user']['token'], 'unused'))
    recipient_name = json.loads(rr.text)['username']

    rs = requests.get(api_url + '/user/' + mail['sender_id'],
                      headers=headers, auth=(session['user']['token'], 'unused'))
    sender_name = json.loads(rs.text)['username']

    mail.update({'recipient_name': recipient_name, 'sender_name': sender_name})
    return mail


def _render_template(template, **kwargs):
    return render_template(template,
                           user=(LoggedUser(username=session['user']['username'])
                                 if 'user' in session.keys() else None), **kwargs)
