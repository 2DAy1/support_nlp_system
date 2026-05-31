from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import CreateView

from accounts.forms import UserRegisterForm


class RegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('ticket_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)

        return response