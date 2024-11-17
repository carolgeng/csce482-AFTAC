import reflex as rx

# downloads google's SDK and supplies client id
class GoogleOAuthProvider(rx.Component):
    library = "@react-oauth/google"
    tag = "GoogleOAuthProvider"

    client_id: rx.Var[str]

# renders 'sign in with google' button
class GoogleLogin(rx.Component):
    library = "@react-oauth/google"
    tag = "GoogleLogin"

    on_success: rx.EventHandler[lambda data: [data]]
