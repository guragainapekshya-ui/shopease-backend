
from django.contrib import admin
from app.orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "customer_name",
        "phone",
        "total_amount",
        "status",
        "created_at",
    )

    list_filter = ("status", "created_at")
    list_editable = ("status",)

    search_fields = (
        "user__username",
        "user__email",
        "customer_name",
        "phone",
        "city",
    )

    readonly_fields = (
        "user",
        "total_amount",
        "created_at",
        "updated_at",
    )

    inlines = [OrderItemInline]

    list_per_page = 20


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product",
        "quantity",
        "unit_price",
    )

    list_filter = ("order__status",)
