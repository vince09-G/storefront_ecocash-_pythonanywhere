import random

from django.core.management.base import BaseCommand

from store.models import (
    Cart,
    CartItem,
    Collection,
    Product,
    Promotion,
    Review,
)


class Command(BaseCommand):
    help = "Create dummy store data for development and testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing seeded store data before creating new data.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.clear_data()

        self.create_data()
        self.stdout.write(self.style.SUCCESS("Dummy data created successfully."))

    def clear_data(self):
        self.stdout.write("Clearing existing seeded store data...")
        Review.objects.all().delete()
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        Product.objects.all().delete()
        Collection.objects.all().delete()
        Promotion.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Existing data cleared."))

    def create_data(self):
        self.stdout.write("Creating dummy data...")
        self.create_promotions_and_collections()
        self.create_products()
        self.create_carts_and_cart_items()
        self.create_reviews()

    def create_promotions_and_collections(self):
        self.promotions = [
            Promotion.objects.create(description="Summer sale - 10% off", discount=10.0),
            Promotion.objects.create(description="Clearance discount", discount=20.0),
            Promotion.objects.create(description="Buy more, save more", discount=15.0),
        ]

        self.collections = [
            Collection.objects.create(title="Home Essentials"),
            Collection.objects.create(title="Beauty & Fashion"),
            Collection.objects.create(title="Electronics"),
        ]

    def create_products(self):
        product_data = [
            {
                "title": "Eco Cotton T-Shirt",
                "slug": "eco-cotton-tshirt",
                "description": "Soft organic cotton t-shirt made for everyday comfort.",
                "price": 12.99,
                "inventory": 45,
                "collection": self.collections[1],
            },
            {
                "title": "Solar Lantern",
                "slug": "solar-lantern",
                "description": "Rechargeable solar lantern with multiple brightness modes.",
                "price": 25.50,
                "inventory": 30,
                "collection": self.collections[2],
            },
            {
                "title": "Ceramic Coffee Mug",
                "slug": "ceramic-coffee-mug",
                "description": "Durable ceramic mug with an eco-friendly finish.",
                "price": 8.75,
                "inventory": 60,
                "collection": self.collections[0],
            },
            {
                "title": "Recycled Notebook",
                "slug": "recycled-notebook",
                "description": "Notebook made from recycled paper for notes and sketches.",
                "price": 5.20,
                "inventory": 85,
                "collection": self.collections[0],
            },
            {
                "title": "Bamboo Toothbrush",
                "slug": "bamboo-toothbrush",
                "description": "Plastic-free toothbrush with soft bamboo handle.",
                "price": 3.50,
                "inventory": 120,
                "collection": self.collections[0],
            },
        ]

        self.products = []
        for product_info in product_data:
            product, _ = Product.objects.get_or_create(
                slug=product_info["slug"],
                defaults={
                    "title": product_info["title"],
                    "description": product_info["description"],
                    "price": product_info["price"],
                    "inventory": product_info["inventory"],
                    "collection": product_info["collection"],
                },
            )
            product.promotions.set(random.sample(self.promotions, k=2))
            self.products.append(product)

    def create_carts_and_cart_items(self):
        for _ in range(3):
            cart = Cart.objects.create()
            for product in random.sample(self.products, k=2):
                CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": random.randint(1, 4)})

    def create_reviews(self):
        review_samples = [
            (self.products[0], "Great quality and very comfortable."),
            (self.products[1], "Bright and reliable for evening use."),
            (self.products[2], "Perfect size and beautiful finish."),
        ]
        for product, content in review_samples:
            Review.objects.create(product=product, name="Customer", description=content)
