from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User: AbstractBaseUser = get_user_model()


class TestContent(TestCase):
    '''Класс тестирования содержимого страниц.'''

    @classmethod
    def setUpTestData(cls: TestCase):
        '''
        Создаем фикстуры, необходимые для тестирования:
        пользователь-автор заметки author,
        авторизованный пользователь another_user,
        объект заметки note.
        '''
        cls.author: User = User.objects.create(username='author')
        cls.client_author: Client = Client()
        cls.client_author.force_login(cls.author)

        cls.another_user: User = User.objects.create(username='another_user')
        cls.client_another_user: Client = Client()
        cls.client_another_user.force_login(cls.another_user)

        cls.note: Note = Note.objects.create(
            author=cls.author,
            title='Заметка для теста',
            text='Tекст для теста',
            slug='test-notes',
        )

    def test_note_in_context(self: TestCase):
        '''Проверяем, что объект note передается в контекст страницы.'''
        url: str = reverse('notes:list')
        response: HttpResponse = self.client_author.get(url)
        self.assertIn(self.note, response.context['object_list'])

    def test_author_in_list_notes(self: TestCase):
        '''
        Проверяем, что неавторизованному пользователю недоступны заметки других
        пользователей.
        '''
        url: str = reverse('notes:list')
        response: HttpResponse = self.client_another_user.get(url)
        notes_count: int = len(response.context['object_list'])
        self.assertEqual(notes_count, 0)

    def test_form_create_edit_note(self: TestCase):
        '''
        Проверяем, что авторизованному пользователю доступна форма отправки
        комментария и автору комментария доступна форма редактирования
        комментария.
        '''
        test_urls: tuple[tuple[str, str or None]] = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for test_url, args in test_urls:
            url: str = reverse(test_url, args=args)
            response: HttpResponse = self.client_author.get(url)
            self.assertTrue(response.context['form'])
