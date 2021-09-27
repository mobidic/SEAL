from flask import redirect, url_for, request
from flask_login import current_user
from flask_admin import Admin, AdminIndexView
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from seal import app, db
from seal.models import User, Team, Sample, Family, Variant, Comment, Var2Sample, Filter, Gene, Transcript


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.admin
        return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))


class AdminView(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.admin
        return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))


admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(AdminView(User, db.session, category="Authentication"))
admin.add_view(AdminView(Team, db.session, category="Authentication"))
admin.add_view(AdminView(Sample, db.session, category="Analysis"))
admin.add_view(AdminView(Family, db.session, category="Analysis"))
admin.add_view(AdminView(Variant, db.session, category="Analysis"))
admin.add_view(AdminView(Comment, db.session, category="Analysis"))
admin.add_view(AdminView(Var2Sample, db.session, category="Analysis"))
admin.add_view(AdminView(Filter, db.session, category="Filter"))
admin.add_view(AdminView(Gene, db.session, category="Genes"))
admin.add_view(AdminView(Transcript, db.session, category="Genes"))
admin.add_link(MenuLink(name='Home Page', url='/', category='Links'))
