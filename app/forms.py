import re
from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    DecimalField,
    SelectField,
    StringField,
    TextAreaField,
    SubmitField,
    PasswordField,
    validators,
    ValidationError,
)
from .customoptgroupselect import ExtendedSelectField
from decimal import Decimal


class PeeringQueryForm(FlaskForm):
    options = [
        (20940, "akamai"),
        (16509, "amazon"),
        (11492, "cableone"),
        (209, "centurylink"),
        (7843, "charter"),
        (174, "codgent"),
        (23520, "columbus"),
        (7922, "comcast"),
        (22773, "cox"),
        (62955, "ebay"),
        (32934, "facebook"),
        (15169, "google"),
        (6939, "he"),
        (8075, "microsoft"),
        (2906, "netflix"),
        (2914, "ntt"),
        (3491, "pccw"),
        (1239, "sprint"),
        (4181, "tds"),
        (701, "verizon"),
        (7029, "windstream"),
        (6461, "zayo"),
    ]

    options_grouped_asn = [
        (
            "Access ISPs",
            (
                (11492, "Cable ONE, Inc."),
                (209, "CenturyLink Communications, LLC"),
                (7843, "Charter Communications Inc."),
                (7922, "Comcast Cable Communications, LLC"),
                (22773, "Cox Communications Inc."),
                (4181, "TDS Telecom"),
                (7029, "Windstream Communications LLC"),
            ),
        ),
        (
            "Content ISPs",
            (
                (20940, "Akamai International B.V."),
                (16509, "Amazon"),
                (62955, "Ebay"),
                (32934, "Facebook"),
                (15169, "Google"),
                (8075, "Microsoft Corporation"),
                (2906, "Netflix"),
            ),
        ),
        (
            "Transit ISPs",
            (
                (23520, "Columbus Networks USA, Inc."),
                (174, "Cogent Communications"),
                (6939, "Hurricane Electric LLC"),
                (2914, "NTT America, Inc."),
                (3491, "PCCW Global Inc."),
                (1239, "Sprint"),
                (701, "Verizon Communications, Inc."),
                (6461, "Zayo (Abovenet Communications Inc.)"),
            ),
        ),
    ]

    asn1 = ExtendedSelectField(
        "ASN 1",
        choices=[("-1", "Select your own ISP")] + options_grouped_asn,
        coerce=int,
    )
    asn2 = ExtendedSelectField(
        "ASN 2",
        choices=[("-1", "Select potential peer ISP")] + options_grouped_asn,
        coerce=int,
    )
    threshold = DecimalField(
        "Threshold",
    )
    submit = SubmitField("Submit")

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        asn1_val = int(self.asn1.data)
        asn2_val = int(self.asn2.data)
        if asn1_val == -1:
            self.asn1.errors.append("Please select ASN1.")
        if asn2_val == -1:
            self.asn1.errors.append("Please select ASN2.")
        if asn1_val == asn2_val:
            self.asn1.errors.append(
                "ASN1 and ANS2 can not be same. Please choose different ASN1."
            )
            self.asn2.errors.append(
                "ASN1 and ANS2 can not be same. Please choose different ASN2."
            )
            return False
        return True


class ContactUsForm(FlaskForm):
    name = StringField(
        "Name",
        [validators.DataRequired()],
        render_kw={"autofocus": True, "placeholder": "Your name"},
    )
    email = StringField(
        "Email",
        [
            validators.Email(message="Not a valid email address."),
            validators.DataRequired(),
        ],
        render_kw={"placeholder": "Email address"},
    )
    body = TextAreaField(
        "Message",
        [
            validators.DataRequired(),
            validators.Length(min=4, message="Your message is too short"),
        ],
        render_kw={"placeholder": "Your feedback or feature request"},
    )
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        [validators.InputRequired()],
        render_kw={"autofocus": True, "placeholder": "Username"},
    )
    password = PasswordField(
        "Password", [validators.InputRequired()], render_kw={"placeholder": "Password"}
    )
    submit = SubmitField("Login")





class CustomPeeringQuerryForm(FlaskForm):
    # def validate_asn(self, field):
    #     if not re.search("^AS[0-9]+$", field.data):
    #         raise ValidationError("The ASN format should be ASXXXX")

    asn1 = StringField(
        "ASN1",
        [
            validators.InputRequired(),
            validators.Length(min=1, max=20, message="Invalid ASN"),
        ],
        render_kw={"autofocus": True, "placeholder": "ASXXXX"},
    )
    asn2 = StringField(
        "ASN2",
        [
            validators.InputRequired(),
            validators.Length(min=1, max=20, message="Invalid ASN"),
        ],
        render_kw={"autofocus": True, "placeholder": "ASXXXX"},
    )
    threshold = DecimalField(
        "Threshold",
        [
            validators.InputRequired(),
            validators.NumberRange(
                min=0.0, max=1.0, message="Value must be between 0.0 and 1.0"
            )
        ],
    )
    submit = SubmitField("Search")

    def validate(self):
        valid = True
        if not FlaskForm.validate(self):
            return False
        asn1_val = self.asn1.data
        asn2_val = self.asn2.data

        if not re.search("^AS[0-9]+$", asn1_val):
            self.asn1.errors.append("The ASN format should be ASXXXX")
            valid = False
        if not re.search("^AS[0-9]+$", asn2_val):
            self.asn2.errors.append("The ASN format should be ASXXXX")
            valid = False

        if asn1_val == "":
            self.asn1.errors.append("Please select ASN1.")
            valid = False
        if asn2_val == "":
            self.asn1.errors.append("Please select ASN2.")
            valid = False
        if asn1_val == asn2_val:
            self.asn1.errors.append(
                "ASN1 and ANS2 can not be same. Please choose different ASN1."
            )
            self.asn2.errors.append(
                "ASN1 and ANS2 can not be same. Please choose different ASN2."
            )
            return False
        return valid

class MLPeeringQuerryForm(FlaskForm):
    # def validate_asn(self, field):
    #     if not re.search("^AS[0-9]+$", field.data):
    #         raise ValidationError("The ASN format should be ASXXXX")

    asn1 = StringField(
        "ASN1",
        [
            validators.InputRequired(),
            validators.Length(min=1, max=20, message="Invalid ASN"),
        ],
        render_kw={"autofocus": True, "placeholder": "ASXXXX"},
    )
    asn2 = StringField(
        "ASN2",
        [
            validators.InputRequired(),
            validators.Length(min=1, max=20, message="Invalid ASN"),
        ],
        render_kw={"autofocus": True, "placeholder": "ASXXXX"},
    )

    submit = SubmitField("Search")

    def validate(self):
        valid = True
        if not FlaskForm.validate(self):
            return False
        asn1_val = self.asn1.data
        asn2_val = self.asn2.data

        if not re.search("^AS[0-9]+$", asn1_val):
            self.asn1.errors.append("The ASN format should be ASXXXX")
            valid = False
        if not re.search("^AS[0-9]+$", asn2_val):
            self.asn2.errors.append("The ASN format should be ASXXXX")
            valid = False

        if asn1_val == "":
            self.asn1.errors.append("Please select ASN1.")
            valid = False
        if asn2_val == "":
            self.asn1.errors.append("Please select ASN2.")
            valid = False
        if asn1_val == asn2_val:
            self.asn1.errors.append(
                "ASN1 and ANS2 can not be same. Please choose different ASN1."
            )
            self.asn2.errors.append(
                "ASN1 and ANS2 can not be same. Please choose different ASN2."
            )
            return False
        return valid
