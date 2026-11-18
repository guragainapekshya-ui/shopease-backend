
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from app.products.models import Category, Product

categories = {
    "Electronics": "Explore modern electronic gadgets and devices.",
    "Fashion": "Discover stylish clothing, shoes and fashion products.",
    "Accessories": "Find useful and stylish everyday accessories.",
    "Beauty": "Explore beauty and personal care products."
}

for name, description in categories.items():
    Category.objects.get_or_create(
        name=name,
        defaults={"description": description}
    )

products = [
    {
        "name": "Wireless Headphones",
        "brand": "boAt",
        "type": "Electronics",
        "description": "Wireless headphones with clear sound and deep bass.",
        "price": 2500,
        "stock_quantity": 20,
        "category": "Electronics"
    },
    {
        "name": "Smart Watch",
        "brand": "Noise",
        "type": "Electronics",
        "description": "Smart watch with fitness tracking and notifications.",
        "price": 3500,
        "stock_quantity": 15,
        "category": "Electronics"
    },
    {
        "name": "Ladies Handbag",
        "brand": "Generic",
        "type": "Fashion",
        "description": "Elegant handbag suitable for everyday use.",
        "price": 1800,
        "stock_quantity": 12,
        "category": "Fashion"
    },
    {
        "name": "Sports Shoes",
        "brand": "Generic",
        "type": "Fashion",
        "description": "Comfortable sports shoes for daily activities.",
        "price": 2800,
        "stock_quantity": 18,
        "category": "Fashion"
    },
    {
        "name": "Sunglasses",
        "brand": "Generic",
        "type": "Accessories",
        "description": "Stylish sunglasses for everyday wear.",
        "price": 900,
        "stock_quantity": 25,
        "category": "Accessories"
    },
    {
        "name": "Digital Camera",
        "brand": "Canon",
        "type": "Electronics",
        "description": "Digital camera for capturing memorable moments.",
        "price": 8500,
        "stock_quantity": 8,
        "category": "Electronics"
    },
    {
        "name": "Backpack",
        "brand": "Generic",
        "type": "Accessories",
        "description": "Spacious backpack for college and travel.",
        "price": 1500,
        "stock_quantity": 20,
        "category": "Accessories"
    },
    {
        "name": "Perfume",
        "brand": "Generic",
        "type": "Beauty",
        "description": "Refreshing fragrance for everyday use.",
        "price": 1200,
        "stock_quantity": 15,
        "category": "Beauty"
    }
]

for item in products:
    category = Category.objects.get(name=item["category"])

    Product.objects.get_or_create(
        name=item["name"],
        brand=item["brand"],
        defaults={
            "type": item["type"],
            "description": item["description"],
            "price": item["price"],
            "stock_quantity": item["stock_quantity"],
            "category": category
        }
    )

print("Categories and sample products added successfully!")
