class InvalidTokenError(Exception):
    pass


def phonetics_description(phonetic_character, description=""):
    return dict(phonetic_character=phonetic_character,
                description=description)


TECHLAND_PHONETICS = [
    ("a2(r)", phonetics_description("aʊə",
                                    "aʊə - our - as in sour")),
    ("(r)", phonetics_description("(r)",
                                  "(r) - as in her")),
    ("A", phonetics_description("a",
                                "a - as in trap")),
    ("(e)", phonetics_description("(ə)",
                                  "(ə) - as in beaten")),
    ("t3", phonetics_description("tʃ",
                                 "tʃ - tch - as in chop, ditch")),
    ("I", phonetics_description("ɪ",
                                "ɪ - i - as in pit, hill or y - as in happy")),
    ("3", phonetics_description("ʃ",
                                "ʃ - sh - as in shop, dish")),
    ("(j)", phonetics_description("(j)",
                                  "(j) - (y) - as in nuclear")),
    ("str", phonetics_description("str",
                                  "str - as in straw")),
    ("ju2r", phonetics_description("jʊər",
                                   "jʊər - yoor - as in curious")),
    ("yoo", phonetics_description("jʊə",
                                  "jʊə - yoor - as in curious")),
    ("fl", phonetics_description("fl",
                                 "fl - as in flower")),
    ("sm", phonetics_description("sm",
                                 "sm - as in small, smart")),
    ("8k", phonetics_description("ŋk",
                                 "ŋk - as in bank")),
    ("fr", phonetics_description("fr",
                                 "fr - as in freeze")),
    ("lt", phonetics_description("lt",
                                 "lt - as in salt")),
    ("j2", phonetics_description("jə",
                                 "jə - yuh - as in onion")),
    ("ks", phonetics_description("ks",
                                 "ks - x - as in oxen")),
    ("E2r", phonetics_description("ɛər",
                                  "ɛər - air - as in caring")),
    ("skw", phonetics_description("skw",
                                  "skw - as in squeal")),
    ("sl", phonetics_description("sl",
                                 "sl - as in slide, parsley")),
    ("u2r", phonetics_description("ʊər",
                                  "oor - as in fury")),
    ("sp", phonetics_description("sp",
                                 "sp - as in spell, respond")),
    ("ld", phonetics_description("ld",
                                 "ld - as in held")),
    ("nd", phonetics_description("nd",
                                 "nd - as in wind")),
    ("ju:", phonetics_description("juː",
                                  "juː - yoo - as in dubious, barbecue")),
    ("aG", phonetics_description("aʊ",
                                 "aʊ - ow - as in mouth")),
    ("ng", phonetics_description("ŋg",
                                 "ŋg - ng - as in finger")),
    ("kl", phonetics_description("kl",
                                 "kl - as in clean")),
    ("gr", phonetics_description("ɡr",
                                 "ɡr - as in green")),
    ("nt", phonetics_description("nt",
                                 "nt - as in paint")),
    ("W", phonetics_description("dʒ",
                                "dʒ - dj - as in judge")),
    ("W", phonetics_description("ʤ",
                                "ʤ - dj - as in judge")),
    ("er", phonetics_description("ər",
                                 "ər - er - as in stirring, runner")),
    ("eI", phonetics_description("eɪ",
                                 "eɪ - ay- as in bay")),
    ("2G", phonetics_description("əʊ",
                                 "əʊ - oh - as in goat")),
    ("tr", phonetics_description("tr",
                                 "tr - as in trade")),
    ("st", phonetics_description("st",
                                 "st - as in stay, post")),
    ("bl", phonetics_description("bl",
                                 "bl - as in blow")),
    ("lk", phonetics_description("lk",
                                 "lk - as in milk")),
    ("kw", phonetics_description("kw",
                                 "kw - as in queen, require")),
    ("dr", phonetics_description("dr",
                                 "dr - as in dream")),
    ("ju", phonetics_description("jᵿ",
                                 "jᵿ - yew - as in reputation")),
    ("mp", phonetics_description("mp",
                                 "mp - as in lamp")),
    ("CI", phonetics_description("ɔɪ",
                                 "ɔɪ - oy - as in boy, voice")),
    ("pl", phonetics_description("pl",
                                 "pl - as in play")),
    ("C:", phonetics_description("ɔː",
                                 "ɔː - or - as in born")),
    ("u:", phonetics_description("uː",
                                 "u: - oo - as in goose")),
    ("sw", phonetics_description("sw",
                                 "sw - as in sweep")),
    ("i:", phonetics_description("iː",
                                 "iː - ee - as in bean")),
    ("sn", phonetics_description("sn",
                                 "sn - as in snake, parsnip")),
    ("E2", phonetics_description("ɛə",
                                 "ɛə - air - as in pair")),
    ("sk", phonetics_description("sk",
                                 "sk - as in ski, risky")),
    ("pr", phonetics_description("pr",
                                 "pr - as in pride")),
    ("lf", phonetics_description("lf",
                                 "lf - as in golf")),
    ("B:", phonetics_description("əː",
                                 "əː - er - as in nurse")),
    ("2:", phonetics_description("ɔə",
                                 "ɔə - or - as in boar")),
    ("Gr", phonetics_description("ʊə",
                                 "ʊə - oor - as in cure")),
    ("aI", phonetics_description("aɪ",
                                 "aɪ - eye - as in buy")),
    ("kr", phonetics_description("kr",
                                 "kr - as in crate")),
    ("br", phonetics_description("br",
                                 "br - as in bread")),
    ("t3", phonetics_description("tʃ",
                                 "tʃ - tch - as in chop, ditch")),
    ("ai", phonetics_description("ʌɪ",
                                 "ʌɪ - eye - as in fly, arise")),
    ("AI", phonetics_description("ʌɪ",
                                 "ʌɪ - eye - as in fly, arise")),
    ("kt", phonetics_description("kt",
                                 "kt - as in actor")),
    ("ɒ̃", phonetics_description("ɒ̃",
                                 "ɒ̃ - oh - as in bon mot (nasalized)")),
    ("r", phonetics_description("r",
                                "r - as in run, terrier")),
    ("A", phonetics_description("a",
                                "a - as in trap")),
    ("6", phonetics_description("ʌ",
                                "ʌ - u as in butter, upset")),
    ("2", phonetics_description("ə",
                                "ə - as in another")),
    ("3:", phonetics_description("ɜː",
                                 "ɜː - ur - as in burn")),
    ("^", phonetics_description("æ",
                                "æ - a - as in pat, attack")),
    ("4:", phonetics_description("ɑː",
                                 "ɑː - ah - as in barn, palm")),
    ("b", phonetics_description("b",
                                "b - as in big")),
    ("9", phonetics_description("ð",
                                "ð - th - as in then, bathe")),
    ("d", phonetics_description("d",
                                "d - d as in dig")),
    ("e", phonetics_description("ɛ",
                                "ɛ - e - as in pet, ten")),
    ("f", phonetics_description("f",
                                "f - as in fig")),
    ("g", phonetics_description("ɡ",
                                "g - as in go, beg")),
    ("h", phonetics_description("h",
                                "h - as in hot, inhale")),
    ("I_", phonetics_description("ᵻ",
                                 "ᵻ - as in roses, business")),
    ("I", phonetics_description("ɪ",
                                "ɪ - i - as in pit, hill or y - as in happy")),
    ("i", phonetics_description("i",
                                "i - ee - as in happy")),
    ("k", phonetics_description("k",
                                "k - as in card, park")),
    ("l", phonetics_description("l",
                                "l - as in leap, hill")),
    ("m", phonetics_description("m",
                                "m - m - as in mine")),
    ("8", phonetics_description("ŋ",
                                "ŋ - ng - as in singing, think")),
    ("n", phonetics_description("n",
                                "n - n - as in nine")),
    ("j", phonetics_description("j",
                                "y - as in you")),
    ("G", phonetics_description("ʊ",
                                "uh - as in put, wood")),
    ("p", phonetics_description("p",
                                "p - as in pine")),
    ("s", phonetics_description("s",
                                "s - ss - as in mess, succeed")),
    ("D", phonetics_description("θ",
                                "θ - th - as in thin, bath")),
    ("t", phonetics_description("t",
                                "t - as in tan")),
    ("u", phonetics_description("ᵿ",
                                "ᵿ - ue - as in mortuary")),
    ("v", phonetics_description("v",
                                "v - as in van")),
    ("w", phonetics_description("w",
                                "w - as in wear")),
    ("z", phonetics_description("z",
                                "z - as in zoo, trees")),
    ("7", phonetics_description("ʒ",
                                "ʒ - zh - as in vision, déjeuner")),
    ("C", phonetics_description("ɒ",
                                "ɒ - о - as in pot, option")),
]


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

    @property
    def html_output(self):
        if self._token_type == "UNRECOGNIZED":
            title = ""
            phonetic_character = self.lexeme
        else:
            title = self._description
            phonetic_character = self._phonetic_character

        return (f'<span class="phonetic-entity" title="{title}">'
                f'{phonetic_character}</span>')

    def __str__(self):
        return " ".join(
            [str(item) for item in (self._token_type, self.lexeme,)]).strip()


class PhoneticsConverter:
    _available_tokens = {tpl[0]: Token(tpl[0], **tpl[1])
                         for tpl in TECHLAND_PHONETICS}

    def __init__(self, phonetics):
        self._phonetics = phonetics
        self._tokens = []
        self._current = 0
        self._longest_available_lexeme = self.longest_lexeme
        self._scan_phonetics()

    tokens = property(lambda self: tuple(self._tokens))

    longest_lexeme = property(
        lambda self: max([len(key) for key in self._available_tokens.keys()]))

    converted_phonetics = property(
        lambda self: "".join(token.html_output for token in self.tokens))

    def _scan_token(self, length):
        end = self._current + length
        current_char = self._phonetics[self._current:end]
        self._add_token(current_char)

    def _add_token(self, lexeme):
        if len(lexeme) < 2:
            token = self._available_tokens.get(
                lexeme, Token(lexeme, "UNRECOGNIZED"))
        else:
            token = self._available_tokens[lexeme]
        self._tokens.append(token)

    def _scan_phonetics(self):
        while not self.is_at_end():
            self._scan_tokens()

    def _scan_tokens(self):
        for length in range(self._longest_available_lexeme, 0, -1):
            try:
                self._scan_token(length)
                self._current += length
                break
            except KeyError:
                pass

    def is_at_end(self):
        return self._current >= len(self._phonetics)


def convert_techland_phonetics(phonetics):
    converter = PhoneticsConverter(phonetics)
    return converter.converted_phonetics
