from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView


class CustomView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/custom.html')


class CustomModelView(ModelView):
    pass