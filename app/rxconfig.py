import reflex as rx

config = rx.Config(
    app_name="app",
    frontend_port=3000,  # Force frontend port
    backend_port=8000,   # Force backend port
)