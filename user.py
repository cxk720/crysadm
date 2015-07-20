__author__ = 'powergx'
from flask import request, Response, render_template, session, url_for, redirect
from XunleiCrystal import app, r_session
from auth import requires_admin, requires_auth
import json
from util import hash_password
import uuid
import re


@app.route('/user/login', methods=['POST'])
def user_login():
    username = request.values.get('username')
    password = request.values.get('password')

    hashed_password = hash_password(password)

    user_info = r_session.get('%s:%s' % ('user', username))
    if user_info is None:
        session['error_message'] = '用户不存在'
        return redirect(url_for('login'))

    user = json.loads(user_info.decode('utf-8'))

    if user.get('password') != hashed_password:
        session['error_message'] = '密码错误'
        return redirect(url_for('login'))

    session['user_info'] = user

    return redirect(url_for('dashboard'))


@app.route('/login')
def login():
    if session.get('user_info') is not None:
        return redirect(url_for('dashboard'))

    err_msg = None
    if session.get('error_message') is not None:
        err_msg = session.get('error_message')
        session['error_message'] = None

    return render_template('login.html', err_msg=err_msg)


@app.route('/user/logout')
@requires_auth
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/user/profile')
@requires_auth
def user_profile():
    user = session.get('user_info')

    user_key = '%s:%s' % ('user', user.get('username'))
    user_info = json.loads(r_session.get(user_key).decode('utf-8'))

    err_msg = None
    if session.get('error_message') is not None:
        err_msg = session.get('error_message')
        session['error_message'] = None
    action = None
    if session.get('action') is not None:
        action = session.get('action')
        session['action'] = None

    return render_template('profile.html', user_info=user_info, err_msg=err_msg, action=action)


@app.route('/user/change_info', methods=['POST'])
@requires_auth
def user_change_info():
    user = session.get('user_info')
    email = request.values.get('email')
    session['action'] = 'info'
    r = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

    if re.match(r, email) is None:
        session['error_message'] = '邮箱地址格式不正确.'

        return redirect(url_for('user_profile'))

    user_key = '%s:%s' % ('user', user.get('username'))
    user_info = json.loads(r_session.get(user_key).decode('utf-8'))

    user_info['email'] = email
    r_session.set(user_key, json.dumps(user_info))

    return redirect(url_for('user_profile'))


@app.route('/user/change_password', methods=['POST'])
@requires_auth
def user_change_password():
    user = session.get('user_info')
    o_password = request.values.get('old_password')
    n_password = request.values.get('new_password')
    n2_password = request.values.get('new2_password')
    session['action'] = 'password'

    if n_password != n2_password:
        session['error_message'] = '新密码输入不一致.'
        return redirect(url_for('user_profile'))

    r = r"(?!^[0-9]*$)(?!^[a-zA-Z]*$)^([a-zA-Z0-9]{6,15})$"

    if re.match(r, n_password) is None:
        session['error_message'] = '密码太弱了(6~15位数字加字母).'
        return redirect(url_for('user_profile'))

    user_key = '%s:%s' % ('user', user.get('username'))
    user_info = json.loads(r_session.get(user_key).decode('utf-8'))

    hashed_password = hash_password(o_password)

    if user_info.get('password') != hashed_password:
        session['error_message'] = '原密码错误'
        return redirect(url_for('user_profile'))

    user_info['password'] = hash_password(n_password)
    r_session.set(user_key, json.dumps(user_info))

    return redirect(url_for('user_profile'))


@app.route('/register')
def register():
    if session.get('user_info') is not None:
        return redirect(url_for('dashboard'))

    err_msg = None
    if session.get('error_message') is not None:
        err_msg = session.get('error_message')
        session['error_message'] = None

    invitation_code = request.values.get('inv_code')



    return render_template('register.html', err_msg=err_msg)


@app.route('/user/register', methods=['POST'])
def user_register():
    invitation_code = request.values.get('invitation_code')
    username = request.values.get('username')
    password = request.values.get('password')
    re_password = request.values.get('re_password')

    if r_session.get('%s:%s' % ('user', username)) is not None:
        return '账号已存在'
    user = dict(username=username, password=hash_password(password), id=str(uuid.uuid1()),
                active=True, is_admin=False, max_account_no=2, refresh_interval=30)
    r_session.set('%s:%s' % ('user', username), json.dumps(user))
    r_session.sadd('users', username)
    return '创建成功'
