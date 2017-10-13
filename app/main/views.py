# -*- coding: utf-8 -*-
from flask import render_template, abort, redirect, url_for, flash, request, current_app, make_response, g
from . import main
from ..models import User, Role, Permission, Post, Comment, Tag, Message
from flask_login import login_required, current_user
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, SendmessageForm
from .. import db, cache
from ..decorators import admin_required, permission_required
from ..utils import keywords_split


def change_tags(tags):
    l = []
    for tag in keywords_split(tags):
        tag_obj = Tag.query.filter_by(name=tag).first()
        if tag_obj is None:
            tag_obj = Tag(name=tag)
            db.session.add(tag_obj)
            db.session.commit()
        l.append(tag_obj)
    return l


@main.route('/', methods=['GET', 'POST'])
def index():
    g.tags = Tag.query.all()
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    # 为了显示某页中的记录，要把 all() 换成 Flask-SQLAlchemy 提供的 paginate() 方法。页数是 paginate() 方法的第一个参数，也是唯一必需的参数。可选参数 per_page 用来指定每页显示的记录数量；如果没有指定，则默认显示 20 个记录。另一个可选参数为 error_out ，当其设为 True 时（默认值），如果请求的页数超出了范围，则会返回 404 错误；如果设为 False ，页数超出范围时会返回一个空列表。为了能够很便利地配置每页显示的记录数量，参数 per_page 的值从程序的环境变量 FLASKY_POSTS_PER_PAGE 中读取。这样修改之后，首页中的文章列表只会显示有限数量的文章。若想查看第 2 页中的文章，要在浏览器地址栏中的 URL 后加上查询字符串 ?page=2。
    pagination = query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                error_out=False)
    posts = pagination.items

    import flask_whooshalchemyplus
    flask_whooshalchemyplus.index_one_model(Post)
    return render_template('index.html',  posts=posts,
                           show_followed=show_followed, pagination=pagination)


@main.route('/new-post', methods=['GET', 'POST'])
def new_post():
    form = PostForm()
    g.tags = Tag.query.all()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data, title=form.title.data,
                    author=current_user._get_current_object())

        # add tags to post
        for t in change_tags(form.tags.data):
            if t:
                post.tags.append(t)
        db.session.add(post)
        return redirect(url_for('.index'))
    return render_template('new_post.html', form=form)

@cache.cached(timeout=300)
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                     error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts, pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        avatar = request.files['avatar']
        fname = avatar.filename
        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
        flag = '.' in fname and fname.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
        if not flag:
            flash('文件类型错误')
            return redirect(url_for('.user', username=current_user.username))
        avatar.save('{}{}_{}'.format(UPLOAD_FOLDER, current_user.username, fname))
        current_user.real_avatar = '/static/avatar/{}_{}'.format(current_user.username, fname)
        db.session.add(current_user)
        flash(u'资料已经更新.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash(u'资料已经更新')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash(u'评论已经发表.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.tags = form.tags.data
        db.session.add(post)
        flash(u'文章已更新.')
        return redirect(url_for('.post', id=post.id))
    form.title.data = post.title
    form.body.data = post.body
    tag= post.tags.all()
    for i in tag:
        n = i.name
    form.tags.data = n
    return render_template('edit_post.html', form=form, post=post)


@main.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    db.session.delete(post)
    flash(u'文章已经被删除')
    return redirect(url_for('.index', id=post.id))


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'未登录，请登录')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash(u'已关注.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'未登录， 请登录')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash(u'已取消关注')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(page,
                                         per_page=current_app.config[
                                             'FLASKY_FOLLOWERS_PER_PAGE'],
                                         error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='Followers of',
                           endpoint='.followers', pagination=pagination, follows=follows)


@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination, follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/moderate', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments, pagination=pagination,
                           page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/tags/<name>', methods=['GET', 'POST'])
def tag(name):
    tag = Tag.query.filter_by(name=name).first()
    return render_template('result.html', item=tag)


@main.route('/tags', methods=['GET', 'POST'])
def tags_posts():
    tags = Tag.query.all()
    return render_template('tags.html', tags=tags)


#点赞
@main.route('/agree/<id>')
@login_required
def agree(id):
    post = Post.query.filter_by(id=id).first()
    if post is None:
        flash(u'答案找不到了')
        return redirect(url_for('.index'))
    if current_user.is_agreeing(post):
        flash(u'已经点过赞了.')
        return redirect(url_for('.index'))
    current_user.agree(post)
    flash(u'点赞成功')
    return redirect(url_for('.index'))

#取消点赞
@main.route('/unagree/<id>')
@login_required
def unagree(id):
    post = Post.query.filter_by(id=id).first()
    if post is None:
        flash(u'答案找不到了')
        return redirect(url_for('.index'))
    if not current_user.is_agreeing(post):
        flash(u'还没点过赞呢.')
        return redirect(url_for('.index', id=id))
    current_user.unagree(post)
    flash(u'取消成功!')
    return redirect(url_for('.index', id=id))

#搜索文章的路由
@main.route('/search/', methods=['GET', 'POST'])
@login_required
def search():
    #获取搜索表单传过来的数据
    keyword = request.form.get('q','default value')

    page = request.args.get('page', 1, type=int)
    show_followed = False

    pagination = Post.query.whoosh_search(keyword).order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items

    return render_template('searched.html',posts=posts, show_followed=show_followed, pagination=pagination)


@main.route('/showmessage')
@login_required
@permission_required(Permission.COMMENT)
def showmessage():
    page = request.args.get('page', 1, type=int)
    pagination = Message.query.order_by(Message.timestamp.desc()).filter_by(sendto=current_user).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    messages = pagination.items
    return render_template('showmessage.html', messages=messages,
                           pagination=pagination, page=page )


@main.route('/showmessage/unconfirmed/<int:id>')
@login_required
@permission_required(Permission.COMMENT)
def showmessage_unconfirmed(id):
    message = Message.query.get_or_404(id)
    message.confirmed = True
    db.session.add(message)
    return redirect(url_for('.showmessage',
                            page=request.args.get('page', 1, type=int)))


@main.route('/showmessage/confirmed/<int:id>')
@login_required
@permission_required(Permission.COMMENT)
def showmessage_confirmed(id):
    message = Message.query.get_or_404(id)
    message.confirmed = False
    db.session.add(message)
    return redirect(url_for('.showmessage',
                            page=request.args.get('page', 1, type=int)))


@main.route('/showmessage/delete/<int:id>')
@login_required
@permission_required(Permission.COMMENT)
def message_delete(id):
    message = Message.query.get_or_404(id)
    db.session.delete(message)
    flash(u'私信删除成功')
    return redirect(url_for('.showmessage',
                            page=request.args.get('page', 1, type=int)))


@main.route('/sendmessage/<username>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.COMMENT)
def sendmessage(username):
    user = User.query.filter_by(username=username).first()
    form = SendmessageForm()
    if form.validate_on_submit():
        message = Message(body=form.body.data, \
                          author=current_user,
                          sendto=user)
        db.session.add(message)
        db.session.commit()
        flash(u'私信发送成功')
        return redirect(url_for('.user', username=username))

    return render_template('sendmessage.html', form=form, )

