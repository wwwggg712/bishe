def test_create_app():
    from app import create_app

    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    assert app is not None
