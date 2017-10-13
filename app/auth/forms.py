#-*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField(u'电子邮箱', validators=[Required(),
                                             Length(1, 64), Email()])
    password = PasswordField(u'密码', validators=[Required()])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField(u'登录')


class RegistrationForm(FlaskForm):
    email = StringField(u'电子邮箱', validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField(u'用户名', validators=[Required(), Length(1, 64),
                                                   Regexp('^[A-Za-z0-9_.]*$', 0,
                                                          u'用户名只能由数字字母下划线构成')])
    password = PasswordField(u'密码', validators=[Required(), EqualTo('password2',
                                                                         message=u'密码必须一致')])
    password2 = PasswordField(u'请确认密码', validators=[Required()])
    submit = SubmitField(u'注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'该邮箱已经被注册')

    def validate_usernaem(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'该用户名已经被使用')


class PasswordChangeForm(FlaskForm):
    old_password = PasswordField(u'请输入密码', validators=[
                                 Required(), Length(1, 64)])
    password = PasswordField(u'请输入新密码', validators=[
                             Required(), Length(1, 64)])
    password2 = PasswordField(u'确认密码', validators=[Required(),
                                                                EqualTo('password', message=u'请输入相同的密码')])
    submit = SubmitField(u'确认更改')


class PasswordResetRequestForm(FlaskForm):
    email = StringField(u'密码', validators=[Required(), Email()])
    submit = SubmitField(u'提交')


class PasseordResetForm(FlaskForm):
    email = StringField(u'邮箱', validators=[
                        Required(), Length(1, 64), Email()])
    password = PasswordField(u'密码', validators=[
                             Required(), Length(1, 64)])
    password2 = PasswordField(u'确认密码', validators=[Required(), Length(
        1, 64), EqualTo('password', message=u'请输入相同的密码')])
    submit = SubmitField(u'重置密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'错误的电子邮箱地址')


class ChangeEmailForm(FlaskForm):
    email = StringField(u'邮箱', validators=[
                        Required(), Length(1, 64), Email()])
    password = PasswordField(u'密码', validators=[Required(),Length(1, 64)])
    submit = SubmitField(u'更新邮箱')

    def validate_email(self, field):
    	if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'该邮箱已经被注册')
