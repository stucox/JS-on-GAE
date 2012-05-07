import logging
from django import forms
from django.views.generic import TemplateView
from django.views.generic.edit import FormMixin
from django.conf import settings

from set_trace import set_trace

from lib.pyjon import interpr

class AddForm(forms.Form):
    a = forms.FloatField(initial=1, label=u'A')
    b = forms.FloatField(initial=2, label=u'B')


class JSTest(TemplateView):
    template_name = "js-test.html"
       
    def dispatch(self, request, *args, **kwargs):
        self.form = AddForm(request.GET)

        with open('core/shared-functions.js') as f:
            js_funcs = f.read()

        if request.GET.get('submit') == 'server' and self.form.is_valid():
            js_code = js_funcs + 'var result = add(%s, %s)' % \
                    (self.form.cleaned_data.get('a'),
                            self.form.cleaned_data.get('b'))
            self.js_context = interpr.PyJS()
            self.js_context.eval_(js_code)

        return super(JSTest, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(JSTest, self).get_context_data(**kwargs)
        
        context['form'] = self.form
        if hasattr(self, 'js_context'):
            context['result'] = self.js_context['result']

        return context
