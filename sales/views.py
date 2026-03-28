import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Sum
from .models import Client, Product, Order, OrderItem


def index(request):
    return render(request, "sales/index.html")


# ─── Clients ────────────────────────────────────────────────────────

def client_list(request):
    query = request.GET.get("q", "")
    clients = Client.objects.all()
    if query:
        clients = clients.filter(name__icontains=query)
    return render(request, "sales/client_list.html", {"clients": clients, "query": query})


def client_search_api(request):
    q = request.GET.get("q", "")
    clients = Client.objects.filter(name__icontains=q)[:10] if q else []
    data = [
        {
            "id": c.id,
            "name": c.name,
            "total_purchases": str(c.total_purchases),
            "current_account": str(c.current_account),
            "credit_limit": str(c.credit_limit),
            "current_debt": str(c.current_debt),
            "credit_remaining": str(c.credit_remaining),
            "comment": c.comment,
            "debt_warning": c.debt_warning,
        }
        for c in clients
    ]
    return JsonResponse(data, safe=False)


def client_add(request):
    if request.method == "POST":
        Client.objects.create(
            name=request.POST["name"],
            total_purchases=Decimal(request.POST.get("total_purchases", "0")),
            current_account=Decimal(request.POST.get("current_account", "0")),
            credit_limit=Decimal(request.POST.get("credit_limit", "0")),
            current_debt=Decimal(request.POST.get("current_debt", "0")),
            comment=request.POST.get("comment", ""),
        )
        return redirect("client_list")
    return render(request, "sales/client_form.html")


def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.name = request.POST["name"]
        client.total_purchases = Decimal(request.POST.get("total_purchases", "0"))
        client.current_account = Decimal(request.POST.get("current_account", "0"))
        client.credit_limit = Decimal(request.POST.get("credit_limit", "0"))
        client.current_debt = Decimal(request.POST.get("current_debt", "0"))
        client.comment = request.POST.get("comment", "")
        client.save()
        return redirect("client_list")
    return render(request, "sales/client_form.html", {"client": client})


# ─── Products ───────────────────────────────────────────────────────

def product_list(request):
    products = Product.objects.all()
    return render(request, "sales/product_list.html", {"products": products})


def product_add(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        price_str = request.POST.get("price", "0")
        stock_str = request.POST.get("stock", "0")
        errors = []
        if not name:
            errors.append("Наименование товара не заполнено.")
        try:
            price = Decimal(price_str)
            if price <= 0:
                errors.append("Цена должна быть больше нуля.")
        except Exception:
            errors.append("Некорректная цена.")
            price = Decimal("0")
        try:
            stock = int(stock_str)
            if stock < 0:
                errors.append("Количество не может быть отрицательным.")
        except Exception:
            errors.append("Некорректное количество.")
            stock = 0
        if errors:
            form_data = {"name": name, "price": price_str, "stock": stock_str}
            return render(request, "sales/product_form.html", {"errors": errors, "form_data": form_data})
        Product.objects.create(name=name, price=price, stock=stock)
        return redirect("product_list")
    return render(request, "sales/product_form.html")


def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        price_str = request.POST.get("price", "0")
        stock_str = request.POST.get("stock", "0")
        errors = []
        if not name:
            errors.append("Наименование товара не заполнено.")
        try:
            price = Decimal(price_str)
            if price <= 0:
                errors.append("Цена должна быть больше нуля.")
        except Exception:
            errors.append("Некорректная цена.")
            price = Decimal("0")
        try:
            stock = int(stock_str)
            if stock < 0:
                errors.append("Количество не может быть отрицательным.")
        except Exception:
            errors.append("Некорректное количество.")
            stock = 0
        if errors:
            return render(request, "sales/product_form.html", {"product": product, "errors": errors})
        product.name = name
        product.price = price
        product.stock = stock
        product.save()
        return redirect("product_list")
    return render(request, "sales/product_form.html", {"product": product})


def product_api(request):
    products = Product.objects.all()
    data = [
        {"id": p.id, "name": p.name, "price": str(p.price), "stock": p.stock}
        for p in products
    ]
    return JsonResponse(data, safe=False)


# ─── Orders ─────────────────────────────────────────────────────────

def order_create(request):
    clients = Client.objects.all()
    products = Product.objects.all()

    if request.method == "POST":
        client_id = request.POST.get("client_id")
        sale_type = request.POST.get("sale_type")
        items_json = request.POST.get("items_json", "[]")

        barter_items_json = request.POST.get("barter_items_json", "[]")

        client = get_object_or_404(Client, pk=client_id)
        items_data = json.loads(items_json)
        barter_items_data = json.loads(barter_items_json)

        warnings = []

        # Validate barter items
        if sale_type == "barter":
            if not barter_items_data:
                warnings.append("Для бартера необходимо указать товары в обмен.")
            else:
                barter_total = Decimal("0")
                for bi in barter_items_data:
                    if not bi.get("product_id"):
                        warnings.append("Есть незаполненные товары в обмене.")
                        break
                    bp = Product.objects.filter(pk=bi["product_id"]).first()
                    if bp:
                        barter_total += bp.price * int(bi.get("quantity", 0))
                items_total = Decimal("0")
                for item in items_data:
                    p = Product.objects.filter(pk=item.get("product_id")).first()
                    if p:
                        items_total += p.price * int(item.get("quantity", 0))
                if abs(items_total - barter_total) >= Decimal("0.01"):
                    warnings.append(f"Суммы не совпадают: отдано {items_total} руб., получено {barter_total} руб.")

        # Validate items
        for item in items_data:
            if not item.get("product_id"):
                warnings.append("Есть строки с незаполненным товаром.")
                break
            if Decimal(str(item.get("price", 0))) <= 0:
                warnings.append("Есть строки с нулевой ценой.")
                break
            if int(item.get("quantity", 0)) <= 0:
                warnings.append("Есть строки с нулевым количеством.")
                break

        if warnings:
            return JsonResponse({"status": "error", "warnings": warnings})

        order = Order.objects.create(
            client=client, sale_type=sale_type, total_sum=0
        )

        total = Decimal("0")
        for item in items_data:
            product = get_object_or_404(Product, pk=item["product_id"])
            qty = int(item["quantity"])
            price = product.price
            line_total = price * qty

            OrderItem.objects.create(
                order=order, product=product, quantity=qty, price=price
            )
            total += line_total

            # Update stock based on sale type
            if sale_type in ("cash", "cashless", "credit"):
                product.stock -= qty
                product.save()
            elif sale_type == "barter":
                # For barter, items being sold decrease stock
                # Items being received increase stock (handled via barter_items)
                product.stock -= qty
                product.save()
            elif sale_type == "offset":
                product.stock += qty
                product.save()

        order.total_sum = total
        order.save()

        # Update client accounts based on sale type
        if sale_type == "cash":
            client.total_purchases += total
        elif sale_type == "cashless":
            client.total_purchases += total
            client.current_account -= total
        elif sale_type == "credit":
            client.total_purchases += total
            if client.current_account > 0:
                account_use = min(client.current_account, total)
                client.current_account -= account_use
                remaining = total - account_use
            else:
                remaining = total
            client.current_debt += remaining
        elif sale_type == "barter":
            # Increase stock for received barter items
            for bi in barter_items_data:
                barter_product = get_object_or_404(Product, pk=bi["product_id"])
                bqty = int(bi["quantity"])
                barter_product.stock += bqty
                barter_product.save()
        elif sale_type == "offset":
            client.current_debt -= total
        client.save()

        result = {
            "status": "ok",
            "order_id": order.pk,
            "debt_warning": client.debt_warning,
            "current_debt": str(client.current_debt),
            "credit_remaining": str(client.credit_remaining),
        }

        # Credit warning
        if sale_type == "credit" and client.debt_warning:
            result["credit_warning"] = (
                f"Текущий долг клиента ({client.current_debt} руб.) приближается "
                f"к потолку кредита ({client.credit_limit} руб.)!"
            )

        return JsonResponse(result)

    return render(
        request,
        "sales/order_create.html",
        {"clients": clients, "products": products},
    )


def order_list(request):
    orders = Order.objects.select_related("client").prefetch_related("items__product").all()
    return render(request, "sales/order_list.html", {"orders": orders})


def report(request):
    clients = Client.objects.all()
    report_data = []
    for client in clients:
        orders = Order.objects.filter(client=client)
        orders_info = []
        for order in orders:
            items = order.items.select_related("product").all()
            orders_info.append({"order": order, "items": items})
        report_data.append({
            "client": client,
            "orders": orders_info,
            "total": orders.aggregate(total=Sum("total_sum"))["total"] or 0,
        })
    return render(request, "sales/report.html", {"report_data": report_data})


# ═══════════════════════════════════════════════════════════════════════
# V2 — Альтернативный дизайн (боковая навигация, градиенты)
# ═══════════════════════════════════════════════════════════════════════

def index_v2(request):
    return render(request, "sales/v2/index.html")


def client_list_v2(request):
    query = request.GET.get("q", "")
    clients = Client.objects.all()
    if query:
        clients = clients.filter(name__icontains=query)
    return render(request, "sales/v2/client_list.html", {"clients": clients, "query": query})


def client_add_v2(request):
    if request.method == "POST":
        Client.objects.create(
            name=request.POST["name"],
            total_purchases=Decimal(request.POST.get("total_purchases", "0")),
            current_account=Decimal(request.POST.get("current_account", "0")),
            credit_limit=Decimal(request.POST.get("credit_limit", "0")),
            current_debt=Decimal(request.POST.get("current_debt", "0")),
            comment=request.POST.get("comment", ""),
        )
        return redirect("client_list_v2")
    return render(request, "sales/v2/client_form.html")


def client_edit_v2(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.name = request.POST["name"]
        client.total_purchases = Decimal(request.POST.get("total_purchases", "0"))
        client.current_account = Decimal(request.POST.get("current_account", "0"))
        client.credit_limit = Decimal(request.POST.get("credit_limit", "0"))
        client.current_debt = Decimal(request.POST.get("current_debt", "0"))
        client.comment = request.POST.get("comment", "")
        client.save()
        return redirect("client_list_v2")
    return render(request, "sales/v2/client_form.html", {"client": client})


def product_list_v2(request):
    products = Product.objects.all()
    return render(request, "sales/v2/product_list.html", {"products": products})


def product_add_v2(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        price_str = request.POST.get("price", "0")
        stock_str = request.POST.get("stock", "0")
        errors = []
        if not name:
            errors.append("Наименование товара не заполнено.")
        try:
            price = Decimal(price_str)
            if price <= 0:
                errors.append("Цена должна быть больше нуля.")
        except Exception:
            errors.append("Некорректная цена.")
            price = Decimal("0")
        try:
            stock = int(stock_str)
            if stock < 0:
                errors.append("Количество не может быть отрицательным.")
        except Exception:
            errors.append("Некорректное количество.")
            stock = 0
        if errors:
            form_data = {"name": name, "price": price_str, "stock": stock_str}
            return render(request, "sales/v2/product_form.html", {"errors": errors, "form_data": form_data})
        Product.objects.create(name=name, price=price, stock=stock)
        return redirect("product_list_v2")
    return render(request, "sales/v2/product_form.html")


def product_edit_v2(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        price_str = request.POST.get("price", "0")
        stock_str = request.POST.get("stock", "0")
        errors = []
        if not name:
            errors.append("Наименование товара не заполнено.")
        try:
            price = Decimal(price_str)
            if price <= 0:
                errors.append("Цена должна быть больше нуля.")
        except Exception:
            errors.append("Некорректная цена.")
            price = Decimal("0")
        try:
            stock = int(stock_str)
            if stock < 0:
                errors.append("Количество не может быть отрицательным.")
        except Exception:
            errors.append("Некорректное количество.")
            stock = 0
        if errors:
            return render(request, "sales/v2/product_form.html", {"product": product, "errors": errors})
        product.name = name
        product.price = price
        product.stock = stock
        product.save()
        return redirect("product_list_v2")
    return render(request, "sales/v2/product_form.html", {"product": product})


def order_create_v2(request):
    clients = Client.objects.all()
    products = Product.objects.all()
    return render(request, "sales/v2/order_create.html", {"clients": clients, "products": products})


def order_list_v2(request):
    orders = Order.objects.select_related("client").prefetch_related("items__product").all()
    return render(request, "sales/v2/order_list.html", {"orders": orders})


def report_v2(request):
    clients = Client.objects.all()
    report_data = []
    for client in clients:
        orders = Order.objects.filter(client=client)
        orders_info = []
        for order in orders:
            items = order.items.select_related("product").all()
            orders_info.append({"order": order, "items": items})
        report_data.append({
            "client": client,
            "orders": orders_info,
            "total": orders.aggregate(total=Sum("total_sum"))["total"] or 0,
        })
    return render(request, "sales/v2/report.html", {"report_data": report_data})
