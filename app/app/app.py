from .pages.user import user_page
from .pages.admin import admin_page
from .pages.login import login_page
import reflex as rx

app = rx.App()
app.add_page(login_page)
app.add_page(user_page)
app.add_page(admin_page)
