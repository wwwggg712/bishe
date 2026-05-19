import json
import os
import sys


def _load_env_file(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _read_mapping(mapping_path):
    with open(mapping_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("mapping 必须是 JSON object")
    normalized = {}
    for key, value in payload.items():
        name = str(key or "").strip()
        url = str(value or "").strip()
        if name:
            normalized[name] = url
    return normalized


def main():
    root_dir = os.path.dirname(os.path.dirname(__file__))
    _load_env_file(os.path.join(root_dir, ".env"))

    if len(sys.argv) > 1:
        mapping_path = sys.argv[1]
    else:
        mapping_path = os.path.join(root_dir, "app", "utils", "product_images.json")

    if not os.path.exists(mapping_path):
        raise FileNotFoundError(f"找不到映射文件: {mapping_path}")

    mapping = _read_mapping(mapping_path)

    sys.path.insert(0, root_dir)
    from app import create_app
    from app.extensions import db
    from app.models.product import Product

    app = create_app()
    updated = 0
    skipped = 0
    missing = 0

    with app.app_context():
        for name, url in mapping.items():
            if not url:
                skipped += 1
                continue
            product = Product.query.filter_by(name=name).first()
            if product is None:
                missing += 1
                continue
            product.image_url = url
            updated += 1

        db.session.commit()

    print(f"updated={updated} skipped={skipped} missing={missing}")


if __name__ == "__main__":
    main()

