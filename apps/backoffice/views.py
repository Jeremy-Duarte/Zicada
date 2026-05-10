from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_dashboard(request):
    context = {'section': 'dashboard'}
    return render(request, 'backoffice/admin_dashboard.html', context)

@staff_member_required
def admin_orders(request):
    context = {'section': 'orders'}
    return render(request, 'backoffice/admin_orders.html', context)

@staff_member_required
def admin_products(request):
    context = {'section': 'products'}
    return render(request, 'backoffice/admin_products.html', context)

@staff_member_required
def admin_users(request):
    context = {'section': 'users'}
    return render(request, 'backoffice/admin_users.html', context)

@staff_member_required
def admin_config(request):
    context = {'section': 'config'}
    return render(request, 'backoffice/admin_config.html', context)