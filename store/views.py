from urllib import response

from django.shortcuts import render, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter,OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import CreateModelMixin,RetrieveModelMixin,DestroyModelMixin, UpdateModelMixin
from .models import Product,ProductImage, Collection, Review, Cart,CartItem, Customer, Order, Orderitem, Payment
from .serializer import ProductSerializer,CollectionSerializer, ReviewSerializer, CartSerializer,CartItemSerializer,AddCartItemSerializer,CartItemQuantitySerializer,CustomerSerializer,OrderSerializer,CreateOrderSerializer, OrderItemSerializer,UpdateOrderSerializer, ProductImageSerializer
from .filters import ProductFilter
from .permissions import IsAdminOrReadOnly
from django.conf import settings
from django.http import HttpResponse
import requests
import uuid
from decimal import Decimal
# Create your views here.
class ProductViewset(ModelViewSet):
    queryset= Product.objects.prefetch_related('images').all()
    serializer_class= ProductSerializer 
    permission_classes=[IsAdminOrReadOnly]
    filter_backends=[DjangoFilterBackend,SearchFilter,OrderingFilter]
    filterset_class=ProductFilter
    search_fields=['title','description']
    ordering_fields=['price', 'last_update']
    pagination_class= PageNumberPagination

class ProductImageViewset(ModelViewSet):
    
    serializer_class= ProductImageSerializer
    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}
    def get_queryset(self):
        return ProductImage.objects.filter(product_id=self.kwargs['product_pk'])
   

class CollectionViewset(ModelViewSet):
    queryset= Collection.objects.all()
    serializer_class= CollectionSerializer 
    permission_classes=[IsAdminOrReadOnly]

class CartViewset(CreateModelMixin,RetrieveModelMixin,DestroyModelMixin, GenericViewSet, ):
    queryset= Cart.objects.prefetch_related('items__product').all()
    serializer_class= CartSerializer  


class CartItemViewset(ModelViewSet):
    http_method_names=['get','post','patch','delete']
 
    def get_serializer_class(self):
        if self.request.method== 'POST':
            return AddCartItemSerializer
        elif self.request.method=='PATCH':
            return CartItemQuantitySerializer
        return CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart=self.kwargs['cart_pk']).select_related('product')
    
    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}  
    
class OrderViewset(ModelViewSet):
    # queryset= Order.objects.prefetch_related('items__product').all()
    #serializer_class= OrderSerializer
    def get_permissions(self):
        http_method_names= ['get','post','patch','delete','head','options']
        if self.request.method in ['PATCH','DELETE']:
            return  [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer= CreateOrderSerializer(data=request.data, context= {'user_id': self.request.user.id})
        serializer.is_valid(raise_exception=True)
        order= serializer.save()
        serializer= OrderSerializer(order)
        return Response(serializer.data)
    def get_serializer_class(self):
        if self.request.method== 'POST':
            return CreateOrderSerializer
        elif self.request.method== 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user= self.request.user
        if user.is_staff:
            return Order.objects.all()
        customer_id = Customer.objects.only('id').get(user_id=user.id)
        return Order.objects.filter(customer_id=customer_id)
    #permission_classes=[IsAdminUser]

    # @action(detail=False, methods=['GET', 'POST'], permission_classes=[IsAuthenticated])
    # def me(self, request):
    #     print(request.user)
    #     customer, created= Customer.objects.get_or_create(user_id=request.user.id)

    #     if request.method == 'GET':
    #         if request.user.id == None:
    #             return Response('Not logged in')
    #         orders= Order.objects.filter(customer=customer)
    #         serializer = OrderSerializer(orders, many=True)
    #         return Response(serializer.data)
           
    #     elif request.method == 'POST':
    #         serializer = OrderSerializer(data=request.data)
    #         serializer.is_valid(raise_exception='True')
    #         serializer.save(customer=customer)
    #         return Response(serializer.data)

class ReviewViewset(ModelViewSet):
    serializer_class= ReviewSerializer 

    def get_queryset(self):
        return Review.objects.filter(product=self.kwargs['product_pk'])
    
    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}

class CustomerViewset(ModelViewSet):
    queryset= Customer.objects.all()
    serializer_class= CustomerSerializer
    permission_classes=[IsAdminUser]
    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        print(request.user)
        customer= Customer.objects.get(user_id=request.user.id)

        if request.method == 'GET':
            if request.user.id == None:
                return Response('Not logged in')
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
           
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception='True')
            serializer.save()
            return Response(serializer.data)


def products_page(request):
    return render(request, "products.html")

def cart_page(request):
    return render(request, "cart.html")

def product_detail_page(request, id): 
    return render(request, "product_detail.html", {"product_id": id})

#@login_required
def checkout_page(request):
    return render(request, "checkout.html")

from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
import requests
import uuid
import json
def start_payment(request, order_id):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "POST request required"
        }, status=400)

    order = Order.objects.get(id=order_id)

    total = sum(
        item.quantity * item.unit_price
        for item in order.items.all()
    )

    data = json.loads(request.body)

    phone = data.get("phone")

    if not phone:
        return JsonResponse({
            "success": False,
            "message": "Phone number is required"
        }, status=400)

    source_reference = str(uuid.uuid4())

    payload = {
        "customerMsisdn": phone,
        "amount": float(total),
        "reason": f"Order {order.id}",
        "currency": "USD",
        "sourceReference": source_reference
    }

    headers = {
        "X-API-KEY": settings.ECOCASH_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(
        settings.ECOCASH_PAYMENT_URL,
        json=payload,
        headers=headers
    )
    print("PAYMENT RESPONSE CODE:", response.status_code)
    print("PAYMENT RESPONSE:", response.text)

    if response.status_code == 200:

        payment = Payment.objects.create(
            order=order,
            amount=total,
            status=Payment.STATUS_PENDING,
            reference=source_reference
        )

        return JsonResponse({
            "success": True,
            "payment_id": payment.id,
            "message": (
                "Payment request sent. "
                "Check your EcoCash phone and enter your PIN."
            )
        })

    return JsonResponse({
        "success": False,
        "message": response.text
    }, status=response.status_code)

def check_payment_status(request, payment_id):

    payment = Payment.objects.get(id=payment_id)

    phone = request.GET.get("phone")

    payload = {
        "sourceMobileNumber": phone,
        "sourceReference": payment.reference
    }

    headers = {
        "X-API-KEY": settings.ECOCASH_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(
        settings.ECOCASH_LOOKUP_URL,
        json=payload,
        headers=headers
    )

    print("STATUS CODE:", response.status_code)
    print("RESPONSE:", response.text)

    return JsonResponse(response.json())


# class ProductList(ListCreateAPIView):
#     queryset= Product.objects.all()
#     serializer_class= ProductSerializer

# class ProductDetails(RetrieveUpdateDestroyAPIView):
#     queryset= Product.objects.all()
#     serializer_class= ProductSerializer
  

# class CollectionList(ListCreateAPIView):
#     queryset= Collection.objects.all()
#     serializer_class= CollectionSerializer

# class CollectionDetails(RetrieveUpdateDestroyAPIView):
#     queryset= Collection.objects.all()
#     serializer_class= CollectionSerializer

# @api_view(['GET', 'POST'])
# def product_list(request):
#     if request.method == 'GET':
#         products=Product.objects.select_related('collection').all()
#         serializer= ProductSerializer(products, many=True)
#         return Response(serializer.data)
#     elif request.method == 'POST':
#         serializer= ProductSerializer(data= request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         return Response(serializer.data)

# @api_view(['GET', 'PUT'])
# def product_detail(request, id):
#     product= get_object_or_404(Product, pk=id)
#     if request.method == 'GET':
#         serializer= ProductSerializer(product)
#         return Response(serializer.data)
    
#     elif request.method == 'PUT':
#         serializer= ProductSerializer(product, data= request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
