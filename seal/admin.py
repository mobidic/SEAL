from flask import redirect, url_for, request
from flask_login import current_user
from flask_admin import Admin, AdminIndexView
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from seal import app, db
from seal.models import User, Team, Sample, Family, Variant, Comment, Var2Sample, Filter, Transcript, Run, Region, Bed


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.admin
        return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))


class CustomView(ModelView):

    column_exclude_list = []
    column_searchable_list = []
    column_editable_list = []
    column_display_pk = True
    column_hide_backrefs = False
    form_excluded_columns = []

    def __init__(self, *args, **kwargs):
        if 'column_exclude_list' in kwargs:
            self.column_exclude_list = kwargs.pop('column_exclude_list')
        if 'column_searchable_list' in kwargs:
            self.column_searchable_list = kwargs.pop('column_searchable_list')
        if 'column_editable_list' in kwargs:
            self.column_editable_list = kwargs.pop('column_editable_list')
        if 'form_excluded_columns' in kwargs:
            self.form_excluded_columns = kwargs.pop('form_excluded_columns')
        super(CustomView, self).__init__(*args, **kwargs)

    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.admin
        return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))


admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(
    CustomView(
        User,
        db.session,
        category="Authentication",
        column_exclude_list=['password', 'transcripts'],
        column_searchable_list=['username', 'mail'],
        column_editable_list=['username', 'mail', 'filter'],
        form_excluded_columns=['comments', 'transcripts']
    )
)
admin.add_view(
    CustomView(
        Team,
        db.session,
        category="Authentication",
        column_searchable_list=['teamname'],
        column_editable_list=['teamname', 'color'],
        form_excluded_columns=['members', 'samples']
    )
)
admin.add_view(
    CustomView(
        Sample,
        db.session,
        category="Analysis",
        column_searchable_list=["samplename"],
        column_editable_list=['samplename', 'status'],
        form_excluded_columns=['variants']
    )
)
admin.add_view(
    CustomView(
        Family,
        db.session,
        category="Analysis",
        column_searchable_list=["family"],
        column_editable_list=['family']
    )
)
admin.add_view(
    CustomView(
        Run,
        db.session,
        category="Analysis",
        column_searchable_list=["name", "alias"],
        column_editable_list=["name", "alias"]
    )
)
admin.add_view(
    CustomView(
        Variant,
        db.session,
        category="Analysis",
        column_searchable_list=["chr", "pos", "ref", "alt", "annotations"],
        column_editable_list=["chr", "pos", "ref", "alt", "class_variant"],
        form_excluded_columns=['samples']
    )
)
admin.add_view(
    CustomView(
        Comment,
        db.session,
        category="Analysis",
        column_searchable_list=["comment"],
        column_editable_list=["comment"]
    )
)
admin.add_view(
    CustomView(
        Var2Sample,
        db.session,
        category="Analysis",
        column_searchable_list=["filter"],
        column_editable_list=["depth", "allelic_depth"]
    )
)
admin.add_view(
    CustomView(
        Filter,
        db.session,
        category="Filter",
        column_searchable_list=["filtername", "filter"],
        column_editable_list=["filtername"],
        form_excluded_columns=['users']
    )
)

admin.add_view(
    CustomView(
        Transcript,
        db.session,
        category="Genes",
        column_searchable_list=["feature", "biotype", "feature_type", "symbol", "symbol_source", "gene", "source", "protein", "canonical", "hgnc"],
        column_editable_list=["biotype", "feature_type", "symbol", "symbol_source", "gene", "source", "protein", "canonical", "hgnc"]
    )
)

admin.add_view(
    CustomView(
        Region,
        db.session,
        category="Bed"
    )
)

admin.add_view(
    CustomView(
        Bed,
        db.session,
        category="Bed"
    )
)

admin.add_link(MenuLink(name='Home Page', url='/', category='Links'))
