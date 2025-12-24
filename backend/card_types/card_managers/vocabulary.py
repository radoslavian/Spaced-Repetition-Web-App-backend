from card_types.card_managers import DoubleSidedFormatted


class FormattedVocabulary(DoubleSidedFormatted):
    """
    Double-sided formatted card with extra contents.
    The extra content currently is:
    * example sentences shown in an answer field
    * phonetics
    * an audio track attached only to the side on which extra
      content is displayed
    """
    def _update_text_fields(self, card, back, front):
        extra_content = self.card_note.card_description.get("extra_content")
        card.front = self._render_side(front)
        card.back = self._render_side(back, extra_content)

    def _render_side(self, side, extra_content=None):
        context_data = {
            "side": side,
            "extra_content": extra_content
        }
        rendered_side = self._render_with_context(context_data)
        return rendered_side

    def _update_audio_fields(self, card, back, front):
        extra_content = self.card_note.card_description.get(
            'extra_content', {})
        card.front_audio = self.get_sound_from(front)
        extra_audio = self.get_sound_from(extra_content)

        if extra_audio:
            card.back_audio = extra_audio
        else:
            card.back_audio = self.get_sound_from(back)