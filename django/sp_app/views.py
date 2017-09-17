from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from .models import Article, Conversation
from .forms import ArticleForm, ConversationForm
from .sp_constants import Constants

import requests
import json


class ArticleList(ListView):
    model = Article
    context_object_name = 'articles'
    template_name = 'articles/list_page.html'


@login_required(login_url='/login')
def new_article(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            if request.user.has_perm('sp_app.change_article'):
                article = form.save()
                return redirect('sp_app:display', pk=article.pk)
    else:
        if request.user.has_perm('sp_app.add_article'):
            form = ArticleForm()
            return render(request, 'articles/edit.html', { 'form': form })

class ArticleEdit(UpdateView):
    model = Article
    fields = [ 'title', 'document' ]
    template_name = 'articles/edit.html'

    def get_success_url(self):
        return reverse('sp_app:display_article', kwargs={'pk': self.object.pk})


def display_article(request, pk):
    article = Article.objects.get(pk=pk)

    basex_id = str(article.pk) + '.html'
    data = ''

    my_url = Constants.BASEX_URL + '/sph/tim' +  "/articles/view/" + basex_id
    print('Calling ' + my_url)
    r_basex = requests.get(my_url)

    if r_basex.status_code == 200:
        data = r_basex.content

    """ Look for annotations in hypothes.is """
    my_url = Constants.HYPOTHESIS_API_URL + "/search?uri=" + request.build_absolute_uri()
    r_hypothesis = requests.get(my_url)

    if r_hypothesis.status_code == 200:
        annotations = json.loads(r_hypothesis.content)

    return render(request, 'articles/display.html', {
        'article': article,
        'basex_document': data,
        'annotations': annotations['rows'],
    })


class ConversationList(ListView):
    model = Conversation
    context_object_name = 'conversations'
    template_name = 'conversations/list_page.html'


class ConversationDisplay(DetailView):
    model = Conversation
    context_object_name = 'conversation'
    template_name = 'conversations/display.html'


class ConversationEdit(UpdateView):
    model = Conversation
    fields = [ 'title', 'articles' ]
    template_name = 'conversations/edit.html'

    def get_success_url(self):
        return reverse('sp_app:display_conversation', kwargs={'pk': self.object.pk})

# Class based view, form
class ConversationNew(CreateView):
    model = Conversation
    fields = [ 'title', 'articles' ]
    template_name = 'conversations/edit.html'

    def get_success_url(self):
        return reverse_lazy('sp_app:display_conversation', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        if self.request.user.has_perm('sp_app.add_conversation'):
            form.instance.creator = self.request.user
            return super(ConversationNew, self).form_valid(form)
        else:
            return HttpResponseForbidden()


def list_articles_basex(request):
    my_url = Constants.BASEX_API_URL + "/articles/list"
    r = requests.get(my_url)

    if r.status_code == 200:
        data = json.loads(r.content)

    return render(request, 'articles/list_basex.html', { 'articles': data, 'source_url': my_url})
