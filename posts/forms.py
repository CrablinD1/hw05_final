from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {'text': 'Текст записи', 'group': 'Группа',
                  'image': 'Изображение'}
        help_texts = {
            'group': 'Выберите группу, в которой будет опубликован пост',
            'text': 'Введите текст публикации',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Комментарий'}
