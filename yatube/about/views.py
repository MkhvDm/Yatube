from django.views.generic import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/author.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        links = {
            'GitHub': 'https://github.com/MkhvDm',
            'Telegram': 'https://t.me/MkhvDm',
            'VK': 'https://vk.com/id116503226'
        }
        context['title'] = 'Обо мне'
        context['pic'] = 'place for the pic'
        context['links'] = links
        return context


class AboutTechView(TemplateView):
    template_name = 'about/tech.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tech_stack = {
            'db': 'SQLite 3',
            'backend': 'Python + Django',
            'frontend': 'Bootstrap'
        }
        context['title'] = 'My tech stack'
        context['tech_stack'] = tech_stack
        return context
