import pytest

from pydantic import ValidationError
from pyenzyme.enzymeml.core.creator import Creator


class TestCreator:

    def test_content(self):
        # Test positive case
        creator = Creator(
            given_name="Jan", family_name="Range", mail="jan@somemail.com", id=None
        )

        assert creator.given_name == "Jan"
        assert creator.family_name == "Range"
        assert creator.mail == "jan@somemail.com"

    def test_empty_strings(self):
        # Test empty strings case
        with pytest.raises(ValidationError) as exc_info:
            Creator(
                given_name="", family_name="", mail="", id=None
            )

    def test_wrong_mail(self):
        # Test mail consistency
        with pytest.raises(ValidationError) as exc_info:
            Creator(
                given_name="Jan", family_name="Range", mail="someone.com", id=None
            )
