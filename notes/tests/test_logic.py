from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User: AbstractBaseUser = get_user_model()


class TestLogic(TestCase):
    '''Класс тестирования логики приложения.'''

    @classmethod
    def setUpTestData(cls: TestCase):
        '''
        Создаем фикстуры, необходимые для тестирования:
        пользователь-автор заметки author,
        авторизованный пользователь another_user,
        объект заметки note, данные для формы form-data.
        '''
        cls.author: User = User.objects.create(username='author')
        cls.client_author: Client = Client()
        cls.client_author.force_login(cls.author)

        cls.another_user: User = User.objects.create(username='another_user')
        cls.client_another_user: Client = Client()
        cls.client_another_user.force_login(cls.another_user)

        cls.note: Note = Note.objects.create(
            author=cls.author,
            title='Новость для теста',
            text='Правильный текст для теста',
            slug='test-news',
        )
        cls.form_data: type[dict] = {
            'title': 'new title',
            'text': 'new text',
            'slug': 'slug',
        }

    def test_user_can_create_note(self: TestCase):
        '''
        Проверяем, что авторизованный пользователь может создать заметку.
        Дополнительно проверяем, что поля новой записи соответствуют
        переданный данным.
        '''
        url: str = reverse('notes:add')
        response: HttpResponse = self.client_author.post(
            url,
            data=self.form_data
        )
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note: Note = Note.objects.get(id=2)
        self.assertEqual(new_note.title, 'new title')
        self.assertEqual(new_note.text, 'new text')
        self.assertEqual(new_note.slug, 'slug')

    def test_anonymous_user_cant_create_note(self: TestCase):
        '''
        Проверяем, что неавторизованный пользователь не может создать заметку.
        '''
        url: str = reverse('notes:add')
        login_url: str = reverse('users:login')
        response: HttpResponse = self.client.post(url, self.form_data)
        expected_url: str = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self: TestCase):
        '''
        Проверяем, что нельзя создать заявку с дублирующимся slug.
        '''
        url: str = reverse('notes:add')
        self.form_data['slug'] = self.note.slug
        response: HttpResponse = self.client_author.post(
            url,
            data=self.form_data
        )
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self: TestCase):
        '''
        Проверяем, что нельзя создать заявку с пустым slug.
        '''
        url: str = reverse('notes:add')
        self.form_data.pop('slug')
        response: HttpResponse = self.client_author.post(
            url,
            data=self.form_data
        )
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note: Note = Note.objects.get(id=2)
        expected_slug: str = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self: TestCase):
        '''
        Проверяем, что автору доступно редактирование заметки.
        '''
        url: str = reverse('notes:edit', args=(self.note.slug,))
        response: HttpResponse = self.client_author.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self: TestCase):
        '''
        Проверяем, что пользователю недоступно редактирование чужой заметки.
        '''
        url: str = reverse('notes:edit', args=(self.note.slug,))
        response: HttpResponse = self.client_another_user.post(
            url,
            self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db: Note = Note.objects.get(id=self.note.id)
        assert self.note.title == note_from_db.title
        assert self.note.text == note_from_db.text
        assert self.note.slug == note_from_db.slug

    def test_author_can_delete_note(self: TestCase):
        '''
        Проверяем, что автору доступно удаление своей заметки.
        '''
        url: str = reverse('notes:delete', args=(self.note.slug,))
        response: HttpResponse = self.client_author.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self: TestCase):
        '''
        Проверяем, что пользователю недоступно удаление чужой заметки.
        '''
        url: str = reverse('notes:delete', args=(self.note.slug,))
        response: HttpResponse = self.client_another_user.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
