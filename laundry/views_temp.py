# ============================================================
# AUTHENTICATION
# ============================================================
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/login/')
