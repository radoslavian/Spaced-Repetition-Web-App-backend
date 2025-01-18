class InvalidTokenError(Exception):
    pass


class Token:
    allowed_token_types = [
        "SINGLE_CHAR", "MULTI_CHAR", "UNRECOGNIZED"
    ]

    def __init__(self, lexeme, token_type="", description="",
                 phonetic_character=""):
        self.lexeme = str(lexeme)
        self._token_type = self._set_token_type(token_type)
        self._description = description
        self._phonetic_character = phonetic_character

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

    def _get_html_output(self):
        if self._token_type == "UNRECOGNIZED":
            title = "unrecognized phonetics"
            phonetic_character = self.lexeme
        else:
            title = self._description
            phonetic_character = self._phonetic_character

        return (f'<span class="phonetics-entity" title="{title}">'
                f'{phonetic_character}</span>')

    html_output = property(_get_html_output)

    def __str__(self):
        return " ".join(
            [str(item) for item in (self._token_type, self.lexeme,)]).strip()


# scanner
class PhoneticsConverter:
    _available_tokens = {
        "a2(r)": Token("a2(r)",
                       phonetic_character="aʊə",
                       description="aʊə - our - as in sour"),
        "r": Token("r"),
        "A": Token("A",
                   phonetic_character="a",
                   description="a - as in trap"),
        "(e)": Token("(e)",
                     phonetic_character="(ə)",
                     description="(ə) - as in beaten"),
        "t3": Token("t3",
                    phonetic_character="tʃ",
                    description="tʃ - tch - as in chop, ditch"),
        "I": Token("I",
                   phonetic_character="ɪ",
                   description="ɪ - i - as in pit, hill or y - as in happy"),
        "3": Token("3",
                   phonetic_character="ʃ",
                   description="ʃ - sh - as in shop, dish"),

    }

    def __init__(self, phonetics):
        self._phonetics = phonetics
        self._tokens = []
        self._start = 0
        self._current = 0
        self._longest_available_lexeme = self.longest_lexeme
        self._scan_tokens()

    tokens = property(lambda self: self._tokens)

    longest_lexeme = property(
        lambda self: max([len(key) for key in self._available_tokens.keys()]))

    converted_phonetics = property(
        lambda self: "".join(token.html_output for token in self.tokens))

    def _scan_token(self, length):
        end = self._start+length
        current_char = self._phonetics[self._start:end]
        self._add_token(current_char)

    def _add_token(self, lexeme):
        if len(lexeme) < 2:
            token = self._available_tokens.get(
                lexeme, Token(lexeme, "UNRECOGNIZED"))
        else:
            token = self._available_tokens[lexeme]
        self._tokens.append(token)

    def _scan_tokens(self):
        while not self.is_at_end():
            self._start = self._current
            for length in range(self._longest_available_lexeme + 1, 0, -1):
                try:
                    self._scan_token(length)
                    self._current += length
                    break
                except KeyError:
                    pass

    def is_at_end(self):
        return self._current >= len(self._phonetics)
