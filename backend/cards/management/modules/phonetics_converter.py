class InvalidTokenError(Exception):
    pass


class Token:
    allowed_token_types = [
        "SINGLE_CHAR", "MULTI_CHAR", "UNRECOGNIZED"
    ]

    def __init__(self, lexeme, token_type=""):
        self.lexeme = str(lexeme)
        self.type = self._set_token_type(token_type)

    def _guess_token_type_from_lexeme(self):
        lexeme_len = len(self.lexeme)

        if lexeme_len < 1:
            raise InvalidTokenError
        elif lexeme_len < 2:
            return "SINGLE_CHAR"
        else:
            return "MULTI_CHAR"

    def _set_token_type(self, token_type):
        if not token_type:
            return self._guess_token_type_from_lexeme()
        elif token_type in self.allowed_token_types:
            return token_type
        else:
            raise InvalidTokenError

    def __str__(self):
        return " ".join(
            [str(item) for item in (self.type, self.lexeme,)]).strip()


# scanner
class PhoneticsConverter:
    _available_tokens = {
        "a2(r)": Token("a2(r)", "MULTI_CHAR"),
        "r": Token("r", "SINGLE_CHAR")
    }

    def __init__(self, phonetics):
        self._phonetics = phonetics
        self._tokens = []
        self._start = 0
        self._current = 0
        self._longest_available_lexeme = self.longest_lexeme

    def _get_length_longest_lexeme(self):
        return max([len(key) for key in self._available_tokens.keys()])

    longest_lexeme = property(_get_length_longest_lexeme)

    def _scan_token(self, length):
        current_char = self._phonetics[self._start:
                                       self._start+length]
        self._add_token(current_char)

    def _add_token(self, lexeme):
        if len(lexeme) < 2:
            token = self._available_tokens.get(
                lexeme, Token(lexeme, "UNRECOGNIZED"))
        else:
            token = self._available_tokens[lexeme]
        self._tokens.append(token)

    def scan_tokens(self):
        while not self.is_at_end():
            self._start = self._current
            for length in range(self._longest_available_lexeme + 1, 0, -1):
                try:
                    self._scan_token(length)
                    self._current += length
                    break
                except KeyError:
                    pass

        return self._tokens

    def is_at_end(self):
        return self._current >= len(self._phonetics)

    def get_converted(self):
        pass
