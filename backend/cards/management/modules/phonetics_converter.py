class Token:
    def __init__(self,  lexeme):
        self.type = self._set_token_type(lexeme)
        self.lexeme = str(lexeme)

    @classmethod
    def _set_token_type(cls, lexeme: str):
        lexeme_len = len(lexeme.strip())
        if lexeme_len == 1:
            return "SINGLE_CHAR"
        elif lexeme_len > 1:
            return "MULTI_CHAR"
        else:
            return None

    def __str__(self):
        return " ".join(
            [str(item) for item in (self.type, self.lexeme,)]).strip()


# scanner
class PhoneticsConverter:
    _available_tokens = {
        "a2(r)": Token("a2(r)"),
        "r": Token("r")
    }

    def __init__(self, phonetics):
        self._phonetics = phonetics
        self._tokens = []
        self._start = 0
        self._current = 0
        self._longest_available_lexem = self.longest_available_lexem

    def _get_length_longest_lexem(self):
        return max([len(key) for key in self._available_tokens.keys()])

    longest_available_lexem = property(_get_length_longest_lexem)

    def _scan_token(self, length):
        current_char = self._phonetics[self._start:
                                       self._start+length]
        print("Current char:", current_char, "at:", self._current,
              self._current+length)
        self._add_token(current_char)

    def _add_token(self, lexeme):
        if len(lexeme) < 2:
            token = self._available_tokens.get(lexeme, lexeme)
        else:
            token = self._available_tokens[lexeme]
        self._tokens.append(token)

    def scan_tokens(self):
        while not self.is_at_end():
            self._start = self._current
            for length in range(self._longest_available_lexem+1, 0, -1):
                try:
                    self._scan_token(length)
                    self._current += length
                    break
                except KeyError:
                    pass

        print("Current:", self._current)
        print("len(self._phonetics):", len(self._phonetics))
        self._tokens.append(Token(""))
        return self._tokens

    def is_at_end(self):
        return self._current >= len(self._phonetics)

    def get_converted(self):
        pass
