from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('books/', views.BookListView.as_view(), name = 'books'),
    path('book/<int:pk>', views.BookDetailView.as_view(), name='book-detail'),
    path('authors/', views.AuthorListView.as_view(), name = 'authors'),
    path('author/<int:pk>', views.AuthorDetailView.as_view(), name='author-detail'),
]
urlpatterns += [
    path('mybooks/', views.LoanedBooksByUserListView.as_view(), name='my-borrowed'),
    path('allbooks/', views.AllLoanedBooksListView.as_view(), name='all-borrowed'),
    path('registration/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('registration/mylogout/', views.my_logout, name='my-logout'),
    path('members/', views.member_list, name='member_list'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/create/', views.member_create, name='member_create'),
    path('members/<int:pk>/edit/', views.member_update, name='member_update'),
    path('members/<int:pk>/delete/', views.member_delete, name='member_delete'),
   

]
urlpatterns += [
    path('book/<uuid:pk>/renew/', views.renew_book_librarian, name='renew-book-librarian'),
]
urlpatterns += [
    path('author/create/', views.AuthorCreate.as_view(), name='author-create'),
    path('author/<int:pk>/update/', views.AuthorUpdate.as_view(), name='author-update'),
    path('author/<int:pk>/delete/', views.AuthorDelete.as_view(), name='author-delete'),
]
urlpatterns += [
    path('book/create/', views.BookCreate.as_view(), name='book-create'),
    path('bookinstance/add/', views.add_book_instance, name='bookinstance-create'),
    path('bookinstances/', views.bookinstance_list, name='bookinstance-list'),
    path('bookinstance/<uuid:pk>/update/', views.BookInstanceUpdateView.as_view(), name='bookinstance-update'),
    path('bookinstance/<uuid:pk>/delete/', views.delete_bookinstance, name='bookinstance-delete'),
    path('book/<int:pk>/update/', views.BookUpdate.as_view(), name='book-update'),
    path('book/<int:pk>/delete/', views.BookDelete.as_view(), name='book-delete'),
    path('issue/', views.issue_book, name='issue-book'),
    path('return/', views.return_book, name='return-book'),
    path('search-books/', views.search_books, name='search-books'),
    path('search-results/', views.search_results, name='search-results'),
]
