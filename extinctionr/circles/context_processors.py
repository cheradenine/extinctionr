from .forms import SimpleSignupForm


def signup(request):
    return {
        'simple_signup_form': SimpleSignupForm()
    }
