from django.shortcuts import render , get_object_or_404
from django.contrib.auth.models import User
from .models import Book, Author, BookInstance, Genre, Member
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
import datetime
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db import IntegrityError, transaction

from catalog.forms import BookInstanceForm, RenewBookForm, IssueBookForm, UserForm, MemberForm


def index(request):
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()
    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
    }

    return render(request, 'index.html', context=context)

def my_logout(request):
    return render(request, 'registration/logout.html')

class BookListView(generic.ListView):
    model = Book
    paginate_by = 10

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        author = context['object']
        context['books'] = Book.objects.filter(author=author)

        return context
    
class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    model = BookInstance
    template_name = 'bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(borrower=self.request.user)
            .filter(status__exact='o')
            .order_by('due_back')
        )

class AllLoanedBooksListView(PermissionRequiredMixin, generic.ListView):
    permission_required = 'catalog.can_mark_returned'
    model = BookInstance
    template_name = 'catalog/bookinstance_loaned_books.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(status__exact='o')
            .order_by('due_back')
        )
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book_instances = context['object_list']
        
        # Add rent fees and outstanding debts to the context
        for book_instance in book_instances:
            if book_instance.borrower and hasattr(book_instance.borrower, 'member'):
                book_instance.outstanding_debt = book_instance.borrower.member.outstanding_debt
                book_instance.rent_fee = book_instance.rent_fee

        context['book_instances'] = book_instances
        return context
    
@login_required
@permission_required('catalog.can_mark_returned', raise_exception= True)
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = RenewBookForm(request.POST)
        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()
            return HttpResponseRedirect(reverse('all-borrowed'))
    else:
        proposed_renewal_date = datetime.date.today()+datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})
    context = {
                'form': form,
                'book_instance': book_instance,
            }
    return render(request, 'catalog/book_renew_librarian.html', context)
            
class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial= {'date_of_death': '11/11/2023'}
    permission_required = 'catalog.add_author'

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = '__all__'
    permission_required = 'catalog.change_author'

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.delete_author'

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse("author-delete", kwargs={"pk": self.object.pk})
            )
        
class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.add_book'

class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = '__all__'
    permission_required = 'catalog.change_book'

class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.delete_book'

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse("book-delete", kwargs={"pk": self.object.pk})
            )
        
@permission_required('catalog.can_mark_returned', raise_exception=True)
def issue_book(request):
    if request.method == 'POST':
        form = IssueBookForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            book_instance = form.cleaned_data['book_instance']
            book_instance.borrower = user
            book_instance.due_back = datetime.date.today() + datetime.timedelta(weeks=3)
            book_instance.status = 'o'
            book_instance.save()
            return HttpResponseRedirect(reverse('all-borrowed'))
    else:
        form = IssueBookForm()
        
    context = {
        'form': form,
    }
    return render(request, 'catalog/issue_book.html', context)
 
@permission_required('catalog.can_mark_returned', raise_exception=True)
def return_book(request):
    book_instances = BookInstance.objects.filter(status='o')
    
    if request.method == 'POST':
        book_instance_id = request.POST.get('book_instance_id')
        book_instance = get_object_or_404(BookInstance, pk=book_instance_id)

        # Calculate rent fee using today's date as the return date
        return_date = datetime.date.today()
        book_instance.calculate_rent_fee(return_date)
        
        book_instance.update_member_outstanding_debt()
        
        book_instance.borrower = None
        book_instance.due_back = None
        book_instance.status = 'a'
        book_instance.save()
        
        return HttpResponseRedirect(reverse('return-book'))

    context = {
        'book_instances': book_instances,
    }
    return render(request, 'catalog/return_book.html', context)


def search_books(request):
    return render(request, 'catalog/search_books.html')

def search_results(request):
    query = request.GET.get('book_name')
    author_query = request.GET.get('author_name')
    
    books = Book.objects.all()
    
    if query:
        books = books.filter(title__icontains=query)
    
    if author_query:
        books = books.filter(author__first_name__icontains=author_query) | books.filter(author__last_name__icontains=author_query)
    
    context = {
        'books': books,
        'query': query,
        'author_query': author_query,
    }
    
    return render(request, 'catalog/search_results.html', context)

@permission_required('catalog.can_manage_members')
def member_list(request):
    members = Member.objects.all()
    return render(request, 'members/member_list.html', {'members': members})

@permission_required('catalog.can_manage_members')
def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    return render(request, 'members/member_detail.html', {'member': member})


@permission_required('catalog.can_manage_members')
def member_create(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        member_form = MemberForm(request.POST)
        if user_form.is_valid() and member_form.is_valid():
            try:
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data["password"])
                user.save()
                member = member_form.save(commit=False)
                member.user = user
                member.save()
                return redirect('member_detail', pk=member.pk)
            except IntegrityError:
                user_form.add_error(None, 'A member already exists for this user.')
    else:
        user_form = UserForm()
        member_form = MemberForm()
    return render(request, 'members/member_form.html', {'user_form': user_form, 'member_form': member_form})


@permission_required('catalog.can_manage_members')
def member_update(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=member.user)
        member_form = MemberForm(request.POST, instance=member)
        if user_form.is_valid() and member_form.is_valid():
            user_form.save()
            member_form.save()
            return redirect('member_detail', pk=member.pk)
    else:
        user_form = UserForm(instance=member.user)
        member_form = MemberForm(instance=member)
    return render(request, 'members/member_form.html', {'user_form': user_form, 'member_form': member_form})

@permission_required('catalog.can_manage_members')
def member_delete(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        user = member.user
        member.delete()
        user.delete()
        return redirect('member_list')
    return render(request, 'members/member_confirm_delete.html', {'member': member})

def is_librarian(user):
    return user.groups.filter(name='Librarian').exists()

@user_passes_test(is_librarian)
def add_book_instance(request):
    if request.method == 'POST':
        form = BookInstanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('bookinstance-list') 
    else:
        form = BookInstanceForm()
    return render(request, 'catalog/bookinstance_form.html', {'form': form})

def bookinstance_list(request):
    bookinstances = BookInstance.objects.all()
    return render(request, 'catalog/bookinstance_list.html', {'bookinstances': bookinstances})

class BookInstanceUpdateView(UpdateView):
    model = BookInstance
    fields = ['imprint', 'due_back', 'status', 'borrower']
    template_name = 'catalog/bookinstance_form_update.html'
    success_url = reverse_lazy('bookinstance-list')

def delete_bookinstance(request, pk):
    bookinstance = get_object_or_404(BookInstance, pk=pk)
    if request.method == 'POST':
        bookinstance.delete()
        return redirect('bookinstance-list')
    return render(request, 'catalog/bookinstance_confirm_delete.html', {'bookinstance': bookinstance})