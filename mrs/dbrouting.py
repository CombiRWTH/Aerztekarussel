import threading
from django.conf import settings
from datamodel.models import *

request_cfg = threading.local()

class RouterMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        return response

    def get_db(self, is_superuser):
        # get the current used db for user
        dmStatusCache, created = DatamodelStatus.objects.using("default").get_or_create(
            id=0,
            defaults={"is_admin_primary": True, "is_user_primary": True},
        )

        if (is_superuser and dmStatusCache.is_admin_primary) or (not is_superuser and dmStatusCache.is_user_primary):
            return "default"
        else:
            return "only_datamodel"

    def process_view(self, request, view_func, view_args, view_kwargs):
        request_cfg.db = self.get_db(request.user.is_superuser)

    def process_response(self, request, response):
        if hasattr(request_cfg, 'db'):
            del request_cfg.db
        return response

class DatabaseRouter(object):
    def _default_db(self):
        # evaluate if teh Middleware specified a database
        if hasattr(request_cfg, 'db') and request_cfg.db in settings.DATABASES:
            return request_cfg.db
        else:
            return 'default'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == "datamodel":
            return self._default_db()

        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "datamodel":
            return self._default_db()

        return "default"

    def allow_relation(self, obj1, obj2, **hints):

        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if not app_label == "datamodel" and db == "only_datamodel":
            return False

        return True