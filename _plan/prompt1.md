Rivo Django Project

Create a Django 5+ project with Django REST Framework.

Project Setup
```bash
django-admin startproject rivo .
```

Create two apps:
- `account`
- `dashboard`

**Note:** Don't create urls.py or any models yet.

---

Models (account app)

Add these models to `account/models.py`:
```python

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Role(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')

    def __str__(self):
        return self.name


class User(AbstractUser, BaseModel):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    def __str__(self):
        return self.email or self.username
```

Authentication (account app)

Create login and logout APIs using DRF TokenAuthentication.

Frontend (dashboard app)

Create a simple elegant interface for login and logout. Use your frontend-design skills.

Questions

Before starting, please ask me any clarifying questions you need about:
- Authentication flow
- UI design preferences
- Any other technical decisions

Then build the project.
