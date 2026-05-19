from app.models.product import Product


def test_product_has_image_url(seeded_demo_data):
    product = Product.query.first()
    assert hasattr(product, "image_url")
    assert product.image_url

