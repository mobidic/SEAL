import re

from flask import redirect, url_for, request, flash
from flask_admin import Admin, AdminIndexView
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from seal import app, db, bcrypt
from seal.models import (User, Team, Sample, Family, Variant, Comment_variant,
                         Comment_sample, Var2Sample, Filter, Transcript, Run,
                         Region, Bed, Phenotype, Omim, History)


BCRYPT_PATTERN = re.compile("^\$2[aby]?\$\d{1,2}\$[.\/A-Za-z0-9]{53}$")


class MyAdminIndexView(AdminIndexView):
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


admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(
    UserView(
        User,
        db.session,
        category = "Authentication",
        column_exclude_list = ['password', 'transcripts'],
        column_searchable_list = ['username', 'mail', 'api_key_md'],
        column_editable_list = ['username', 'mail', 'filter', "api_key_md"],
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
admin.add_view(
    SampleView(
        Sample,
        db.session,
        category="Analysis",
        column_searchable_list = ["samplename"],
        column_editable_list = ['samplename', 'status'],
        form_excluded_columns = ['variants', 'historics']
    )
)
admin.add_view(
    CustomView(
        History,
        db.session,
        category="Analysis",
        column_searchable_list = ["action"]
    )
)
admin.add_view(
    CustomView(
        Family,
        db.session,
        category="Analysis",
        column_searchable_list = ["family"],
        column_editable_list = ['family']
    )
)
admin.add_view(
    CustomView(
        Run,
        db.session,
        category="Analysis",
        column_searchable_list = ["name", "alias"],
        column_editable_list = ["name", "alias"]
    )
)
admin.add_view(
    CustomView(
        Variant,
        db.session,
        category="Analysis",
        column_searchable_list = ["chr", "pos", "ref", "alt", "annotations"],
        column_editable_list = ["chr", "pos", "ref", "alt", "class_variant"],
        form_excluded_columns = ['samples']
    )
)
admin.add_view(
    CustomView(
        Comment_variant,
        db.session,
        category="Analysis",
        column_searchable_list = ["comment"],
        column_editable_list = ["comment"]
    )
)
admin.add_view(
    CustomView(
        Comment_sample,
        db.session,
        category="Analysis",
        column_searchable_list = ["comment"],
        column_editable_list = ["comment"]
    )
)
admin.add_view(
    CustomView(
        Var2Sample,
        db.session,
        category="Analysis",
        column_searchable_list = ["filter", "variant.id", "sample.samplename",
                                  "sample.family.family"],
        column_editable_list = ["depth", "allelic_depth"]
    )
)
admin.add_view(
    CustomView(
        Filter,
        db.session,
        category="Filter",
        column_searchable_list = ["filtername", "filter"],
        column_editable_list = ["filtername"],
        form_excluded_columns = ['users','samples']
    )
)

admin.add_view(
    CustomView(
        Transcript,
        db.session,
        category="Genes",
        column_searchable_list = ["feature", "biotype", "feature_type",
                                  "symbol", "symbol_source", "gene", "source",
                                  "protein", "canonical", "hgnc"],
        column_editable_list = ["biotype", "feature_type", "symbol",
                                "symbol_source", "gene", "source", "protein",
                                "canonical", "hgnc"]
    )
)

admin.add_view(
    CustomView(
        Region,
        db.session,
        category="Bed",
        column_searchable_list = ["name", "chr", "start", "stop"],
        column_editable_list = ["name", "chr", "start", "stop"]
    )
)

admin.add_view(
    CustomView(
        Bed,
        db.session,
        category="Bed",
        column_searchable_list = ["name"],
        column_editable_list = ["name"],
        form_excluded_columns = ['regions','samples']
    )
)


admin.add_view(
    CustomView(
        Phenotype,
        db.session,
        category="Phenotypes",
        column_searchable_list = ["phenotypeMimNumber", "phenotype",
                                  "inheritances", "phenotypeMappingKey"],
    )
)


admin.add_view(
    CustomView(
        Omim,
        db.session,
        category="Phenotypes",
        column_searchable_list = ["mimNumber", "approvedGeneSymbol",
                                  "comments", "computedCytoLocation",
                                  "cytoLocation", "ensemblGeneID",
                                  "entrezGeneID", "geneSymbols"],
    )
)

admin.add_link(MenuLink(name='Home Page', url='/', category='Links'))
