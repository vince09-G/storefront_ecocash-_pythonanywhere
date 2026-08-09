from django.urls import path
from store import views

urlpatterns = [
    path("", views.products_page, name="products_page"),
    path("cart/", views.cart_page, name="cart_page"),
    path("product/<int:id>/", views.product_detail_page, name="product_detail"),
    path("checkout/", views.checkout_page, name="checkout"),

    # PAYMENT ROUTES
    path("payment/start/<int:order_id>/", views.start_payment),

    # ECOCASH STATUS CHECK
    path(
        "payment/status/<int:payment_id>/",
        views.check_payment_status,
        name="check-payment-status"
    ),
]