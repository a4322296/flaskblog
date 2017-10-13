# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, FileField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from ..models import Role, User
from flask_pagedown.fields import PageDownField


class EditProfileForm(FlaskForm):
    avatar = FileField(u'头像')
    name = StringField(u'真实姓名', validators=[Length(0, 64)])
    location = StringField(u'详细地址', validators=[Length(0, 64)])
    about_me = TextAreaField(u'自我介绍')
    submit = SubmitField(u'提交')


class EditProfileAdminForm(FlaskForm):
    email = StringField(u'邮箱', validators=[
                        Required(), Length(1, 64), Email()])
    username = StringField(u'用户名', validators=[Required(), Length(1, 64),
                                               Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                      'Usernames must have only letters, members, dots and underscores.')])
    confirmed = BooleanField(u'是否认证')
    role = SelectField(u'角色', coerce=int)
    name = StringField(u'真实姓名', validators=[Length(0, 64)])
    location = StringField(u'住址', validators=[Length(0, 64)])
    about_me = TextAreaField(u'自我介绍')
    submit = SubmitField(u'提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already register.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class PostForm(FlaskForm):
    title = StringField(u'标题', validators=[Required(), Length(2)])
    tags = StringField(u'标签', validators=[Required()])
    body = TextAreaField(u'快写下你的想法吧！', validators=[Required()])
    submit = SubmitField(u'提交')


class CommentForm(FlaskForm):
    body = StringField('', validators=[Required()])
    submit = SubmitField(u'提交')


class SendmessageForm(FlaskForm):
    body = StringField(u'私信内容', validators=[Length(0, 256)])
    submit = SubmitField(u'发送')
