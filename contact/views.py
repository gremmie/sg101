"""Views for the contact application."""

from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from contact.forms import ContactForm
from core.functions import get_full_name


def contact_form(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contact-thanks')
    else:
        initial_data = {}
        if request.user.is_authenticated():
            name = get_full_name(request.user).strip()
            if name != request.user.username:
                name = '{} ({})'.format(name, request.user.username)

            initial_data = {'name': name, 'email': request.user.email}

        subject = request.GET.get('subject')
        if subject:
            initial_data['subject'] = subject

        form = ContactForm(initial=initial_data)

    return render(request, 'contact/contact_form.html', {
        'form': form,
        'V3_DESIGN': True,
    })


class ContactThanksView(TemplateView):
    template_name = 'contact/contact_thanks.html'

    def get_context_data(self, **kwargs):
        context = super(ContactThanksView, self).get_context_data(**kwargs)
        context['V3_DESIGN'] = True
        return context
