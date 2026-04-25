from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # Clients
    path("clients/", views.client_list, name="client_list"),
    path("clients/add/", views.client_add, name="client_add"),
    path("clients/<int:pk>/edit/", views.client_edit, name="client_edit"),
    path("api/clients/search/", views.client_search_api, name="client_search_api"),
    # Лаб. №7: демо-страница + AJAX-проверка дублей ИНН
    path("lab7/", views.lab7_inn_demo, name="lab7_demo"),
    path("api/clients/check_inn/", views.check_duplicate_inn, name="check_duplicate_inn"),
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
    # Лаб. №8: Печатные формы (PDF)
    path("pdf/order/<int:pk>/", views.pdf_order, name="pdf_order"),
    path("pdf/clients/", views.pdf_clients, name="pdf_clients"),
    path("pdf/report/", views.pdf_report, name="pdf_report"),
]
