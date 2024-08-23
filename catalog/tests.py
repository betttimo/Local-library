from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.utils import timezone
import datetime
from .models import Book, BookInstance, Author, Genre, Language, Member

class BookIssuingTestCase(TestCase):
    def setUp(self):
        # Create a user and give them permission to issue books
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user.user_permissions.add(Permission.objects.get(codename='can_mark_returned'))

        # Create a genre, language, author, and book
        genre = Genre.objects.create(name='Fiction')
        language = Language.objects.create(name='English')
        author = Author.objects.create(first_name='John', last_name='Doe')
        self.book = Book.objects.create(
            title='Sample Book',
            author=author,
            summary='A simple summary.',
            isbn='1234567890123',
            language=language
        )
        self.book.genre.set([genre])

        # Create a BookInstance
        self.book_instance = BookInstance.objects.create(
            book=self.book,
            imprint='Sample Imprint',
            status='a'
        )

        # Create a Member linked to the user
        self.member = Member.objects.create(user=self.user)

    def test_issue_book(self):
        # Log in the user
        self.client.login(username='testuser', password='12345')

        # Issue the book instance to the user
        response = self.client.post(reverse('issue-book'), {
            'user': self.user.id,
            'book_instance': self.book_instance.id
        })

        # Check if the book instance is issued correctly
        self.book_instance.refresh_from_db()
        self.assertEqual(self.book_instance.borrower, self.user)
        self.assertEqual(self.book_instance.status, 'o')
        self.assertEqual(response.status_code, 302)  # Redirects after issuing

class OutstandingDebtValidationTestCase(TestCase):
    def setUp(self):
        # Set up a user, member, book, and book instance
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.member = Member.objects.create(user=self.user)
        author = Author.objects.create(first_name='John', last_name='Doe')
        language = Language.objects.create(name='English')
        book = Book.objects.create(
            title='Sample Book',
            author=author,
            summary='A simple summary.',
            isbn='1234567890123',
            language=language
        )
        self.book_instance = BookInstance.objects.create(
            book=book,
            imprint='Sample Imprint',
            status='o',
            borrower=self.user,
            due_back=datetime.date.today() - datetime.timedelta(days=5)  # Overdue by 5 days
        )

    def test_outstanding_debt_calculation(self):
        # Calculate the rent fee using today's date as return date
        return_date = datetime.date.today()
        self.book_instance.calculate_rent_fee(return_date)
        self.book_instance.update_member_outstanding_debt()

        self.member.refresh_from_db()
        self.assertEqual(self.member.outstanding_debt, 250)  # 5 days overdue at KES 50 per day

class BookInstanceDeletionTestCase(TestCase):
    def setUp(self):
        # Set up a user, author, language, book, and book instance
        self.user = User.objects.create_user(username='testuser', password='12345')
        author = Author.objects.create(first_name='John', last_name='Doe')
        language = Language.objects.create(name='English')
        book = Book.objects.create(
            title='Sample Book',
            author=author,
            summary='A simple summary.',
            isbn='1234567890123',
            language=language
        )
        self.book_instance = BookInstance.objects.create(
            book=book,
            imprint='Sample Imprint',
            status='a'
        )

    def test_delete_book_instance(self):
        # Log in the user
        self.client.login(username='testuser', password='12345')

        # Attempt to delete the book instance
        response = self.client.post(reverse('bookinstance-delete', args=[self.book_instance.id]))

        # Check if the book instance is deleted
        self.assertFalse(BookInstance.objects.filter(id=self.book_instance.id).exists())
        self.assertEqual(response.status_code, 302)  # Redirects after deletion

class UserAuthenticationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_user_login(self):
        # Attempt to log in
        login = self.client.login(username='testuser', password='12345')
        self.assertTrue(login)

    def test_user_logout(self):
        # Log in and then log out
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('my-logout'))
        self.assertEqual(response.status_code, 200)

class SearchFunctionalityTestCase(TestCase):
    def setUp(self):
        author = Author.objects.create(first_name='John', last_name='Doe')
        language = Language.objects.create(name='English')
        self.book = Book.objects.create(
            title='Sample Book',
            author=author,
            summary='A simple summary.',
            isbn='1234567890123',
            language=language
        )

    def test_search_books(self):
        response = self.client.get(reverse('search-results'), {'book_name': 'Sample'})
        self.assertContains(response, self.book.title)

    def test_search_books_by_author(self):
        response = self.client.get(reverse('search-results'), {'author_name': 'John'})
        self.assertContains(response, self.book.title)
