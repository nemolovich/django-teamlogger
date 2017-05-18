from datetime import timedelta

from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.views.generic.base import ContextMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin
from django.views.generic.edit import FormMixin

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib.messages.views import SuccessMessageMixin

from nouvelles.forms import ArchiveFiltersForm, UploadAttachmentForm, ArticleForm
from nouvelles.models import Article, Attachment
from nouvelles.settings import HEADLINES_DAYS

# ----------------
#      Mixins
# ----------------


class ViewTitleMixin(ContextMixin):
    """
    Mixin that add a title context variable
    """
    title = None
    context_title_name = 'title'

    def get_page_title(self):
        import re
        if self.title:
            return self.title
        else:
            return re.sub(r"(?<=\w)([A-Z])", r" \1", self.__class__.__name__)

    def get_context_data(self, **kwargs):
        context = super(ViewTitleMixin, self).get_context_data(**kwargs)
        context[self.context_title_name] = self.get_page_title()
        return context


class FilterMixin(MultipleObjectMixin, View):
    allowed_filters = {}

    def get_queryset_filters(self):
        filters = {}
        for item in self.allowed_filters:
            if item in self.request.GET:
                filters[self.allowed_filters[item]] = self.request.GET[item]
        return filters

    def get_queryset(self):
        return super(FilterMixin, self).get_queryset().filter(**self.get_queryset_filters())


class FormFilterMixin(FormMixin, FilterMixin):
    def get_form_kwargs(self):
        kwargs = super(FormFilterMixin, self).get_form_kwargs()

        if self.request.method == 'GET':
            kwargs.update({'data': self.request.GET})

        return kwargs

    def get_queryset(self):
        queryset = super(FilterMixin, self).get_queryset()
        form = self.get_form()

        if form.is_valid():
            return queryset.filter(**self.get_queryset_filters())
        else:
            return queryset

# ----------------
#      CBVs
# ----------------


class ArticleNewsListView(ViewTitleMixin, FilterMixin, ListView):
    query_date = (timezone.now() - timedelta(HEADLINES_DAYS)).date()

    title = 'Headlines'
    context_object_name = 'article_list'
    template_name = 'nouvelles/article_news_list.html'
    queryset = Article.objects\
        .filter(effective_date__gte=query_date)\
        .order_by('-effective_date', '-creation_date')
    allowed_filters = {
        'criticality': 'criticality',
        'author': 'author__username',
        'tag': 'tags__slug'
    }

    def url(self, field, value):
        req_params = self.request.GET.copy()
        if req_params.get(field) == value:
            req_params.pop(field)
        elif req_params.get(field) is not None:
            req_params.pop(field)
            req_params.update({field: value})
        else:
            req_params.update({field: value})

        if len(req_params):
            return "%s?%s" % (reverse('index'), req_params.urlencode())
        else:
            return "%s" % reverse('index')

    def get_filters(self):
        criticalities = [None] * 3
        authors = []
        tags = []

        criticality_choices = dict(Article.CRITICALITY_CHOICES)

        # Gets all criticality
        for criticality_id in self.queryset.values_list('criticality', flat=True):
            if criticality_id == Article.CRITICALITY_HIGH:
                criticalities[0] = {
                    'id': criticality_id,
                    'name': criticality_choices[criticality_id],
                    'icon': 'i-exclamation',
                    'url': self.url('criticality', criticality_id)}

            elif criticality_id == Article.CRITICALITY_MEDIUM:
                criticalities[1] = {
                    'id': criticality_id,
                    'name': criticality_choices[criticality_id],
                    'icon': 'i-error',
                    'url': self.url('criticality', criticality_id)}

            elif criticality_id == Article.CRITICALITY_LOW:
                criticalities[2] = {
                    'id': criticality_id,
                    'name': criticality_choices[criticality_id],
                    'icon': 'i-information',
                    'url': self.url('criticality', criticality_id)}

        # Gets articles authors
        for author_username in self.queryset.values_list('author__username', flat=True):
            if not any(d['username'] == author_username for d in authors):
                authors.append({'username': author_username, 'url': self.url('author', author_username)})

        # Gets articles tags
        for (tag_slug, tag_name) in self.queryset.values_list('tags__slug', 'tags__name'):
            if (tag_slug is not None) and (not any(d['slug'] == tag_slug for d in tags)):
                tags.append({'slug': tag_slug, 'name': tag_name, 'url': self.url('tag', tag_slug)})

        return {'criticality_filters': criticalities, 'author_filters': authors, 'tag_filters': tags}

    def get_context_data(self, **kwargs):
        context = super(ArticleNewsListView, self).get_context_data(**kwargs)
        context['query_date'] = self.query_date

        new_context = context.copy()
        new_context.update(self.get_filters())

        return new_context


class ArticleArchiveListView(ViewTitleMixin, FormFilterMixin, ListView):
    title = "Archives"
    context_object_name = 'article_list'
    template_name = 'nouvelles/article_archives_list.html'
    form_class = ArchiveFiltersForm
    queryset = Article.objects \
        .order_by('-effective_date', '-creation_date')
    paginate_by = 10
    allowed_filters = {
        'title': 'title__contains',
        'criticality': 'criticality',
        'author': 'author__username',
        'date': 'effective_date',
        'tag': 'tags__slug'
    }

    def get_queryset_filters(self):
        filters = super(ArticleArchiveListView, self).get_queryset_filters()
        # Ignore empty filters
        return dict((k, v) for (k, v) in filters.items() if v)


class ArticleDetailView(DetailView):
    model = Article


class ArticleCreateView(LoginRequiredMixin, ViewTitleMixin, CreateView):
    title = "New article"
    model = Article
    form_class = ArticleForm

    def form_valid(self, form):
        # Add connected user as author
        form.instance.author = self.request.user
        return super(ArticleCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ArticleCreateView, self).get_context_data(**kwargs)
        context['attachment_form'] = UploadAttachmentForm()
        return context


class ArticleReplyView(ArticleCreateView):
    title = 'New reply'
    parent_article = None
    
    def dispatch(self, request, *args, **kwargs):
        self.parent_article = get_object_or_404(Article, slug=kwargs['slug'])
        return super(ArticleReplyView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super(ArticleReplyView, self).get_initial().copy()

        if self.parent_article.title.find('Re: ') >= 0:
            initial.update({'title': self.parent_article.title})
        else:
            initial.update({'title': 'Re: %s' % self.parent_article.title})

        initial.update({'tags': self.parent_article.tags.all()})
        return initial

    def get_context_data(self, **kwargs):
        context = super(ArticleReplyView, self).get_context_data(**kwargs)
        context['parent_article'] = self.parent_article
        return context

    def form_valid(self, form):
        # Add parent article
        form.instance.parent_article = self.parent_article
        return super(ArticleReplyView, self).form_valid(form)


class ArticleEditView(LoginRequiredMixin, ViewTitleMixin, UpdateView):
    title = "Edit article"
    model = Article
    form_class = ArticleForm

    def form_valid(self, form):
        form.instance.editor = self.request.user
        form.instance.edition_date = timezone.now()
        return super(ArticleEditView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ArticleEditView, self).get_context_data(**kwargs)
        context['attachment_form'] = UploadAttachmentForm()
        return context


class ArticleDeleteView(LoginRequiredMixin, ViewTitleMixin, SuccessMessageMixin, DeleteView):
    model = Article
    success_url = reverse_lazy('index')
    title = 'Delete confirmation'
    success_message = 'The article "%(title)s" has been deleted.'

    def delete(self, request, *args, **kwargs):
        from django.contrib import messages
        success_message = self.get_success_message(self.get_object())
        response = super(ArticleDeleteView, self).delete(request, *args, **kwargs)
        if success_message:
            messages.success(self.request, success_message)
        return response

    def get_success_message(self, instance):
        from django.forms.models import model_to_dict
        return super(ArticleDeleteView, self).get_success_message(model_to_dict(instance))


class AttachmentDownloadView(SingleObjectMixin, View):
    model = Attachment

    def get(self, request, *args, **kwargs):
        attach = self.get_object()

        try:
            response = HttpResponse(attach.file, content_type=attach.content_type)
            response['Content-Disposition'] = 'attachment; filename="%s"' % attach.file_name

            return response
        except FileNotFoundError:
            raise Http404('Attachment not found')


class AttachmentUploadAjaxView(LoginRequiredMixin, CreateView):
    model = Attachment
    form_class = UploadAttachmentForm

    def form_invalid(self, form):
        response = super(AttachmentUploadAjaxView, self).form_invalid(form)
        return JsonResponse(form.errors, status=400)

    def form_valid(self, form):
        from django.db import IntegrityError
        form.instance.upload_by = self.request.user

        try:
            # Try to save the attachment
            super(AttachmentUploadAjaxView, self).form_valid(form)
        except IntegrityError as e:
            # The file already exists in database, we get it
            self.object = Attachment.objects.get(file_md5=form.instance.get_or_compute_file_md5())

        data = {
            'id': self.object.pk,
            'file_name': self.object.file_name,
            'file_md5': self.object.file_md5,
            'file_size': self.object.file.size
        }
        return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
class PreviewMarkdownAjaxView(View):
    def post(self, request, *args, **kwargs):
        from markdown_deux.templatetags.markdown_deux_tags import markdown_filter
        return HttpResponse(markdown_filter(request.POST['text']))

