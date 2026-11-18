import pytest
from pydantic import ValidationError

import tests.conftest  # noqa: F401  (positionne les variables d'environnement)
from app.config import Settings

SECRET = "x" * 40
NEON = "postgresql://neondb_owner:secret-pass@ep-cool-name-123.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
EXPECTED = NEON.replace("postgresql://", "postgresql+psycopg://", 1)


def settings(**values):
    return Settings(_env_file=None, jwt_secret=values.pop("jwt_secret", SECRET), **values)


@pytest.mark.parametrize(
    "pasted",
    [
        NEON,
        f"  {NEON}  ",
        f"'{NEON}'",
        f'"{NEON}"',
        f"psql '{NEON}'",
        NEON.replace("postgresql://", "postgres://", 1),
        EXPECTED,
    ],
)
def test_database_url_survives_common_copy_paste_mistakes(pasted):
    assert settings(database_url=pasted).database_url == EXPECTED


def test_sqlite_is_kept():
    assert settings(database_url="sqlite:///./local.db").database_url == "sqlite:///./local.db"


@pytest.mark.parametrize("bad", ["l'Internal Database URL de l'étape 2", "", "mysql://u:p@h/b", "postgresql://"])
def test_invalid_database_url_gives_a_clear_message_without_the_value(bad):
    with pytest.raises(ValidationError) as failure:
        settings(database_url=bad)
    message = str(failure.value)
    assert "DATABASE_URL invalide" in message
    # La valeur fautive ne doit pas être recopiée (le message d'aide cite lui-même "postgresql://").
    assert bad in ("", "postgresql://") or bad not in message


def test_secret_must_be_a_real_key_and_is_never_echoed():
    with pytest.raises(ValidationError) as failure:
        settings(jwt_secret="la clé générée en 3.1")
    assert "la clé générée" not in str(failure.value)
    assert settings(jwt_secret=f"  '{SECRET}' ").jwt_secret == SECRET


def test_database_password_never_appears_in_errors():
    with pytest.raises(ValidationError) as failure:
        Settings(_env_file=None, jwt_secret="court", database_url=NEON)
    assert "secret-pass" not in str(failure.value)


def test_cors_origins_are_normalised():
    value = " https://mes-depenses.onrender.com/ , mes-depenses-2.onrender.com,http://localhost:5173 "
    assert settings(cors_origins=value).cors_origin_list == [
        "https://mes-depenses.onrender.com",
        "https://mes-depenses-2.onrender.com",
        "http://localhost:5173",
    ]


def test_groq_key_is_unwrapped():
    assert settings(groq_api_key=' "gsk_abc" ').groq_api_key == "gsk_abc"
