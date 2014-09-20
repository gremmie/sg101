"""Views for the contact application."""

from django.shortcuts import redirect, render

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
            name = get_full_name(request.user)
            initial_data = {'name': name, 'email': request.user.email}

        subject = request.GET.get('subject')
        if subject:
            initial_data['subject'] = subject

        form = ContactForm(initial=initial_data)

    return render(request, 'contact/contact_form.html', {'form': form})
