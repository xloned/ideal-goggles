from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # Clients
    path("clients/", views.client_list, name="client_list"),
    path("clients/add/", views.client_add, name="client_add"),
    path("clients/<int:pk>/edit/", views.client_edit, name="client_edit"),
    path("api/clients/search/", views.client_search_api, name="client_search_api"),
    # Products
    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_add, name="product_add"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("api/products/", views.product_api, name="product_api"),
    # Orders
    path("orders/create/", views.order_create, name="order_create"),
    path("orders/", views.order_list, name="order_list"),
    # Report
    path("report/", views.report, name="report"),
    # ─── V2 Design ───
    path("v2/", views.index_v2, name="index_v2"),
    path("v2/clients/", views.client_list_v2, name="client_list_v2"),
    path("v2/clients/add/", views.client_add_v2, name="client_add_v2"),
    path("v2/clients/<int:pk>/edit/", views.client_edit_v2, name="client_edit_v2"),
    path("v2/products/", views.product_list_v2, name="product_list_v2"),
    path("v2/products/add/", views.product_add_v2, name="product_add_v2"),
    path("v2/products/<int:pk>/edit/", views.product_edit_v2, name="product_edit_v2"),
    path("v2/orders/create/", views.order_create_v2, name="order_create_v2"),
    path("v2/orders/", views.order_list_v2, name="order_list_v2"),
    path("v2/report/", views.report_v2, name="report_v2"),
]
