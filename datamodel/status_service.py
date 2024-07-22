from datamodel.models import *

def set_admin_primary():
    # check, which db should be activated for the admins
    # default db
    status_default = DatamodelStatus.objects.using("default").get(id=0)        
    status_default.is_admin_primary = not status_default.is_admin_primary
    status_default.save(using="default")

    # only_datamodel db
    status_only_datamodel = DatamodelStatus.objects.using("only_datamodel").get(id=0)        
    status_only_datamodel.is_admin_primary = not status_only_datamodel.is_admin_primary
    status_only_datamodel.save(using="only_datamodel")

def set_user_primary():
    # check, which db should be activated for the users
    # default db
    status_default = DatamodelStatus.objects.using("default").get(id=0)        
    status_default.is_user_primary = not status_default.is_user_primary
    status_default.save(using="default")

    # only_datamodel db
    status_only_datamodel = DatamodelStatus.objects.using("only_datamodel").get(id=0)        
    status_only_datamodel.is_user_primary = not status_only_datamodel.is_user_primary
    status_only_datamodel.save(using="only_datamodel")

