from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User: AbstractBaseUser = get_user_model()


class TestRoutes(TestCase):
    '''Класс тестирования маршрутов приложения.'''

    @classmethod
    def setUpTestData(cls: TestCase):
        '''Создаем фикстуры, необходимые для тестирования:
        пользователь-автор заметки author,
        авторизованный пользователь another_user.'''
        cls.user: User = User.objects.create(username='Пользователь')
        cls.note_author: User = User.objects.create(username='Автор')
        cls.author_client: Client = Client()
        cls.author_client.force_login(cls.note_author)
        cls.auth_client: Client = Client()
        cls.auth_client.force_login(cls.user)
        cls.note: Note = Note.objects.create(
            author=cls.note_author,
            title='Заметка для теста',
            text='Текст заметки для теста',
            slug='test-notes',
        )

    def test_pages_availability_all_users(self: TestCase):
        '''Проверяем, что главная страница, страницы регистрации, авторизации
        и выхода из аккаунта доступны неавторизованным пользователям.'''
        urls: tuple[tuple[str, tuple]] = (
            ('notes:home', HTTPStatus.OK),
            ('users:signup', HTTPStatus.OK),
            ('users:login', HTTPStatus.OK),
            ('users:logout', HTTPStatus.OK),
        )
        for item in urls:
            with self.subTest():
                url, expected_status = item
                response: HttpResponse = self.client.get(reverse(url))
                self.assertEqual(response.status_code, expected_status)

    def test_redirects_anonymus_user(self: TestCase):
        '''
        Проверяем, что неавторизованный пользователь при переходе на страницы
        списка заметок, успешного добавления заметки, добавления,
        редактирования, удаления заметки и страницу детальной информации будет
        перенаправлен на страницу авторизации.
        '''
        data: tuple[tuple[str, tuple]] = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        login_url: str = reverse('users:login')

        for items in data:
            url_name, args = items
            with self.subTest():
                url: str = reverse(url_name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response: HttpResponse = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_available_authenticated_user(self: TestCase):
        '''
        Проверяем, что авторизованному пользователю доступны страница
        добавления заметки, страница списка заметок и страница
        успешного добавления заметки.
        '''
        test_urls: tuple[str] = (
            'notes:list',
            'notes:success',
            'notes:add',
        )
        for url_name in test_urls:
            with self.subTest():
                url: str = reverse(url_name)
                response: HttpResponse = self.auth_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_only_author_available(self: TestCase):
        '''
        Проверяем, что страница заметки, а также страницы редактирования
        и удаления заметки недоступны другим пользователям.
        '''
        test_urls: tuple[tuple[str, tuple]] = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        clients = (
            (self.author_client, HTTPStatus.OK),
            (self.auth_client, HTTPStatus.NOT_FOUND),
        )
        for url_name, args in test_urls:
            for client, expected_status in clients:
                with self.subTest():
                    url: str = reverse(url_name, args=args)
                    response: HttpResponse = client.get(url)
                    self.assertEqual(response.status_code, expected_status)
