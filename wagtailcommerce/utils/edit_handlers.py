from django.forms.utils import pretty_name
from django.template.defaultfilters import linebreaksbr
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from wagtail.admin.edit_handlers import EditHandler


class ReadOnlyPanel(EditHandler):
    def __init__(self, attr, heading=None, classname='', *args, **kwargs):
        super().__init__(heading=heading, classname=classname)
        self.attr = attr
        self.heading = pretty_name(self.attr) if heading is None else heading
        self.classname = classname

    def clone(self):
        return self.__class__(
            attr=self.attr,
            heading=self.heading,
            classname=self.classname,
        )

    def render(self):
        value = getattr(self.instance, self.attr)
        if callable(value):
            value = value()
        return format_html('<div style="padding-top: 1.2em;">{}</div>', linebreaksbr(value))

    def render_as_object(self):
        return format_html(
            '<fieldset><legend>{}</legend>'
            '<ul class="fields"><li><div class="field">{}</div></li></ul>'
            '</fieldset>',
            self.heading, self.render())

    def render_as_field(self):
        return format_html(
            '<div class="field">'
            '<label>{}{}</label>'
            '<div class="field-content">{}</div>'
            '</div>',
            self.heading, _(':'), self.render())
