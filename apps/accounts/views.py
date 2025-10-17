# apps/accounts/views.py
from django.shortcuts import render, redirect

def role_gate(request):
    # SI YA ESTA LOGUEADO Y LLEGA CON ?role=, REDIRIGE AL DASHBOARD
    role = request.GET.get("role")
    if request.user.is_authenticated and role:
        return redirect(f"/dashboard/{role}/")
    return render(request, "accounts/role_login.html")
