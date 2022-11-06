import pytest

import pike.auth


# pike uses the "NONE" domain when one isn't provided
NONE = "NONE"


@pytest.mark.parametrize(
    "cred_str,exp_cred_tuple",
    (
        ("foo%bar", (NONE, "foo", "bar")),
        ("foo%ba%r", (NONE, "foo", "ba%r")),
        ("BAZ\\foo%bar", ("BAZ", "foo", "bar")),
        ("BAZ\\foo%b%ar", ("BAZ", "foo", "b%ar")),
        # not convinced this is valid, but it won't crash the splitter
        ("BA\\Z\\foo%bar", ("BA", "Z\\foo", "bar")),
        ("BA\\Z\\foo%bar%", ("BA", "Z\\foo", "bar%")),
    ),
)
def test_split_credentials(cred_str, exp_cred_tuple):
    assert pike.auth.split_credentials(cred_str) == exp_cred_tuple
