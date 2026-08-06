import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class CardCheckResult:
    normalized_number: str
    issuer: str
    format_valid: bool
    luhn_valid: bool

    @property
    def is_valid(self) -> bool:
        return self.format_valid and self.luhn_valid


def normalize_card_number(card_number: str) -> str:
    allowed_separators = {' ', '-'}
    if any(not char.isdigit() and char not in allowed_separators for char in card_number):
        return ''
    return ''.join(char for char in card_number if char.isdigit())


def detect_issuer(card_number: str) -> str:
    length = len(card_number)
    if not card_number:
        return 'Unknown'

    first_two = int(card_number[:2]) if length >= 2 else -1
    first_three = int(card_number[:3]) if length >= 3 else -1
    first_four = int(card_number[:4]) if length >= 4 else -1
    first_six = int(card_number[:6]) if length >= 6 else -1

    if card_number.startswith('4') and length in {13, 16, 19}:
        return 'Visa'
    if (51 <= first_two <= 55 or 2221 <= first_four <= 2720) and length == 16:
        return 'Mastercard'
    if card_number.startswith(('34', '37')) and length == 15:
        return 'American Express'
    if (
        card_number.startswith('6011')
        or card_number.startswith('65')
        or 644 <= first_three <= 649
        or 622126 <= first_six <= 622925
    ) and length in {16, 19}:
        return 'Discover'
    if card_number.startswith(('300', '301', '302', '303', '304', '305', '36', '38', '39')) and length == 14:
        return 'Diners Club'
    if 3528 <= first_four <= 3589 and length in {16, 19}:
        return 'JCB'
    return 'Unknown'


def passes_luhn(card_number: str) -> bool:
    checksum = 0
    should_double = False

    for digit_char in reversed(card_number):
        digit = int(digit_char)
        if should_double:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
        should_double = not should_double

    return checksum % 10 == 0


def check_credit_card(card_number: str) -> CardCheckResult:
    normalized_number = normalize_card_number(card_number)
    format_valid = 13 <= len(normalized_number) <= 19
    luhn_valid = format_valid and passes_luhn(normalized_number)

    return CardCheckResult(
        normalized_number=normalized_number,
        issuer=detect_issuer(normalized_number),
        format_valid=format_valid,
        luhn_valid=luhn_valid,
    )


def mask_card_number(card_number: str) -> str:
    if len(card_number) <= 4:
        return card_number
    return f"{'*' * (len(card_number) - 4)}{card_number[-4:]}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Offline credit card checker using issuer rules and the Luhn algorithm.'
    )
    parser.add_argument('card_number', help='Card number to validate. Spaces and dashes are allowed.')
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    result = check_credit_card(args.card_number)
    masked_number = mask_card_number(result.normalized_number)

    print(f'Card: {masked_number or "Invalid input"}')
    print(f'Issuer: {result.issuer}')

    if not result.normalized_number:
        print('Status: invalid')
        print('Reason: card number can only contain digits, spaces, or dashes')
        return 1

    if not result.format_valid:
        print('Status: invalid')
        print('Reason: card number must contain between 13 and 19 digits')
        return 1

    print(f'Luhn check: {"passed" if result.luhn_valid else "failed"}')
    print(f'Status: {"valid" if result.is_valid else "invalid"}')
    return 0 if result.is_valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
