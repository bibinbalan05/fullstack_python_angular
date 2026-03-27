from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

@deconstructible
class EanValidator:
    message = _('Enter a valid EAN-8 (8 digits), UPC-A (12 digits), or EAN-13 (13 digits) code.')
    code = 'invalid_ean_upc'

    def _calculate_checksum_ean13(self, digits_str):
        """
        Calculates the EAN/UPC checksum for the given string of digits
        (excluding the checksum digit itself).
        Works for EAN-13 (input 12 digits).
        Also works for UPC-A (input '0' + first 11 digits).
        """
        digits = [int(d) for d in digits_str]
        length = len(digits)
        # Sum odd positions (index 0, 2, 4, ...)
        odd_sum = sum(digits[i] for i in range(0, length, 2))
        # Sum even positions (index 1, 3, 5, ...)
        even_sum = sum(digits[i] for i in range(1, length, 2))

        total_sum = odd_sum + (even_sum * 3)
        remainder = total_sum % 10
        calculated_checksum = 0 if remainder == 0 else 10 - remainder
        return calculated_checksum

    def _calculate_checksum_ean8(self, digits_str):
        """
        Calculates the EAN/UPC checksum for the given string of digits (excluding the checksum digit itself).
        Works for and EAN-8 (input 7 digits). Also works for UPC-A (input '0' + first 11 digits).
        """
        digits = [int(d) for d in digits_str]
        length = len(digits)
        # Sum odd positions (index 0, 2, 4, ...)
        odd_sum = sum(digits[i] for i in range(0, length, 2))
        # Sum even positions (index 1, 3, 5, ...)
        even_sum = sum(digits[i] for i in range(1, length, 2))

        total_sum = even_sum + (odd_sum * 3)
        remainder = total_sum % 10
        calculated_checksum = 0 if remainder == 0 else 10 - remainder
        return calculated_checksum

    def __call__(self, value):
        """
        Validates that the input value is a valid EAN-8, UPC-A (12-digit), or EAN-13 code.
        Rejects codes of other lengths (including 11 digits).
        """
        if not value:
            return # Allow empty values if field allows

        ean_str = str(value).strip() # Ensure string and strip whitespace

        # 1. Digit check
        if not ean_str.isdigit():
            raise ValidationError(
                _('%(message)s Must contain only digits. Received: "%(value)s"') %
                {'message': self.message, 'value': ean_str[:20]},
                code=self.code
            )

        length = len(ean_str)
        validation_passed = False
        error_message = '' # error variable for later use

        if length == 13:
            # Validate as EAN-13
            provided_checksum = int(ean_str[-1])
            digits_to_check = ean_str[:-1] # First 12 digits
            calculated_checksum = self._calculate_checksum_ean13(digits_to_check)
            if calculated_checksum == provided_checksum:
                validation_passed = True
            else:
                error_message = _('Invalid EAN-13 checksum. Calculated %(calc)s, expected %(prov)s.') % {'calc': calculated_checksum, 'prov': provided_checksum}

        elif length == 12:
            # Validate as UPC-A (by treating as EAN-13 internally)
            provided_checksum = int(ean_str[-1])
            # Checksum calculation uses '0' + first 11 digits
            digits_to_check = '0' + ean_str[:-1]
            calculated_checksum = self._calculate_checksum_ean13(digits_to_check)
            if calculated_checksum == provided_checksum:
                validation_passed = True
            else:
                error_message = _('Invalid UPC-A checksum. Calculated %(calc)s (using EAN-13 method), expected %(prov)s.') % {'calc': calculated_checksum, 'prov': provided_checksum}

        elif length == 8:
            # Validate as EAN-8
            provided_checksum = int(ean_str[-1])
            digits_to_check = ean_str[:-1] # First 7 digits
            calculated_checksum = self._calculate_checksum_ean8(digits_to_check)
            if calculated_checksum == provided_checksum:
                validation_passed = True
            else:
                error_message = _('Invalid EAN-8 checksum. Calculated %(calc)s, expected %(prov)s.') % {'calc': calculated_checksum, 'prov': provided_checksum}

        # Handle invalid lengths (INCLUDING 11)
        else:
            error_message = _('%(message)s Allowed lengths are 8 (EAN-8), 12 (UPC-A), or 13 (EAN-13). You entered %(length)s.') % {'message': self.message, 'length': length}

        # Raise error if any check failed
        if not validation_passed:
             raise ValidationError(error_message, code=self.code)


    def __eq__(self, other):
        return isinstance(other, EanValidator)
