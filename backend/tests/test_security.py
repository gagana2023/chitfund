from app.security import hash_pin, verify_pin


def test_verify_pin_accepts_correct_pin():
    stored = hash_pin("4242")
    assert verify_pin("4242", stored) is True


def test_verify_pin_rejects_wrong_pin():
    stored = hash_pin("4242")
    assert verify_pin("0000", stored) is False


def test_hash_pin_is_salted_and_nondeterministic():
    a = hash_pin("4242")
    b = hash_pin("4242")
    assert a != b
    assert verify_pin("4242", a) is True
    assert verify_pin("4242", b) is True
