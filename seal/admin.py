# (c) 2023, Charles VAN GOETHEM <c-vangoethem (at) chu-montpellier (dot) fr>
#
# This file is part of SEAL
# 
# SEAL db - Simple, Efficient And Lite database for NGS
# Copyright (C) 2023  Charles VAN GOETHEM - MoBiDiC - CHU Montpellier
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re

from flask import redirect, url_for, request, flash
from flask_admin import expose, AdminIndexView, Admin
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from seal import app, db, bcrypt
from seal.models import (User, Team, Sample, Family, Variant, Comment_variant,
                         Comment_sample, Var2Sample, Filter, Transcript, Run,
                         Region, Bed, Phenotype, Omim, History, Clinvar)

###############################################################################


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        cnt = {
            "user": User.query.count(),
            "sample": Sample.query.count(),
            "variant": Variant.query.count(),
            "family": Family.query.count(),
            "bed": Bed.query.count(),
        }
        return self.render('admin/index.html', cnt=cnt)
    """
    Custom class for Flask-Admin index view.

    Attributes:
        None

    Methods:
        is_accessible(): Checks if the current user is authenticated and has
                         admin access.
        inaccessible_callback(name, **kwargs): Redirects to the login page if
                                               the user doesn't have access.
    """
    def is_accessible(self):
        """
        Determines if the current user has access to the admin view.

        Returns:
            bool: True if the current user is authenticated and has admin
                  access, False otherwise.
        """
        if current_user.is_authenticated:
            return current_user.admin
        return False

    def inaccessible_callback(self, name, **kwargs):
        """
        Redirects to the login page if the current user doesn't have access to
        the admin view.

        Args:
            name: The name of the view.
            **kwargs: Additional arguments.

        Returns:
            redirect: A Flask redirect to the login page.
        """
        return redirect(url_for('login', next=request.url))

    def is_visible(self):
        # This view won't appear in the menu structure
        return False


class CustomView(ModelView):
    """
    Custom class for Flask-Admin ModelView.

    Attributes:
        column_exclude_list (list): Columns to exclude from the view.
        column_searchable_list (list): Columns to make searchable.
        column_editable_list (list): Columns to make editable.
        column_display_pk (bool): Whether to display the primary key column.
        column_hide_backrefs (bool): Whether to hide backref columns.
        form_excluded_columns (list): Columns to exclude from the form.

    Methods:
        __init__(*args, **kwargs): Initializes the CustomView instance.
        is_accessible(): Checks if the current user is authenticated and has
                         admin access.
        inaccessible_callback(name, **kwargs): Redirects to the login page if
                                               the user doesn't have access.
    """

    column_exclude_list = []
    column_searchable_list = []
    column_editable_list = []
    column_display_pk = True
    column_hide_backrefs = False
    form_excluded_columns = []

    def __init__(self, *args, **kwargs):
        """
        Initializes CustomView.

        Args:
            *args: Arguments.
            **kwargs: Keyword arguments.

        Returns:
            None.
        """
        if 'column_exclude_list' in kwargs:
            self.column_exclude_list = kwargs.pop('column_exclude_list')
        if 'column_searchable_list' in kwargs:
            self.column_searchable_list = kwargs.pop('column_searchable_list')
        if 'column_editable_list' in kwargs:
            self.column_editable_list = kwargs.pop('column_editable_list')
        if 'column_orderable_list' in kwargs:
            self.column_orderable_list = kwargs.pop('column_orderable_list')
        if 'form_excluded_columns' in kwargs:
            self.form_excluded_columns = kwargs.pop('form_excluded_columns')
        super(CustomView, self).__init__(*args, **kwargs)

    def is_accessible(self):
        """
        Determines if the current user has access to the view.

        Returns:
            bool: True if the current user is authenticated and has access,
                  False otherwise.
        """
        if current_user.is_authenticated:
            return current_user.admin
        return False

    def inaccessible_callback(self, name, **kwargs):
        """
        Redirects to the login page if the current user doesn't have access to
        the view.

        Args:
            name: The name of the view.
            **kwargs: Additional arguments.

        Returns:
            redirect: A Flask redirect to the login page.
        """
        return redirect(url_for('login', next=request.url))


class SampleView(CustomView):
    """
    Custom class for Flask-Admin ModelView for the Sample model.

    Attributes:
        None

    Methods:
        delete_model(model): Deletes the specified sample and associated data
                             from the database.
    """
    def delete_model(self, model):
        """
        Deletes a sample model.

        Args:
            model: The model to delete.

        Returns:
            bool: True if the model was deleted successfully, False otherwise.
        """
        try:
            self.session.flush()

            var2samples = db.session.query(Var2Sample).filter(Var2Sample.sample_ID == int(model.id))
            for var2sample in var2samples:
                self.session.delete(var2sample)

            historical = db.session.query(History).filter(History.sample_ID == int(model.id))
            for history in historical:
                self.session.delete(history)

            self.session.delete(model)
            self.session.commit()
        except Exception as ex:
            flash(f'Failed to delete record: {ex} (Please contact the admin)', 'error')
            app.logger.exception(f'Failed to delete record: {ex}')
            self.session.rollback()

            return False
        else:
            self.after_model_delete(model)

        return True


class UserView(CustomView):
    """
    Custom class for Flask-Admin ModelView for the User model.

    Attributes:
        None

    Methods:
        on_model_change(form, model, is_created): Hashes the user's password if
                                                  it's not already hashed.
        validate_form(form): Custom validation code that checks if the password
                             is long enough or a correct hash.
    """
    def on_model_change(self, form, model, is_created):
        """
        Called when a user object is created or modified. Hashes the user's
        password before storing it in the database.

        Args:
            form: The form object.
            model: The User model object.
            is_created: Boolean indicating whether the user is being created or modified.
        """
        if BCRYPT_PATTERN.match(model.password):
            return False
        model.password = bcrypt.generate_password_hash(model.password).decode('utf-8')

    def validate_form(self, form):
        """
        Custom validation code that checks the user's password for length and
        correct hashing format.

        Args:
            form: The form object.

        Returns:
            Boolean indicating whether the form is valid or not.
        """
        try:
            if (form.password.data and len(form.password.data) < 6 and
                    not BCRYPT_PATTERN.match(form.password.data)):
                flash("""The password must be more than 6 characters long or a
                      correct hash (please change)!""")
                return False
        except AttributeError:
            pass
        return super(UserView, self).validate_form(form)


###############################################################################


admin = Admin(app, index_view = MyAdminIndexView(), template_mode='bootstrap3')
BCRYPT_PATTERN = re.compile("^\$2[aby]?\$\d{1,2}\$[.\/A-Za-z0-9]{53}$")


###############################################################################


admin.add_category(name="Authentication")

admin.add_view(
    UserView(
        User,
        db.session,
        category = "Authentication",
        column_exclude_list = ['password', 'transcripts'],
        column_searchable_list = ['username', 'mail', 'api_key_md'],
        column_editable_list = ['username', 'mail', 'filter', 'api_key_md',
                                'logged', 'admin', 'bioinfo', 'technician',
                                'biologist', 'sidebar'],
        form_excluded_columns = ['comments_variants', 'comments_samples', 
                                 'historics', 'transcripts']
    )
)
admin.add_view(
    CustomView(
        Team,
        db.session,
        category="Authentication",
        column_searchable_list = ['teamname'],
        column_editable_list = ['teamname', 'color'],
        form_excluded_columns = ['members', 'samples']
    )
)


###############################################################################


admin.add_category(name="Analysis")

admin.add_sub_category(name="Sample", parent_name="Analysis")
admin.add_sub_category(name="Run", parent_name="Analysis")
admin.add_sub_category(name="Variant", parent_name="Analysis")

admin.add_view(
    SampleView(
        Sample,
        db.session,
        category="Sample",
        column_searchable_list = ['filter.filtername', 'bed.name',
                                  'family.family', 'run.name', 'samplename'],
        column_editable_list = ['filter', 'bed', 'family', 'run', 'samplename',
                                'status', 'affected', 'index'],
        form_excluded_columns = ['variants', 'historics']
    )
)
admin.add_view(
    CustomView(
        Family,
        db.session,
        category="Sample",
        column_searchable_list = ['family'],
        column_editable_list = ['family']
    )
)
admin.add_view(
    CustomView(
        Run,
        db.session,
        category="Run",
        column_searchable_list = ['name', 'alias'],
        column_editable_list = ['name', 'alias']
    )
)
admin.add_view(
    CustomView(
        Variant,
        db.session,
        category="Variant",
        column_searchable_list = ['chr', 'pos', 'ref', 'alt', 'class_variant', 'clinvar_VARID', 'clinvar_CLNSIG', 'clinvar_CLNSIGCONF', 'clinvar_CLNREVSTAT'],
        column_editable_list = ['chr', 'pos', 'ref', 'alt', 'class_variant', 'clinvar_VARID', 'clinvar_CLNSIG', 'clinvar_CLNSIGCONF', 'clinvar_CLNREVSTAT'],
        column_exclude_list = ['annotations'],
        form_excluded_columns = ['samples']
    )
)
admin.add_view(
    CustomView(
        Comment_variant,
        db.session,
        category="Variant",
        column_searchable_list = ['variant.id', 'user.username', 'comment', 'date'],
        column_editable_list = ['user', 'comment'],
        form_excluded_columns = ['variant']
    )
)
admin.add_view(
    CustomView(
        Comment_sample,
        db.session,
        category="Sample",
        column_searchable_list = ['sample.samplename', 'user.username', 'comment', 'date'],
        column_editable_list = ['sample', 'user', 'comment']
    )
)
admin.add_view(
    CustomView(
        Var2Sample,
        db.session,
        category="Variant",
        column_searchable_list = ['filter', 'variant.id', 'sample.samplename',
                                  'sample.family.family'],
        column_editable_list = ['depth', 'allelic_depth', 'reported', 'hide']
    )
)
admin.add_view(
    CustomView(
        History,
        db.session,
        category="Analysis",
        column_searchable_list = ['user.username', 'sample.samplename', 'date',
                                  'action'],
        column_editable_list = ['user', 'sample', 'action'],
    )
)
admin.add_view(
    CustomView(
        Filter,
        db.session,
        category="Analysis",
        column_searchable_list = ['filtername', 'filter'],
        column_editable_list = ['filtername'],
        form_excluded_columns = ['users', 'samples']
    )
)

admin.add_view(
    CustomView(
        Clinvar,
        db.session,
        category="Analysis"
    )
)


###############################################################################


admin.add_category(name="Genes")

admin.add_sub_category(name="Bed", parent_name="Genes")
admin.add_sub_category(name="OMIM", parent_name="Genes")

admin.add_view(
    CustomView(
        Transcript,
        db.session,
        category="Genes",
        column_searchable_list = ['feature', 'biotype', 'feature_type',
                                  'symbol', 'symbol_source', 'gene', 'source',
                                  'protein', 'canonical', 'hgnc'],
        column_editable_list = ['biotype', 'feature_type', 'symbol',
                                'symbol_source', 'gene', 'source', 'protein',
                                'canonical', 'hgnc']
    )
)

admin.add_view(
    CustomView(
        Region,
        db.session,
        category="Bed",
        column_searchable_list = ['name', 'chr', 'start', 'stop'],
        column_editable_list = ['name', 'chr', 'start', 'stop']
    )
)

admin.add_view(
    CustomView(
        Bed,
        db.session,
        category="Bed",
        column_searchable_list = ['name'],
        column_editable_list = ['name'],
        form_excluded_columns = ['regions','samples']
    )
)


admin.add_view(
    CustomView(
        Phenotype,
        db.session,
        category="OMIM",
        column_searchable_list = ['phenotypeMimNumber', 'phenotype',
                                  'inheritances', 'phenotypeMappingKey'],
        column_editable_list = ['phenotypeMimNumber', 'phenotype',
                                'phenotypeMappingKey']
    )
)


admin.add_view(
    CustomView(
        Omim,
        db.session,
        category="OMIM",
        column_searchable_list = ['mimNumber', 'approvedGeneSymbol',
                                  'comments', 'computedCytoLocation',
                                  'cytoLocation', 'ensemblGeneID',
                                  'entrezGeneID', 'geneSymbols'],
        column_editable_list = ['approvedGeneSymbol',
                                  'comments', 'computedCytoLocation',
                                  'cytoLocation', 'ensemblGeneID',
                                  'entrezGeneID']
    )
)
