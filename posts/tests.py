from django.test import TestCase, Client, override_settings
from django.urls import reverse
from posts.models import User, Post, Group, Follow, Comment

import time

TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}


def check_text(client, user, post, text):
    """ Проверяем наличие поста на странице этого поста,
    на странице пользователя и на главной странице сайта """

    # Проверяем публикацию на персональной странице пользователя
    response = client.get("/sarah/")
    assert response.context['total_posts'] == 1, 'На странице пользователя неправильно отображается количество постов'
    assert text in response.content.decode('utf8'), 'Не найден текст поста на странице'

    # Проверяем публикацию на странице публикации
    url = reverse('post', kwargs={'username': user.username, 'post_id': post.pk})
    response = client.get(url)
    assert response.status_code == 200, 'Страница публикации не найдена'
    assert response.context['post'].text == text, 'На странице публикации неправильный текст'

    # Проверяем публикацию на главной странице
    url = reverse('index')
    response = client.get(url)
    assert text in response.content.decode('utf8'), 'Не найден текст поста на странице'


class ProfileTest(TestCase):
    def setUp(self):
        # создание тестовых клиентов: авторизованного и неавторизованного
        self.auth_client = Client()
        self.non_auth_client = Client()
        # создаём пользователя
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345"
        )
        # создаём пост от имени пользователя
        self.post = Post.objects.create(
            text="Текст нового поста тестового пользователя",
            author=self.user)
        self.group = Group.objects.create(title='Test Group', slug='tg',
                                          description='testing group')
        self.auth_client.force_login(self.user)

    def test_profile(self):
        """После регистрации пользователя создается его персональная страница"""
        # формируем GET-запрос к странице сайта
        response = self.auth_client.get("/sarah/")

        # проверяем что страница найдена
        try:
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            assert False, f'''Страница пользователя работает неправильно. Ошибка: `{e}`'''

    def test_new_post(self):
        """Авторизованный пользователь может опубликовать пост (new)"""

        url = reverse('new')
        url_index = reverse('index')

        # Проверяем, что страница `/new/` найдена
        try:
            response = self.auth_client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            assert False, f'''Страница `/new` работает неправильно. Ошибка: `{e}`'''

        # Проверяем перенаправление на главную страницу сайта
        response = self.auth_client.post(url, data={'text': self.post.text})
        try:
            self.assertIn(response.status_code, (301, 302))
        except Exception as e:
            assert False, f'''Не перенаправляет на главную страницу. Ошибка: `{e}`'''

        assert response.url == url_index, 'Не перенаправляет на главную страницу `/`'

    def test_check_new_post(self):
        """После публикации поста новая запись появляется на главной странице сайта (index)
        , на персональной странице пользователя (profile),
        и на отдельной странице поста (post)"""

        check_text(self.auth_client, self.user, self.post, self.post.text)

    def test_non_auth_new_post(self):
        """Неавторизованный посетитель не может опубликовать пост
        (его редиректит на страницу входа)"""

        response = self.non_auth_client.post("/new/", data={'text': self.post.text})
        assert response.status_code in (301, 302), 'Не перенаправляет на другую страницу'

    @override_settings(CACHES=TEST_CACHES)
    def test_edit_post(self):
        """Авторизованный пользователь может отредактировать свой пост
        и его содержимое изменится на всех связанных страницах"""

        url = reverse('post_edit', kwargs={'username': self.user.username, 'post_id': self.post.pk})

        # Проверяем, что страница редактирования поста найдена
        try:
            response = self.auth_client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            assert False, f'''Страница редактирования поста работает неправильно. Ошибка: `{e}`'''

        # Редактируем данный пост
        new_text = 'Отредактированный текст поста'
        response = self.auth_client.post(url, data={'text': new_text})
        try:
            self.assertIn(response.status_code, (301, 302))
        except Exception as e:
            assert False, f'''Не перенаправляет на главную страницу. Ошибка: `{e}`'''

        check_text(self.auth_client, self.user, self.post, new_text)

    def test_page_not_found_404(self):
        """Для своего локального проекта напишите тест: возвращает ли сервер код 404, если страница не найдена."""

        url = "wrong_page"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def tearDown(self):
        # Clean up after each test
        self.user.delete()
        self.post.delete()


class PostTest6(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345"
        )
        self.group = Group.objects.create(title='Test Group', slug='tg', description='testing group')
        self.post = Post.objects.create(text="Testing post.", author=self.user)
        self.user1 = User.objects.create_user(
            username="user1", email="user1@mail.com", password="111111111111"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user1@mail.com", password="222222222222"
        )
        self.test_image = "media/posts/test.jpg"

    @override_settings(CACHES=TEST_CACHES)
    def test_post_with_img(self):
        """проверяют страницу конкретной записи с картинкой."""

        self.client.force_login(self.user)
        with open(self.test_image, mode='rb') as img:
            self.client.post("/new/",
                             {"text": 'Testing post with image',
                              'image': img})
        response = self.client.get(f"/{self.user.username}/")
        self.assertContains(response, 'img')

    @override_settings(CACHES=TEST_CACHES)
    def test_post_with_img_everywhere(self):
        """проверяют, что на главной странице, на странице профайла
        и на странице группы пост с картинкой отображается корректно."""

        self.client.force_login(self.user)
        with open(self.test_image, 'rb') as img:
            self.client.post('/new/', {'text': 'new text', 'image': img,
                                       'group': self.group.id})
        response_index = self.client.get(f"/")
        response_profile = self.client.get(f"/{self.user.username}/")
        response_group = self.client.get(f"/group/{self.group.slug}/")
        self.assertContains(response_index, 'img')
        self.assertContains(response_profile, 'img')
        self.assertContains(response_group, 'img')

    @override_settings(CACHES=TEST_CACHES)
    def test_post_with_non_graphic_files(self):
        """проверяют, что срабатывает защита от загрузки файлов не-графических форматов."""

        self.client.force_login(self.user)
        with open('models.py', 'rb') as file:
            self.client.post('/new/', {'text': 'new text', 'image': file})
        post = Post.objects.last()
        with self.assertRaises(ValueError):
            post.image.open()

    def test_check_cache(self):
        """Напишите тесты, которые проверяют работу кэша."""

        self.client.force_login(self.user)
        self.client.post('/new/', {'text': 'new text for testing cash', 'group': self.group.id})
        response = self.client.get("/")
        self.assertNotContains(response, 'new text for testing cash')
        time.sleep(20)
        response_2 = self.client.get("/")
        self.assertContains(response_2, 'new text for testing cash')

    @override_settings(CACHES=TEST_CACHES)
    def test_follow_unfollow_authorized_user(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""

        self.client.force_login(self.user1)
        followers = Follow.objects.filter(author=self.user2.id).count()
        following = Follow.objects.filter(user=self.user1.id).count()
        self.assertEqual(followers, 0)
        self.assertEqual(following, 0)
        self.client.get(f"/{self.user2.username}/follow/")
        followers = Follow.objects.filter(author=self.user2).count()
        following = Follow.objects.filter(user=self.user1).count()
        self.assertEqual(followers, 1)
        self.assertEqual(following, 1)
        self.client.get(f"/{self.user2.username}/unfollow/")
        followers = Follow.objects.filter(author=self.user2).count()
        following = Follow.objects.filter(user=self.user1).count()
        self.assertEqual(followers, 0)
        self.assertEqual(following, 0)

    def test_check_new_post_from_follower(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан на него."""

        Follow.objects.create(user=self.user1, author=self.user2)
        self.client.force_login(self.user2)
        self.client.post("/new/", {"text": 'test follower text'})
        self.client.force_login(self.user1)
        response = self.client.get('/follow/')
        self.assertContains(response, 'test follower text')

    def test_authorized_user_comments_posts(self):
        """Только авторизированный пользователь может комментировать посты."""

        self.client.force_login(self.user1)
        self.client.post(f'/{self.user.username}/{self.post.id}/comment/',
                         {'text': 'new comment'})
        comment = Comment.objects.filter(post=self.post.id).last().text
        self.assertEqual(comment, 'new comment')

    def tearDown(self):
        # Clean up after each test
        self.user.delete()
        self.post.delete()
