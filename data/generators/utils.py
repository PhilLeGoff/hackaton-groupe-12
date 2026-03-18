from __future__ import annotations

import random
import string


def luhn_checksum(number: str) -> int:
    digits = [int(char) for char in reversed(number)]
    checksum = 0

    for index, digit in enumerate(digits):
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit

    return checksum % 10


def complete_luhn_number(prefix: str) -> str:
    check_digit = (-luhn_checksum(prefix + "0")) % 10
    return f"{prefix}{check_digit}"


def generate_siren(rng: random.Random) -> str:
    prefix = "".join(str(rng.randint(0, 9)) for _ in range(8))
    return complete_luhn_number(prefix)


def generate_siret(rng: random.Random, siren: str | None = None) -> tuple[str, str]:
    base_siren = siren or generate_siren(rng)
    nic_prefix = "".join(str(rng.randint(0, 9)) for _ in range(4))
    siret = complete_luhn_number(f"{base_siren}{nic_prefix}")
    return base_siren, siret


def invalidate_luhn_number(number: str) -> str:
    last_digit = int(number[-1])
    new_digit = (last_digit + 1) % 10
    if new_digit == last_digit:
        new_digit = (last_digit + 2) % 10
    return f"{number[:-1]}{new_digit}"


def generate_french_vat_from_siren(siren: str) -> str:
    key = (12 + 3 * (int(siren) % 97)) % 97
    return f"FR{key:02d}{siren}"


def iban_numeric_representation(iban: str) -> str:
    rearranged = (iban[4:] + iban[:4]).upper().replace(" ", "")
    return "".join(str(int(char, 36)) if char.isalpha() else char for char in rearranged)


def compute_iban_check_digits(country_code: str, bban: str) -> str:
    numeric = iban_numeric_representation(f"{country_code}00{bban}")
    check_digits = 98 - (int(numeric) % 97)
    return f"{check_digits:02d}"


def format_iban(iban: str) -> str:
    compact = iban.replace(" ", "")
    return " ".join(compact[index:index + 4] for index in range(0, len(compact), 4))


def generate_french_rib(rng: random.Random) -> dict[str, str]:
    bank_code = "".join(str(rng.randint(0, 9)) for _ in range(5))
    branch_code = "".join(str(rng.randint(0, 9)) for _ in range(5))
    account_number = "".join(str(rng.randint(0, 9)) for _ in range(11))
    rib_key = "".join(str(rng.randint(0, 9)) for _ in range(2))
    bban = f"{bank_code}{branch_code}{account_number}{rib_key}"
    check_digits = compute_iban_check_digits("FR", bban)
    return {
        "bank_code": bank_code,
        "branch_code": branch_code,
        "account_number": account_number,
        "rib_key": rib_key,
        "iban": format_iban(f"FR{check_digits}{bban}"),
    }


def generate_french_iban(rng: random.Random) -> str:
    return generate_french_rib(rng)["iban"]


def invalidate_iban(iban: str) -> str:
    compact = iban.replace(" ", "")
    last_char = compact[-1]
    if last_char.isdigit():
        replacement = str((int(last_char) + 1) % 10)
    else:
        replacement = "A" if last_char != "A" else "B"
    return format_iban(f"{compact[:-1]}{replacement}")


def generate_bic(rng: random.Random) -> str:
    letters = string.ascii_uppercase
    bank_code = "".join(rng.choice(letters) for _ in range(4))
    country_code = "FR"
    location_code = "".join(rng.choice(letters + string.digits) for _ in range(2))
    branch_code = "".join(rng.choice(letters + string.digits) for _ in range(3))
    return f"{bank_code}{country_code}{location_code}{branch_code}"


def invalidate_bic(bic: str) -> str:
    return bic[:-1]
