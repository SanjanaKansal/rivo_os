"""
Permissions for the leads app.

We now use Django REST Framework's built-in DjangoModelPermissions instead of custom permissions.

DjangoModelPermissions automatically checks:
- view_source / view_rawlead for GET (list/retrieve)
- add_source / add_rawlead for POST (create)
- change_source / change_rawlead for PUT/PATCH (update)
- delete_source / delete_rawlead for DELETE

Permissions are assigned to users via their Role in the admin panel.

Data visibility (what users see) is controlled via get_queryset() in views:
- Sources: Users see only sources they own
- Leads: Users see only leads assigned to them or by them
- Staff/Superusers see everything
"""